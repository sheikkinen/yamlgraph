# Feature Request: Copilot Node — Node-Level Model Selection

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-04-21
**FR:** FR-266

## Summary

Support `model` as a top-level node config key for copilot nodes, consistent with LLM nodes. Fall back to `defaults.model` from graph metadata when not specified. `cli_flags.model` continues to work as the highest-priority override.

## Value Statement

Graph authors can use the same `model` and `defaults.model` convention for copilot nodes as they do for LLM nodes, eliminating inconsistency and enabling DRY model configuration across mixed graphs.

## Problem

Copilot nodes support model selection only via `cli_flags.model`, which is a Copilot CLI implementation detail:

```yaml
nodes:
  plan:
    type: copilot
    cli_flags:
      model: claude-sonnet-4-5  # buried in cli_flags
```

LLM nodes use `model` at the node level and inherit from graph `defaults`:

```yaml
defaults:
  model: claude-sonnet-4-5

nodes:
  generate:
    type: llm
    model: gpt-4o          # node-level override
    provider: openai
```

This inconsistency has two consequences:

1. **No defaults fallback** — `create_copilot_node()` does not receive `effective_defaults` from `node_compiler.py`, so `defaults.model` is unreachable. Every copilot node must hardcode its model in `cli_flags`.
2. **Inconsistent interface** — Graph authors must remember that copilot nodes use `cli_flags.model` while every other node type uses top-level `model`.

### Root Cause

`_compile_copilot_node()` in `node_compiler.py` (line 231) does not pass `ctx.effective_defaults` to the factory, unlike `_compile_llm_node()` (line 262) which passes it as the third argument. The copilot node factory (`copilot_node.py:138`) has no `defaults` parameter and reads model exclusively from `cli_flags.get("model")` (line 231).

## Proposed Solution

### Priority Order

```
cli_flags.model > node-level model > defaults.model > (omit --model flag)
```

### YAML Interface

```yaml
defaults:
  model: claude-sonnet-4-5

nodes:
  plan:
    type: copilot
    prompt: prompts/plan
    model: claude-sonnet-4-5    # top-level, consistent with LLM nodes
    cli_flags:
      allow_all_paths: true

  judge:
    type: copilot
    prompt: prompts/judge
    # inherits defaults.model automatically
    cli_flags:
      allow_all_paths: true

  special:
    type: copilot
    prompt: prompts/special
    model: gpt-4o               # node-level override
    cli_flags:
      allow_all_paths: true
      model: claude-opus-4      # highest priority override
```

### Implementation

Three files change:

#### 1. `yamlgraph/models/graph_schema.py` — Add `model` field to `NodeConfig`

`NodeConfig` already has `provider: str | None` (line 101) but lacks `model`. Add it:

```python
provider: str | None = Field(default=None)
model: str | None = Field(default=None, description="Model name override")
```

This benefits all node types, not just copilot — LLM nodes currently read `model` from the raw config dict via `node_config.get("model")` in `llm_nodes.py:141`. Adding the field to the Pydantic schema makes it validated and documented.

#### 2. `yamlgraph/node_compiler.py` — Pass `effective_defaults` to copilot factory

```python
# Before (line 232-238)
def _compile_copilot_node(ctx: NodeCompileContext) -> None:
    node_fn = create_copilot_node(
        ctx.node_name,
        ctx.node_config,
        graph_path=ctx.config.source_path,
        prompts_dir=ctx.prompts_dir,
        prompts_relative=ctx.prompts_relative,
    )

# After
def _compile_copilot_node(ctx: NodeCompileContext) -> None:
    node_fn = create_copilot_node(
        ctx.node_name,
        ctx.node_config,
        defaults=ctx.effective_defaults,
        graph_path=ctx.config.source_path,
        prompts_dir=ctx.prompts_dir,
        prompts_relative=ctx.prompts_relative,
    )
```

#### 3. `yamlgraph/node_factory/copilot_node.py` — Resolve model with priority chain

Add `defaults` parameter to `create_copilot_node()` and resolve model before passing to `_execute_cli()`:

