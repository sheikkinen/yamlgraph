# Feature Request: FR-392 sanitize `_race_winner` in shared FSM event payloads

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 0.5 day
**Requested:** 2026-05-15

## Summary

Sanitize framework-internal race metadata in `yamlgraph.utils.fsm.graph_runner.run_and_dispatch()` by stripping top-level `_race_winner` from the graph result before FSM payload construction, and log the stripped value at INFO for diagnostics.

## Value Statement

FSM consumers receive only contract payload fields (not framework-internal race telemetry), removing application-level workaround code and restoring boundary hygiene in the shared bridge.

## Problem

`type: race` and router-race (`router` with `candidates`) intentionally emit `_race_winner` metadata into graph state for telemetry. The shared FSM runner currently has no explicit metadata-sanitization step before payload assembly, so `_race_winner` can leak into dispatched FSM event payloads.

This violates the bridge boundary contract: internal framework metadata should remain internal unless explicitly part of the configured FSM payload.

## Research: Existing Patterns, Prior Art, and Gaps

1. **Race telemetry is intentionally produced in core nodes.**
   - `yamlgraph/node_factory/race_node.py` returns `_race_winner` alongside `state_key`.
   - `yamlgraph/node_factory/router_race_node.py` returns `_race_winner` for router-race telemetry parity.

2. **Shared bridge owns payload dispatch boundary.**
   - `yamlgraph/utils/fsm/graph_runner.py` is the canonical dispatch path (`run_and_dispatch`), aligned to `REQ-YG-319` in `ARCHITECTURE.md`.

3. **No existing sanitization in shared FSM utilities.**
   - Search across `yamlgraph/utils/fsm/` shows no `_race_winner` strip/pop/redaction logic.

4. **Application-layer workaround exists outside framework.**
   - GitHub issue #395 documents a consumer-side `_pop_race_winner(result)` workaround; this indicates the fix belongs in framework boundary code, not per-application subclasses.

5. **Current test coverage misses this boundary contract.**
   - `tests/unit/test_fsm_bridge_shared.py` validates event cascade and guard semantics, but has no assertion that framework metadata is removed from dispatched payload.

6. **Problem is not already solved in this repository.**
   - No FR or test in this worktree currently codifies `_race_winner` payload sanitization in the shared runner.

## Objectives

1. Enforce payload hygiene at the shared bridge boundary by removing top-level `_race_winner` before payload construction.
2. Preserve race telemetry observability via INFO logging of the stripped value.
3. Keep behavior stable for event resolution, guard lifecycle, and non-race payload fields.

## Constraints

1. **Single responsibility:** only `_race_winner` sanitization in `run_and_dispatch`.
2. **Do not change race/router-race node outputs:** `_race_winner` remains in graph state for telemetry.
3. **Do not alter event cascade order** (`interrupt -> phase -> done -> event_map -> route -> success`).
4. **No new capability/requirement IDs:** bug fix remains under existing `REQ-YG-319`.
5. **No Chaplain subprocess action refactor** (`.chaplain/actions/yamlgraph_async_action.py` remains out of scope).

## Proposed Solution

### In Scope

1. In `yamlgraph/utils/fsm/graph_runner.py`, immediately after `result = await run_fn(...)`:
   - If `result` is `dict`, remove `_race_winner` via `winner = result.pop("_race_winner", None)`.
   - If stripped, log at INFO (e.g., `logger.info("race.winner: %s", winner)`).
2. Keep existing payload assembly flow intact after sanitization.
3. Add focused unit tests for sanitization + logging + no-regression behavior.

### Out of Scope

1. Changing race-node telemetry schema.
2. General-purpose payload redaction framework for arbitrary metadata keys.
3. Any changes in external consumer repositories.

## Acceptance Criteria

- [x] **AC-01:** `run_and_dispatch` strips top-level `_race_winner` from `result` before payload construction.
- [x] **AC-02:** When `_race_winner` is stripped, runner logs the stripped value at INFO level.
- [x] **AC-03:** A result containing `_race_winner` does not dispatch that key in FSM payload.
- [x] **AC-04:** Existing event-resolution/guard behavior remains unchanged for non-race metadata paths.
- [x] **AC-05:** Requirement-tagged unit tests cover AC-01..AC-04 under `REQ-YG-319`.

## Failing Acceptance Tests (RED plan)

RED test artifact:

- `tests/unit/test_fr392_fsm_race_winner_payload_sanitization.py`

Planned RED tests:

1. `test_ac01_run_and_dispatch_strips_race_winner_before_payload_build`
2. `test_ac02_stripped_race_winner_is_logged_at_info`
3. `test_ac03_dispatched_payload_excludes_race_winner_metadata`
4. `test_ac04_existing_event_cascade_behavior_is_unchanged`

RED command:

```bash
pytest tests/unit/test_fr392_fsm_race_winner_payload_sanitization.py -q --no-cov
```

Targeted regression command:

```bash
pytest tests/unit/test_fsm_bridge_shared.py -q --no-cov
pytest tests/unit/test_fr391_fsm_phase_aware_event_resolution.py -q --no-cov
```

## Alternatives Considered

1. **Keep app-level workaround (`_pop_race_winner`) in each consumer**
   - Rejected: duplicates framework boundary logic and causes drift across integrations.

2. **Stop emitting `_race_winner` from race/router-race nodes**
   - Rejected: removes intended telemetry contract (`REQ-YG-233`, `REQ-YG-271`).

3. **Filter metadata only in subclass `pre_dispatch` hooks**
   - Rejected: hook-based filtering is optional and non-uniform; boundary normalization must be enforced in shared runner.

## Related

- Issue #395: <https://github.com/sheikkinen/yamlgraph/issues/395>
- `yamlgraph/utils/fsm/graph_runner.py`
- `yamlgraph/node_factory/race_node.py`
- `yamlgraph/node_factory/router_race_node.py`
- `tests/unit/test_fsm_bridge_shared.py`
- `ARCHITECTURE.md` (`REQ-YG-319`, `REQ-YG-233`, `REQ-YG-271`)
