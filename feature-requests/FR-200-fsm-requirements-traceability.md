# Feature Request: FSM Requirements Traceability

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved
**Effort:** 1.5 days
**Requested:** 2026-03-13

## Summary

Add full requirements traceability to the `fsm/` (statemachine-engine) subproject: create `fsm/ARCHITECTURE.md` with REQ-FSM-001–036 covering all capability areas, tag all 36 existing test files with `@pytest.mark.req`, adapt `scripts/req_coverage.py` for the FSM prefix, and add a `req-coverage-strict` pre-commit hook to `fsm/.pre-commit-config.yaml`.

## Value Statement

FSM contributors get automated proof that every capability has a test, matching the traceability gate already enforced on YAMLGraph — eliminating undocumented requirements and silent regressions.

## Problem

`fsm/` has 38 test files exercising a rich set of capabilities (engine, actions, database, monitoring, communication, tools, utils) but zero requirements traceability. There is no `ARCHITECTURE.md`, no `@pytest.mark.req` tags, and no coverage script. This means:

- Silent regressions cannot be attributed to a specific requirement.
- PRs cannot be blocked for requirement coverage gaps.
- The doctrine rule *"every test must have `@pytest.mark.req`"* is enforced on YAMLGraph but not on FSM, violating the `infrastructure-self-exempt` trap (see Scripture Knowledge Graph).

## Proposed Solution

### Step 1: Create `fsm/ARCHITECTURE.md`

A flat requirements table (no capability YAML files — FSM is self-contained) with 36 requirements grouped by subsystem:

| ID | Description |
|----|-------------|
| REQ-FSM-001 | State machine definition loaded from YAML |
| REQ-FSM-002 | State transition execution on event receipt |
| REQ-FSM-003 | Entry/exit actions executed on state change |
| REQ-FSM-004 | Event-driven transitions between states |
| REQ-FSM-005 | Context variable interpolation in action params |
| REQ-FSM-006 | Timeout-triggered transitions |
| REQ-FSM-007 | Error state transitions on action failure |
| REQ-FSM-008 | Multiple engine instances run concurrently |
| REQ-FSM-009 | Log action writes structured state events |
| REQ-FSM-010 | Bash action executes shell commands |
| REQ-FSM-011 | Bash action enforces timeout |
| REQ-FSM-012 | Bash action falls back on command failure |
| REQ-FSM-013 | Bash action handles quote-safe variable injection |
| REQ-FSM-014 | Activity log action appends to activity history |
| REQ-FSM-015 | List management actions (add/clear) |
| REQ-FSM-016 | Nested FSM start action |
| REQ-FSM-017 | Job claim action reserves a queued job |
| REQ-FSM-018 | Job complete action marks job done |
| REQ-FSM-019 | Get pending jobs action queries the job queue |
| REQ-FSM-020 | Wait-for-jobs action blocks until jobs finish |
| REQ-FSM-021 | Send event action dispatches events |
| REQ-FSM-022 | Clear events action flushes pending events |
| REQ-FSM-023 | SQLite job queue persists jobs across restarts |
| REQ-FSM-024 | Job queue CLI exposes management commands |
| REQ-FSM-025 | Job history commands retrieve past runs |
| REQ-FSM-026 | Job queue is machine-agnostic |
| REQ-FSM-027 | No SQLite connection leaks |
| REQ-FSM-028 | WebSocket server broadcasts state changes |
| REQ-FSM-029 | Async logging does not block the engine |
| REQ-FSM-030 | Realtime event delivery to connected clients |
| REQ-FSM-031 | WebSocket server handles stress load |
| REQ-FSM-032 | Control socket accepts runtime commands |
| REQ-FSM-033 | Realtime integration end-to-end delivery |
| REQ-FSM-034 | State machine YAML validation reports errors |
| REQ-FSM-035 | Diagram generation produces valid output |
| REQ-FSM-036 | String interpolation resolves nested field paths |

### Step 2: Tag all tests with `@pytest.mark.req`

Tag every test function in `fsm/tests/` with one or more `@pytest.mark.req("REQ-FSM-XXX")` markers. Mapping guidance:

| Test file | Primary REQ |
|-----------|-------------|
| `test_engine_interpolation.py` | REQ-FSM-005 |
| `test_timeout_events.py` | REQ-FSM-006 |
| `test_engine_error_emission.py` | REQ-FSM-007 |
| `test_multiple_engines.py` | REQ-FSM-008 |
| `test_log_action.py` | REQ-FSM-009 |
| `test_bash_action_timeout.py` | REQ-FSM-011 |
| `test_bash_action_fallback.py` | REQ-FSM-012 |
| `test_bash_action_quotes.py` | REQ-FSM-013 |
| `test_activity_log_action.py` | REQ-FSM-014 |
| `test_add_to_list_action.py` | REQ-FSM-015 |
| `test_clear_events_action.py` | REQ-FSM-022 |
| `test_start_fsm_action.py` | REQ-FSM-016 |
| `test_claim_job_action.py` | REQ-FSM-017 |
| `test_complete_job_action.py` | REQ-FSM-018 |
| `test_get_pending_jobs_action.py` | REQ-FSM-019 |
| `test_wait_for_jobs_action.py` | REQ-FSM-020 |
| `test_send_event_nested_fields.py` | REQ-FSM-021 |
| `test_cli_history_commands.py` | REQ-FSM-025 |
| `test_job_queue_machine_agnostic.py` | REQ-FSM-026 |
| `test_connection_leak.py` | REQ-FSM-027 |
| `test_cli_send_event_realtime.py` | REQ-FSM-030 |
| `test_walking_skeleton.py` | REQ-FSM-023 |
| `test_realtime_event_exceptions.py` | REQ-FSM-030 |
| `test_websocket_server.py` | REQ-FSM-028 |
| `test_async_logging.py` | REQ-FSM-029 |
| `test_websocket_stress.py` | REQ-FSM-031 |
| `test_control_socket.py` | REQ-FSM-032 |
| `test_realtime_integration.py` | REQ-FSM-033 |
| `test_context_map.py` | REQ-FSM-005 |
| `test_custom_actions_dir.py` | REQ-FSM-003 |
| `test_event_socket_reconnect.py` | REQ-FSM-004 |
| `test_json_payload_parsing.py` | REQ-FSM-005 |
| `test_action_loader.py` | REQ-FSM-003 |
| `test_hang_detection.py` | REQ-FSM-006 |
| `test_state_logging.py` | REQ-FSM-009 |
| `test_interpolation.py` | REQ-FSM-036 |

### Step 3: Adapt `scripts/req_coverage.py` for FSM

Create `fsm/scripts/req_coverage.py` that:
- Reads requirements from `fsm/ARCHITECTURE.md` (flat table, no capabilities YAML)
- Scans `fsm/tests/` for `@pytest.mark.req("REQ-FSM-XXX")` markers
- Reports coverage, phantoms, and gaps
- Exits 1 under `--strict` when any requirement is uncovered

The adapter reads the markdown table directly (no `capabilities/` directory) since FSM has no CAP-XXX structure.

### Step 4: Add `req-coverage-strict` to `fsm/.pre-commit-config.yaml`

```yaml
- repo: local
  hooks:
    - id: req-coverage-strict
      name: Requirement coverage (strict)
      entry: python fsm/scripts/req_coverage.py --strict
      language: system
      pass_filenames: false
      always_run: true
```

This hook must be appended to the existing (or new) `fsm/.pre-commit-config.yaml`. If FR-186 (FSM Pre-commit Quality Gates) is already implemented, append to that config; otherwise create the file.

```python
# Example pytest marker (fsm/tests/core/test_engine_error_emission.py)
import pytest

@pytest.mark.req("REQ-FSM-007")
def test_engine_emits_error_event_on_action_failure(fsm_fixture):
    ...
```

## Acceptance Criteria

- [ ] `fsm/ARCHITECTURE.md` exists with a requirements table containing exactly REQ-FSM-001 through REQ-FSM-036, each with a one-line description
- [ ] Every test function in `fsm/tests/` (all 36 files) has at least one `@pytest.mark.req("REQ-FSM-XXX")` decorator
- [ ] `fsm/scripts/req_coverage.py` exists and runs without error: `python fsm/scripts/req_coverage.py`
- [ ] `python fsm/scripts/req_coverage.py --strict` exits 0 (all 36 requirements covered)
- [ ] No phantom requirements: all markers reference IDs present in `fsm/ARCHITECTURE.md`
- [ ] `fsm/.pre-commit-config.yaml` includes the `req-coverage-strict` hook
- [ ] `pre-commit run req-coverage-strict --all-files` in `fsm/` passes
- [ ] New tests added to `fsm/tests/` that lack `@pytest.mark.req` cause `req-coverage-strict` to fail (regression guard)
- [ ] `fsm/pytest.ini` or `pyproject.toml` registers the `req` marker to suppress `PytestUnknownMarkWarning`

## Alternatives Considered

**Share the YAMLGraph `scripts/req_coverage.py` verbatim** — rejected because it reads from `capabilities/*.yaml` files (CAP-XXX pattern), which FSM does not have. A flat ARCHITECTURE.md reader is simpler and avoids forcing a capabilities hierarchy onto a project that doesn't need it.

**Skip FSM traceability, apply only to YAMLGraph** — rejected. The `infrastructure-self-exempt` trap is explicitly named in the Scripture Knowledge Graph: *"Meta-tooling exempted from gates it enforces → apply same rules to the guardrail as to what it guards."* FSM enforces workflow discipline; it must obey the same doctrine.

**Use a shared library for req_coverage** — deferred. Once both scripts stabilize, extract a common parser; premature now.

## Related

- `scripts/req_coverage.py` — YAMLGraph implementation to adapt
- `ARCHITECTURE.md` (root) — pattern for requirements table format
- `fsm/tests/` — 38 test files requiring `@pytest.mark.req` tags
- `fsm/.pre-commit-config.yaml` — target config for the new hook (see FR-186)
- FR-186 — FSM Pre-commit Quality Gates
- FR-199 — FSM CLAUDE.md Doctrine Upgrade
- Scripture: `infrastructure-self-exempt` trap
