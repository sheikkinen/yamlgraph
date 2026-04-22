# FR-274: Copilot Session ID Extraction — Diary Reflection

**Date:** 2026-04-22
**FR:** FR-274
**Type:** Fix

## Cognitive Process

The investigation began with a hypothesis: copilot nodes cannot pass session context to following nodes. The hypothesis was validated empirically — copilot CLI with `--silent` produces empty stderr, and without `--silent` produces only ANSI stats. The regex `Session:\s*([a-zA-Z0-9-]+)` was speculative from FR-105 and never empirically verified.

## Trap: Plausible Wrong Answer

The original test `test_session_id_extracted_from_stderr` passed because the mock stderr was fabricated to match the regex. The test proved the regex worked — not that copilot CLI produced matching output. This is the "plausible wrong answer" trap: the test infrastructure confirmed the mechanism but not the contract with the external system.

## Insight: Boundary Normalization

The fix follows the One Law: normalize at the boundary where external data enters. The copilot CLI's session ID is an external boundary. Instead of guessing the stderr format, we command the tool to write structured output (`--share`) and parse that known format.

## Bonus: Duplicate Model Resolution

While implementing, discovered `create_copilot_node()` had an exact duplicate block (lines 173-180 and 183-190) — model resolution ran twice with `defaults = defaults or {}` also duplicated. This was a copy-paste artifact unrelated to the session bug but cleaned up in the same change.

## Seed

If copilot CLI changes the `--share` file format, the extraction silently falls back to `None`. Should we add a warning when the share file exists but no session ID is found — distinguishing "copilot didn't write a share file" from "copilot changed the format"?
