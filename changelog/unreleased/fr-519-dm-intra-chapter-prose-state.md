---
type: feat
scope: examples
---
- **FR-519 DM v2 intra-chapter prose-vs-state enforcement (Phase 1)**: The
  per-chapter final cut now receives the chapter's committed physical state as a
  hard constraint. Confirmed-dead characters are split into `dead_before_open`
  (never appear) and `dead_within_chapter` (may act only up to their death), and a
  `possession_facts` block tells the model who holds what so the prose cannot let a
  character use an object it just lost. The close-graph output is threaded into
  `invoke_final_cut` because the chapter's own `world_state` is not committed until
  after the final cut runs. Warn-only diagnostics (`DEAD_CHARACTER_ACTS_POST_DEATH`,
  `OBJECT_USED_AFTER_LOSS`) measure the residual without raising. Witnessed on
  10021-BC ch6: possession contradictions cleared; the within-chapter post-death
  residual triggered the FR-520 Phase-2 working-memory gate.
