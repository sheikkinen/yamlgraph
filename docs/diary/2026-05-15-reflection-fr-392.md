# Reflection: FR-392 Forward `snapshot.payload_keys` into Shared FSM Dispatch Payload

**Date:** 2026-05-15
**FR:** FR-392 — Forward `snapshot.payload_keys` into shared FSM dispatch payload
**Reviewer:** watcher2 (validate-fix pass)

## What Happened

FR-392 closes a contract gap in `run_and_dispatch()`: `SnapshotParams` already
declared `payload_keys`, but the runner silently ignored them when composing
dispatch payloads. The fix adds `_collect_payload_from_after_state()` to read
configured keys from `after_state.values` on the checkpointer path, serializing
each value via `json_safe()` while preserving `output_key` precedence via
`setdefault`.

Key deliverables verified:
- `_collect_payload_from_after_state()` iterates `snapshot.payload_keys` and
  populates only present, non-`None` values — absent keys are silently skipped.
- `output_key` payload entries are set first; `setdefault` ensures forwarded
  payload keys do not overwrite them (AC-04).
- Non-checkpointed path (no `thread_id`) is untouched — `after_state` stays
  `None` and `_collect_payload_from_after_state` returns `{}` (AC-05).
- 5 new acceptance tests pass; all 3849 existing unit tests remain green.

## Trap

**`continuation_bias` narrowly avoided.** The initial reflex was to read
`payload_keys` directly from `result` (the graph run output), which would have
been faster to implement. Research revealed the values are intended to come from
checkpointed graph state (`after_state.values`), not only the node return
payload — the distinction is documented in the FR alternatives section. Slowing
down to re-read the constraint ("checkpoint path only, because only then
`after_state` exists") steered the implementation to the correct boundary.

## Root Cause

`SnapshotParams` carried a typed contract (`payload_keys`) that was accepted by
action configuration but never consumed by the runner. The gap was invisible in
tests because existing shared FSM bridge tests verified `output_key` behavior
only. The typed boundary existed but was partially consumed — a classic
`downstream_fix` setup where the symptom (missing context in dispatched events)
could only be diagnosed at integration time.

## What Worked

- **Boundary-first reading.** Identifying `after_state` as the single
  authoritative boundary for checkpointed state values directed the fix to the
  right location without scope creep.
- **`setdefault` over conditional overwrite.** Using `setdefault` for forwarded
  keys naturally preserves `output_key` precedence without an explicit collision
  check — the code expresses the contract.
- **Helper extraction.** `_collect_payload_from_after_state()` is a pure function
  with a clear contract, making the AC-05 (non-checkpoint path unchanged)
  guarantee testable in isolation.
- **No silent broad fallback.** The constraint "absent keys are skipped" is
  enforced at the helper level, not documented as a footnote. Raising is avoided,
  but so is injecting defaults.

## Seed

Seed: When a typed configuration field (`payload_keys`) is accepted at the schema
boundary but not consumed at the execution boundary, what automated contract
coverage check would surface this gap before integration — similar to how
`req_coverage.py` maps test IDs to requirements, but mapping config fields to
their runtime consumption sites?
