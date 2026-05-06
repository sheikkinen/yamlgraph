# FR-339 Watcher2 Sanity Check Reflection

**Date:** 2026-05-06
**FR:** FR-339 watcher2 post-merge processing cleanup
**Reviewer:** watcher2 (post-validate sanity check)

## What Happened

FR-339 addressed a boundary gap in watcher2's post-merge flow: successful merges left `.chaplain/processing/*.md` topic files behind because `done` executed `rm -f {topic_file}` from the worktree context and called `post_merge.sh` without explicit merge-outcome wiring. The fix transfers ownership of processing cleanup to `post_merge.sh`, gates it on a confirmed `MERGED` PR state check via `gh pr view --json state`, and moves matching topics from `.chaplain/processing/` to `.chaplain/done/` with collision-safe naming.

All 6 acceptance tests pass (0.13s). The pipeline log confirms `validate_fix` reported 3725 passed, 135 skipped, 2 xfailed, and the FSM transitioned cleanly to `sanity_check`.

## Trap

**downstream_fix**: The stale topic symptom manifested as a leftover file in `.chaplain/processing/`; the prior `rm -f {topic_file}` patch was applied at the `done` action (where the symptom appeared) rather than at the true ownership boundary (`post_merge.sh`, which holds the merged-outcome context). The fix correctly moved cleanup to the boundary where PR state is known, not where the file path was convenient.

## Root Cause

The `done` action lacked explicit post-merge context (PR number, title, absolute topic path). Without these, `post_merge.sh` could not distinguish a successfully merged topic from an abandoned or failed one. The result was a no-op deletion from the wrong directory context (worktree vs. main), leaving `.chaplain/processing/` polluted after teardown.

## What Worked

- **Normalize at the boundary**: Passing `PR_NUMBER`, `PR_TITLE`, and `TOPIC_FILE` as env vars to `post_merge.sh` ensures the cleanup function operates on confirmed merge context rather than inferring from file presence.
- **Explicit gate with three cases**: The `cleanup_processing_topic()` function handles all three outcomes — MERGED (move), missing source (no-op log), unmerged/unknown (skip log) — preventing silent failure.
- **Safety guard on path**: The `*.chaplain/processing/*` path check in `cleanup_processing_topic` prevents accidental cleanup of unrelated files if context wiring produces an unexpected `TOPIC_FILE` value.
- **Pipeline log evidence**: `validate_fix` reported a clean green (3725 passed) before handing off to `sanity_check`, confirming no regression.

## Minor Observation

`TOPIC_FILE="{main_dir}/{topic_file}"` in the pipeline could produce double-prefixed paths if `{topic_file}` is ever set as an absolute value. The path-guard check (`*.chaplain/processing/*`) in `cleanup_processing_topic` provides a silent fallback in that case, which is safe but produces a `log_warn` rather than surfacing the misconfiguration. A future improvement could assert at the pipeline level that `{topic_file}` is always relative.

## Seed

If `post_merge.sh` now owns three distinct responsibilities (inbox consumption, processing cleanup, main sync), should each be a separate, independently testable script invoked from a thin `post_merge.sh` orchestrator — or does the current monolithic structure remain proportional as long as each function stays under 30 lines?
