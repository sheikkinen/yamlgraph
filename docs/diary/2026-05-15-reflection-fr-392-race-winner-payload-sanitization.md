# Reflection: FR-392 — Race Winner Payload Sanitization

**Date:** 2026-05-15
**FR:** FR-392 — sanitize `_race_winner` in shared FSM event payloads

## Trap

`downstream_fix` — The temptation was to let each consumer strip `_race_winner` from
dispatched payloads (as documented in issue #395). This is a classic downstream fix:
the symptom manifests in consumer code, but the root cause is the shared bridge
emitting framework-internal metadata into contract payloads.

## Cure

`normalize_at_boundary` — The fix belongs in `run_and_dispatch()`, the canonical
dispatch boundary defined by `REQ-YG-319`. A single `result.pop("_race_winner", None)`
before payload construction enforces the contract once, eliminating per-consumer
workaround drift.

## Insight

Telemetry keys intentionally produced by nodes (`_race_winner` in race and router-race)
are legitimate in graph state but must not cross the FSM bridge boundary. The
sanitization belongs at the boundary, not at the producer or the consumer. This is a
direct instance of the One Law: normalize at the boundary where external data enters.

## Seed:

Could the FSM bridge declare a schema of "allowed payload keys" so that any future
internal metadata key is automatically stripped, rather than requiring per-key pop logic?
