---
type: feat
scope: examples
req:
---
- **FR-557 DM v2 turn engine (Contract B)**: Extract the doc-free engine core of
  `turn_ops.invoke_turn` into a new `turn_engine` module -- typed request/result
  packets (`TurnRequest`, `TurnResult`, and a CLOSED `TurnExtras` set), the single
  turn-graph invocation, intent normalization, and the beat-FSM helpers
  (`_phase_for_count`, `_satisfied_indices`, `_apply_beat_ledger`,
  `_direction_dict`) moved verbatim. The adapter keeps assembly and gating (roster
  scope, cast bundles, memory/lifecycle gates) and now builds a `TurnRequest` and
  calls `turn_engine.play_turn`. A golden characterization test pins the
  byte-identical turn record and recap across the move; no behavior changes.
