---
type: fix
scope: examples
---
- **FR-547 Fact-Reversal Entity-Disagreement Suppression**: Fix a false positive in the DM v2
  `fact_reversal` continuity witness where two facts about DIFFERENT named characters sharing only
  an incidental locative token (e.g. `Reinmar arrived at the flood zone` vs `Arnulf is still
  missing in the flood zone`) composed a phantom `present <-> absent` reversal. `fact_reversal_gap`
  gains an optional `entities` set (a corpus proper-noun lexicon) and suppresses a reversal only
  when both lines name DISJOINT entities -- a pure veto that never strips a subject, so reversals
  about places that name no entity (a sealed ford reopened) still fire. The lexicon is built in
  `emit_continuity_witness._proper_noun_entities` from tokens capitalized non-sentence-initial at
  least twice across the committed prose (recovering off-roster names the roster omits, while
  locatives stay out), unioned with roster name-tokens. The cited 10032-BC witness now reports
  `fact_reversal.gap_count == 0`.
