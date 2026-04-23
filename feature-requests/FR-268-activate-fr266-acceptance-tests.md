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

## Research Brief

### Competitive Landscape

**Test skip management is framework-agnostic** — all major testing frameworks (pytest, unittest, Jest, JUnit) use skip decorators for conditional test execution, but **none provide built-in automation for skip removal**. The pattern of manually removing skips when conditions are met is universal:

| Framework | Skip Pattern | Activation Process |
|-----------|-------------|-------------------|
| **pytest** | `@pytest.mark.skip(reason="...")` | Manual decorator removal |
| **unittest** | `@unittest.skip("reason")` | Manual decorator removal |
| **Jest** | `describe.skip()` / `it.skip()` | Manual rename to `describe()` / `it()` |
| **JUnit** | `@Disabled("reason")` | Manual annotation removal |
| **RSpec** | `pending "reason"` | Manual removal/rename to `it` |

**Industry pattern**: Test activation is a **maintenance task**, not a framework feature. No competing LLM framework (LangGraph, CrewAI, AutoGen) provides skip automation — it's handled at the test framework level. The value is in **process discipline** (TDD RED → GREEN → REFACTOR), not tooling innovation.

### Existing Abstractions

**YAMLGraph has standardized TDD patterns** with dedicated tooling:

| Pattern | Implementation | Usage |
|---------|---------------|-------|
| **RED commits** | `SKIP=pytest git commit` (bypasses test runner, preserves linting) | 15+ FRs use this pattern |
| **Condemning tests** | `examples/bugfix/` pipeline with explicit RED phase | FR-173 implementation |
| **Acceptance test automation** | `.chaplain/graphs/copilot/prompts/write-acceptance-tests.yaml` | Generates skipped tests for new FRs |
| **Requirement traceability** | `scripts/req_coverage.py` detects skipped tests in coverage reports | REQ-YG-XXX validation |

**Current skip usage (6 test files)**:
- `test_copilot_node_model_selection.py` — 9 skips (this FR)
- `test_providers.py` — API key guards (`@pytest.mark.skipif(not os.getenv("API_KEY"))`)
- `test_interactive_tool.py` — Redis availability guards
- Integration tests — Environmental dependency skips
- Examples — Optional dependency skips (`@pytest.mark.skipif(not HAS_LANCEDB)`)

**Gap**: Only the `test_copilot_node_model_selection.py` uses the **TDD RED pattern** (`@pytest.mark.skip(reason="FR-266 RED: awaiting implementation")`). All others are **conditional skips** based on environment, not development phase.

### Diary Precedents

| Diary Entry | Pattern | Relevance |
|-------------|---------|-----------|
| **2026-04-21-chaplain.md** | **TDD cycle closure discipline** — Documents FR-268 as the **REFACTOR** phase completion for FR-266 | **Direct precedent** — This exact pattern |
| **2026-04-20-reflection-fr-260.md** | **Bugfix-condemn template** — Same structure as acceptance test writing: "read criteria, write tests, run to confirm RED, commit with `SKIP=pytest`" | Template for skip → activate workflow |
| **2026-04-08-inquisitor-audit-162.md** | **RED-GREEN separation violations** — Multiple audits cite bundled test+implementation commits | Test activation must be separate from implementation |
| **2026-04-19-inquisitor-audit-211.md** | **TDD compliance** — RED commit with `SKIP=pytest`; GREEN commit makes them pass. "Textbook discipline" | Model for proper TDD separation |

**Graduated heuristic from Scripture**:
```yaml
process:
  RED_GREEN_separation: "Commit RED (failing test, SKIP=pytest) and GREEN (fix) separately"
  test_activation_as_refactor: "REFACTOR phase = remove skips to complete TDD cycle"
  automation_inherits_doctrine: "Scripts follow same rules as humans → no --no-verify bypass"
```

### Usage Evidence

- **Existing graphs using skip activation**: 0 (first instance)
- **Real-world use cases beyond the proposal**: 
  - **FR-173 bugfix pipeline** — Uses `SKIP=pytest` for condemning tests, then activates by commit
  - **Acceptance test automation** — `.chaplain/graphs/copilot/` generates skipped tests for immediate RED commits
  - **15+ FRs documented** using `SKIP=pytest git commit` pattern in feature-requests/
  - **6 test files with skips** — but only 1 uses TDD RED pattern; others are environmental guards

**Frequency**: TDD RED → activate pattern appears in **1 of 6 skip files** (16.7%). Environmental skips (84.3%) use `@pytest.mark.skipif()` for conditional execution, not activation.

### Classification Signal

- **Abstraction level**: **pattern** — This is test maintenance discipline, not a framework primitive
- **Recommended approach**: **document** — This is a one-time cleanup task completing the TDD cycle for FR-266; the pattern exists and works
- **Key risk**: **Pattern drift** — Without clear documentation, teams may accumulate skipped tests as technical debt rather than completing TDD cycles