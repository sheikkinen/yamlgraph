# Reflection: FR-391 Watcher2 Sanity-Check — Phase-Aware FSM Event Resolution

**Date:** 2026-05-15
**FR:** FR-391 — phase-aware completion event resolution in shared FSM runner
**Reviewer:** watcher2 (post-validate sanity check)

## Trap

`gate_checks_shape_not_substance` — A sanity reviewer risks confirming that files exist and
tests pass without verifying that the cascade semantics are *semantically* correct. This
check was designed to go deeper: confirm that AC-04 (interrupt wins over phase) is not just
present in test name but structurally tested with `interrupt_pending=True` and a `phase`
value in state simultaneously.

## What Happened

Review of `test_ac04_interrupt_continue_semantics_unchanged` confirmed the test sets
`next=("awaiting_input",)` (interrupt pending) AND `values={"phase": "crisis"}` in the
after-state simultaneously, then asserts `sent == [("router", "on_continue", None)]`.
This is a genuine substance check: the interrupt branch wins over phase routing even when
`event_map` has a `"crisis"` key.

Cascade order in `graph_runner.py` post-patch:
1. `interrupt_pending is True` → `event_map["continue"]`  ← interrupt wins
2. `interrupt_pending is False` and `completion_phase in event_map` → `event_map[completion_phase]`  ← new
3. `interrupt_pending is False` and `"done" in event_map` → `event_map["done"]`
4. `result[event_key]` match
5. `_route` / `route`
6. `success_event`

All 12 tests passed (4 new FR-391 acceptance tests, 8 existing bridge regression tests).

## Root Cause

The original `_resolve_event()` never received or consulted checkpoint state. The fix is
12 lines: `completion_phase` extracted via `getattr(after_state, "values", {}) or {}` for
mock compatibility, then inserted as a cascade step between `interrupt_pending is True`
and `"done"` fallback.

## What Worked

- **Proportionality confirmed**: 9 files, 411 insertions — core production diff is 15
  lines; the rest is required artifacts (FR, tests, changelog, ARCHITECTURE, docs).
- **Test substance confirmed**: AC tests check routing outcomes (event names), not
  internal implementation details (function call counts, argument ordering).
- **Requirement traceability confirmed**: `@pytest.mark.req("REQ-YG-319")` class-level
  decorator covers all 4 AC test functions under the correct capability requirement.
- **Boundary normalization**: phase extraction at `run_and_dispatch` (the boundary where
  checkpoint state enters resolution), not downstream in FSM dispatcher.

## Seed:

> `completion_phase` is currently a single scalar; what if the phase value is absent at
> the checkpoint boundary but available from a secondary state key (e.g. `substate`,
> `terminal_reason`)? Should the cascade accept a list of state-key candidates to probe
> in priority order before falling back to `done`, making the resolution strategy
> declarative rather than hard-coded?
