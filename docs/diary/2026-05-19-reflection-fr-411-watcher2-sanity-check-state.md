# FR-411 Watcher2 Sanity Check — Reflection

**Date:** 2026-05-19
**FR:** FR-411 — Inquisitor Watcher2 Reintegration
**Reviewer:** watcher2 post-validate sanity agent

## Trap

**recent_changes_blindness** + **workspace_is_not_boundary**: The branch was cut before
FR-406 and FR-410 landed on `main`. The cumulative `git diff main..HEAD` shows those
features appearing as deletions — they exist in `main` but not in this branch's HEAD.
A naive merge would regress both features. The implementation itself is correct; the
hazard is entirely positional (branch age relative to main).

## What Happened

FR-411 introduces exactly the three files specified in the FR plan:
- `.chaplain/actions/syncing_inbox_action.py` — cadence-aware inbox dispatch
- `.chaplain/actions/audit_action.py` — inquisitor invocation with `last_audit_ts` update
- `.chaplain/config/watcher-dispatcher.yaml` — `auditing` state, `audit_needed`/`audit_done` events

All 9 acceptance tests pass (0.15s). ARCHITECTURE.md, CAP-151, REQ-YG-406, and
changelog fragment are present. FR status is updated to Implemented. No scope creep
within the feature commit itself.

However, the branch merge-base (`b6817b8f` — FR-412) predates three main commits
(FR-410, FR-406, nuke of FR-409). The `git diff main..HEAD` stat (-942 lines) vastly
overstates the apparent impact of this PR because it includes regressed work that
lives only on `main`. The branch protection rule "Require up to date before merge"
is the primary gate that must fire before this lands.

## Root Cause

Branch was created at a point-in-time that has since been superseded by three merged
PRs. The FSM pipeline did not rebase the worktree before the feature commit, so the
worktree drifted. This is a process gap: the post-validate stage catches it, but the
enforce stage should ideally rebase before feature work starts.

## What Worked

- Implementation proportionality is excellent: 693 insertions, 7 deletions in the
  feature commit itself — exactly matching the FR's "3 files" target.
- Behavioral tests (not shape tests): every assertion checks event routing or state
  mutation, not internal call counts or implementation structure.
- Cadence threshold is tested with deterministic time mocking (`monkeypatch`).
- Non-fatal error paths (AC-08, AC-09) are explicitly covered.
- Registry artefacts (CAP-151, REQ-YG-406, changelog, FR status) are complete.

## Seed:

If a worktree can drift silently until post-validate, should the dispatcher FSM emit a
`rebase_required` event (or refuse to start) when `git merge-base HEAD main` != the
current `main` tip — so stale branches are caught at FSM startup rather than at merge
time?
