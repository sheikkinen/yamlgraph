# Feature Request: Runtime Repair Metadata on PipelineError

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Rejected
**Effort:** 1.5 days
**Requested:** 2026-05-18
**Judged:** 2026-05-18

## Summary

Add structured `repair` metadata and stable diagnostic codes to `PipelineError`, enabling `on_error` handlers and agent nodes to apply deterministic recovery actions before escalating to LLM re-prompting.

## Value Statement

Graph nodes that fail at runtime get machine-actionable recovery hints — turning "retry and hope" into "apply named fix, then retry only if deterministic repair fails."

## Problem

Current `PipelineError` provides:
```python
PipelineError(
    type=ErrorType.VALIDATION_ERROR,
    message="1 validation error for Analysis\nscore\n  Input should be a valid integer",
    node="analyze",
    retryable=False,
    details={"exception_type": "ValidationError"}
)
```

The `on_error: retry` handler blindly re-executes. The `on_error: fallback` handler switches providers. Neither uses the structured information about *what went wrong* to attempt a cheaper deterministic fix first.

When the error is "LLM returned score as string '8' instead of int 8", the correct fix is type coercion — not a full LLM re-prompt costing 1000+ tokens.

## Proposed Solution

### Extended PipelineError:

```python
class PipelineError(BaseModel):
    type: ErrorType
    code: str = Field(default="RT-000")  # NEW: stable runtime diagnostic code
    message: str
    node: str
    retryable: bool
    repair: RepairAction | None = None  # NEW: reuse from FR-407
    details: dict[str, Any]
```

### Runtime diagnostic code registry:

| Code | ErrorType | repair.id | Meaning |
|------|-----------|-----------|---------|
| RT-001 | STATE_ERROR | `inject-default` | Required state key missing |
| RT-002 | VALIDATION_ERROR | `coerce-field-type` | LLM output has correct value, wrong type |
| RT-003 | VALIDATION_ERROR | `retry-with-schema` | LLM output structurally wrong |
| RT-004 | LLM_ERROR | `wait-and-retry` | Rate limit / transient API error |
| RT-005 | LLM_ERROR | `switch-provider` | Provider down, use fallback |
| RT-006 | PROMPT_ERROR | `resolve-prompt-path` | Prompt file not found at expected path |
| RT-007 | VERIFICATION_ERROR | `relax-threshold` | Output almost passes verification |
| RT-008 | TIMEOUT_ERROR | `increase-timeout` | Node exceeded time limit |
| RT-009 | GUARD_ERROR | `skip-guarded-node` | Pre/post guard failed |

### Enhanced error construction:

```python
@classmethod
def from_exception(cls, e: Exception, node: str, ...) -> "PipelineError":
    # Existing type inference...

    # NEW: Infer repair action from exception details
    repair = _infer_repair(e, error_type)
    code = _infer_code(e, error_type)

    return cls(
        type=error_type,
        code=code,
        message=str(e),
        node=node,
        retryable=retryable,
        repair=repair,
        details={"exception_type": type(e).__name__},
    )
```

### New error handling strategy: `on_error: auto_repair`

```yaml
nodes:
  analyze:
    type: llm
    prompt: analyze
    on_error: auto_repair  # Try deterministic repair first, then retry
    max_retries: 2
```

Execution flow:
1. Node fails → `PipelineError` with `repair` populated
2. If `repair.id` has a registered handler → apply deterministic fix
3. If fix succeeds → return result (no LLM call)
4. If fix fails or no repair available → fall through to `retry` behavior

### Repair handlers for common cases:

```python
# yamlgraph/error_handlers.py (or new repairs.py)
RUNTIME_REPAIRS: dict[str, Callable] = {
    "coerce-field-type": _coerce_field_type,      # int("8") → 8
    "inject-default": _inject_default_state,       # None → ""
    "retry-with-schema": _add_schema_to_prompt,    # Inject schema reminder
    "wait-and-retry": _exponential_backoff,        # Already exists, now named
}
```

## Acceptance Criteria

- [ ] `PipelineError.code` field added with `RT-XXX` codes
- [ ] `PipelineError.repair` field added (reuses `RepairAction` from FR-407)
- [ ] `from_exception()` infers repair action for validation errors (coerce-field-type)
- [ ] `from_exception()` infers repair action for state errors (inject-default)
- [ ] `on_error: auto_repair` strategy implemented
- [ ] At least 3 deterministic repair handlers registered
- [ ] LangSmith traces include `repair.id` when applied
- [ ] Tests: repair applied → no LLM re-prompt; repair fails → falls through to retry
- [ ] Existing `on_error` strategies unchanged (skip, fail, retry, fallback)

## Alternatives Considered

- **Always retry with LLM**: Current behavior. Works but expensive. A type coercion error doesn't need 1000 tokens to fix.
- **Custom error handlers per node**: Too much boilerplate for graph authors. Named repairs centralize common recovery patterns.
- **Let agent nodes handle all recovery**: Agents can still observe `state.errors` — but deterministic repairs should fire before the agent spends tokens reasoning about the fix.

## Related

- FR-407: Structured repair actions (shared `RepairAction` model)
- FR-406: JSON lint output (same philosophy: machine-readable at boundaries)
- `yamlgraph/models/schemas.py` — `PipelineError`, `ErrorType`
- `yamlgraph/error_handlers.py` — `handle_retry`, `handle_fallback`, `handle_skip`
- Scripture: "normalize at the boundary where external data enters"
- Scripture trap: `downstream_fix` — repair at the error source, not downstream

## Judgement

**Verdict: REJECTED**

The legitimate kernel — avoid wasteful retries for trivial type coercion — has a simpler solution: enable Pydantic coercion mode in `execute_prompt` or add a `pre_retry_coerce` hook (~20 lines). The proposed solution is wildly disproportionate: new `on_error: auto_repair` strategy, a 9-code registry, callable dispatch, and repair coupling inside `from_exception()`. Rate-limit backoff already exists. Silent `inject-default` for missing state keys masks graph authoring errors (worse than failing). The `relax-threshold` repair is actively dangerous — it lowers quality gates programmatically. Over-engineered solution for problems that mostly don't exist or have simpler fixes.