```python
def create_copilot_node(
    node_name: str,
    config: dict[str, Any],
    defaults: dict[str, Any] | None = None,   # NEW
    graph_path: Path | None = None,
    prompts_dir: Path | None = None,
    prompts_relative: bool = False,
) -> Callable[[GraphState], dict]:
    ...
    cli_flags = config.get("cli_flags", {})
    defaults = defaults or {}

    # Resolve model: cli_flags.model > node-level model > defaults.model
    resolved_model = (
        cli_flags.get("model")
        or config.get("model")
        or defaults.get("model")
    )

    # Inject resolved model into cli_flags for _execute_cli
    if resolved_model:
        cli_flags = {**cli_flags, "model": resolved_model}
    ...
```

The `CopilotResult.model` field (line 273) automatically picks up the resolved value since it reads from `cli_flags.get("model")`.

## Acceptance Criteria

- [ ] `NodeConfig` has a `model: str | None` field in `graph_schema.py`
- [ ] `create_copilot_node()` accepts a `defaults` parameter
- [ ] `_compile_copilot_node()` passes `ctx.effective_defaults` to the factory
- [ ] Model resolution follows: `cli_flags.model` > node-level `model` > `defaults.model` > omit
- [ ] `CopilotResult.model` reflects the resolved model, regardless of source
- [ ] Existing `cli_flags.model` behavior unchanged (no regression)
- [ ] Test: node-level `model` passed as `--model` flag to CLI
- [ ] Test: `defaults.model` used when no node-level or cli_flags model
- [ ] Test: `cli_flags.model` overrides node-level `model`
- [ ] Test: no `--model` flag when no model specified anywhere
- [ ] Tests tagged with `@pytest.mark.req("REQ-YG-265")`
- [ ] REQ-YG-265 added to `ARCHITECTURE.md` and `scripts/req_coverage.py`

## Alternatives Considered

### 1. Only support node-level `model`, no defaults fallback

Simpler change (no `defaults` plumbing) but misses the primary value: DRY model configuration via `defaults.model`. Graph authors still need to repeat model on every copilot node.

### 2. Remove `cli_flags.model` entirely

Breaking change. Existing graphs use `cli_flags.model` (documented in FR-081). The priority chain preserves it as an escape hatch for Copilot CLI-specific model identifiers.

### 3. Add a linter warning instead of runtime support

FR-119 already warns about misplaced top-level `provider`/`model`. A linter warning for copilot nodes would tell users to use `cli_flags.model` — the opposite of the desired direction. The fix is to make the runtime support the consistent pattern.

## Related

- **FR-081** — Copilot Node Type (original implementation; `cli_flags.model` introduced here)
- **FR-119** — W016 lint warning for top-level provider/model (adjacent concern)
- **REQ-YG-087** — Copilot node CLI backend requirement
- `yamlgraph/node_factory/llm_nodes.py:141` — LLM model resolution pattern (reference implementation)
- `tests/unit/test_copilot_node.py::test_cli_flags_passed` — Existing test for `cli_flags.model`

## Research Brief

### Competitive Landscape

All five major competing frameworks implement **consistent per-node model selection** across all node/agent types. YAMLGraph's mixed approach (`model:` for LLM nodes, `cli_flags.model` for copilot nodes) has no parallel in the ecosystem.

| Framework | Stars | Model Config | Inheritance Depth | Consistent? |
|-----------|-------|-------------|-------------------|-------------|
| **LangGraph** | 29.8K | `ChatModel` instance per node | Implicit (composition) | ✅ Uniform |
| **CrewAI** | 49.4K | `Agent(llm_config={"model": ...})` | 3-level (agent > config file > env) | ✅ Uniform |
| **AutoGen** | 57.3K | `Agent(model_client=...)` | 3-level (agent > JSON config > defaults) | ✅ Uniform |
| **Google ADK** | — | `Agent(model=...)` | 2-level (param > env) | ✅ Uniform |
| **OpenAI Agents SDK** | — | `Agent(model=...)` | 2-level (param > env) | ✅ Uniform |
| **YAMLGraph (current)** | — | Mixed: `model:` vs `cli_flags.model` | 4-level LLM / 1-level copilot | ❌ Split |

Every competitor treats model selection as a **top-level, explicitly named parameter**, never buried in a flags dictionary. Documenting the inconsistency would not resolve it — the gap is in runtime behavior, not documentation.

### Existing Abstractions

**LLM node model resolution** — the reference pattern already exists:
- `yamlgraph/node_factory/llm_nodes.py:142`: `model=node_config.get("model", defaults.get("model"))` — 4-level chain (node > defaults > prompt > provider default)
- `yamlgraph/node_compiler.py:258-267`: `_compile_llm_node()` passes `ctx.effective_defaults` to the factory

