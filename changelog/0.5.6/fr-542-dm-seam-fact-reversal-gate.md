---
type: feat
scope: examples
---
- **FR-542 DM v2 seam fact reversal**: Two boundary defenses against the
  cross-chapter fact reversal class (10029-BC "Arnulf swept away yet logged alive").
  **Part A** (interim): a new `ledger_reconcile` leaf reconciles the close-chapter
  `world_state` ledger against the director's reported `cast_exits` at the close
  boundary — any benched actor the prose-derived ledger left reading present is
  marked absent before the next chapter inherits it (pure, roster-bounded, no LLM).
  **Part B** (the novel, generic contribution): a `fact_reversal` leaf with a
  deterministic `fact_reversal_gap(prev_card, card)` that diffs a chapter's resolved
  events and forbidden regressions against the next chapter's facts, flagging a
  reversal of the SAME subject across a FROZEN antonym set. Surfaced as a
  visibility-only `fact_reversal` block in the continuity witness (posture:
  visibility-not-gate). The cast-exit accrual moved to `turn_state` beside its
  `turn_direction`/`chapter_turns` siblings (FR-536 concern seam).
