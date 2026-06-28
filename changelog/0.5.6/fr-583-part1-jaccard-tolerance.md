---
type: feat
scope: examples
---
- **FR-583 Part 1 — evaluator Jaccard arg tolerance**: Add `_args_jaccard_match`
  + shared `_arg_matches` per-arg comparator, called by both `_fluent_matches`
  (L1/L5 world) and `_goal_matches` (L2) so multi-word arg tolerance cannot
  drift between layers (J:C1). Multi-word args match on token-set Jaccard ≥ 0.5
  (order-swapped / non-contiguous overlap); single-word synonyms stay rejected
  (AC#7). Re-score is conservative: L2 13/18 (0.72) and L5 43/85 (0.51)
  unchanged with precision flat (L2 0.42, L5 0.19) — zero manufactured positives
  (C3). The residual L2 misses are all genuine semantic gaps (goal omission or
  single-word synonym), not multi-word strictness → L2 GO per J:N2.
