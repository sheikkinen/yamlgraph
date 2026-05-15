# Reflection: FR-391 Phase-Aware FSM Completion Event Resolution

**Date:** 2026-05-15
**FR:** FR-391 — phase-aware completion event resolution in shared FSM runner
**Reviewer:** watcher2 (validate-fix pass)

## Trap

`downstream_fix` — The original `_resolve_event()` function returned `event_map["done"]`
immediately when `interrupt_pending is False`, never consulting the checkpoint state's
`phase` value. Any caller that encoded terminal subtype in `phase` (e.g. `phase="crisis"`)
would silently fall through to generic `done` routing. The symptom appeared far downstream
(wrong FSM state reached) while the fix belonged at the single event-resolution entry point.

## What Happened

The shared FSM runner's `_resolve_event()` cascade was:
1. `interrupt_pending is True` → `event_map["continue"]`
2. `interrupt_pending is False` → `event_map["done"]`  ← phase-aware case missing here
3. `result[event_key]` match
4. `_route` / `route` key
5. `success_event`

When a graph checkpoint state contained `phase="crisis"` and the caller's `event_map`
had a `"crisis"` key, step 2 short-circuited to `done` before the phase value was
ever consulted. Domain flows that encode terminal subtype in `phase` were silently
misrouted.

## Root Cause

The event-resolution function operated on `event_map` keys only; it never received
or inspected checkpoint state values. The `completion_phase` parameter and the
extraction of `after_values.get("phase")` from the checkpoint result were both absent.

## What Worked

- **Boundary normalization**: `completion_phase` is extracted from the checkpoint
  state at the single call site (`run_graph_async`) and passed into `_resolve_event()`,
  keeping resolution logic in one function.
- **Cascade ordering preserved**: phase-aware lookup is inserted between
  `interrupt_pending is False → done` and the existing `event_map[done]` fallback,
  so all prior callers without `phase` in state see no behavior change.
- **TDD**: Failing tests written first (AC-01..AC-05 in `test_fr391_fsm_phase_aware_event_resolution.py`),
  confirmed RED before implementation, then GREEN with minimal change to `graph_runner.py`.

## Seed:

> The `phase` key is a single string scalar; future domain flows may encode richer
> terminal state (e.g. nested substates or lists of active phases). Could the cascade
> be extended to support a priority-ordered list of phase candidates from state, so
> that callers can declare fallback chains (`["crisis", "error", "done"]`) without
> replicating the lookup logic in every integration?
