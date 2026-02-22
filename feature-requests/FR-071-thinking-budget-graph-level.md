# Feature Request: FR-071 Graph-Level Thinking Budget

**Priority:** MEDIUM
**Type:** Feature
**Status:** Approved
**Effort:** 1 day
**Requested:** 2026-02-22
**Judged:** 2026-02-22

## Summary

Allow Anthropic extended-thinking `budget_tokens` to be declared in a graph's
`defaults:` block and optionally overridden per-node, so reasoning depth is configured
declaratively in YAML rather than hard-coded in Python.

## Problem

Anthropic's Claude 3.7+ models support extended thinking (`thinking: {type: enabled,
budget_tokens: N}`), which trades latency and cost for deeper reasoning.
Today there is no way to enable or size this budget in a graph YAML file — it requires
custom Python tooling outside the framework. This means:

- Multi-step reasoning graphs (analysis, code review, planning) cannot opt in.
- Different nodes in the same graph cannot use different reasoning depths.
- Users must bypass the YAML-first design and write Python to unlock the feature.

## Proposed Solution

### YAML interface

```yaml
# graph.yaml — graph-wide default
defaults:
  provider: anthropic
  model: claude-3-7-sonnet-20250219   # required; thinking only works on 3.7+
  thinking_budget: 8000               # budget_tokens; 0 or absent = disabled

nodes:
  plan:
    prompt: plan
    state_key: plan
    # inherits defaults.thinking_budget = 8000

  summarize:
    prompt: summarize
    state_key: summary
    thinking_budget: 0    # explicit opt-out for this node
