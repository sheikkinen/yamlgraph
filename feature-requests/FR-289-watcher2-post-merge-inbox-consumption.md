# Feature Request: FR-289 watcher2 post-merge inbox consumption for matching FR items

**Priority:** HIGH  
**Type:** Bug  
**Status:** Proposed  
**Effort:** 0.5 days  
**Requested:** 2026-04-26

## Summary

Extend watcher2 post-merge cleanup to consume stale inbox items that reference the same FR as the just-merged work, so orphaned duplicates are not re-processed later.

## Value Statement

Watcher2 operators avoid duplicate pipeline cycles and ghost follow-up PRs because related inbox items are consumed immediately after a successful merge.

## Problem

`post_merge` currently closes the originating GitHub issue (`gh-*.md`) but does not remove other inbox files that reference the same completed FR.

This leaves stale files in `.chaplain/inbox/` that can be picked up in later cycles. Even with FR-287 dedup at processing time, these leftovers still create avoidable poll churn and unnecessary skip cycles.

Observed context from topic:

1. A topic referencing `FR-277` remained in inbox after successful merge.
2. The leftover item survived restarts and was re-processed later.

## Objectives

1. After successful merge, identify the merged FR token (`FR-XXX`) for the completed work item.
2. Scan `.chaplain/inbox/` for files referencing that same token.
3. Consume matched inbox files into a completed queue (`.chaplain/done/`) so they are not re-picked.
4. Preserve existing watcher2 behavior when no FR token can be resolved.

## Constraints

- Scope is limited to watcher2 shell infrastructure (`.chaplain/lib/watcher/post_merge.sh`, `.chaplain/README.md`, and tests).
- No changes to YAMLGraph runtime, node types, or CLI behavior.
- Keep existing success-path ownership: orchestrator still removes `TOPIC_FILE`; post-merge consumes only *other* inbox matches.
- Use existing shell + `gh` tooling only; no new dependencies.
- Post-merge cleanup failures should be surfaced via logs but must not undo a successful merge.

## Proposed Solution

Implement FR-token-based inbox consumption in `post_merge.sh`.

### 1. Resolve merged FR token in post-merge boundary

Add a small helper in `post_merge.sh` to resolve the first `FR-[0-9]+` token using:

1. `PR_NUMBER` title lookup (`gh pr view "$PR_NUMBER" --json title --jq '.title'`) when available.
2. Fallback to already-derived `PR_TITLE`.
3. Optional final fallback to current `TOPIC_FILE` content.

If no FR token is found, log and exit cleanup path without error.

### 2. Consume matching inbox files

After successful merge and issue-close handling:

1. Scan `.chaplain/inbox/*.md` for the resolved token.
2. Create `.chaplain/done/` if missing.
3. Move matching files from inbox to done (leave non-matching files untouched).
4. Log consumed filenames and total count.

If a destination filename already exists in `.chaplain/done/`, append a deterministic suffix (timestamp) to avoid overwrite.

### 3. Keep behavior explicit in docs

Update `.chaplain/README.md` to document:

- post-merge FR-token extraction source order,
- inbox scan behavior,
- `.chaplain/done/` role as consumed-completed queue.

## Acceptance Criteria

- [ ] **AC-01:** `post_merge.sh` resolves an `FR-[0-9]+` token from merged work context (PR metadata and/or existing watcher variables).
- [ ] **AC-02:** On successful token resolution, post-merge scans `.chaplain/inbox/` for markdown files containing that token.
- [ ] **AC-03:** Matching inbox files are moved to `.chaplain/done/` (not left in inbox), and non-matching files remain unchanged.
- [ ] **AC-04:** `.chaplain/done/` is created automatically when absent.
- [ ] **AC-05:** Destination collision is handled safely (no silent overwrite of existing done files).
- [ ] **AC-06:** If no FR token is resolved, watcher2 continues normally and no inbox files are moved.
- [ ] **AC-07:** Cleanup emits explicit logs for token resolution outcome and number of consumed files.
- [ ] **AC-08:** Tests added in `tests/unit/test_fr289_watcher2_post_merge_inbox_consumption.py` covering token resolution path, inbox match consumption path, no-token no-op path, and done-directory handling.
- [ ] **AC-09:** `.chaplain/README.md` documents post-merge inbox consumption and `.chaplain/done/` semantics.

## Alternatives Considered

1. **Rely only on FR-287 processing-time dedup skip:** Rejected. It prevents duplicate execution but still allows stale inbox accumulation and repeated skip churn.
2. **Delete matching inbox files immediately (no done queue):** Rejected for this FR. Hard deletion removes audit visibility; moving to `.chaplain/done/` preserves traceability.
3. **Only close source GitHub issue and do no local cleanup:** Rejected. Duplicate local inbox entries can still survive and trigger later cycles.

## Related

- Topic: `.chaplain/processing/gh-234.md`
- `.chaplain/lib/watcher/post_merge.sh`
- `.chaplain/watcher2.sh`
- `.chaplain/lib/watcher/inbox_sync.sh` (FR-243 remote inbox import)
- `.chaplain/lib/watcher/dedup_gate.sh` (FR-287 processing-time dedup)
- `feature-requests/FR-287-watcher2-deduplication-gate.md`
- `feature-requests/FR-243-github-issues-remote-inbox.md`
