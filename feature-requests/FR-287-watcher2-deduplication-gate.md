# Feature Request: FR-287 watcher2 deduplication gate — skip already-completed FRs

**Priority:** HIGH  
**Type:** Bug  
**Status:** Proposed  
**Effort:** 0.5 days  
**Requested:** 2026-04-26

## Summary

Add a pre-pipeline deduplication gate in watcher2 that detects when an inbox topic references an FR already merged in a prior PR, then skips the item instead of running a full duplicate cycle.

## Value Statement

Watcher2 operators avoid duplicate PR churn and save pipeline runtime by preventing re-processing of already-completed FR topics.

## Problem

Watcher2 can re-process old inbox items and execute the full Plan → Enforce pipeline even when the referenced FR is already merged. This caused a duplicate flow (`gh-208.md`) that consumed compute and produced a stale PR.

Current defenses are incomplete for this case:

1. `.chaplain/lib/watcher/inbox_sync.sh` deduplicates by file presence across inbox/processing/failed, not by completion state.
2. `.chaplain/lib/watcher/worktree_setup.sh` (FR-286) guards against merged **branch-name** reuse, but the stronger semantic check should happen earlier at topic intake.
3. `.chaplain/watcher2.sh` currently starts cycle work after moving an item to processing, without checking whether the FR in that topic was already completed.

## Objectives

1. Skip watcher2 cycles early when a topic references an FR already merged.
2. Consume skipped processing items so they are not retried on the next poll.
3. Preserve normal behavior when no FR reference exists or no merged PR is found.

## Constraints

- Scope is limited to watcher2 shell orchestration (`.chaplain/`); no YAMLGraph runtime changes.
- Keep deterministic branch naming and existing merged-branch guard from FR-286 unchanged.
- No hard failure if `gh` is unavailable or query fails; degrade gracefully with warning logs.
- Skip logic must be explicit in metrics (`outcome: "skipped"`).

## Research Findings

- `inbox_sync.sh` already performs stage-level dedup (`inbox`/`processing`/`failed`) but does not check completion state from merged PR history.
- `worktree_setup.sh` already uses dedicated skip-code control flow (`return 2`) for merged branch-collision handling; this pattern can be reused for the FR dedup gate.
- `watcher2.sh` already has a skip path that sets `CYCLE_OUTCOME="skipped"`, removes `TOPIC_FILE`, and writes metrics, so the new gate can slot into existing control-flow semantics.

## Proposed Solution

Implement a dedicated dedup boundary check before preflight/worktree setup.

### 1. Add a dedup guard helper in watcher shell libs

Create a focused helper (e.g., `.chaplain/lib/watcher/dedup_gate.sh`) that:

1. Extracts first FR token from the topic file (`FR-[0-9]+`).
2. If no FR token is present, returns success (continue pipeline).
3. Queries merged PR history by FR identifier:

```bash
gh pr list --state merged --search "FR-277" --json number,url,mergedAt,title \
  --jq '.[0] | select(.number != null)'
```

4. Returns a dedicated skip code when a merged PR is found and exposes merged PR metadata for logging.
5. Returns success with warning when `gh` is unavailable or query fails.

### 2. Wire guard into `.chaplain/watcher2.sh` before preflight

After moving topic to processing and initializing cycle variables:

1. Call the dedup guard with `TOPIC_FILE`.
2. On skip code:
   - set `CYCLE_OUTCOME="skipped"`,
   - log the matched merged PR,
   - remove `$TOPIC_FILE`,
   - write metrics,
   - continue polling loop without invoking `handle_failure`.
3. On non-skip, proceed with existing preflight/worktree pipeline.

### 3. Document behavior

Update `.chaplain/README.md` with:

- dedup gate purpose,
- FR extraction behavior,
- merged PR search pattern (`gh pr list --state merged --search "FR-XXX"`),
- graceful-degradation semantics.

## Acceptance Criteria

- [ ] **AC-01:** Watcher2 checks topic content for an FR token (`FR-[0-9]+`) before preflight/worktree setup.
- [ ] **AC-02:** When an FR token exists, watcher2 queries merged PR history using `gh pr list --state merged --search "FR-XXX"`.
- [ ] **AC-03:** If a merged PR is found for the FR token, watcher2 treats the cycle as skip (not failure) and does not run plan/enforce steps.
- [ ] **AC-04:** Skip path consumes the processing topic file (`rm "$TOPIC_FILE"`), preventing immediate re-pick.
- [ ] **AC-05:** Skip path writes cycle metrics with `outcome` set to `skipped`.
- [ ] **AC-06:** If no FR token is present in the topic, watcher2 behavior is unchanged (pipeline proceeds normally).
- [ ] **AC-07:** If `gh` is unavailable or merged-query fails, watcher2 logs a warning and continues (no crash).
- [ ] **AC-08:** Tests added in `tests/unit/test_fr287_watcher2_deduplication_gate.py` covering merged-hit skip, no-token pass-through, and graceful failure behavior.
- [ ] **AC-09:** `.chaplain/README.md` documents the dedup gate and merged-PR search contract.

## Alternatives Considered

1. **Rely only on branch-collision guard (FR-286):** Rejected. It is defense-in-depth, but dedup by FR completion should happen earlier and semantically at topic intake.
2. **Randomized branch names:** Rejected. Avoids collisions but does not prevent duplicate execution for already-completed FRs.
3. **Manual inbox hygiene only:** Rejected. Operator-driven cleanup is not reliable for daemonized automation.

## Related

- Issue #232: watcher2 deduplication gate — skip already-completed FRs
- Issue #233: merged-branch collision follow-up
- PR #211 (merged FR-277) and PR #231 (duplicate)
- `.chaplain/watcher2.sh`
- `.chaplain/lib/watcher/inbox_sync.sh`
- `.chaplain/lib/watcher/worktree_setup.sh`
- FR-275 watcher2 PR reuse
- FR-286 merged-branch collision guard