```

### Implementation

1. **`GraphConfigSchema` / `NodeConfig`** (`yamlgraph/models/graph_schema.py`):
   Add `thinking_budget: int | None = Field(default=None)` to both models.
   Apply a Pydantic validator: value must be `None`, `0`, or `≥ 1024`.
   Values in range `1–1023` raise `ValueError` (Anthropic API minimum is 1024).
   `None` means "not set" (inherit or disabled); `0` means "disabled explicitly".

2. **`create_llm`** (`yamlgraph/utils/llm_factory.py`):
   Add `thinking_budget: int | None = None` parameter. When `thinking_budget ≥ 1024`
   and provider is `"anthropic"`:
   - Force `temperature = 1` (Anthropic API requirement for extended thinking).
     **Temperature override MUST happen before `cache_key` is computed** (see ISSUE-5
     resolution below) so all thinking-enabled calls for the same
     `(provider, model, max_tokens, thinking_budget)` share a single cache entry
     regardless of the requested temperature. If the caller supplied a different
     temperature, emit `logger.warning` after the override.
   - Pass `thinking={"type": "enabled", "budget_tokens": thinking_budget}` to `ChatAnthropic`.
   Raise `ValueError` if `thinking_budget ≥ 1024` and provider is not `"anthropic"`.

3. **Node factories** (`yamlgraph/node_factory/llm_nodes.py`):
   Resolve the effective `thinking_budget` using the same cascade as `temperature` /
   `max_tokens`: node value → graph default → `None`. Pass it to `create_llm`.

4. **Linter** (`yamlgraph/cli/graph_validate.py`):
   Emit a warning when:
   - `thinking_budget > 0` is combined with a non-Anthropic provider.
   - `thinking_budget > 0` is combined with a model name that does not contain any of
     the known thinking-capable substrings (see ISSUE-4 resolution below), **only when
     the model name is explicitly set** (not `None`/default).
   - `0 < thinking_budget < 1024` (below Anthropic minimum).
   - `thinking_budget > 0` and explicit `temperature != 1` (will be silently overridden).

5. **Cache key** (`llm_factory.py`):
   Include `thinking_budget` in `cache_key` so thinking/non-thinking instances for the
   same model are not aliased. The cache key is computed **after** the temperature
   override, so the key always uses `temperature=1` for thinking-enabled calls.

### Temperature handling

Anthropic's API **requires `temperature=1`** for extended thinking. When
`thinking_budget ≥ 1024` and `provider = "anthropic"`, `create_llm`:
1. Records whether the incoming temperature differs from `1`.
2. Overrides temperature to `1`.
3. Computes the cache key (now using the overridden `temperature=1`).
4. If temperature was overridden, emits `logger.warning`.

The linter emits a separate warning for explicit `temperature != 1` + `thinking_budget > 0`
so authors can fix their YAML rather than relying on silent override.

### Non-goals

- No support for reading thinking blocks from the response (Anthropic streams them
  separately; they are currently invisible to YAMLGraph — that is a separate FR).
- No environment-variable override (graph YAML is the single source of truth for
  reasoning depth; token cost is a graph-design decision, not a deployment secret).

## Acceptance Criteria

- [ ] `thinking_budget` field accepted in `defaults:` and per-node config; validated as
  `None`, `0`, or `int ≥ 1024` — values in range `1–1023` raise `ValueError`.
- [ ] When `thinking_budget ≥ 1024` and `provider = anthropic`, `ChatAnthropic` is
  created with `thinking={"type": "enabled", "budget_tokens": N}` and `temperature=1`.
- [ ] Temperature override to `1` happens **before** cache key is computed; all
  thinking-enabled calls for the same `(provider, model, max_tokens, thinking_budget)`
  share a single cache entry regardless of the originally requested temperature.
- [ ] If the resolved temperature differs from `1`, `logger.warning` is emitted (not an error).
- [ ] Node-level `thinking_budget` overrides graph-level default; `0` disables it even
  when the default is non-zero.
- [ ] `create_llm` raises `ValueError` if `thinking_budget ≥ 1024` and provider is not
  `"anthropic"`.
- [ ] Linter emits warnings for: non-Anthropic provider + budget > 0; explicitly-set
  model name not matching a thinking-capable substring + budget > 0;
  `0 < budget < 1024`; explicit `temperature != 1` + budget > 0.
- [ ] `thinking_budget` is included in the LLM cache key (after temperature override)
  so thinking/non-thinking instances remain distinct.
- [ ] Unit tests cover: budget enabled (mock), budget disabled (0), node-level override,
  non-Anthropic provider raises, budget in range 1–1023 raises, cache-key isolation,
  temperature auto-override warning, cache-key uses overridden temperature.
- [ ] Integration test (guarded by `ANTHROPIC_API_KEY`) runs a graph with
  `thinking_budget: 1024` and asserts the node completes successfully.
- [ ] `reference/graph-yaml.md` updated with `thinking_budget` in the `defaults` and
  node-config tables.
- [ ] Tests tagged `@pytest.mark.req("REQ-YG-083")`.
- [ ] `REQ-YG-083` added to `ARCHITECTURE.md` capability and requirement tables.
- [ ] `ALL_REQS` range in `scripts/req_coverage.py` extended to `range(1, 84)` and
  `CAPABILITIES` dict updated.

## Requirements Mapping

| ID | Description |
|---|---|
| REQ-YG-083 | `thinking_budget` YAML field on graph `defaults` and per-node; validated as `0` or `≥ 1024`; passed as `thinking={"type":"enabled","budget_tokens":N}` to `ChatAnthropic` with forced `temperature=1` (override before cache key); raises on non-Anthropic provider; included in LLM cache key |

## Alternatives Considered

| Alternative | Why rejected |
|---|---|
| Environment variable (`THINKING_BUDGET=8000`) | Reasoning depth is a graph-design choice, not a deployment secret; per-node overrides are impossible with a global env var |
| New node type (`type: thinking`) | Overkill; `thinking_budget` is an LLM parameter, not a structural change — adding it to existing LLM nodes is minimal and consistent |
| Expose thinking-block content in state | Out of scope; Anthropic streams thinking blocks separately; capturing them requires streaming changes (separate FR) |
| Hardcode via `model_kwargs` pass-through | `model_kwargs` is not validated and leaks implementation details; a typed field preserves the contract and enables linting |
| Strict raise on `temperature != 1` | Degrades gracefully like other YAMLGraph parameters; auto-override with warning is friendlier and consistent with framework style |

## Judge Resolutions

### ISSUE-1: Temperature must be 1 when thinking is enabled ✓ Resolved
Auto-override strategy adopted: when `thinking_budget ≥ 1024` and `provider = anthropic`,
`create_llm` forces `temperature = 1` and emits `logger.warning` if the value differed.
Linter additionally warns on explicit `temperature != 1` + `thinking_budget > 0`.
Acceptance criteria updated accordingly.

### ISSUE-2: `budget_tokens` minimum is 1024, not 1 ✓ Resolved
Pydantic validator on `thinking_budget` rejects values in range `1–1023` with `ValueError`.
Linter emits a warning for `0 < thinking_budget < 1024`. Field annotation changed from
`ge=0` to the custom validator. Acceptance criteria updated with a test for the 1–1023 range.

### ISSUE-3: Wrong file references ✓ Resolved
Removed reference to non-existent `agent_nodes.py`; only `llm_nodes.py` needs updating.
Fixed linter path from non-existent `lint_commands.py` to the actual `graph_validate.py`.

### ISSUE-4: Pre-3.7 model allowlist not specified ✓ Resolved
Linter uses a **positive allowlist** of known thinking-capable model name substrings.
Initial allowlist:

```python
THINKING_CAPABLE_MODEL_SUBSTRINGS = ["claude-3-7", "claude-3-8"]
```

New entries are added as Anthropic releases thinking-capable models. The warning fires
only when `thinking_budget > 0`, the model name is explicitly set (not `None`/default),
**and** the model name does not contain any allowlist substring. When the model is
`None`/default, no warning is emitted (the factory selects a default that may or may
not support thinking; runtime will catch invalid combinations).

### ISSUE-5: Temperature override must precede cache key construction ✓ Resolved
`create_llm` must execute in this order:
1. Resolve `temperature` (apply default if `None`).
2. If `thinking_budget ≥ 1024` and `provider = "anthropic"`: record original temperature,
   set `temperature = 1`, note override for warning.
3. Compute `cache_key = (selected_provider, selected_model, temperature, max_tokens, thinking_budget)`.
4. Check cache; return cached instance if hit.
5. Build LLM with the (possibly overridden) `temperature`.
6. Emit `logger.warning` if temperature was overridden.

This ensures that `(temperature=0.5, thinking_budget=8000)` and
`(temperature=1, thinking_budget=8000)` produce identical cache keys and share one LLM instance.

## Related

- `yamlgraph/utils/llm_factory.py` — `create_llm` and LLM cache
- `yamlgraph/models/graph_schema.py` — `NodeConfig` and `GraphConfigSchema`
- `yamlgraph/node_factory/llm_nodes.py` — node temperature/provider resolution
- `yamlgraph/cli/graph_validate.py` — linter (actual path)
- `reference/graph-yaml.md` — documentation target (`defaults` and node-config tables)
- Anthropic docs: [Extended thinking](https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking)
