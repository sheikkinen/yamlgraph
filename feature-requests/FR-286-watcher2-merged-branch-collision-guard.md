# Feature Request: FR-286 watcher2 merged-branch collision guard

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-04-26

## Summary

Add a pre-worktree guard in watcher2 that skips processing when the deterministic branch name for a topic already has a merged PR, preventing ghost duplicate PRs from branch-name reuse.

## Value Statement

Watcher2 operators avoid duplicate PR churn and wasted pipeline runtime when previously completed inbox items are accidentally re-processed.

## Problem

Watcher2 currently derives branch names deterministically from inbox filenames in `.chaplain/lib/watcher/worktree_setup.sh`:

- `WT_BRANCH="feat/watcher2-${topic_basename}"`

If an item like `gh-208.md` is processed again after its original branch was merged and deleted, watcher2 recreates the same branch name and runs the full pipeline again. This produced a stale duplicate:

- PR #211 (merged) and PR #231 (stale duplicate) both used `feat/watcher2-gh-208`

Why this happens in the current architecture:

1. `worktree_setup.sh` has no historical merged-branch check before `git worktree add`.
2. `create_pr.sh` (FR-275) only reuses **open** PRs; it does not prevent creating new PRs on recycled branch names.
3. Remote inbox retries are intentionally possible via relabeling (`chaplain`) from FR-243, so re-processing can occur unless explicitly gated.

## Objectives

1. Prevent branch-name collision duplicates before worktree creation.
2. Keep deterministic branch naming (`feat/watcher2-{topic}`) for traceability and existing tooling.
3. Keep this fix scoped to watcher2 shell infrastructure (no YAMLGraph core changes).

## Constraints

- Do not add random/timestamp branch suffixes in this FR.
- Do not change `create_pr.sh` open-PR reuse behavior.
- Follow existing watcher2 architecture: shell lib does the boundary check, orchestrator owns skip/continue control flow.
- Keep graceful degradation if `gh` is unavailable or the merged-query fails.
- Maintain compatibility with Issue #232 as primary dedup strategy; this FR is defense-in-depth.

## Proposed Solution

Implement Option B (merged-branch guard) as defense-in-depth while Issue #232 dedup gate remains the primary prevention layer.

### 1. Add merged-branch guard to `worktree_setup.sh`

After deriving `WT_BRANCH`, query merged PR history for that head branch:

```bash
existing_merged_pr=$(gh pr list \
  --state merged \
  --head "$WT_BRANCH" \
  --json number,url,mergedAt \
  --jq '.[0] | select(.number != null)' 2>/dev/null || true)
```

If found:
- log skip with PR URL/number,
- set skip metadata variables (for orchestrator/metrics),
- return a dedicated non-crash skip code (for example `2`).

If query fails (auth/network/CLI unavailable):
- log warning,
- continue with existing behavior (do not hard-fail cycle).

### 2. Handle skip code in `.chaplain/watcher2.sh`

When `worktree_setup` returns the collision skip code:
- treat as **skip**, not failure,
- remove the processing topic file to prevent immediate re-pick,
- write cycle metrics with explicit skip outcome,
- continue main loop without invoking `handle_failure`.

### 3. Keep branch format unchanged

No branch suffixing in this FR. Deterministic naming remains:
- `feat/watcher2-{topic_basename}`

This preserves existing assumptions in docs, scripts, and FR traceability while blocking known collision scenarios.

## Acceptance Criteria

- [ ] **AC-01:** `worktree_setup.sh` checks for merged PR history on the derived `WT_BRANCH` before `git worktree add`.
- [ ] **AC-02:** If a merged PR exists for `WT_BRANCH`, `worktree_setup.sh` returns a dedicated skip code and logs the merged PR reference.
- [ ] **AC-03:** `watcher2.sh` handles that skip code as non-failure (no `handle_failure` invocation).
- [ ] **AC-04:** On skip, the processing topic file is consumed (removed from `.chaplain/processing`) so it is not retried in the next poll.
- [ ] **AC-05:** Metrics record an explicit skip outcome for this path.
- [ ] **AC-06:** When no merged PR exists, watcher2 behavior is unchanged (worktree creation proceeds normally).
- [ ] **AC-07:** If `gh` is unavailable/query fails, guard degrades gracefully and does not crash watcher2.
- [ ] **AC-08:** Tests added for merged-branch detection, skip control flow, and unchanged happy path.
- [ ] **AC-09:** `.chaplain/README.md` updated to document the merged-branch collision guard.

## Alternatives Considered

1. **Option A: Timestamp/hash suffix branch names (`feat/watcher2-gh-208-<suffix>`)**  
   Rejected for this FR. It avoids collisions but reduces traceability, complicates cleanup/debugging, and hides the missing dedup boundary instead of guarding it.

2. **Option C only: Rely solely on Issue #232 dedup gate**  
   Rejected as sole mitigation. It should remain the primary gate, but this branch-level check is needed as defense-in-depth if dedup logic regresses or misses edge cases.

3. **Remote branch-only detection via `git branch -r --list`**  
   Rejected. Remote branch existence is weaker than merged PR history and can be absent after normal branch deletion.

## Related

- Issue #233: watcher2 branch name collision with previously merged PRs
- Issue #232: watcher2 deduplication gate — skip already-completed FRs
- PR #211 (merged) and PR #231 (stale duplicate)
- `.chaplain/lib/watcher/worktree_setup.sh`
- `.chaplain/watcher2.sh`
- `.chaplain/lib/watcher/create_pr.sh` (FR-275 open-PR reuse behavior)
- `.chaplain/lib/watcher/inbox_sync.sh` (FR-243 remote inbox retry semantics)
