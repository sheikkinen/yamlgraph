# Feature Request: FR-384 Cost profile / model tiering

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 1.5 days
**Requested:** 2026-05-14

## Summary

Add `cost_profile: economy | balanced | premium` to graph `defaults:` and a
`YAMLGRAPH_COST_PROFILE` environment variable override. Each profile maps to a
set of default models per provider. Add a linter check that warns when Opus-tier
models are used without an explicit justification comment.

## Value Statement

Graph authors and operators can switch an entire pipeline to cheaper models
with one env var, and the linter prevents accidental expensive model drift
without documented justification.

## Problem

Token costs are diverging. Frontier models (Opus 4.7: $5/$25 MTok) cost 5–25×
more than task-specific models (Haiku 4.5: $1/$5 MTok). Currently:

1. **No global override exists.** Every graph that doesn't specify `model:` uses
   the provider's default (set in `yamlgraph/config.py`). Switching all graphs
   to a cheaper model requires editing each YAML file.

2. **No drift prevention exists.** Nothing stops a node from specifying
   `model: claude-opus-4-7` without justification. The linter does not check
   model cost tier.

3. **No operator lever.** A deployment operator cannot run the same graph corpus
   at economy tier without modifying graph files — violating the principle that
   config is truth.

## Research

### Existing model defaults

`yamlgraph/config.py` has:
```python
# Default models per provider (override with {PROVIDER}_MODEL env var)
```
Per-provider env vars exist (`ANTHROPIC_MODEL`, etc.) but no cross-provider
`COST_PROFILE` concept.

### Model tier mapping

| Profile | Anthropic | OpenAI | Google | Mistral |
|---------|-----------|--------|--------|---------|
| economy | claude-haiku-4-5 | gpt-5-mini | gemini-2.0-flash | mistral-small-latest |
| balanced | claude-sonnet-4-6 | gpt-5.4 | gemini-2.0-pro | mistral-large-latest |
| premium | claude-opus-4-7 | gpt-5.5 | gemini-2.0-ultra | mistral-large-latest |

Default (no profile set): `balanced` — preserves existing behavior.

## Proposed Solution

### YAML interface

```yaml
# graph-level default profile
defaults:
  cost_profile: economy     # economy | balanced | premium

# node-level override (explicit model always wins)
nodes:
  reason:
    type: llm
    prompt: reason
    model: claude-opus-4-7  # cost: justified — extended thinking required
    state_key: reasoning
```

### Environment variable override

```bash
# Override all graphs to economy tier at deploy time
YAMLGRAPH_COST_PROFILE=economy yamlgraph graph run graphs/chaplain.yaml
```

Priority order for model resolution:
1. Node-level explicit `model:` field (unchanged)
2. Graph-level `defaults.cost_profile` mapping
3. `YAMLGRAPH_COST_PROFILE` env var mapping
4. Per-provider env var (`ANTHROPIC_MODEL`, etc.)
5. Config default (current behavior)

### Linter check: Opus-without-justification

```
WARNING: node 'analyze' uses claude-opus-4-7 without justification.
  If Opus is required, add a comment: # cost: justified — <reason>
  Consider claude-sonnet-4-6 ($3/$15 vs $5/$25 per MTok).
```

The check scans for `model:` values matching premium tier and looks for
a `# cost: justified` comment on the preceding line. If absent, emit WARNING
(not error — justification is advisory, not blocking).

### Files to modify

| File | Change |
|------|--------|
| `yamlgraph/config.py` | Add `COST_PROFILE` env var, profile→model mapping dict |
| `yamlgraph/utils/llm_factory.py` | Resolve model from profile in `create_llm()` |
| `yamlgraph/models/graph_schema.py` | Add `cost_profile: str | None` to `GraphDefaults` |
| `yamlgraph/linter/checks_providers.py` | Opus-without-justification lint check |
| `reference/graph-yaml.md` | Document `cost_profile` in defaults |
| `reference/cli.md` | Document `YAMLGRAPH_COST_PROFILE` env var |
| `tests/unit/test_cost_profile.py` | Unit tests |

## Acceptance Criteria

- [ ] AC-01: Graph with `defaults.cost_profile: economy` and no explicit `model:`
  on nodes resolves to Haiku 4.5 (Anthropic) without code change
- [ ] AC-02: `YAMLGRAPH_COST_PROFILE=economy` env var overrides graph-level profile
- [ ] AC-03: Explicit `model:` on a node always wins over profile — profile is
  default, not override
- [ ] AC-04: Linter emits WARNING (not error) for `model: claude-opus-4-7` (or
  equivalent premium tier) without `# cost: justified` comment
- [ ] AC-05: Linter emits no warning when `# cost: justified` comment is present
  on the line before the `model:` field
- [ ] AC-06: Default behavior unchanged when no `cost_profile` is set (balanced
  tier = current model defaults)
- [ ] AC-07: `YAMLGRAPH_COST_PROFILE=balanced` produces identical behavior to
  no profile set
- [ ] AC-08: Profile mapping is documented in `reference/graph-yaml.md`
- [ ] Tests added with `@pytest.mark.req("REQ-YG-XXX")`
- [ ] New requirement added to `ARCHITECTURE.md` and `scripts/req_coverage.py`
- [ ] Changelog fragment in `changelog/unreleased/`
- [ ] Diary reflection in `docs/diary/`

## Constraints

1. `balanced` profile default preserves 100% backward compatibility.
2. Profile mapping is static configuration (dict in `config.py`), not dynamic.
   Model names in the mapping must be updated manually when providers release
   new models — this is intentional governance, not a bug.
3. Linter check is WARNING, not ERROR. Blocking premium models outright would
   prevent legitimate use cases (extended thinking, complex reasoning tasks).
4. The `cost_profile` field does not affect `type: copilot` nodes — they have
   their own model selection via Copilot CLI or `backend: api` (FR-383).
5. Scope: Anthropic, OpenAI, Google, Mistral. Other providers (Replicate,
   DeepSeek, xAI, Inception, LMStudio) are excluded from the tier mapping
   in v1 — they do not fit the standard 3-tier structure cleanly.

## Alternatives Considered

### Per-provider env vars only (current state)
`ANTHROPIC_MODEL=claude-haiku-4-5` already works per provider. The gap is:
(a) no cross-provider profile concept, (b) no linter governance, (c) no
YAML-level declaration.

### Enforce economy tier as default
Rejected: would break existing graphs and surprise users. Balanced (current
behavior) is the safe default.

### Cost estimation before execution
A pre-execution cost estimator node (one of the plan seeds) could route to
the cheapest capable tier automatically. More powerful but much more complex —
deferred to a future FR.

## Related

- `docs/plan-token-cost-mitigation.md` — Priority 4 in the mitigation plan
- FR-382 — Prompt caching (Priority 1, land first)
- FR-383 — Copilot backend: api (Priority 2)
- FR-381 — Batch API (Priority 3)
- `yamlgraph/utils/llm_factory.py` — model resolution target
- `yamlgraph/linter/checks_providers.py` — lint check target
- Seed: "Could a cost estimator node route to economy tier when the task is simple?"
