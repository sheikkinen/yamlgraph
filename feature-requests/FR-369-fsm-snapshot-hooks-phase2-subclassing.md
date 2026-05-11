# Feature Request: FR-369 FSM snapshot contract and lifecycle hooks for shared bridge subclassing

**Priority:** HIGH
**Type:** Feature
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-05-11

## Summary

Add the missing extension surface to `yamlgraph.utils.fsm` by introducing a typed snapshot contract (`snapshot.py`) and lifecycle hooks in the shared action/runner so domain integrations can subclass safely without forking dispatch logic.

## Value Statement

FSM integrators can add metrics, stale-event suppression, and pre-snapshot normalization via subclass overrides while keeping one shared bridge implementation.

## Problem

FR-346 established `yamlgraph.utils.fsm` as the shared bridge, but two planned contracts are still missing:

1. `yamlgraph/utils/fsm/snapshot.py` with a typed `SnapshotParams` boundary and `snapshot_params()` factory.
2. Lifecycle hook points in `YamlgraphAsyncAction` and `run_and_dispatch` (`pre_snapshot`, `pre_dispatch`, `on_success`, `on_error`).

Without these contracts, downstream domains must duplicate core dispatch flow to inject domain behavior.

## Research: Existing Patterns, Prior Art, and Gaps

1. **The shared bridge exists but has no extension seam yet.**
   - `yamlgraph/utils/fsm/action.py` and `yamlgraph/utils/fsm/graph_runner.py` implement core behavior but expose no subclass hook callbacks beyond `send_fn`.
2. **Snapshot+hook shape was already planned in prior artifacts.**
   - `.chaplain/done/gh-346.md` documents a Phase 2 design with `snapshot.py` and lifecycle hooks.
3. **Current behavior to preserve is already covered.**
   - `tests/unit/test_fsm_bridge_shared.py` and `examples/fsm-router/tests/test_yamlgraph_async_action.py` lock in guard and event-cascade semantics.
4. **Capability is not already implemented.**
   - `yamlgraph/utils/fsm/` currently contains only `action.py`, `event_sender.py`, `graph_runner.py`, `helpers.py`, and `__init__.py`; no `snapshot.py`.
5. **Topic source discrepancy in this worktree.**
   - Requested source `.chaplain/processing/gh-369.md` is not present; planning source used: GitHub issue #369 plus in-repo artifacts.

## Objectives

1. Add a typed snapshot factory boundary for action execution params/context.
2. Add deterministic, overridable lifecycle hooks without changing default behavior.
3. Keep this extension seam in framework code, not domain forks.

## Constraints

1. **Single responsibility:** snapshot contract + hook points only.
2. **No default behavior regression:** unchanged semantics when hooks are not overridden.
3. **Optional dependency safety:** import-safe behavior without `yamlgraph[fsm]` outside action class constraints.
4. **No domain migration in this FR:** `projects/*` consumers are out of scope.
5. **No Chaplain subprocess bridge changes:** `.chaplain/actions/*` remains out of scope.

## Proposed Solution

### In Scope

1. Add `yamlgraph/utils/fsm/snapshot.py` with:
   - `SnapshotParams` dataclass fields:
     `graph_path`, `initial_state`, `input_key`, `output_key`, `event_key`, `event_map`,
     `success_event`, `failure_event`, `thread_id`, `phase`, `payload_keys`.
   - `snapshot_params(params, context, *, project_root=None)` factory that:
     - raises `ValueError` when `graph` is missing,
     - maps `params["success"]`/`params["failure"]` to `success_event`/`failure_event`,
     - builds `initial_state` from resolved `input_value` and `variables`,
     - defaults `phase="graph"` and `payload_keys=None`.
2. Update `yamlgraph/utils/fsm/action.py` with no-op overridable hooks:
   - `pre_snapshot(params, context) -> None`
   - `on_success(snap, event, elapsed_ms, context) -> None`
   - `on_error(snap, exc, elapsed_ms, context) -> None`
   - `pre_dispatch(snap, event, payload, context) -> bool` (default `True`)
3. Wire hook boundaries explicitly:
   - `execute()` calls `pre_snapshot` before `snapshot_params()`.
   - `execute()` passes `snapshot` and bound callbacks into `run_and_dispatch(...)` (`pre_dispatch_fn`, `on_success_fn`, `on_error_fn`).
