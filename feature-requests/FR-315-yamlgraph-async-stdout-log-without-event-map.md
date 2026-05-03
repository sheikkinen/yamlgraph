# Feature Request: FR-315 yamlgraph_async stdout logging without event_map

**Priority:** MEDIUM
**Type:** Bug
**Status:** Implemented
**Effort:** 0.25 day
**Requested:** 2026-05-03

## Summary

Log `yamlgraph` stdout at DEBUG level on successful runs even when `event_map` is not configured, so watcher planning/enforcement output is not silently discarded.

## Value Statement

Watcher2 operators can diagnose successful-but-wrong graph behavior from a single log stream instead of rerunning pipelines blind.

## Problem

GitHub issue #288 reports that `.chaplain/actions/yamlgraph_async_action.py` only emits `yamlgraph stdout` logs inside the `event_map` match branch.

Current behavior:

1. `execute()` decodes `stdout_text` and `stderr_text`, logs exit/length metadata, and returns `success_event` on zero exit.
2. The DEBUG stdout dump is currently inside:
   - `if event_map:`
   - `if pattern in stdout_text:`
3. When `event_map` is omitted (default) or `{}`, no stdout content is logged before `return success_event`.

Observed impact from issue topic:

- Plan output may be captured by subprocess but never appears in logs, reducing debuggability of planner/enforcer steps that rely on `success_event` without routing by output pattern.

## Objectives

1. Ensure successful no-event_map runs log stdout at DEBUG level.
2. Preserve existing event routing semantics and success/error event contracts.
3. Add failing acceptance tests proving the current implementation misses this log path.

## Constraints

- Scope is limited to `.chaplain/actions/yamlgraph_async_action.py` and targeted unit tests.
- No changes to watcher FSM topology or YAML graph prompt content.
- No broad logging redesign; this FR addresses only missing stdout log on the no-event_map success path.

## Proposed Solution

In `YamlgraphAsyncAction.execute()`:

1. Keep existing exit-code and stderr behavior unchanged.
2. Keep `event_map` matching logic unchanged.
3. Add a DEBUG-level stdout log (`[:2000]` cap) on the success path before returning `success_event` when no `event_map` branch returns.

This should ensure all successful runs have an inspectable stdout trace, regardless of whether event routing uses `event_map`.

## Acceptance Criteria

- [x] **AC-01:** When `event_map` is omitted and subprocess exits `0`, action logs `yamlgraph stdout:` at DEBUG level before returning `success_event`.
- [x] **AC-02:** When `event_map` is explicitly `{}` and subprocess exits `0`, action logs `yamlgraph stdout:` at DEBUG level before returning `success_event`.
- [x] **AC-03:** The added success-path stdout DEBUG log remains capped to 2000 characters.
- [x] **AC-04:** Existing event_map routing behavior is unchanged (matches still return mapped events).
- [x] **AC-05:** Acceptance tests in `tests/unit/test_fr315_yamlgraph_async_stdout_logging_without_event_map.py` fail on current behavior and pass after implementation.

## Implementation Notes

- Added a success-path DEBUG log in `.chaplain/actions/yamlgraph_async_action.py` so `yamlgraph stdout` is emitted (capped at 2000 chars) before returning the default success event when no `event_map` branch returns.
- Preserved existing event-map match routing semantics and error/success event contracts.

## Failing Acceptance Tests (RED)

Created RED contracts:

- `tests/unit/test_fr315_yamlgraph_async_stdout_logging_without_event_map.py`
  1. `test_ac01_logs_stdout_debug_when_event_map_not_configured`
  2. `test_ac02_logs_stdout_debug_when_event_map_is_empty_dict`
  3. `test_ac03_stdout_debug_log_is_capped_to_2000_chars`
  4. `test_ac04_event_map_routing_behavior_is_unchanged`

RED run command (from repo root):

```bash
pytest tests/unit/test_fr315_yamlgraph_async_stdout_logging_without_event_map.py -q --no-cov
```

Expected RED status on current implementation:

- AC-01/AC-02/AC-03 fail because no DEBUG stdout log is emitted when `event_map` is not used.
- Current run result: `3 failed, 1 passed` (`AC-04` passes, confirming existing event_map routing remains intact).

## Alternatives Considered

1. **Rely on existing INFO exit/length log only** — Rejected; length metadata does not reveal actual planner/enforcer output content.
2. **Expand FR-307 and postpone this issue** — Rejected for this topic; #288 is a narrow missing-log defect and can be planned as a minimal, single-responsibility bug fix.
3. **Log stdout only at WARNING when event_map miss occurs** — Rejected; no-event_map runs never enter miss logic, so the gap remains.

## Related

- Topic source: GitHub issue #288 (`https://github.com/sheikkinen/yamlgraph/issues/288`)
- Requested local topic file: `.chaplain/processing/gh-288.md` (not present in this worktree)
- Target implementation file: `.chaplain/actions/yamlgraph_async_action.py`
- Related draft: `feature-requests/FR-307-yamlgraph-async-action-logging.md`
- Prior art action: `.chaplain/actions/bash_context_action.py` (captures subprocess output boundary in action layer)

## Research Brief

### Existing Abstractions

- `YamlgraphAsyncAction` is the subprocess boundary for watcher yamlgraph graph runs.
- Logging is already centralized in this action (command log, exit/length log, stderr warning, event_map match/miss logs), so this is the correct boundary for the fix.

### Gap Check

- There is no existing unit test in `tests/unit/` covering `.chaplain/actions/yamlgraph_async_action.py`.
- Existing `yamlgraph stdout` DEBUG logging only executes on `event_map` match path; success-without-event_map has no stdout content log.

### Strategic Evidence

- FR-307 identifies broader logging hardening opportunities in the same file, but remains Draft and does not provide a shipped fix for issue #288.
- Adjacent watcher action prior art (`precommit_action.py`, `git_commit_action.py` tests) uses targeted acceptance tests per bug boundary; this FR follows the same minimal test-first pattern.

### Classification Signal

- Abstraction level: **watcher action boundary**
- Recommended approach: **build** (small code+test bug fix)
- Key risk: accidental behavior change in event routing; mitigated by AC-04 scope guard.