**Copilot node — the gap:**
- `yamlgraph/node_factory/copilot_node.py:230-232`: reads model **only** from `cli_flags.get("model")` — 1-level chain
- `yamlgraph/node_compiler.py:231-240`: `_compile_copilot_node()` does **not** pass `effective_defaults`

**Schema gap:**
- `yamlgraph/models/graph_schema.py:101`: `NodeConfig` has `provider: str | None` but **no `model` field**. The `extra="allow"` config (line 168) silently accepts `model:` in YAML without validation.

**Related FRs:**
- `feature-requests/FR-081-copilot-node.md` — original copilot implementation; `cli_flags.model` was the only model path by design
- `feature-requests/FR-119-lint-provider-model-toplevel.md` — W016 lint warning catches graph-level `provider`/`model` outside `defaults:` block; companion issue to this FR

**Existing tests:**
- `tests/unit/test_copilot_node.py::test_cli_flags_passed` — verifies `--model` flag from `cli_flags` (REQ-YG-087)
- `tests/unit/test_node_model_override.py` — 8 tests for LLM node model override chain

**Real-world evidence of the gap:**
- `.chaplain/graphs/copilot/graph.yaml` sets `defaults.model: claude-haiku-4-5` but copilot nodes in the same graph **ignore it**, falling back to the Copilot CLI default instead

### Diary Precedents

| Diary Entry | Trap/Pattern | Relevance |
|-------------|-------------|-----------|
| `2026-04-19-reflection-fr-252-python-node-variables.md` | **"Feature parity is a boundary contract"** — when a capability exists for most node types but not all, the missing type is a latent defect | Directly applicable: `model:` exists for LLM nodes but not copilot |
| `2026-04-19-reflection-fr-069-map-node-timeout.md` | **"Cross-cutting concerns belong at compile-time wrapper"** — implement at `node_compiler` level, not per-node | Model resolution should be handled uniformly at the compiler boundary |
| `2026-04-18-reflection-fr-235-compile-time-pipeline-templates.md` | **"Normalize at the boundary"** — expansion at compile time, not runtime | Model fallback resolution should occur during `create_copilot_node()`, not at CLI execution |
| `2026-04-02-reflection-fr-214-extract-variables-nested-set.md` | **`downstream_fix` trap** — patching callers instead of normalizing at boundary | Model resolution belongs at node compilation boundary, not in per-node handlers |
| `2026-03-07-inquisitor-audit-xiv.md` | Provider/model moved to `defaults` block in copilot graph examples | Evidence that `defaults` fallback was already the intended configuration pattern |
| `2026-03-12-philosopher-fr185.md` | Copilot node migration exposed normalization cascades | Supports need for consistent, boundary-normalized model handling |

**Graduated heuristic:** The `the_one_law` ("normalize at the boundary where external data enters") applies directly — model configuration enters at YAML parse time and should be resolved at compile time in `node_compiler.py`, not delegated to per-node runtime logic.

### Usage Evidence

- **Graphs using `type: copilot`:** 15 files (`.chaplain/graphs/`, `examples/demos/`, `examples/ebook/`, `examples/bugfix/`)
- **Graphs using `defaults.model`:** 8 files — all effective only for LLM nodes; copilot nodes in the same graphs silently ignore the default
- **Real-world use cases beyond the proposal:**
  - `.chaplain/graphs/enforce/graph.yaml` — multi-step enforcement pipeline with copilot nodes that would benefit from centralized model config
  - `examples/ebook/graph-ch*.yaml` (9 files) — tutorial chapters where DRY model configuration via `defaults.model` would eliminate repetition
  - Mixed graphs (copilot + LLM nodes sharing `defaults.model`) — the primary scenario where the inconsistency creates user confusion

### Classification Signal

- **Abstraction level:** primitive — consistent model selection is a core graph compilation contract, not a niche integration
- **Recommended approach:** build — 3-file surgical change (~15 lines net); the reference implementation already exists in LLM nodes; documenting the inconsistency would not resolve it since the gap is in runtime behavior
- **Key risk:** Low — the `cli_flags.model > node.model > defaults.model` priority chain preserves full backward compatibility; existing `cli_flags.model` usage continues to win
