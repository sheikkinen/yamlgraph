# Feature Request: Fix count_range verification for Pydantic model outputs

**Priority:** MEDIUM
**Type:** Bug
**Status:** Completed
**Verdict:** APPROVE — Scope frozen, authority granted
**Effort:** 0.5 days
**Requested:** 2026-03-08

## Summary

The `count_range` verification check returns 0 for Pydantic model outputs because `len(PydanticModel)` is not meaningful. The evaluator should extract the countable field from Pydantic models before checking length.

## Value Statement

Graph authors using structured Pydantic schemas get accurate verification checks, preventing false violation warnings on correct LLM outputs.

## Problem

When a node produces a Pydantic model (the standard output format for structured LLM responses), the `count_range` verification check always fails because `len()` on a Pydantic model raises `TypeError` (BaseModel does not implement `__len__`), and the except clause defaults to `length = 0`.

**Reproduction** (using `examples/demos/verification-gate/`):

```bash
yamlgraph graph run examples/demos/verification-gate/graph.yaml --var topic="neural networks" --full
```

Output:
```
⚠ Verification violated [generate_points]: predicted "Will return 3-5 items about {topic}",
got KeyPoints(points=['...', '...', '...', '...']) (check: count_range, on_fail: warn)

Count range check failed: expected 3-5 items, got 0
```

The LLM correctly returns 4 items in `points`, but `len(KeyPoints(...))` returns 0.

**Root cause** in `yamlgraph/verification.py`:

```python
try:
    length = len(actual)
except TypeError:
    length = 0
```

Pydantic v2 `BaseModel` does not implement `__len__`, so `len()` raises `TypeError`. The except clause catches this and defaults to `length = 0`, masking the actual item count inside the model's list field.

## Proposed Solution

Add a `_extract_countable()` helper in `yamlgraph/verification.py` that unwraps Pydantic models before length checks:

```python
from pydantic import BaseModel

def _extract_countable(value: Any) -> Any:
    """Extract a countable value from Pydantic models.

    If the value is a Pydantic model with exactly one list field,
    return that list. Otherwise return the value unchanged.
    """
    if isinstance(value, BaseModel):
        list_fields = [
            v for v in value.model_dump().values()
            if isinstance(v, list)
        ]
        if len(list_fields) == 1:
            return list_fields[0]
    return value
```

Then in the `count_range` check:

```python
countable = _extract_countable(actual)
try:
    length = len(countable)
except TypeError:
    length = 0
```

**Design rationale:**
- Single-list-field heuristic is safe: the common pattern is a wrapper model with one list (e.g., `KeyPoints(points=[...])`).
- Multi-list or no-list models fall through unchanged — no silent wrong answer.
- Uses `model_dump()` (Pydantic v2 API) to access values, avoiding field descriptor issues.

## Acceptance Criteria

- [x] `count_range` check passes when `actual` is a Pydantic model with a single list field containing N items within range
- [x] `count_range` check fails correctly when the single list field has items outside range
- [x] `count_range` check falls back to `len(actual)` when model has zero or multiple list fields
- [x] `count_range` continues to work for plain `list`, `dict`, and `str` inputs (no regression)
- [x] `_extract_countable()` is a private helper with dedicated unit tests
- [x] Verification gate demo (`examples/demos/verification-gate/`) runs without false violations
- [x] Tests tagged with `@pytest.mark.req("REQ-YG-154")`
- [x] No changes to `VerificationConfig` schema or public API

## Alternatives Considered

1. **Fix the demo schema** — Change prompt to return `list[str]` directly instead of `KeyPoints` model. Rejected: treats symptom, not cause; Pydantic models are the standard output format per Commandment 5.

2. **Document as limitation** — Note that `count_range` only works with native collections. Rejected: verification should handle the framework's own output format; documenting the gap normalizes a defect.

3. **Add explicit `count_field` to VerificationConfig** — e.g., `question: "Will return 3-5 items in points"`. Rejected: adds schema complexity; single-list heuristic handles the common case without config changes.

## Related

- FR-164: Verification gate pattern (parent feature)
- `yamlgraph/verification.py`: Bug location
- `examples/demos/verification-gate/`: Reproduction demo
- REQ-YG-154: Verification gate requirement
- `tests/unit/test_verification.py`: Existing test suite
