# Feature Request: FR-392 fix shared FSM runner payload_keys forwarding

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 0.5 day
**Requested:** 2026-05-15

## Summary

Fix `yamlgraph.utils.fsm.graph_runner.run_and_dispatch()` so `SnapshotParams.payload_keys` is actually forwarded into the dispatched FSM event payload from checkpoint state values.

## Value Statement

FSM integrations using the shared bridge receive the expected state fields (`payload_keys`) in dispatched events, preventing silent context loss during migration to `yamlgraph.utils.fsm`.

## Problem

`SnapshotParams` includes a `payload_keys: list[str] | None` contract in `yamlgraph/utils/fsm/snapshot.py`, but `run_and_dispatch()` currently builds payload from `output_key` only. As a result, configured `payload_keys` are silently ignored even when checkpoint state includes those fields.

Current behavior (simplified):

```python
payload: dict[str, Any] = {}
if isinstance(result, dict) and output_key and output_key in result:
    payload[output_key] = json_safe(result[output_key])
# snapshot.payload_keys never merged into payload
```

This breaks the boundary contract introduced by FR-369 when consumers rely on `payload_keys` for cross-turn/context bridge fields.

## Research: Existing Patterns, Prior Art, and Gaps

1. **Typed contract exists but is underused.**
   - `yamlgraph/utils/fsm/snapshot.py` defines `SnapshotParams.payload_keys` and `snapshot_params()` populates it from action params.
2. **Runner already has the correct data boundary in checkpoint path.**
   - `yamlgraph/utils/fsm/graph_runner.py` already reads `after_state.values` for completion-phase routing (`phase`), so payload-key extraction can happen at the same boundary without extra graph calls.
3. **No current test locks payload_keys dispatch behavior.**
   - Existing FSM bridge tests verify output-key payload and event cascade, but not forwarding of `snapshot.payload_keys`.
4. **Architecture alignment points to existing capability, not a new subsystem.**
   - `ARCHITECTURE.md` Capability 141 (`REQ-YG-319`) owns runner dispatch semantics.
   - Capability 146 (`REQ-YG-347`) introduced `SnapshotParams` and hook wiring, including the `payload_keys` field.
5. **Requested local topic file is missing in this worktree snapshot.**
   - Source used: GitHub issue #392 (`fix(fsm): run_and_dispatch ignores SnapshotParams.payload_keys`).

## Objectives

1. Ensure `run_and_dispatch()` forwards configured `payload_keys` from checkpoint state into dispatched payload.
2. Preserve existing payload behavior (`output_key`) and existing event-resolution cascade.
3. Keep legacy non-checkpointer path unchanged.

## Constraints

1. Single responsibility: payload enrichment only (no cascade/routing refactor).
2. Extraction must only run when checkpoint state is available (`thread_id`/`run_config` path).
3. Missing keys must be skipped without raising errors.
4. Serialization must stay JSON-safe via existing `json_safe()` helper.

## Proposed Solution

### In Scope

1. In `yamlgraph/utils/fsm/graph_runner.py`, after result payload initialization, merge `snapshot.payload_keys` values from `after_state.values` when:
   - `snapshot is not None`
   - `snapshot.payload_keys` is a non-empty list
   - `after_state.values` is a dict
2. For each key in `payload_keys`:
   - if key exists in `after_state.values` and value is not `None`, add `payload[key] = json_safe(value)`.
   - if key is missing or `None`, skip silently.
3. Keep existing `output_key` payload insertion behavior intact.
4. Add focused RED tests for payload-key forwarding and skip semantics.

### Out of Scope

1. Any change to `event_map`/`route`/`success` event resolution order.
2. Any change to action config schema beyond existing `payload_keys`.
3. Any Chaplain subprocess bridge changes under `.chaplain/actions/`.

## Acceptance Criteria

- [x] **AC-01:** `run_and_dispatch()` merges `snapshot.payload_keys` from checkpoint `after_state.values` into dispatched payload.
- [x] **AC-02:** Missing payload keys in checkpoint state are skipped without exception.
- [x] **AC-03:** `None` values for listed payload keys are skipped (not emitted).
- [x] **AC-04:** Existing `output_key` payload behavior remains unchanged.
- [x] **AC-05:** Legacy path without checkpoint state (`thread_id` absent) remains behaviorally unchanged.
- [x] **AC-06:** Requirement-tagged tests cover AC-01..AC-05 under existing FSM bridge requirements.

## Implementation Notes

1. `yamlgraph.utils.fsm.graph_runner.run_and_dispatch()` now collects checkpoint
   `after_state.values` and forwards `snapshot.payload_keys` into payload when
   present, skipping missing/`None` keys.
2. `output_key` payload insertion remains canonical and is not overridden by
   checkpoint payload keys.
3. Added acceptance tests in `tests/unit/test_fr392_fsm_payload_keys_red.py`
   tagged with `@pytest.mark.req("REQ-YG-319")` for AC-01..AC-05.

## Failing Acceptance Tests (RED plan)

RED test artifact:

- `tests/unit/test_fr392_fsm_payload_keys_red.py`

Planned RED tests:

1. `test_ac01_payload_keys_are_forwarded_from_checkpoint_state_values`
2. `test_ac02_missing_payload_keys_are_skipped_without_error`
3. `test_ac03_none_payload_values_are_not_emitted`
4. `test_ac04_output_key_payload_is_preserved_with_payload_keys`
5. `test_ac05_legacy_path_without_thread_id_remains_unchanged`

RED command:

```bash
pytest tests/unit/test_fr392_fsm_payload_keys_red.py -q --no-cov
```

Targeted regression command:

```bash
pytest tests/unit/test_fsm_bridge_shared.py -q --no-cov
pytest tests/unit/test_fr391_fsm_phase_aware_event_resolution.py -q --no-cov
```

## Alternatives Considered

1. **Consumer-specific hook workaround (`pre_dispatch`)**
   - Rejected: duplicates logic in every consumer and keeps shared runner contract incomplete.
2. **Encode all needed fields into `output_key` result upstream**
   - Rejected: pushes transport concerns into graph logic and breaks separation of concerns.
3. **Introduce new payload config surface instead of using `payload_keys`**
   - Rejected: existing field already exists in typed contract; bug is missing wiring, not missing API.

## Related

- Issue #392: <https://github.com/sheikkinen/yamlgraph/issues/392>
- `yamlgraph/utils/fsm/snapshot.py`
- `yamlgraph/utils/fsm/graph_runner.py`
- `tests/unit/test_fsm_bridge_shared.py`
- `feature-requests/FR-369-fsm-snapshot-hooks-phase2-subclassing.md`
- `feature-requests/FR-391-fsm-phase-aware-event-resolution.md`
- `ARCHITECTURE.md` (Capability 141 / `REQ-YG-319`, Capability 146 / `REQ-YG-347`)
