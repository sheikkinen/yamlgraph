---
type: feat
scope: examples
---
- **FR-540 DM v2 chapter entry/exit contracts**: The partitioner authored
  `summary`/`beats`/`cast` but never stated what is true at a chapter's open/close,
  so two adjacent chapters could each be locally coherent yet fail to COMPOSE
  (10029-BC Ch2->Ch3: isolated-grief close into assembled-crowd open, no
  transition). The outline now emits authored `entry_state`/`exit_state` chapter
  contracts (`_state_field` parser, stored per card in `expand_chapters`), and a new
  `composition_gap` leaf flags an adjacent pair whose configurations contradict by a
  FROZEN antonym set {present<->absent, together<->scattered} — deterministic,
  roster-bounded for the presence concept, no LLM. The outline partitioner re-rolls
  on a composition gap (bounded retry, the FR-525/FR-528 pattern) and raises if
  unresolved. `running_scene` surfaces `entry_state` as an explicit turn-1 framing
  block. This is the SOCIAL-configuration seam, carved distinct from the PHYSICAL
  lethal-seam owned by `seam_precondition_gap` (a pure lethal case is not flagged
  here). Absent contracts degrade additively — a pre-FR-540 story replays
  byte-identical.
