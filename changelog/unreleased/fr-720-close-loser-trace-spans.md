---
type: fix
scope: tracing
req: REQ-YG-547
---
- **FR-720 Close trace spans on race-loser cancellation**: race candidates now carry a pre-generated `run_id` per ainvoke attempt (`config={"run_id": ...}`); on cancellation the loser's LangSmith run is closed enqueue-only with `end_time`, a terminal error (`cancelled: lost race to {provider}/{model}` on the winner path, `cancelled: race timed out` on the drain path) and `extra.metadata.race_outcome=lost` — pending-forever zombie spans (NC-367: 38/38 deployed vertex losers) no longer masquerade as hung work, and per-candidate win rates are queryable from traces. Verdict timing (FR-707 cancel-only) unchanged; skipped cleanly when tracing is disabled. (REQ-YG-547)
