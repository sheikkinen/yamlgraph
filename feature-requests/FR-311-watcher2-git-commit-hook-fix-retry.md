# Feature Request: FR-311 watcher2 git_commit hook-fix retry

**Priority:** HIGH
**Type:** Bug
**Status:** Enforced — Implemented
**Effort:** 0.5 day
**Requested:** 2026-05-03

## Summary

Make the watcher2 `git_commit` action resilient when pre-commit hooks auto-fix staged files by re-staging and retrying commit instead of failing the pipeline immediately.

## Value Statement

Watcher2 operators get a fail-closed but self-healing `commit_plan` boundary: hook auto-fixes no longer cause avoidable pipeline failure.

## Problem

The `git_commit` action currently does one `git commit` attempt and returns `error` on any non-zero exit.

1. `.chaplain/actions/git_commit_action.py` returns `error_event` immediately on commit failure.
2. `.chaplain/config/watcher-pipeline-v2.yaml` uses `type: git_commit` in `commit_plan`; `error` routes directly to `failed`.
3. Pre-commit hook behavior often includes "files were modified by this hook" (exit 1 after auto-fix), which is recoverable by re-staging and retrying.
4. Existing watcher2 prior art already uses retry patterns for auto-fix loops:
   - `.chaplain/actions/precommit_action.py` (attempt counter + retry event)
   - `.chaplain/README.md` "Pre-commit Hook Cascade Handling" (re-add + retry loop)

Result: recoverable hook-fix outcomes are treated as fatal at `commit_plan`.

## Objectives

1. Retry `git commit` when failure is caused by hook-applied file modifications.
2. Cap retries to 3 attempts.
3. Preserve existing `git_commit` semantics for success, nothing-to-commit, and genuine failures.
4. Add acceptance tests that currently fail (RED) on the present implementation.

## Constraints

- Scope only `.chaplain/actions/git_commit_action.py` and its targeted tests.
- No watcher FSM topology changes in this FR.
- No broad fallback behavior: non-recoverable commit errors must still emit `error`.
- Keep `capture_fr_path` behavior intact.

## Research Findings

### Existing Abstractions

- `GitCommitAction` already stages files, checks staged diff, optionally captures FR path, and commits.
- `PrecommitAction` already demonstrates canonical retry mechanics (`max_attempts`, attempt counter, re-staging).
- v2 pipeline already centralizes planning commit through `git_commit`, so fixing this action fixes all `commit_plan` callsites.

### Prior Art in Repository

- `.chaplain/actions/precommit_action.py` — bounded retry loop with explicit attempt tracking.
- `.chaplain/README.md` — documented auto-fix + retry workflow in watcher2 finalize process.
- `.chaplain/lib/worktree.py` — explicit commit error classification (`nothing to commit` vs genuine failure) as boundary normalization pattern.

### Gap Check

- No existing unit tests directly cover `GitCommitAction` retry behavior.
- No existing retry path in `git_commit_action.py` for hook-modified-file failures.

## Proposed Solution

Add bounded retry logic to `GitCommitAction.execute()`:

1. Introduce `max_attempts` config key (default `3`).
2. On `git commit` failure:
   1. Detect whether hook auto-fixes modified tracked files (e.g., via `git diff --name-only`).
   2. If modified files exist:
      - run `git add -u`,
      - log retry attempt,
      - retry commit until success or attempt cap.
   3. If no modified files: treat as genuine failure and emit `error` immediately.
3. Preserve existing success behavior and `nothing_event` short-circuit when no staged diff exists.

## Acceptance Criteria

- [ ] **AC-01:** `git_commit` retries commit after hook-modified-file failures and succeeds when a subsequent commit succeeds.
- [ ] **AC-02:** Retry loop is capped at 3 attempts (default behavior).
- [ ] **AC-03:** Each retry attempt is logged with attempt context.
- [ ] **AC-04:** Non-hook/genuine commit failures emit `error` without retry loop.
- [ ] **AC-05:** Hook-modified-file recovery path re-stages tracked changes via `git add -u` before retry.
- [ ] **AC-06:** Existing no-op behavior (`nothing to commit` → `nothing_event`) remains unchanged.
- [ ] **AC-07:** Existing `capture_fr_path` behavior remains unchanged.
- [ ] **AC-08:** Acceptance tests in `tests/unit/test_fr311_watcher2_git_commit_hook_fix_retry.py` fail on current implementation and pass after implementation.

## Failing Acceptance Tests (RED)

Create `tests/unit/test_fr311_watcher2_git_commit_hook_fix_retry.py` with contracts:

1. `test_ac01_retries_and_succeeds_after_hook_modification`
2. `test_ac02_stops_after_three_attempts_and_reports_retries`
3. `test_ac04_non_hook_commit_failures_do_not_retry`

Current behavior expected in RED phase:

- AC-01 fails (action returns `error` after first failed commit).
- AC-02 fails (no retry loop / attempt logging).
- AC-04 passes (current immediate failure behavior already exists).

## Alternatives Considered

1. **Handle this in FSM transitions instead of action logic** — rejected; duplicates retry logic in orchestration and leaves `git_commit` action inconsistent across callsites.
2. **Use shell wrapper in `commit_plan` state** — rejected; bypasses reusable action boundary and increases YAML/bash complexity.
3. **Treat all commit failures as fatal** — rejected; known recoverable hook-fix failures cause avoidable pipeline aborts.

## Judgement

**Verdict:** APPROVE
**Date:** 2026-05-03
**Model:** manual (copilot judge hit wrong FR; evaluated manually against 8 criteria)

**Evaluation:**
1. Scope clear and minimal — YES. Single file (`git_commit_action.py`), single concern (retry on hook auto-fix).
2. No contradictions — clean problem statement, consistent with prior art references.
3. ACs measurable — 8 acceptance criteria, each testable and specific.
4. Feasible — follows existing `PrecommitAction` retry pattern exactly.
5. Architecture aligned — boundary normalization at the action level (the One Law).
6. Single responsibility — only hook-fix retry logic, no FSM topology changes.
7. Classification: **Bug fix** — recoverable failures treated as fatal is a defect.
8. Tests compile and fail correctly — 2 RED (AC-01, AC-02: no retry exists), 1 GREEN (AC-04: genuine errors already fatal). Correct TDD phase.

**Scope frozen. Authority granted to implement.**

## Related

- Topic: `/Users/sheikki/Documents/src/yamlgraph/.chaplain/processing/gh-274.md`
- Action: `.chaplain/actions/git_commit_action.py`
- Pipeline callsite: `.chaplain/config/watcher-pipeline-v2.yaml` (`commit_plan`)
- Prior-art retry action: `.chaplain/actions/precommit_action.py`
- Watcher docs: `.chaplain/README.md`
