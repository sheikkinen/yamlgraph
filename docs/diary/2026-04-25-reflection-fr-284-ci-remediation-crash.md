# Diary: FR-284 — Watcher2 CI Remediation Crash Fix

**Date:** 2026-04-25
**FR:** FR-284
**Outcome:** Implemented

## Cognitive Process

The investigation started when watcher2 exited at "remediation attempt 1/2" — the clue was the exit code 1 and abrupt stop. The root cause was the intersection of three bugs: `gh run view` without a run ID under `set -euo pipefail`.

## Trap Encountered

**downstream_fix** — The initial instinct was to add `|| true` to the failing command. But that alone would have masked the real problem: the `gh run view` call would capture a usage error instead of actual CI logs. The fix required addressing all three bugs together: get the run ID, use absolute paths, and add error guards.

## Insight

Infrastructure scripts under `set -e` are fragile to any unguarded external command. Every `gh` / `curl` / API call in a `set -e` script must be explicitly guarded. The watcher2 pipeline is essentially a state machine where each external call is a potential crash point.

## Seed

Could watcher2 benefit from a `safe_gh()` wrapper function that automatically handles `|| true`, logging, and retry for all GitHub CLI calls?
