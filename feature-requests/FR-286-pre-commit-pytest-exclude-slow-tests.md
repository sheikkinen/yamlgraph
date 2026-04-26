# Feature Request: Exclude Slow Tests from Pre-commit Pytest Hook

**Priority:** MEDIUM
**Type:** Bug
**Status:** Proposed
**Effort:** 0.25 days
**Requested:** 2026-04-26

## Summary

Update the root pre-commit `pytest` hook to run only fast unit tests by adding `-m "not slow"` to the command.

## Value Statement

Contributors get predictable, fast commit feedback and avoid long-running commits caused by intentionally slow test scenarios.

## Problem

The current pre-commit `pytest` hook runs all unit tests, including tests marked `@pytest.mark.slow`:

```yaml
entry: bash -c '.venv/bin/python -m pytest tests/unit/ -q --tb=short --no-cov'
```

This conflicts with the existing test-speed pattern already established in the repository (`pytest -m "not slow"` for fast iteration) and can cause commit-time hangs or excessive wait times.

## Objectives

1. Keep commit-time quality gates fast and reliable.
2. Align pre-commit behavior with the documented fast-test workflow in `CLAUDE.md`.
3. Preserve full slow-test coverage outside pre-commit (manual runs and CI).

## Constraints

1. Scope is limited to the root `.pre-commit-config.yaml` `pytest` hook entry.
2. Do not alter test semantics, marker definitions, or CI workflow scope.
3. Keep current hook messaging that directs users to run integration tests separately.

## Proposed Solution

Change the pre-commit hook entry from:

```yaml
entry: bash -c '.venv/bin/python -m pytest tests/unit/ -q --tb=short --no-cov && echo "" && echo "✓ Unit tests passed. Run integration tests separately:" && echo "  pytest tests/integration/ -v"'
```

to:

```yaml
entry: bash -c '.venv/bin/python -m pytest tests/unit/ -q --tb=short --no-cov -m "not slow" && echo "" && echo "✓ Unit tests passed. Run integration tests separately:" && echo "  pytest tests/integration/ -v"'
```

### Implementation Approach

1. Edit `.pre-commit-config.yaml` and append `-m "not slow"` to the root `pytest` hook command.
2. Run the pre-commit `pytest` hook to confirm fast-test selection behavior remains functional.
3. Update FR status and related trace notes after implementation.

## Acceptance Criteria

- [ ] Root `.pre-commit-config.yaml` `pytest` hook includes `-m "not slow"` in the command.
- [ ] `pre-commit run pytest --all-files` executes unit tests without selecting `@pytest.mark.slow` tests.
- [ ] Hook still fails on non-slow unit test failures.
- [ ] Slow tests remain runnable via `pytest tests/unit/ -q --no-cov -m "slow"`.
- [ ] Tests added (or existing test coverage extended) for hook command behavior if repository patterns require configuration assertions.
- [ ] Documentation updated if any pre-commit command examples are affected.

## Alternatives Considered

1. Keep running all unit tests in pre-commit and optimize individual slow tests further.
   - Rejected: does not guarantee fast commit feedback and duplicates FR-275’s marker strategy.
2. Remove `pytest` from pre-commit entirely.
   - Rejected: weakens local quality gates.
3. Introduce a separate fast test script wrapper.
   - Rejected: unnecessary indirection; direct hook command change is simpler and consistent with existing patterns.

## Related

- `.pre-commit-config.yaml` (current root pytest hook entry)
- `CLAUDE.md` (documents fast command `pytest tests/unit/ -q --no-cov -m "not slow"`)
- `ARCHITECTURE.md` REQ-YG-275 (slow marker infrastructure and fast/slow execution split)
- `feature-requests/FR-275-test-speed-optimization.md`
