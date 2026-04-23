# Feature Request: Activate FR-266 Acceptance Tests

**Priority:** LOW
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.25 days
**Requested:** 2026-04-23
**FR:** FR-268

## Summary

Remove `@pytest.mark.skip` decorators from 9 acceptance tests in `test_copilot_node_model_selection.py` that were pre-implemented for FR-266 but kept in RED state pending implementation. Since FR-266 is implemented and passing, these tests should now be active to validate the copilot node model selection functionality.

## Value Statement

Test suite maintainers get complete coverage validation for REQ-YG-265 (copilot node model selection), ensuring the acceptance criteria remain measurably enforced without skipped tests accumulating technical debt.

## Problem

FR-266 (Copilot Node — Node-Level Model Selection) was implemented using TDD discipline:
1. **RED**: 12 acceptance tests written with `@pytest.mark.skip` to define expected behavior
2. **GREEN**: Implementation applied in 3 files (~15 lines net)
3. **REFACTOR**: _(pending)_ — Remove skip decorators to activate test coverage

The tests remain skipped with `reason="FR-266 RED: awaiting implementation"`, creating:
- **False negative coverage** — `pytest` and `req_coverage.py` don't validate REQ-YG-265
- **Technical debt accumulation** — Skipped tests are easy to forget and hard to track
- **Incomplete TDD cycle** — The refactor phase (test activation) was never completed

### Current State

```python
@pytest.mark.skip(reason="FR-266 RED: awaiting implementation")
@pytest.mark.req("REQ-YG-265")
class TestNodeConfigModelField:
    # ... 12 acceptance tests covering the full model resolution chain
```

9 skip decorators exist across the test classes validating:
- AC-01: NodeConfig has a model field
- AC-02: create_copilot_node accepts defaults parameter  
- AC-03: _compile_copilot_node passes effective_defaults
- AC-04-07: Model resolution priority chain (cli_flags > node > defaults > omit)
- AC-08: CopilotResult.model reflects resolved model

## Proposed Solution

**Simple skip decorator removal** — no production code changes needed.

### File Changes

**Single file modified:** `tests/unit/test_copilot_node_model_selection.py`

**Operation:** Remove 9 lines containing `@pytest.mark.skip(reason="FR-266 RED: awaiting implementation")`

**Lines to remove:**
- Line 43: `@pytest.mark.skip(reason="FR-266 RED: awaiting implementation")`
- Line 69: `@pytest.mark.skip(reason="FR-266 RED: awaiting implementation")`
- Line 95: `@pytest.mark.skip(reason="FR-266 RED: awaiting implementation")`
- Line 136: `@pytest.mark.skip(reason="FR-266 RED: awaiting implementation")`
- Line 167: `@pytest.mark.skip(reason="FR-266 RED: awaiting implementation")`
- Line 199: `@pytest.mark.skip(reason="FR-266 RED: awaiting implementation")`
- Line 259: `@pytest.mark.skip(reason="FR-266 RED: awaiting implementation")`
- Line 289: `@pytest.mark.skip(reason="FR-266 RED: awaiting implementation")`
- Line 338: `@pytest.mark.skip(reason="FR-266 RED: awaiting implementation")`

### Result

```python
# Before
@pytest.mark.skip(reason="FR-266 RED: awaiting implementation")
@pytest.mark.req("REQ-YG-265")
class TestNodeConfigModelField:

# After  
@pytest.mark.req("REQ-YG-265")
class TestNodeConfigModelField:
```

All 12 tests become active and must pass for CI to succeed.

## Acceptance Criteria

- [ ] 9 `@pytest.mark.skip` decorators removed from `test_copilot_node_model_selection.py`
- [ ] All 12 acceptance tests pass when run with `pytest tests/unit/test_copilot_node_model_selection.py -v`
- [ ] `python scripts/req_coverage.py --detail` shows REQ-YG-265 coverage active (not skipped)
- [ ] No production code changes — test activation only
- [ ] CI passes with all tests active

## Alternatives Considered

### 1. Leave tests skipped until next refactor cycle

**Rejected** — Accumulates technical debt. Skipped tests provide no validation value and may be forgotten. The implementation already exists and was validated manually during FR-266 development.

### 2. Remove skips gradually over multiple PRs

**Rejected** — Unnecessary complexity. The tests were written as a cohesive acceptance suite for a single feature. Partial activation provides incomplete coverage validation.

### 3. Rewrite tests instead of activating existing ones

**Rejected** — The existing tests correctly validate the acceptance criteria specified in FR-266. No functional gaps identified. Rewriting would be redundant work without added value.

## Related

- **FR-266** — Copilot Node — Node-Level Model Selection (implementation this activates tests for)
- **REQ-YG-265** — Copilot node model selection requirement (coverage target)
- `tests/unit/test_copilot_node_model_selection.py` — Test file to modify
- `scripts/req_coverage.py` — Tool that will show active coverage post-activation
- TDD discipline pattern — RED → GREEN → **REFACTOR** (this FR completes the cycle)