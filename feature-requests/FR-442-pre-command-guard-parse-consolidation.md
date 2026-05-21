# Feature Request: FR-442 Consolidate PreToolUse parse path in pre-command-guard

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-05-21

## Summary

Consolidate the hot-path input parsing in `.github/hooks/scripts/pre-command-guard.sh` from repeated `python3 -c` reparsing to a single parse call that returns all needed fields (`tool`, `command`, `detail`, `session_id`, `tool_use_id`) in one pass.

## Value Statement

Hook invocations become faster while preserving identical safety behavior, reducing per-tool-call overhead in agent sessions.

## Problem

`pre-command-guard.sh` currently parses JSON once into `PARSED`, then reparses `PARSED` five more times to extract individual fields:

- `TOOL_NAME=$(echo "$PARSED" | python3 -c ...)`
- `COMMAND=$(echo "$PARSED" | python3 -c ...)`
- `DETAIL=$(echo "$PARSED" | python3 -c ...)`
- `SESSION_ID=$(echo "$PARSED" | python3 -c ...)`
- `TOOL_USE_ID=$(echo "$PARSED" | python3 -c ...)`

This makes the normal approve path expensive:

1. parse input JSON (`python3 -c`)
2. reparse 5 fields (`python3 -c` x5)
3. audit log append (`python3 -c`)

Total: **7 Python process starts** in the common path.

## Research Findings

1. `.github/hooks/scripts/pre-command-guard.sh` contains 10 total `python3 -c` call sites; 6 of these are in the parse/extract block that runs on every invocation.
2. Baseline behavior is green: `python3 .github/hooks/tests/test_pre_command_guard.py` currently reports `37 passed, 0 failed`.
3. Existing shared helper `.github/hooks/scripts/checks/common.sh` is PostToolUse-oriented and still uses multiple Python invocations; reusing it directly does not satisfy this FR's parse-path reduction goal.
4. `.github/hooks/README.md` documents fail-closed parse behavior (`reason: parse-error`) and audit fields (`session_id`, `tool_use_id`); this contract must remain intact.

## Objectives

1. Reduce common-path Python process starts in `pre-command-guard.sh`.
2. Preserve all current guard decisions and deny/approve semantics.
3. Preserve fail-closed parsing and audit-log field fidelity.

## Constraints

1. Single responsibility: only pre-command parse-path consolidation in `pre-command-guard.sh`.
2. No policy changes to existing checks (co-authored-by, `--no-verify`, multiline `-m`, pipe-buffer, lockdown, reasoning-pattern).
3. No changes to PostToolUse check scripts in `.github/hooks/scripts/checks/`.
4. No new runtime dependency (`jq`, additional binaries).
5. Architecture alignment: this remains in the side-effects/infrastructure boundary (hook scripts), with no YAML graph runtime changes.

## Proposed Solution

1. Introduce a parse helper in `pre-command-guard.sh` that performs one `python3 -c` parse of stdin and emits all required fields in a delimiter-safe format.
2. Replace the five `echo "$PARSED" | python3 -c ...` extraction calls with native bash assignment from that single parse output.
3. Keep the existing fail-closed branch unchanged in effect: parse failure still emits deny with `parse-error`.
4. Keep `audit_log()` behavior and payload shape unchanged.
5. Keep lockdown/reasoning/status branches behaviorally unchanged.

## Failing Acceptance Tests (RED)

Create:

- `.github/hooks/tests/test_fr442_pre_command_guard_parse_red.py`

Planned RED tests:

1. `test_ac01_parse_block_uses_single_python_invocation`
   Assert the parse/extract block in `pre-command-guard.sh` contains exactly one `python3 -c` call.
2. `test_ac02_parse_block_has_no_reparse_of_PARSED_json`
   Assert `echo "$PARSED" | python3 -c` does not appear in the parse/extract block.
3. `test_ac03_common_non_terminal_path_python_invocations_within_budget`
   Run hook with a `python3` shim counter; assert non-terminal approve path uses at most 3 Python invocations (parse + audit + optional helper allowance).
4. `test_ac04_terminal_clean_path_python_invocations_within_budget`
   Same shim method; assert clean terminal approve path uses at most 3 Python invocations.

RED command:

```bash
pytest -q --no-cov .github/hooks/tests/test_fr442_pre_command_guard_parse_red.py
```

Expected RED reason before implementation: current parse block reparses `PARSED` 5 times, so AC-01/02/03/04 fail.

## Acceptance Criteria

- [x] Parse/extract block in `pre-command-guard.sh` uses one Python parse invocation (no five-field reparsing loop)
- [x] Common approve path (`read_file`/non-terminal tool payload) executes with <=3 Python invocations
- [x] Clean terminal approve path executes with <=3 Python invocations
- [x] Parse-failure path remains fail-closed (`deny` + `parse-error`)
- [x] Existing behavioral test suite remains green (`.github/hooks/tests/test_pre_command_guard.py`)
- [x] No changes to PostToolUse check scripts under `.github/hooks/scripts/checks/`
- [x] `.github/hooks/README.md` wording remains accurate; no parser-internals update required

## Implementation Notes

1. Added `parse_hook_input()` in `.github/hooks/scripts/pre-command-guard.sh` to parse stdin JSON once and emit the required fields as NUL-delimited values.
2. Replaced five `echo "$PARSED" | python3 -c ...` field-extraction subprocesses with native bash `read -d ''` assignments from a single parse stream.
3. Preserved fail-closed parse behavior (`deny` + `parse-error`) and left all policy checks unchanged.
4. Added FR acceptance tests in `.github/hooks/tests/test_fr442_pre_command_guard_parse_red.py` for static parse-block assertions and runtime Python invocation budgets.

## Alternatives Considered

1. **Migrate to `checks/common.sh` immediately**
   Rejected for this FR: broader coupling and does not directly guarantee parse-path invocation reduction.
2. **Use `jq` for extraction in shell**
   Rejected: adds an external dependency not currently required by the hook.
3. **Keep current parser and accept overhead**
   Rejected: unnecessary repeated interpreter startup on every tool call.

## Related

- Topic source: `.chaplain/processing/gh-430.md`
- `.github/hooks/scripts/pre-command-guard.sh`
- `.github/hooks/tests/test_pre_command_guard.py`
- `.github/hooks/README.md`
- `feature-requests/FR-414-copilot-hook-audit-logging.md`
- `feature-requests/FR-434-hook-modular-refactor.md`
