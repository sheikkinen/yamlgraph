# Feature Request: FR-392 strip `_race_winner` from shared FSM dispatch payload path

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 0.5 day
**Requested:** 2026-05-15

## Summary

Ensure `yamlgraph.utils.fsm.graph_runner.run_and_dispatch()` removes race telemetry metadata key `_race_winner` from graph result data before FSM event payload construction, so framework-internal race winner details never cross the FSM bridge boundary.

## Value Statement

FSM consumers get clean, domain-only event payloads while race-node telemetry remains internal to YAMLGraph state, removing application-level cleanup workarounds and preventing internal metadata contract leakage.

## Problem

Race-capable nodes (`type: race` and router-with-candidates race path) intentionally emit `_race_winner` in graph state for telemetry and diagnostics.

`run_and_dispatch()` is the shared FSM boundary. Today it forwards payload data from graph results without explicitly normalizing/removing internal race metadata keys before dispatch payload assembly. This allows framework-private key `_race_winner` to propagate to downstream FSM integrations when selected/output payload keys overlap, violating boundary hygiene and forcing application-level cleanup logic.

The shared bridge should normalize this at the framework boundary rather than require per-application filtering.

## Research Findings

1. **Topic source file requested in prompt is missing in this worktree.**
   - Requested source: `.chaplain/processing/gh-395.md`
   - Actual source used: GitHub issue #395 (`fix(fsm): run_and_dispatch leaks _race_winner into FSM event payload`).

2. **Race metadata is intentionally produced by node factories.**
   - `yamlgraph/node_factory/race_node.py` returns `_race_winner` in node result.
   - `yamlgraph/node_factory/router_race_node.py` also returns `_race_winner`.
   - This is required by race capabilities (`REQ-YG-233`, `REQ-YG-271`) and must remain in graph state.

3. **Shared dispatch boundary is centralized in `run_and_dispatch()`.**
   - `yamlgraph/utils/fsm/graph_runner.py` is the canonical bridge (`REQ-YG-319`, `REQ-YG-347`).
   - Existing tests (`tests/unit/test_fsm_bridge_shared.py`) validate event cascade and payload basics but do not lock a contract that `_race_winner` is excluded from dispatched payload.

4. **No repository-local helper named `_pop_race_winner` exists.**
   - No existing reusable boundary sanitizer for this key is present in the codebase, so the shared runner is the correct callsite for normalization.

## Objectives

1. Strip `_race_winner` from result data at the shared FSM boundary before payload construction.
2. Preserve `_race_winner` telemetry observability via INFO logging in the shared runner.
3. Keep existing event resolution and dispatch semantics unchanged outside this specific metadata normalization.

## Constraints

1. Single responsibility: modify only shared FSM dispatch normalization behavior.
2. Do not change race node output contracts (`_race_winner` remains in graph state generation).
3. Do not alter event resolution ordering, hook APIs, or Unix socket dispatch protocol.
4. Maintain requirement traceability under existing shared-bridge requirement (`REQ-YG-319`); no new capability introduction for this bug fix.

## Proposed Solution

### In scope

1. In `yamlgraph/utils/fsm/graph_runner.py`, immediately after `result = await run_fn(...)`, normalize dict results by removing `_race_winner`:
   - `winner = result.pop("_race_winner", None)`
2. If removed value exists, emit an INFO log entry with winner metadata for diagnostics.
3. Build payload from normalized result, guaranteeing `_race_winner` cannot appear in dispatched FSM payload.
4. Add focused unit tests for payload exclusion + logging + non-regression behavior.

### Out of scope

1. Changes to race node factories or state builder contracts.
2. New telemetry schema or structured logging overhaul.
3. FSM action-level domain customizations outside `yamlgraph.utils.fsm.graph_runner`.

## Acceptance Criteria

- [x] **AC-01:** `run_and_dispatch()` removes `_race_winner` from dict results before payload assembly.
- [x] **AC-02:** When `_race_winner` exists in graph result, dispatched payload does not include `_race_winner` under any output mapping.
- [x] **AC-03:** Removal of `_race_winner` emits an INFO log entry including winner metadata.
- [x] **AC-04:** Existing event resolution cascade behavior remains unchanged for non-race payloads.
- [x] **AC-05:** Requirement-tagged tests cover AC-01..AC-04 under `REQ-YG-319`.

## Failing Acceptance Tests (RED plan)

Create:

- `tests/unit/test_fr392_fsm_strip_race_winner_payload_red.py`

Planned RED tests:

1. `test_ac01_strips_race_winner_before_payload_build`
2. `test_ac02_payload_excludes_race_winner_even_when_result_contains_it`
3. `test_ac03_logs_race_winner_metadata_at_info`
4. `test_ac04_existing_route_and_event_map_resolution_unchanged`

RED command:

```bash
pytest tests/unit/test_fr392_fsm_strip_race_winner_payload_red.py -q --no-cov
```

Targeted regression command:

```bash
pytest tests/unit/test_fsm_bridge_shared.py tests/unit/test_fr391_fsm_phase_aware_event_resolution.py -q --no-cov
```

## Alternatives Considered

1. **Leave filtering to application wrappers**
   - Rejected: duplicates boundary logic across consumers and violates shared bridge contract centralization.

2. **Filter in race node factories**
   - Rejected: `_race_winner` is intentionally part of graph-state telemetry and needed for race capabilities; boundary filtering belongs in FSM bridge.

3. **Introduce generic “strip private keys” mechanism**
   - Rejected for now: broader policy design increases scope and risk; this issue requires a targeted fix for known leaked key.

## Related

- Issue #395: <https://github.com/sheikkinen/yamlgraph/issues/395>
- `yamlgraph/utils/fsm/graph_runner.py`
- `yamlgraph/node_factory/race_node.py`
- `yamlgraph/node_factory/router_race_node.py`
- `tests/unit/test_fsm_bridge_shared.py`
- `tests/unit/test_fr391_fsm_phase_aware_event_resolution.py`
- `ARCHITECTURE.md` (`REQ-YG-233`, `REQ-YG-271`, `REQ-YG-319`, `REQ-YG-347`)
