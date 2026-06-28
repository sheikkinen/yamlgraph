---
type: feat
scope: examples
---
- **FR-576 L5 assign pre/eff spike**: LLM-validator-retry graph assigns
  world-state and belief preconditions/effects (`pre_world`, `eff_world`,
  `pre_belief`, `eff_belief`) to classified beats. `validate_pre_eff` enforces
  Fluent/Belief structure, the 5-predicate vocabulary, and agent membership —
  with NO kind→effect semantic rule (J:C2: the corpus models one death as a
  `rel` change, not `alive=false`). Tolerant predicate matching (J:C1).
  Combined world recall 47/85 (0.55). Verdict: **REVISE** — token substitution
  + departure under-modeling are fixable prompt issues, not a capability
  collapse (follow-up prompt FR, analogous to FR-581 for L2).
