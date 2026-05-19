# Feature Request: FR-411 re-integrate Inquisitor cadence into watcher2 dispatcher FSM

**Priority:** HIGH
**Type:** Enhancement
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-05-19

## Summary

Restore periodic Inquisitor execution in the FSM runtime by adding an `auditing` branch to the watcher2 dispatcher loop, so idle periods trigger `.chaplain/inquisitor.sh --propose` at most once per 24 hours.

## Value Statement

Maintainers regain continuous doctrine enforcement in the active watcher runtime, preventing long audit gaps and turning persistent violations into actionable inbox proposals without manual operator intervention.

## Problem

Issue #411 reports a regression: Inquisitor cadence existed in the retired shell watcher flow but is absent from the current FSM dispatcher pipeline. The result is an audit blind spot (reported 27-day gap) while the production runtime now depends on:

- `.chaplain/scripts/start-system.sh` (entrypoint)
- `.chaplain/config/watcher-dispatcher.yaml` (outer loop)
- `.chaplain/config/watcher-pipeline-v2.yaml` (worker loop)

Current dispatcher behavior only cycles:

```text
idle -> syncing_inbox -> (topic_found -> processing_topic -> idle) | (no_topics -> idle)
```

There is no audit state, no `last_audit_ts` context, and no cadence event routing.

## Research Findings

1. **Requested source topic file is missing in this worktree.**
   `.chaplain/processing/gh-411.md` is absent; GitHub issue #411 body was used as canonical source for this FR.

2. **Regression is plausible from local runtime history.**
   Legacy orchestrators (`.chaplain/watch.sh`, `.chaplain/watcher2.sh`) are intentionally retired (see `tests/unit/test_retire_old_pipeline_scripts.py`), and the current dispatcher config has no Inquisitor path.

3. **Inquisitor capability already exists and is reusable.**
   `.chaplain/inquisitor.sh` already supports `--propose`, commit-delta gating, and worktree gating (`REQ-YG-118`, `REQ-YG-131`, `REQ-YG-142`). This FR is orchestration wiring, not a new audit engine.

4. **Action model supports this change with small surface area.**
   Existing custom actions (`validate_gate_action.py`, `changelog_gen_action.py`) mutate context and return event names, which matches the needed `audit_needed` / `audit_done` dispatcher routing.

5. **`bash_context` cannot express cadence-aware branching on successful no-topic sync.**
   `.chaplain/actions/bash_context_action.py` only emits fixed `success`/`error` events from process return code; it cannot choose between `no_topics` and `audit_needed` based on `last_audit_ts` when dispatch exits non-zero but sync succeeds.

6. **The issue-design “3 files” target remains feasible.**
   In this codebase, `syncing_inbox` routing logic should live in a dedicated action module (rather than static `bash_context` wiring) to emit cadence-aware events deterministically.

## Objectives

1. Reintroduce periodic Inquisitor execution into the active watcher2 FSM runtime.
2. Ensure audits trigger only when no topic is available **and** at least 24h elapsed since last audit.
3. Preserve topic processing priority (topic work must preempt audit).
4. Keep dispatcher resilient: audit failures must not stop the daemon loop.

## Constraints

1. Single responsibility: dispatcher audit cadence only (no changes to pipeline v2 plan/judge/enforce logic).
2. Reuse existing Inquisitor script and gates; no duplicate policy engine.
3. No new dependencies.
4. Preserve existing dispatcher stop semantics and 10s polling cadence.
5. Keep change surface minimal (target: dispatcher YAML + syncing-inbox action + audit action).

## Proposed Solution

### FSM changes (`.chaplain/config/watcher-dispatcher.yaml`)

1. Add context key:
   - `last_audit_ts: 0`
2. Add operational state:
   - `auditing`
3. Add events:
   - `audit_needed`
   - `audit_done`
4. Add transitions:
   - `syncing_inbox --audit_needed--> auditing`
   - `auditing --audit_done--> idle`
   - `auditing --error--> idle` (non-fatal recovery)

### Syncing inbox cadence action (`.chaplain/actions/syncing_inbox_action.py`)

Replace static `bash_context` no-topic routing with cadence-aware event emission.
The action **must** replicate the existing shell execution before applying cadence logic:

1. Run `bash .chaplain/lib/watcher/inbox_sync.sh 2>/dev/null || true` (non-fatal).
2. Run `python .chaplain/lib/watcher/dispatch_topic.py --inbox-dir {inbox_dir} --processing-dir .chaplain/processing` and parse the last JSON line from stdout.
3. Merge the following keys from parsed JSON into `context` when present:
   `topic_file`, `project`, `branch_prefix`, `work_dir`, `test_cmd`, `precommit_config`, `fr_template`, `architecture_doc`.
4. Apply routing:
   - If `dispatch_topic.py` exits 0 (topic found): return `topic_found`.
   - If `dispatch_topic.py` exits non-zero (no topic) **and** shell execution itself succeeded:
     - when `time.time() - context["last_audit_ts"] >= 86400`: return `audit_needed`
     - else return `no_topics`
   - If `dispatch_topic.py` invocation itself raises an exception or subprocess cannot start:
     return `no_topics` (preserves current `bash_context error → no_topics` behavior;
     daemon must not stall on inbox sync failures).

