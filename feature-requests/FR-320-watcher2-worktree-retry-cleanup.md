# Feature Request: FR-320 watcher2 retry-safe worktree setup cleanup

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 0.5 day
**Requested:** 2026-05-03

## Summary

Make `.chaplain/lib/watcher/worktree_setup.sh` retry-safe for re-queued `gh-<NUM>.md` topics by cleaning stale branch/worktree state before creating a new worktree branch.

## Value Statement

Watcher2 operators get self-healing retries instead of manual branch/worktree cleanup on every requeue.

## Problem

Issue #308 reports deterministic setup failure on retry: rerunning the same topic reuses `feat/watcher2-gh-<NUM>`, and setup fails when stale local/remote branch or worktree residue remains.

Current code confirms the gap:

1. `worktree_setup.sh` still uses `git branch -D "$WT_BRANCH" ... || true`, so cleanup failure can be silently ignored.
2. `preflight.sh` prunes stale worktrees older than 12 hours only, so immediate retries are not covered.
3. `.chaplain/README.md` documents manual retry cleanup commands, proving retry hygiene is still operator toil.
4. FR-286 collision guard (`gh pr list --state merged`) prevents merged-branch reuse but does not clean stale retry state from failed runs.

## Research: Existing Patterns, Alternatives, Prior Art

1. **Correct boundary already exists:** setup is centralized in `.chaplain/config/watcher-pipeline-v2.yaml` via `preflight.sh && worktree_setup.sh`; fixing retry hygiene in `worktree_setup.sh` is architecture-aligned.
2. **Reusable cleanup precedent:** `.chaplain/lib/watcher/worktree_teardown.sh` already performs local and remote branch deletion patterns that can inform setup-side retry cleanup.
3. **Test style precedent:** `tests/unit/test_fr286_watcher2_merged_branch_collision_guard.py` validates watcher shell contracts via source assertions; this is the right pattern for RED planning tests.
4. **Canonical topic source:** `.chaplain/processing/gh-308.md` is absent in this worktree, so issue #308 is used as the planning source of truth.

## Objectives

1. Clean stale retry state before `git worktree add`.
2. Fail explicitly when mandatory local cleanup cannot restore preconditions.
3. Preserve deterministic branch naming and FR-286 merged-PR collision guard behavior.

## Constraints

1. Scope is limited to `.chaplain/lib/watcher/worktree_setup.sh`, directly coupled tests, and directly coupled `.chaplain/README.md` retry guidance.
2. No FSM state/transition changes.
3. Preserve naming contract `feat/watcher2-${topic_basename}`.
4. No silent success-shaped fallback for mandatory cleanup failures.

## Proposed Solution

In `worktree_setup.sh`, before `git worktree add`:

1. Enumerate worktree bindings (`git worktree list --porcelain`) and remove entries bound to `WT_BRANCH`.
2. Remove stale existing `WT_DIR` path before creating the new worktree.
3. Replace branch-delete swallow with explicit failure handling for unrecoverable local cleanup.
4. Attempt `git push origin --delete "$WT_BRANCH"` as best effort (warn-only on failure).
5. Keep merged-PR collision guard logic unchanged and evaluated before worktree creation.

## Acceptance Criteria

- [x] **AC-01:** `worktree_setup.sh` removes stale worktree attachment(s) for `WT_BRANCH` before local branch deletion.
- [x] **AC-02:** `worktree_setup.sh` removes stale existing `WT_DIR` before `git worktree add`.
- [x] **AC-03:** Local branch-delete swallow pattern (`git branch -D ... || true`) is removed from retry cleanup path.
- [x] **AC-04:** Setup exits with explicit error when mandatory local cleanup cannot restore branch-create preconditions.
- [x] **AC-05:** Setup attempts stale remote branch cleanup as best effort and does not crash on remote-delete failure.
- [x] **AC-06:** FR-286 merged-PR collision guard behavior remains present.
- [x] **AC-07:** `.chaplain/README.md` retry/requeue section documents automated setup cleanup and narrower manual fallback.
- [x] **AC-08:** RED acceptance tests exist at `tests/unit/test_fr320_watcher2_worktree_retry_cleanup.py` and are tagged `@pytest.mark.req("REQ-YG-276")`.

## Implementation Notes

1. Added branch-attached worktree enumeration/removal using `git worktree list --porcelain` before local branch deletion.
2. Added explicit error path for local stale-branch deletion failure (`log_error` + `return 1`).
3. Added best-effort remote stale-branch cleanup (`git push origin --delete "$WT_BRANCH"` with warning-only failure handling).
4. Added stale `WT_DIR` removal guard before `git worktree add`.
5. Updated `.chaplain/README.md` retry guidance to document automated cleanup and keep manual branch/worktree commands as fallback.

## Failing Acceptance Tests (RED)

RED test file:

- `tests/unit/test_fr320_watcher2_worktree_retry_cleanup.py`

RED command:

```bash
pytest tests/unit/test_fr320_watcher2_worktree_retry_cleanup.py -q --no-cov
```

Expected RED before implementation:

1. Missing branch-attached worktree cleanup sequence.
2. Missing stale `WT_DIR` cleanup step before `git worktree add`.
3. Existing silent branch-delete swallow pattern.
4. Missing remote stale-branch delete attempt in setup.
5. README not yet updated for automated retry cleanup behavior.

Observed RED (current codebase):

- `6 failed, 1 passed`
- Failing tests: AC-01, AC-02, AC-03, AC-04, AC-05, AC-07
- Passing guard test: AC-06 (merged-PR collision guard remains present)

## Alternatives Considered

1. Keep manual cleanup instructions only — rejected; preserves deterministic operator toil.
2. Rely only on preflight prune window — rejected; misses immediate retries.
3. Randomize retry branch names — rejected; breaks deterministic traceability.

## Related

- Topic source requested by prompt: `.chaplain/processing/gh-308.md` (missing in this worktree)
- Canonical source used: GitHub issue #308 (<https://github.com/sheikkinen/yamlgraph/issues/308>)
- `.chaplain/lib/watcher/worktree_setup.sh`
- `.chaplain/lib/watcher/preflight.sh`
- `.chaplain/lib/watcher/worktree_teardown.sh`
- `.chaplain/config/watcher-pipeline-v2.yaml`
- `.chaplain/README.md`
- `tests/unit/test_fr286_watcher2_merged_branch_collision_guard.py`
