# Feature Request: FR-391 phase-aware event resolution in shared FSM runner

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 0.5 day
**Requested:** 2026-05-15

## Summary

Add phase-aware completion routing to `yamlgraph.utils.fsm.graph_runner._resolve_event()` so a checkpoint state `phase` value can map directly to an FSM event before generic `done` fallback is applied.

## Value Statement

FSM integrations using the shared runner preserve domain-correct routing (for example crisis handling) during migration, without silent fallback to generic success/done events.

## Problem

The current shared runner resolves completion events with this order:

1. `interrupt_pending is True` -> `event_map["continue"]` fallback
2. `interrupt_pending is False` -> `event_map["done"]` (if present)
3. `event_map` match from `result[event_key]`
4. `_route` / `route`
5. `success_event`

This misses a required case: when a completed checkpoint state contains `phase` and that phase is explicitly mapped in `event_map`, the runner should emit the phase-mapped event before generic done fallback.

Without this behavior, domain flows that encode terminal subtype in `phase` (e.g. `phase="crisis"`) can route to `done/success` instead of the phase-specific event.

## Research: Existing Patterns, Prior Art, and Gaps

1. **Architecture contract already anchors event-cascade semantics in shared bridge.**
   - `ARCHITECTURE.md` section **141. Shared FSM Bridge Module** (`REQ-YG-319`) defines the canonical interrupt/event_map/route/success cascade in `yamlgraph/utils/fsm/graph_runner.py`.

2. **Current implementation confirms missing phase-aware branch.**
   - `yamlgraph/utils/fsm/graph_runner.py` `_resolve_event()` does not inspect checkpoint state values (`after_state.values`) and returns `event_map["done"]` immediately when `interrupt_pending is False`.

3. **Existing tests cover interrupt + event_map + route cascade, not phase-aware completion.**
   - `tests/unit/test_fsm_bridge_shared.py` validates continue/done precedence and route fallback.
   - No test currently asserts `phase`-key routing from checkpoint state.

4. **Pattern documentation supports event_map-driven routing but has no phase completion clause.**
   - `reference/patterns/fsm-as-conductor.md` documents the cascade and interrupt done/continue semantics; no explicit phase override on completion is specified yet.

5. **Topic source file was missing in this worktree snapshot.**
   - Requested source `.chaplain/processing/gh-393.md` is absent; planning source used: GitHub issue #393.

## Objectives

1. Ensure completion routing can use checkpoint `phase` as an explicit event selector when mapped.
2. Preserve existing interrupt `continue` semantics and non-phase fallback behavior.
3. Keep scope strictly inside shared FSM runner event resolution.

## Constraints

1. Keep single responsibility: event-resolution ordering only.
2. Do not change socket dispatch, guard semantics, or hook APIs.
3. Do not refactor Chaplain subprocess bridge (`.chaplain/actions/yamlgraph_async_action.py`).
4. Maintain requirement traceability under existing `REQ-YG-319` (no new capability required for this bug fix).

## Proposed Solution

### In Scope

1. Extend runner completion context so `_resolve_event()` can read checkpoint state values (or equivalent) in addition to `result`.
2. Add phase-aware mapping rule on non-interrupt completion:
   - If checkpoint state has non-empty `phase`
   - and `phase in event_map`
   - emit `event_map[phase]`
   - before falling back to generic done mapping.
3. Preserve existing cascade for all other cases:
   - interrupt `continue`
   - done fallback
   - `event_key` mapping
   - `_route/route`
   - `success_event`
4. Add focused unit tests for phase-aware behavior and fallback stability.

### Out of Scope

1. Adding new FSM events, states, or transitions.
2. Reworking `event_map` normalization rules.
3. Domain-specific migration work outside this repository.

## Acceptance Criteria

- [x] **AC-01:** Shared runner checks completed checkpoint state `phase` against `event_map` before generic `done` fallback.
- [x] **AC-02:** With `phase="crisis"` and `event_map={"crisis": "crisis_detected", "done": "completed"}`, resolved event is `crisis_detected`.
- [x] **AC-03:** With `phase="done"` (or missing/unknown phase), fallback behavior remains unchanged (`event_map["done"]` when configured).
- [x] **AC-04:** Existing interrupt handling remains intact (`continue` mapping still wins when `interrupt_pending is True`).
- [x] **AC-05:** Requirement-tagged tests cover AC-01..AC-04 under `REQ-YG-319`.

