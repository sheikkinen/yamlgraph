# Feature Request: FR-392 Forward `snapshot.payload_keys` into shared FSM dispatch payload

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 0.5 day
**Requested:** 2026-05-15

## Summary

Fix `yamlgraph.utils.fsm.graph_runner.run_and_dispatch()` so configured `SnapshotParams.payload_keys` are copied from checkpoint state (`after_state.values`) into dispatched event payloads.

## Value Statement

FSM integrators keep intended context keys (for example `prior_messages` and `original_intent`) in emitted events, preventing silent data loss in checkpointed shared-runner flows.

## Problem

`SnapshotParams` already carries `payload_keys` (`yamlgraph/utils/fsm/snapshot.py`), but `run_and_dispatch()` currently only emits `output_key` from `result` and ignores `payload_keys` (`yamlgraph/utils/fsm/graph_runner.py`).

This creates a contract gap: action configuration accepts `payload_keys`, but dispatched payloads drop those keys silently. The gap appears specifically on the checkpointer path where `after_state` is available.

## Research: Existing Patterns, Prior Art, and Gaps

1. **Typed boundary exists but is partially consumed.**
   - `SnapshotParams` includes `payload_keys` and `snapshot_params()` normalizes it.
   - `run_and_dispatch()` receives `snapshot` but never reads `snapshot.payload_keys`.
2. **The exact data source already exists in current flow.**
   - Checkpointed execution already calls `app.aget_state(run_config)` after graph run and stores `after_state`; this is the right boundary to read state-derived payload keys.
3. **Current tests do not cover this contract.**
   - `tests/unit/test_fsm_bridge_shared.py` verifies event cascade and `output_key` payload behavior, but has no assertions for `payload_keys`.
4. **No competing implementation found in this codebase.**
   - Repository search shows no other shared-runner path forwarding `payload_keys`.
5. **Architecture alignment.**
   - REQ-YG-347 (FR-369) defines the snapshot/hook contract including `payload_keys`; this FR closes an uncovered behavior gap in that existing contract.
6. **Topic source discrepancy in this worktree.**
   - Requested source `.chaplain/processing/gh-392.md` is absent; planning source used: GitHub issue #392 plus in-repo code and FR artifacts.

## Objectives

1. Ensure configured `payload_keys` are forwarded into FSM event payloads on checkpointed runs.
2. Preserve existing dispatch semantics (`event_map`, route fallback, success/failure handling, guard cleanup).
3. Keep scope to runner payload composition only (no new hooks, no new action type).

## Constraints

1. **Single responsibility:** only `payload_keys` forwarding behavior.
2. **Checkpoint path only:** behavior applies when `run_config` is used (`thread_id` configured), because only then `after_state` exists.
3. **No silent broad fallback:** absent keys are skipped; do not inject defaults.
4. **Serialization consistency:** all forwarded values pass through existing `json_safe()`.
5. **No architecture expansion:** reuse existing REQ-YG-347 traceability; do not add a new capability.

## Proposed Solution

### In Scope

1. In `run_and_dispatch()`, after checkpointed execution obtains `after_state`:
   - iterate `snapshot.payload_keys` when `snapshot` is provided and `payload_keys` is non-empty,
   - read each key from `after_state.values`,
   - include key in payload only when present/non-`None`,
   - serialize values via `json_safe()`.
2. Keep existing `output_key` payload behavior intact.
3. Add focused unit tests for payload forwarding and missing-key skip behavior.

Example action config:

```yaml
actions:
  classify:
    - type: yamlgraph_async
      params:
        graph: graphs/router.yaml
        thread_id: "{session_id}"
        output_key: yamlgraph_result
        payload_keys:
          - prior_messages
          - original_intent
```

### Out of Scope

1. Changes to `snapshot_params()` shape or defaults.
2. Changes to event-resolution cascade order.
3. Domain-specific migrations outside `yamlgraph/utils/fsm/`.

## Acceptance Criteria

- [x] **AC-01:** `run_and_dispatch()` includes keys from `snapshot.payload_keys` in dispatched payload when running with `run_config` and keys exist in `after_state.values`.
- [x] **AC-02:** Missing keys in `after_state.values` are skipped without raising errors.
- [x] **AC-03:** Values forwarded via `payload_keys` are serialized with `json_safe()` before dispatch.
- [x] **AC-04:** Existing `output_key` payload behavior remains unchanged.
- [x] **AC-05:** Non-checkpointed path (no `thread_id`/`run_config`) keeps current behavior with no dependency on `after_state`.
- [x] **AC-06:** Targeted unit tests are added for AC-01..AC-05 and existing shared FSM bridge tests remain green.

## Failing Acceptance Tests (RED plan)

RED test artifact:

- `tests/unit/test_fr392_fsm_payload_keys_forwarding_red.py`

Planned RED tests (each marked `@pytest.mark.req("REQ-YG-347")`):

1. `test_ac01_forwards_payload_keys_from_after_state`
2. `test_ac02_skips_missing_payload_keys_without_error`
3. `test_ac03_serializes_payload_keys_with_json_safe`
4. `test_ac04_preserves_existing_output_key_payload`
5. `test_ac05_legacy_non_checkpoint_path_unchanged`

RED command:

```bash
pytest tests/unit/test_fr392_fsm_payload_keys_forwarding_red.py -q --no-cov
```

Post-implementation regression command:

```bash
pytest tests/unit/test_fsm_bridge_shared.py -q --no-cov
```

## Alternatives Considered

1. **Read `payload_keys` from `result` only**
   - Rejected: keys are intended to come from checkpointed graph state, not only node return payload.
2. **Resolve/expand payload in `snapshot_params()`**
   - Rejected: `snapshot_params()` runs before execution and has no access to `after_state.values`.
3. **Add a new lifecycle hook just for payload enrichment**
   - Rejected: larger API surface and scope creep for a targeted bug fix.

## Implementation Notes

1. `yamlgraph/utils/fsm/graph_runner.py`
   - Added `_collect_payload_from_after_state()` to read configured `snapshot.payload_keys` from checkpoint `after_state.values`.
   - Forwarded only present and non-`None` keys, serialized via `json_safe()`.
   - Preserved `output_key` precedence by avoiding overwrite when forwarded keys collide.
2. `tests/unit/test_fr392_fsm_payload_keys_forwarding_red.py`
   - Added AC-focused tests for forwarding, missing-key skip, serialization, output_key preservation, and non-checkpoint behavior.
3. Scope stayed within shared runner payload composition; no snapshot contract or event cascade changes.

## Related

- Issue #392: <https://github.com/sheikkinen/yamlgraph/issues/392>
- `yamlgraph/utils/fsm/snapshot.py`
- `yamlgraph/utils/fsm/graph_runner.py`
- `tests/unit/test_fsm_bridge_shared.py`
- `feature-requests/FR-369-fsm-snapshot-hooks-phase2-subclassing.md`
- `ARCHITECTURE.md` (REQ-YG-347)
