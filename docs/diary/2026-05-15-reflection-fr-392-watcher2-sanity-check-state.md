# Watcher2 Sanity Check: FR-392 — FSM Race Winner Payload Sanitization

**Date:** 2026-05-15
**FR:** FR-392 — sanitize `_race_winner` in shared FSM event payloads
**Reviewer:** watcher2 post-validate
**Verdict:** PASS

## What Was Reviewed

`yamlgraph/utils/fsm/graph_runner.py` — `_strip_race_winner()` helper and its call
site in `run_and_dispatch()`.
Four acceptance tests in `tests/unit/test_fr392_fsm_race_winner_payload_sanitization.py`.

## Trap: Downstream Fix Correctly Avoided

`downstream_fix` — the temptation was to let each consumer strip `_race_winner`
(issue #395 documented exactly this consumer-side `_pop_race_winner()` workaround).
The fix correctly landed in `run_and_dispatch()`, the canonical dispatch boundary
defined by `REQ-YG-319`. Single `result.pop("_race_winner", None)` enforces the
contract once, eliminating per-consumer workaround drift.

## What Happened

`_strip_race_winner()` was extracted as a private helper (12 lines including
docstring), called immediately after `result` is obtained and before `_build_payload()`.
When stripped, `logger.info("race.winner: %s", winner)` preserves telemetry
observability. The fix is surgical: no changes to race/router-race node outputs,
no cascade/routing changes, no new public API.

## Root Cause

No explicit metadata-sanitization step existed at the dispatch boundary. The contract
between graph state (internal) and FSM payload (external) was implicit rather than
enforced. `_race_winner` is legitimately produced by race nodes for telemetry but must
not cross the FSM bridge boundary.

## Test Quality

- 4 tests map 1:1 to AC-01..AC-04.
- All assertions target dispatched behavior (what reaches `send_fn`), not internal
  state.
- test_ac01: edge case where `output_key` equals `"_race_winner"` — stripped key
  yields `None` payload.
- test_ac02: INFO log assertion using `monkeypatch` on logger — behavioral, not trivial.
- test_ac03: multiple keys; confirms only `output_key` reaches payload.
- test_ac04: validates event cascade priority (interrupt_pending=False + "done" in
  event_map fires before event_key lookup) is unchanged post-strip.
- Regression: 12/12 tests pass across `test_fsm_bridge_shared.py` and
  `test_fr391_fsm_phase_aware_event_resolution.py`.

## Proportionality

12 lines of production code, 137 lines of acceptance tests, changelog fragment,
FR, diary. Appropriately minimal for a 0.5-day boundary hygiene bug fix.

## Minor Finding

Changelog fragment uses `type: feat` while FR type is `Bug`. Should be `type: fix`.
Non-blocking — does not affect runtime behavior or test coverage.

## Seed:

Could the FSM bridge declare a configurable `_INTERNAL_METADATA_KEYS` set so that
any future framework-private keys (e.g., `_node_timing`, `_checkpoint_id`) are
automatically stripped at the same boundary, without requiring per-key pop additions?
