# Feature Request: Test Speed Optimization

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved
**Effort:** 2 days
**Requested:** 2024-04-24

## Summary

Optimize test suite performance by adding pytest markers for slow tests and optimizing wait/sleep logic to enable faster development cycles.

## Value Statement

Developers get faster test feedback during rapid iteration, reducing development cycle time from 1+ minutes to under 30 seconds for core functionality tests.

## Problem

The test suite currently takes ~76 seconds for unit tests alone (`pytest tests/unit/ -q --no-cov`), which slows down development iteration. Key bottlenecks identified:

1. **No separation of fast vs slow tests** - All tests run together regardless of what's being tested
2. **Hardcoded sleep delays** - Multiple tests use `time.sleep(2)`, `asyncio.sleep(30.0)`, and `CHAOS_DELAY` (default 5s)
3. **Integration tests mixed with unit tests** - Some tests require external services or long operations
4. **Large test files** - Files like `test_graph_commands.py` (1420 lines) may contain both fast and slow tests

## Proposed Solution

### 1. Add Pytest Markers

Add `slow` marker to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = [
    "req(id): links test to requirement(s) e.g. @pytest.mark.req('REQ-YG-014')",
    "integration: marks tests requiring external services",
    "slow: marks tests that take >1 second to complete",
]
```

### 2. Mark Slow Tests

Identify and mark tests that:
- Use `time.sleep()` or `asyncio.sleep()` with values >0.1s
- Test timeout behavior or race conditions
- Use `CHAOS_DELAY` or similar artificial delays
- Test map node concurrency with multiple workers

```python
@pytest.mark.slow
@pytest.mark.req("REQ-YG-XXX")
def test_map_node_timeout_behavior():
    # Test that takes >1s due to timeout simulation
    pass
```

### 3. Optimize Wait Logic

Replace hardcoded delays with configurable minimums for testing:

```python
# Before
time.sleep(2)

# After
import os
delay = float(os.environ.get("TEST_DELAY_SCALE", "1.0"))
time.sleep(0.1 * delay)  # 0.1s in tests, 2s in production if needed
```

### 4. Update Development Commands

Add fast test commands to `CLAUDE.md`:

```bash
# Ultra-fast tests (skip slow tests)
pytest tests/unit/ -q --no-cov -m "not slow"

# Run only slow tests
pytest tests/unit/ -q --no-cov -m "slow"

# Current behavior (all tests)
pytest tests/unit/ -q --no-cov
```

## Acceptance Criteria

- [ ] `slow` pytest marker added to `pyproject.toml`
- [ ] Tests using sleep >1s are marked with `@pytest.mark.slow`
- [ ] Fast test run (`-m "not slow"`) completes in <30 seconds
- [ ] Slow tests can be run separately with `-m "slow"`
- [ ] `CHAOS_DELAY` and similar timing made configurable
- [ ] Development commands updated in `CLAUDE.md`
- [ ] No test behavior changes (same pass/fail results)
- [ ] Tests added for marker functionality
- [ ] Documentation updated

## Alternatives Considered

### Option 1: Split test directories
- **Pro**: Clear separation
- **Con**: Breaks existing REQ-YG requirement traceability patterns, requires moving files

### Option 2: Profile-based optimization only
- **Pro**: Targets actual bottlenecks
- **Con**: Doesn't help developers skip slow tests during iteration

### Option 3: Parallel test execution
- **Pro**: Overall faster runtime
- **Con**: Complex setup, may mask individual slow tests

**Chosen approach**: Pytest markers provide immediate developer benefit with minimal disruption.

## Related

- `tests/chaos_tools.py`: Contains `CHAOS_DELAY` mechanism
- `tests/unit/test_map_node_timeout.py`: Multiple `time.sleep(2)` calls
- `tests/unit/test_race_node.py`: Uses `asyncio.sleep(30.0)`
- `pyproject.toml`: Current pytest configuration with existing markers
- `CLAUDE.md`: Development command documentation

## Research Brief

### Competitive Landscape

**Pytest ecosystem standard:** The official pytest documentation demonstrates exactly this pattern - using `@pytest.mark.slow` and `-m "not slow"` for fast test iterations. This is a well-established practice across Python projects.

**AI Framework patterns:** Limited public evidence of systematic slow test optimization in LangGraph, CrewAI, or AutoGen repositories. Most focus on mocking LLM calls rather than test execution speed optimization. This suggests documenting good practices around pytest markers would be valuable to the ecosystem.

**Industry standard:** The `slow` marker pattern is widely adopted (Django, Flask, Pandas, NumPy all use variations). Command patterns like `pytest -m "not slow"` are developer workflow standards.

### Existing Abstractions  

**Current YAMLGraph test infrastructure:**
- `pyproject.toml`: Already defines `req(id)` and `integration` markers - adding `slow` is consistent
- **3,141 total pytest markers** in codebase (mostly `@pytest.mark.req` for traceability)
- **Integration marker exists** but not consistently used for slow tests
- `tests/chaos_tools.py`: Configurable `CHAOS_DELAY` pattern already exists 
- Asyncio markers already in use (`@pytest.mark.asyncio`)

**No overlapping abstractions** - this is pure testing infrastructure, not framework logic.

### Diary Precedents

**2026-04-19 Inquisitor Audit (FR-205):** Demonstrates the principle that "auditability applies uniformly" - slow/fast markers maintain test traceability while improving developer experience.

**Process patterns:** Multiple diary entries show the "boring = judgment was good" principle - if test optimization becomes routine developer workflow, it validates the abstraction is at the right level.

**No negative precedents found** for test infrastructure improvements in diary entries.

### Usage Evidence

- **Existing graphs using related abstractions:** 300+ YAML graph files
- **Current test markers:** 3,141 markers (mostly REQ traceability)  
- **Integration tests:** 22 explicit integration test references
- **Real-world use cases beyond the proposal:** Every YAMLGraph developer doing rapid iteration

### Classification Signal

- **Abstraction level:** pattern (testing infrastructure, not framework primitive)
- **Recommended approach:** build (implement pytest markers, optimize timing)
- **Key risk:** Over-optimization could mask real performance issues in production code

## Judgment

**VERDICT:** APPROVE

**Scope:** FROZEN - All acceptance criteria are clear, minimal, and measurable. No changes permitted during implementation.

**Authority:** GRANTED - Proceed with implementation following RED-GREEN-REFACTOR discipline.

**Rationale:**
- Single responsibility: test suite performance optimization
- Industry standard pattern (pytest slow markers)
- Measurable value: 76s → <30s test feedback
- Feasible 2-day implementation
- Excellent research showing competitive alignment
- Acceptance tests properly validate missing implementation (not missing dependencies)