4. Extend `yamlgraph/utils/fsm/graph_runner.py` to invoke callbacks deterministically:
   - evaluate `pre_dispatch_fn(...)` before `send_fn(...)`,
   - suppress event send when it returns `False`,
   - call `on_success_fn(...)` on success with event + elapsed time,
   - call `on_error_fn(...)` on exception with error + elapsed time.
5. Export `SnapshotParams` and `snapshot_params` from `yamlgraph/utils/fsm/__init__.py`.
6. Add traceability entries (`CAP-146`, `REQ-YG-347`) in capability and architecture registries.

### Out of Scope

1. Migrating any domain repository implementation.
2. Refactoring event-resolution cascade rules.
3. Changing transport/socket behavior in `event_sender.py`.

## Acceptance Criteria

- [x] **AC-01:** `CAP-146` + `REQ-YG-347` are added to capability and architecture registries for the FSM snapshot/hook extension contract.
- [x] **AC-02:** `yamlgraph/utils/fsm/snapshot.py` exists and defines `SnapshotParams` with fields `graph_path`, `initial_state`, `input_key`, `output_key`, `event_key`, `event_map`, `success_event`, `failure_event`, `thread_id`, `phase`, `payload_keys`.
- [x] **AC-03:** `snapshot_params()` raises `ValueError` when `graph` param is missing.
- [x] **AC-04:** `snapshot_params()` maps `success`/`failure` params into `success_event`/`failure_event`, builds `initial_state` from context-resolved input and variables, and defaults `phase="graph"` and `payload_keys=None`.
- [x] **AC-05:** `YamlgraphAsyncAction` exposes `pre_snapshot`, `on_success`, `on_error`, and `pre_dispatch` base methods with no-op/`True` defaults.
- [x] **AC-06:** `execute()` invokes `pre_snapshot` and passes `snapshot` plus bound hook callbacks into `run_and_dispatch`.
- [x] **AC-07:** `run_and_dispatch` invokes `pre_dispatch` before `send_fn`; when it returns `False`, event dispatch is suppressed.
- [x] **AC-08:** `run_and_dispatch` invokes `on_success` on success and `on_error` on exception with elapsed timing metadata.
- [x] **AC-09:** `yamlgraph.utils.fsm` public API exports `SnapshotParams` and `snapshot_params`.

## Failing Acceptance Tests (RED plan)

RED test artifact:

- `tests/unit/test_fr369_fsm_snapshot_hooks_red.py`

Planned RED tests:

1. `test_ac01_registry_entries_for_cap146_and_reqyg347_exist`
2. `test_ac02_snapshot_dataclass_contract_exists`
3. `test_ac03_snapshot_params_requires_graph`
4. `test_ac04_snapshot_params_maps_fields_and_defaults`
5. `test_ac05_action_exposes_required_hook_methods`
6. `test_ac06_action_wires_snapshot_and_hook_callbacks_to_dispatch`
7. `test_ac07_graph_runner_supports_pre_dispatch_suppression`
8. `test_ac08_graph_runner_calls_success_and_error_hooks`
9. `test_ac09_public_api_exports_snapshot_symbols`

RED command:

```bash
pytest tests/unit/test_fr369_fsm_snapshot_hooks_red.py -q --no-cov
```

Post-implementation regression command:

```bash
pytest tests/unit/test_fsm_bridge_shared.py -q --no-cov
pytest examples/fsm-router/tests/test_yamlgraph_async_action.py -q --no-cov
```

## Alternatives Considered

1. **Domain-level fork of bridge logic**
   - Rejected: recreates drift that shared bridge extraction was meant to eliminate.
2. **Action-only hooks without runner callback support**
   - Rejected: no deterministic seam for dispatch suppression and success/error hook timing.
3. **Keep params untyped in `action.py` only**
   - Rejected: loses explicit boundary contract and repeatable test surface.

## Related

- Issue #369: <https://github.com/sheikkinen/yamlgraph/issues/369>
- `.chaplain/done/gh-346.md`
- `feature-requests/FR-346-extract-shared-fsm-bridge-phase1.md`
- `yamlgraph/utils/fsm/action.py`
- `yamlgraph/utils/fsm/graph_runner.py`
- `yamlgraph/utils/fsm/__init__.py`
