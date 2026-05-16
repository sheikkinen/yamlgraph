# Reflection: FR-392 — Strip `_race_winner` from FSM Dispatch Payload

**Date:** 2026-05-15
**FR:** FR-392 — strip race winner metadata at shared FSM dispatch boundary
**Reviewer:** watcher2 (post-validate remediation)

## Trap

`downstream_fix` — the initial instinct when internal metadata leaks is to add a filter at
the consumer side (e.g., application wrapper or FSM action). This duplicates filtering
logic across every consumer and leaves the breach open for future ones. The correct fix is
to normalize at the entry boundary: `run_and_dispatch()` is the single crossing point
between YAMLGraph's internal race-node state and external FSM consumers.

## What Happened

Race nodes (`race_node.py`, `router_race_node.py`) correctly emit `_race_winner` into graph
state for telemetry. `run_and_dispatch()` forwarded the raw result dict to payload
construction without filtering, so `_race_winner` appeared in dispatched FSM event payloads
whenever a race node was in the pipeline.

The fix is a single helper `_strip_race_winner_metadata()` called immediately after `result
= await run_fn(...)`. It pops the key and emits an INFO log with winner metadata so the
telemetry value is preserved for diagnostics without crossing the FSM boundary.

## What Worked

- **Boundary normalization**: `_strip_race_winner_metadata()` sits at the exact boundary
  where internal graph results meet external FSM payload construction — no downstream
  guards needed.
- **Proportionality**: production change is ~15 lines; no new abstractions, no new
  requirements, no interface changes.
- **Observability preserved**: INFO log retains the stripped value for diagnostics,
  satisfying AC-03 without polluting downstream consumers.
- **Targeted tests**: 4 acceptance tests under `REQ-YG-319` confirm exclusion, logging,
  and non-regression for non-race payloads.

## Root Cause

`run_and_dispatch()` lacked an explicit normalization step for internal metadata keys. Race
telemetry was added to node factories without a corresponding sanitization step at the
shared dispatch boundary.

## Seed:

> `_race_winner` is one known internal metadata key. Are there other framework-private
> state keys (`_loop_count`, `_skip_reason`, etc.) that could similarly leak through
> `run_and_dispatch()`? Should the boundary have a declarative set of `_INTERNAL_KEYS`
> to strip, making the sanitization policy explicit and extensible rather than per-key?
