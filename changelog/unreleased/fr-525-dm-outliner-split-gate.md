---
type: fix
scope: examples
---
- **FR-525 DM v2 outliner split-gate**: The whole-book chapter partitioner
  (`outline_chapters`) now runs the deterministic `reversal_pack_gap` witness over
  every authored chapter; when a chapter packs the same actor's removal AND return —
  a reversal the 16-turn chapter cap (FR-501) cannot play, leaving the return a
  phantom (`beat_coverage_gap`) — the outline is re-invoked with the violation fed
  back (bounded retry) and RAISES if the pack survives, never emitting a packed
  outline downstream.
