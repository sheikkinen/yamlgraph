# Feature Request: FR-339 watcher2 post-merge processing cleanup

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-05-06

## Summary

Ensure successful watcher2 merges consume the originating topic from `.chaplain/processing/` into `.chaplain/done/` with an explicit merged-PR gate, so stale processing entries are not left behind.

## Value Statement

Watcher2 operators get deterministic queue hygiene after merge, avoiding stale `processing/` files that can be re-polled or require manual cleanup.

## Problem

Issue GH-339 reports stale `.chaplain/processing/*.md` files after successful merge. Current flow has a boundary gap:

1. Dispatcher moves topics into `.chaplain/processing/` (`.chaplain/config/watcher-dispatcher.yaml`).
2. Worker `done` action deletes `{topic_file}` from the worktree context and calls `post_merge.sh` with errors swallowed (`.chaplain/config/watcher-pipeline-v2.yaml`).
3. `post_merge.sh` currently handles issue close, FR-token inbox consumption, and main sync, but does not consume processing-topic files based on merge state (`.chaplain/lib/watcher/post_merge.sh`).

Result: a successful merge can still leave stale processing queue artifacts.

## Objectives

1. Move merged topics from `.chaplain/processing/` to `.chaplain/done/` in post-merge.
2. Gate that move on confirmed PR merged state.
3. Keep cleanup idempotent and explicit when the source file is already missing.
4. Preserve existing post-merge behaviors (issue close, FR-token inbox consumption, main sync).

## Constraints

- Scope limited to:
  - `.chaplain/config/watcher-pipeline-v2.yaml`
  - `.chaplain/lib/watcher/post_merge.sh`
  - `.chaplain/README.md`
  - `tests/unit/test_fr339_watcher2_post_merge_processing_cleanup.py`
- No YAMLGraph runtime/node/CLI changes.
- No new dependencies.
- Cleanup must be skipped when PR is not confirmed merged.
- Keep this FR single-responsibility: processing-queue cleanup only.

## Proposed Solution

1. Update the pipeline `done` action to pass explicit post-merge context:
   - `PR_NUMBER`, `PR_TITLE`, and absolute `TOPIC_FILE`.
2. Remove direct `rm -f {topic_file}` from `done`; make `post_merge.sh` the owner of processing cleanup.
3. In `post_merge.sh`, add merged-state check (`gh pr view ... --json state`) before processing-file move.
4. On `MERGED`, move `TOPIC_FILE` from `.chaplain/processing/` to `.chaplain/done/` using existing collision-safe naming style.
5. Log explicit outcomes for cleanup performed, missing-file no-op, and unmerged skip.
6. Document merged-state-gated processing cleanup behavior in `.chaplain/README.md`.

## Acceptance Criteria

- [x] **AC-01:** `watcher-pipeline-v2.yaml` `done` action passes `PR_NUMBER`, `PR_TITLE`, and absolute `TOPIC_FILE` to `post_merge.sh`.
- [x] **AC-02:** `watcher-pipeline-v2.yaml` `done` action no longer directly executes `rm -f {topic_file}`.
- [x] **AC-03:** `post_merge.sh` checks PR merged state (`gh pr view ... --json state`) before processing cleanup.
- [x] **AC-04:** On confirmed merged PR, `post_merge.sh` moves the processing topic from `.chaplain/processing/` to `.chaplain/done/`.
- [x] **AC-05:** If the processing file is already missing, `post_merge.sh` logs explicit idempotent no-op and succeeds.
- [x] **AC-06:** If PR state is not merged or unavailable, processing move is skipped with explicit logging.
- [x] **AC-07:** Existing behaviors remain: issue close, FR-token inbox consumption, and main sync.
- [x] **AC-08:** Failing acceptance tests exist in `tests/unit/test_fr339_watcher2_post_merge_processing_cleanup.py`.
- [x] **AC-09:** `.chaplain/README.md` documents merged-state-gated processing cleanup.

## Failing Acceptance Tests (RED plan)

Acceptance test file:

- `tests/unit/test_fr339_watcher2_post_merge_processing_cleanup.py`

Planned RED tests:

1. `test_ac01_ac02_done_action_exports_post_merge_context_and_owns_cleanup`
2. `test_ac03_post_merge_verifies_merged_state_before_processing_cleanup`
3. `test_ac04_ac05_processing_topic_moves_to_done_with_idempotent_missing_path`
4. `test_ac06_unmerged_pr_state_skips_processing_move_explicitly`
5. `test_ac07_existing_post_merge_behaviors_still_present`
6. `test_ac09_readme_documents_processing_cleanup_contract`

RED evidence command:

```bash
pytest tests/unit/test_fr339_watcher2_post_merge_processing_cleanup.py -q --no-cov
```

## Alternatives Considered

1. **Keep direct `rm -f {topic_file}` in `done` and add periodic janitor cleanup**
   Rejected: ownership stays ambiguous and stale files can persist between janitor runs.
2. **Move processing cleanup to dispatcher**
   Rejected: dispatcher does not own merged-PR outcome context; post-merge boundary does.
3. **Delete processing topics unconditionally**
   Rejected: risks deleting topics for unmerged/failed paths.

## Related

- Issue: <https://github.com/sheikkinen/yamlgraph/issues/339>
- Topic source: `.chaplain/processing/gh-339.md` (not present in this worktree snapshot; issue body used)
- `.chaplain/config/watcher-dispatcher.yaml`
- `.chaplain/config/watcher-pipeline-v2.yaml`
- `.chaplain/lib/watcher/post_merge.sh`
- `.chaplain/README.md`
- `feature-requests/FR-289-watcher2-post-merge-inbox-consumption.md`
- `feature-requests/FR-312-watcher2-post-merge-main-sync.md`

## Research Brief

### Existing abstractions

- FR-289 already made `post_merge.sh` consume matching inbox items into `.chaplain/done/`.
- FR-312 already made `post_merge.sh` own main sync and explicit failure logging.
- Current `done` action still performs direct `rm -f {topic_file}` and invokes `post_merge.sh` without explicit merge/context wiring.
- Current `post_merge.sh` has no merged-state-gated processing-topic move.

### Scope impact

- This is an **integration boundary fix** in watcher shell orchestration, not a YAMLGraph framework primitive.
- Existing behavior is incomplete for processing queue exit, not duplicated elsewhere.

### Key risks

- Context-path mismatch (`{wt_dir}` vs main worktree absolute path) can create success-shaped runs with stale queue artifacts.
- Merge-state checks must be explicit and non-silent to avoid accidental cleanup on unmerged PRs.
- Existing acceptance tests currently reuse `REQ-YG-276`; traceability alignment should be addressed when implementing this FR.
