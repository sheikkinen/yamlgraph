# Feature Request: Refactor create_node_function God Factory

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 3 days
**Requested:** 2026-04-12

## Summary

Split `create_node_function` (C901=35) and its nested `node_fn` (C901=26) in
`yamlgraph/node_factory/llm_nodes.py` into composable, independently testable
phases — each below C901=10.

## Value Statement

Contributors can reason about LLM node execution phases (config resolution,
verification, routing, error handling) independently, reducing defect
surface and enabling targeted unit tests for each phase.

## Problem

`yamlgraph/node_factory/llm_nodes.py:create_node_function` (lines 51–321,
271 lines) is the highest-complexity function in the codebase:

| Metric | `create_node_function` | inner `node_fn` |
|--------|------------------------|-----------------|
| Ruff C901 | **35** (3.5× threshold of 10) | **26** (2.6×) |
| Radon CC | 10 (grade B — **passes gate**) | — |

The Radon CC gate at grade D never fires because it counts branches, not
nesting depth. C901 catches the problem; the gate does not block it.

### What the outer function does (7 jobs)

1. Prompt resolution (path, relative, dir)
2. Streaming dispatch (early return to `create_streaming_node`)
3. Output model resolution (`parse_json` vs Pydantic vs `None`)
4. LLM parameter defaults (temperature, provider, model, tokens, thinking)
5. State/variable config (`state_key`, `variables`, `requires`)
6. Error-handling config (`on_error`, retries, fallback, routes)
7. Verification gate config (`verification_question`, `on_fail`, `max_retries`)

### What the inner `node_fn` does (10-phase gauntlet, lines 152–321)

1. Loop limit check → early return
2. Skip-if-exists → early return
3. Requirements check → early return with error
4. Variable resolution
5. LLM execution via `attempt_execute()`
6. JSON extraction (if `parse_json`)
7. Verification gate with retry loop (highest nesting depth, lines 208–254)
8. Router routing with `isinstance` type dispatch (lines 263–282)
9. State update assembly
10. Error handling — 5-way if/elif (`skip`/`fail`/`retry`/`fallback`/default)

The verification retry loop (phase 7) duplicates the extract-then-verify
pattern from the main path — jscpd-flagged duplication.

## Proposed Solution

### Phase 1 — Extract config resolution

```python
@dataclass(frozen=True)
class LLMNodeConfig:
    """Resolved, validated config for a single LLM/router node."""
    prompt_name: str
    state_key: str
    provider: str | None
    model: str | None
    temperature: float
    max_tokens: int | None
    thinking_budget: int | None
    output_model: type | None
    parse_json: bool
    variable_templates: dict
    requires: list[str]
    on_error: str | None
    max_retries: int
    fallback_provider: str | None
    routes: dict
    default_route: str | None
    route_field: str | None
    loop_limit: int | None
    skip_if_exists: bool
    verification_question: str | None
    verification_on_fail: str | None
    verification_max_retries: int
    prompts_dir: Path | None
    prompts_relative: bool

def resolve_llm_node_config(node_name: str, node_config: dict, defaults: dict, graph_path: Path | None) -> LLMNodeConfig:
    """Extract and validate all config — one job, no side effects."""
    ...
```

### Phase 2 — Extract execution phases into functions

```python
def _execute_with_retry(cfg: LLMNodeConfig, variables: dict, provider: str | None) -> tuple[Any, Exception | None]: ...
def _apply_verification(cfg: LLMNodeConfig, result: Any, state: dict) -> tuple[Any, PipelineError | None]: ...
def _resolve_route(cfg: LLMNodeConfig, result: Any) -> str | None: ...
def _handle_error(cfg: LLMNodeConfig, error: Exception, state: dict, loop_counts: dict) -> dict: ...
```

### Phase 3 — Slim `node_fn` becomes orchestrator only

```python
def node_fn(state: dict) -> dict:
    if loop_limit_reached(...): return ...
    if should_skip(...): return ...
    if req_error := check_requirements(...): return ...
    variables = resolve_node_variables(cfg.variable_templates, state)
    result, error = _execute_with_retry(cfg, variables, cfg.provider)
    if error: return _handle_error(cfg, error, state, loop_counts)
    result, violation = _apply_verification(cfg, result, state)
    if violation and cfg.verification_on_fail == "halt": raise ...
    route = _resolve_route(cfg, result)
    return _build_state_update(cfg, result, route, loop_counts, violation)
```

## Acceptance Criteria

- [x] `LLMNodeConfig` frozen dataclass encapsulates all resolved config
- [x] `resolve_llm_node_config()` is a pure function (no graph mutations, no closures)
- [x] `_apply_verification()` extracted — eliminates retry-loop duplication
- [x] `_handle_error()` extracted — 5-way dispatch is a single testable function
- [x] `_resolve_route()` extracted — `isinstance` type dispatch is a single testable function
- [x] Ruff C901 passes for all functions in `llm_nodes.py` (≤ 10)
- [ ] Radon CC gate tightened to grade B (≤ 10) — currently passes at grade D
- [x] All existing LLM node tests pass unchanged
- [x] New unit tests cover each extracted phase independently
- [x] REQ-YG-223 added to ARCHITECTURE.md and CAP-02

## Alternatives Considered

1. **`node_fn` as a class with `__call__`**: More OO, but config already solved by dataclass; not worth the ceremony.
2. **LangGraph's built-in node decorators**: Doesn't address internal complexity.
3. **Leave as-is**: C901=35 already blocks `ruff --select C901` in CI if enabled; technical debt compounds every time a new execution phase is added.

## Related

- `yamlgraph/node_factory/llm_nodes.py` — The function to split
- FR-220 — Refactored `compile_node` dispatch (registry pattern); this FR targets the execution factory
- `tests/unit/test_node_factory.py` — Existing LLM node branch coverage
- REQ-YG-007 — "Compile individual nodes" (CAP-02)