## Implementation Notes

1. `yamlgraph.utils.fsm.graph_runner._resolve_event()` now accepts `completion_phase` and resolves it before `"done"` when completion is non-interrupt.
2. `run_and_dispatch()` now reads checkpoint `phase` from `after_state.values` using `getattr(after_state, "values", {}) or {}` for mock compatibility.
3. Added acceptance tests in `tests/unit/test_fr391_fsm_phase_aware_event_resolution.py` (REQ-YG-319) covering AC-01..AC-04.

## Failing Acceptance Tests (RED plan)

RED test artifact:

- `tests/unit/test_fr391_fsm_phase_aware_event_resolution.py`

Planned RED tests:

1. `test_ac01_completed_state_phase_is_checked_before_done_fallback`
2. `test_ac02_phase_crisis_maps_to_crisis_event`
3. `test_ac03_missing_or_unknown_phase_falls_back_to_done`
4. `test_ac04_interrupt_continue_semantics_unchanged`

RED command:

```bash
pytest tests/unit/test_fr391_fsm_phase_aware_event_resolution.py -q --no-cov
```

Targeted regression command:

```bash
pytest tests/unit/test_fsm_bridge_shared.py -q --no-cov
```

## Alternatives Considered

1. **Keep current done-first behavior and rely on downstream domain mapping**
   - Rejected: silently misroutes completion for phase-encoded outcomes.

2. **Encode phase into `result[event_key]` upstream only**
   - Rejected: checkpoint state already carries authoritative completion phase; forcing downstream reshaping duplicates responsibility.

3. **Create separate phase-specific action implementation**
   - Rejected: violates shared bridge goal and reintroduces drift.

## Related

- Issue #393: <https://github.com/sheikkinen/yamlgraph/issues/393>
- `yamlgraph/utils/fsm/graph_runner.py`
- `yamlgraph/utils/fsm/helpers.py`
- `tests/unit/test_fsm_bridge_shared.py`
- `ARCHITECTURE.md` (Capability 141, `REQ-YG-319`)
- `reference/patterns/fsm-as-conductor.md`

## Judgement

**Verdict: APPROVE** — 2026-05-15

Scope, constraints, acceptance criteria, and cascade semantics are clear and internally consistent. No contradictions found.

**Key findings:**

1. **Root cause confirmed**: `_resolve_event()` receives only `interrupt_pending: bool | None` from `run_and_dispatch()`; `after_state.values` is never consulted, so `phase`-encoded completion falls silently through to `event_map["done"]`.

2. **Implementation path is unambiguous**: Extract `phase` from `after_state.values` in `run_and_dispatch()` (only when `run_config` is set, i.e. `interrupt_pending is not None`) and pass it as a new `completion_phase: str | None = None` keyword argument to `_resolve_event()`. Insert the phase check between the `interrupt_pending is True` branch and the `"done"` fallback branch. Existing behaviour is fully preserved for `completion_phase=None`.

3. **Mock compatibility**: Existing tests mock `app.aget_state` as `SimpleNamespace(next=...)` without `.values`. `after_state.values` must be read with `getattr(after_state, "values", {}) or {}` to stay backward-compatible with existing test mocks.

4. **Cascade order locked**:
   1. `interrupt_pending is True` → `event_map["continue"]`
   2. `interrupt_pending is False` and `completion_phase and completion_phase in event_map` → `event_map[completion_phase]` ← new
   3. `interrupt_pending is False` and `"done" in event_map` → `event_map["done"]`
   4. `event_map` match from `result[event_key]`
   5. `_route` / `route`
   6. `success_event`

5. **Classification**: Bug fix to existing framework primitive under REQ-YG-319. No new capability or requirement ID required.

**Authority granted**: Implement exactly the cascade extension above. Write RED tests first as specified in the FR before making the production change.
