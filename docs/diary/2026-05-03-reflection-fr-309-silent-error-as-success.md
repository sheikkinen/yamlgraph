# Diary: FR-307/309 — Silent Error Masquerading as Success

**Date:** 2026-05-03
**FR:** FR-307, FR-309
**Trap:** plausible_wrong_answer, downstream_fix

## What Happened

The watcher pipeline's judge step was silently failing for 5+ runs. The copilot CLI was invoked with model name `claude-sonnet-4-20250514`, which doesn't exist. The copilot binary returned exit code 0, printed "Error: Model ... is not available" to stdout, and produced no actual work. The yamlgraph copilot node captured this as `output=''` with `exit_code=0` — a successful empty response.

The pipeline then matched no event_map keyword, fell through to `success: approve`, and auto-approved. The enforce step ran on an unapproved FR. The full pipeline appeared to work.

## The Trap Chain

1. **plausible_wrong_answer**: Exit code 0 + empty output passed shape checks. No assertion verified that the judge actually rendered a verdict. The pipeline saw "success" where there was failure.

2. **downstream_fix**: The first three fixes targeted symptoms — vocabulary alignment (FR-309), fallback safety (`success: error`), missing transitions. These were real bugs, but they masked the root cause: the model name was wrong. Each fix was correct in isolation but didn't solve the actual problem.

3. **quick_confidence**: After aligning the event_map vocabulary and adding the prompt instruction for verdict output, I felt certain the next run would work. The 7-second judge execution (vs 2+ minutes for a real LLM call) should have been an immediate red flag. I didn't check the timing until run 5.

## The Root Cause

`claude-sonnet-4-20250514` is a LangChain model identifier, not a GitHub Copilot CLI model name. The copilot CLI model name is `claude-sonnet-4`. A provider boundary crossed without normalization — the exact trap documented in the Scripture under `boundaries: provider`.

## What Worked

- **FR-307 logging** exposed the empty stdout on event_map miss. Without it, the auto-approve fallback would have hidden the failure permanently.
- **`success: error`** (FR-309) turned silent success into visible failure.
- **Manual testing** (`yamlgraph graph run ... 2>/dev/null`) reproduced the exact behavior and showed `output=''` clearly.
- **Running copilot with stderr visible** showed the error message that `--silent` suppressed.

## Heuristic

**When a CLI returns exit code 0 with empty output, treat it as failure until proven otherwise.** Empty output from an LLM is never a valid success case. Assert on output non-emptiness at the boundary, not downstream.

**Check execution time, not just exit code.** A 7-second "judge" that should take 2+ minutes is diagnostic evidence of a startup-only failure. Timing is a signal.

## Graduate Candidate

The `boundaries: provider` entry in the Scripture already covers this: "API responses differ." But it should be expanded: provider boundaries include not just response shapes but also **model identifiers**. A model name valid for one provider's API is invalid for another's CLI. Normalize model names at the boundary where they enter the system.

## Seed

Could the copilot node validate the model name against `copilot --help` or a known-models list before invoking? A 100ms pre-check would catch this class of error before a 10-minute pipeline run discovers it at step 4 of 6.