### Audit action (`.chaplain/actions/audit_action.py`)

- Execute: `bash .chaplain/inquisitor.sh --propose`
- On success:
  - set `context["last_audit_ts"] = int(time.time())`
  - return `audit_done`
- On failure:
  - return `error` (dispatcher routes back to `idle`)

### Expected flow

```text
idle -> syncing_inbox
  topic_found  -> processing_topic -> idle
  no_topics    -> idle
  audit_needed -> auditing -> audit_done/error -> idle
```

## Known Limitations

- **`last_audit_ts` is in-memory only.** It is not persisted across daemon restarts. Default value `0` means the first idle cycle after any daemon start triggers an audit immediately. This is acceptable behavior (fills any gap created by a restart) and is intentional.

## Out of Scope

1. Altering Inquisitor internals (`.chaplain/inquisitor.sh`) beyond invocation.
2. Reworking watcher-pipeline-v2 states or validate/remediation logic.
3. Changing audit cadence from fixed 24h to configurable policy.
4. Multi-project cadence partitioning (single `last_audit_ts` only in this FR).

## Requirement Traceability Plan

1. Add new capability entry (proposed): `CAP-152 Watcher2 Dispatcher Audit Cadence`.
2. Add new requirement (proposed): `REQ-YG-407`.
3. Add ARCHITECTURE row for `REQ-YG-407`.
4. Tag new acceptance tests with `@pytest.mark.req("REQ-YG-407")`.

## Acceptance Criteria

- [x] **AC-01:** Dispatcher config defines `auditing` state, `audit_needed` event, and `audit_done` event.
- [x] **AC-02:** Dispatcher context includes `last_audit_ts` initialized to `0`.
- [x] **AC-03:** When no topic is available and `last_audit_ts` is older than 24h, `syncing_inbox` emits `audit_needed`.
- [x] **AC-04:** When no topic is available and cadence window is not elapsed, `syncing_inbox` emits `no_topics`.
- [x] **AC-05:** When a topic is available, `syncing_inbox` still emits `topic_found` (audit path does not delay topic processing).
- [x] **AC-06:** `audit_action` invokes `.chaplain/inquisitor.sh --propose`.
- [x] **AC-07:** Successful `audit_action` updates `last_audit_ts` and emits `audit_done`.
- [x] **AC-08:** Failed `audit_action` emits `error` and dispatcher returns to `idle` (daemon remains alive).
- [x] **AC-09:** Shell failure in `syncing_inbox_action` returns `no_topics` (daemon does not stall on inbox sync errors; preserves current `bash_context error → no_topics` behavior).
- [x] **AC-10:** Requirement and capability registries are updated for `REQ-YG-407` and tests are tagged accordingly.

## Failing Acceptance Tests (RED plan)

Create:

- `tests/unit/test_fr411_watcher2_dispatcher_inquisitor_audit_cadence.py`

Planned RED tests:

1. `test_ac01_dispatcher_declares_auditing_state_and_audit_events`
2. `test_ac02_dispatcher_context_includes_last_audit_ts`
3. `test_ac03_syncing_inbox_emits_audit_needed_when_cadence_elapsed`
4. `test_ac04_syncing_inbox_emits_no_topics_when_cadence_not_elapsed`
5. `test_ac05_syncing_inbox_preserves_topic_found_priority`
6. `test_ac06_audit_action_invokes_inquisitor_with_propose_flag`
7. `test_ac07_audit_action_updates_last_audit_ts_on_success`
8. `test_ac08_audit_error_routes_back_to_idle`
9. `test_ac09_syncing_inbox_returns_no_topics_on_shell_failure`

RED command:

```bash
pytest tests/unit/test_fr411_watcher2_dispatcher_inquisitor_audit_cadence.py -q --no-cov
```

## Alternatives Considered

1. **Run Inquisitor on every idle loop (`no_topics`)**
   Rejected: turns audit into ritual noise and increases unnecessary runs.

2. **Run Inquisitor only after each processed topic**
   Rejected: starvation risk during long idle periods (the regression scenario).

3. **External cron/systemd timer outside dispatcher FSM**
   Rejected: splits orchestration ownership and weakens FSM observability.

4. **Keep manual Inquisitor-only workflow**
   Rejected: proven operational drift (long audit gaps).

## Related

- Issue #411: <https://github.com/sheikkinen/yamlgraph/issues/411>
- `.chaplain/config/watcher-dispatcher.yaml`
- `.chaplain/actions/` (custom FSM action pattern)
- `.chaplain/inquisitor.sh`
- `.chaplain/scripts/start-system.sh`
- `feature-requests/FR-261-inquisitor-into-watch-loop.md`
- `feature-requests/FR-276-retire-old-pipeline-scripts.md`
- `feature-requests/FR-296-watcher-fsm-startup-script.md`
- `feature-requests/FR-305-watcher-pipeline-fsm-simplification.md`
- `ARCHITECTURE.md` (`REQ-YG-118`, `REQ-YG-131`, `REQ-YG-142`, proposed `REQ-YG-407`)
