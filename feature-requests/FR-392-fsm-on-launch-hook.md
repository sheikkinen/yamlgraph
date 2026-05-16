# Feature Request: FR-392 on_launch lifecycle hook for YamlgraphAsyncAction

**Priority:** HIGH
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-05-15

## Summary

Add an `on_launch(snap, context)` lifecycle hook to `yamlgraph.utils.fsm.action.YamlgraphAsyncAction`, invoked after `snapshot_params()` succeeds and before `asyncio.create_task(...)`.

## Value Statement

FSM bridge subclasses can observe fully resolved launch metadata (graph path, phase, success/failure events) without duplicating snapshot derivation logic or overriding `execute()`.

## Problem

`YamlgraphAsyncAction` currently exposes:

1. `pre_snapshot(params, context)` before snapshot materialization
2. `pre_dispatch(...)`, `on_success(...)`, and `on_error(...)` during/after runner dispatch

There is no hook at the boundary immediately after `SnapshotParams` is created and validated, but before background task launch. Subclasses that need resolved launch telemetry must currently:

1. Reconstruct resolved values in `pre_snapshot` from raw params (duplicates `snapshot_params()` behavior), or
2. Override `execute()` to inject one line of custom logic (copies core orchestration and increases drift risk).

## Research: Existing Patterns, Prior Art, and Gaps

1. **Existing hook surface confirms a gap.**
   - `yamlgraph/utils/fsm/action.py` has `pre_snapshot`, `pre_dispatch`, `on_success`, `on_error`; no launch-time hook between snapshot and task scheduling.

2. **Snapshot contract already provides the needed typed payload.**
   - `yamlgraph/utils/fsm/snapshot.py` defines `SnapshotParams` with resolved fields (`graph_path`, `phase`, `success_event`, `failure_event`, etc.), making this boundary ideal for a launch hook.

3. **Architecture alignment exists under current capability.**
   - `ARCHITECTURE.md` Capability 146 (`REQ-YG-347`) already tracks FSM snapshot + lifecycle hook behavior. This FR extends that same lifecycle contract with one additional hook.

4. **Feature source discrepancy in this worktree.**
   - Requested source `.chaplain/processing/feat-fsm-on-launch-hook.md` is not present; planning source used: GitHub issue #394 (`feat(fsm): add on_launch hook to YamlgraphAsyncAction`).

## Objectives

1. Add a launch-time extension seam with resolved snapshot values.
2. Keep default behavior unchanged for callers that do not override the hook.
3. Preserve fail-closed behavior when snapshot creation fails.

## Constraints

1. Single responsibility: lifecycle hook addition only.
2. No changes to event resolution, dispatch transport, or guard semantics.
3. No Chaplain subprocess bridge changes under `.chaplain/actions/`.
4. Preserve existing `ValueError` handling path in `execute()`.

## Proposed Solution

### In Scope

1. Add base no-op hook:
   - `def on_launch(self, _snap: SnapshotParams, _context: dict[str, Any]) -> None: ...`
2. In `YamlgraphAsyncAction.execute()`:
   - call `self.on_launch(snapshot, context)` immediately after `snapshot_params(...)` returns
   - call occurs before `asyncio.create_task(...)`
3. Keep existing behavior unchanged when `snapshot_params(...)` raises `ValueError`:
   - return failure event and do not invoke `on_launch`.
4. Extend REQ-aligned tests for lifecycle contract.

### Out of Scope

1. New telemetry/output payload formats.
2. Any changes in `yamlgraph.utils.fsm.graph_runner` hook sequence.
3. Migration changes in downstream domain repositories.

## Acceptance Criteria

- [x] **AC-01:** `YamlgraphAsyncAction` exposes `on_launch(snap, context)` with a default no-op implementation.
- [x] **AC-02:** `execute()` invokes `on_launch` after `snapshot_params()` succeeds and before `asyncio.create_task(...)`.
- [x] **AC-03:** `on_launch` receives the resolved `SnapshotParams` instance produced by `snapshot_params()`.
- [x] **AC-04:** `on_launch` is not called when `snapshot_params()` raises `ValueError`.
- [x] **AC-05:** Existing lifecycle behavior (`pre_snapshot`, `pre_dispatch`, `on_success`, `on_error`) remains unchanged.

## Failing Acceptance Tests (RED plan)

RED test artifact:

- `tests/unit/test_fr392_fsm_on_launch_hook_red.py`

Planned RED tests:

1. `test_ac01_action_exposes_on_launch_hook_method`
2. `test_ac02_execute_calls_on_launch_between_snapshot_and_create_task`
3. `test_ac03_subclass_receives_resolved_snapshot_in_on_launch`
4. `test_ac04_on_launch_not_called_when_snapshot_params_raises`

RED command:

```bash
pytest tests/unit/test_fr392_fsm_on_launch_hook_red.py -q --no-cov
```

Targeted regression command after implementation:

```bash
pytest tests/unit/test_fr369_fsm_snapshot_hooks_red.py -q --no-cov
pytest tests/unit/test_fsm_bridge_shared.py -q --no-cov
```

## Alternatives Considered

1. **Use `pre_snapshot` only and reconstruct resolved values**
   - Rejected: duplicates `snapshot_params()` logic and invites drift.
2. **Override `execute()` in every subclass**
   - Rejected: recreates orchestration code and weakens shared-bridge guarantees.
3. **Emit launch telemetry from `run_and_dispatch`**
   - Rejected: too late; launch metadata should be available before background scheduling.

## Related

- Issue #394: <https://github.com/sheikkinen/yamlgraph/issues/394>
- `yamlgraph/utils/fsm/action.py`
- `yamlgraph/utils/fsm/snapshot.py`
- `feature-requests/FR-369-fsm-snapshot-hooks-phase2-subclassing.md`
- `ARCHITECTURE.md` (`REQ-YG-347`, Capability 146)
