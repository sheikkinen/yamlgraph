# Reflection: FR-442 Pre-Command Guard Parse Consolidation — Watcher2 Sanity Check

**Date:** 2026-05-21
**FR:** FR-442 — Consolidate PreToolUse parse path in pre-command-guard.sh
**Reviewer:** watcher2 post-validate sanity check

## Trap

`downstream_fix` — the original code extracted five fields from an already-parsed JSON object by spawning five new Python interpreter processes. Each extraction felt like a "simple one-liner" at the call site, masking that the real problem was the entry boundary (stdin parse) not being the single normalisation point.

## What Happened

`pre-command-guard.sh` parsed stdin once into `$PARSED`, then re-parsed `$PARSED` five more times to extract `TOOL_NAME`, `COMMAND`, `DETAIL`, `SESSION_ID`, `TOOL_USE_ID` — each spawning a cold Python interpreter (~30 ms). Total: 7 Python starts per hook invocation on the common approve path.

The fix introduced `parse_hook_input()` which emits all five fields as NUL-delimited values in one Python call, then uses `IFS= read -r -d ''` bash assignments to avoid any further Python subprocesses. Fail-closed behaviour and all existing policy checks were left untouched.

## Root Cause

The parse path had not been revisited when `common.sh` was introduced for PostToolUse hooks (FR-434). The pre-command guard inherited its own copy of the parse pattern and was never refactored, making repeated spawning the implicit default.

## What Worked

- **Boundary-first thinking:** once the consolidation was treated as a boundary normalisation problem (stdin JSON enters; all fields exit together), the solution was straightforward.
- **TDD structural + runtime tests:** AC-01/02 static assertions caught the old pattern immediately; AC-03/04 runtime shim counter verified the budget claim without needing to measure wall-clock latency.
- **Minimal scope:** no PostToolUse scripts, no policy changes, no new runtime dependencies — the change is exactly proportional to the stated objective.

## Evidence

- 4 FR acceptance tests: all 4 pass.
- 13 existing behavioral tests: all 13 pass.
- Diff: 28 net lines in the hook script, one new test file (93 lines), FR (122 lines), changelog fragment (5 lines).

## Seed

**Seed:** When a refactored shared helper (`common.sh`) exists but the older sibling script (`pre-command-guard.sh`) still carries its own copy of the parse pattern, what automated gate would detect the drift — a structural lint rule that flags duplicate `python3 -c` parse patterns across hook scripts, or an import-linter analog for shell scripts?
