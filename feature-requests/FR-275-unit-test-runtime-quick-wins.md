# Feature Request: Unit Test Runtime Quick Wins

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-04-22
**Related:** FR-073 (fast unit tests), FR-243 (GitHub Issues remote inbox)

## Summary

Reduce `pytest tests/unit/ -q --no-cov` runtime by applying low-risk quick wins: move process-heavy script tests to integration and remove avoidable real-time waits from unit tests.

## Value Statement

Developers get faster local feedback loops while preserving confidence, because true unit tests stay fast and deterministic and script-level behavior remains covered in integration.

## Problem

Current unit suite runtime is dominated by tests that execute shell scripts, create temporary git repositories, and spawn nested subprocesses. These tests validate real script integration behavior, but they live under `tests/unit/` and slow the default fast path.

Profile snapshot (2026-04-22):

- `3648 passed` in `68.53s` for `tests/unit/`
- Top file-level contributors:
  - `tests/unit/test_inquisitor_gate.py` (~7.4s)
  - `tests/unit/test_finalize_merge.py` (~6.3s)
  - `tests/unit/test_requirement_enforcement.py` (~3.9s)
  - `tests/unit/test_watch_sequential_enforcement.py` (~2.3s)
  - `tests/unit/test_harden_remote_inbox.py` (~2.5s)

The suite is not catastrophically slow, but it has avoidable latency and classification drift.

## Proposed Solution

### 1) Reclassify process-heavy tests as integration

Move script/subprocess/git-heavy tests from `tests/unit/` to `tests/integration/` and mark with `@pytest.mark.integration`:

- `tests/unit/test_requirement_enforcement.py`
- `tests/unit/test_watch_sequential_enforcement.py`
- `tests/unit/test_inquisitor_gate.py`
- `tests/unit/test_finalize_merge.py`
- `tests/unit/test_harden_remote_inbox.py`

These tests are local integration tests (shell + filesystem + git + subprocess), even if they do not require external network services.

### 2) Keep semantically unit tests in unit, but remove avoidable waits

Apply quick timing reductions without reducing assertion strength:

- Replace long real sleeps with minimal timeout-triggering delays in:
  - `tests/unit/test_shell_tools.py`
  - `tests/unit/test_fr027_execution_safety.py`
- Keep provider/linter mock-based tests (for example `test_fr230_google_vertex_thinking.py`) in unit.

### 3) Clarify marker semantics

Update pytest marker documentation in `pyproject.toml` so `integration` explicitly includes local script/process integration, not only external services.

### 4) Preserve coverage lanes

- Fast lane: `pytest tests/unit/ -q --no-cov`
- Full lane: unit + integration in CI (existing or explicit command)

No tests are deleted; classification reflects behavior.

## Acceptance Criteria

- [ ] The five identified script/subprocess-heavy files are moved to `tests/integration/` and marked `@pytest.mark.integration`
- [ ] `pytest tests/unit/ -q --no-cov` runtime improves by at least 20% from the 2026-04-22 baseline
- [ ] `pytest tests/integration/ -q --no-cov` includes the moved files and passes
- [ ] `pyproject.toml` marker description documents local integration semantics
- [ ] No regressions in total pass count across unit + integration suites
- [ ] Changelog fragment added

## Alternatives Considered

1. Keep all tests in unit and optimize only sleeps

This helps, but leaves classification drift unresolved and keeps script-level integration behavior in the fast lane.

2. Add a `slow` marker and skip slow tests

Rejected as primary strategy: hides cost rather than classifying tests by behavior.

3. Add `pytest-xdist` immediately

Deferred: parallelism can mask classification and isolation issues. Fix semantics and easy waits first.

## Related

- `feature-requests/FR-073-fast-unit-tests.md`
- `feature-requests/FR-243-github-issues-remote-inbox.md`
- `tests/unit/test_requirement_enforcement.py`
- `tests/unit/test_watch_sequential_enforcement.py`
- `tests/unit/test_inquisitor_gate.py`
- `tests/unit/test_finalize_merge.py`
- `tests/unit/test_harden_remote_inbox.py`
