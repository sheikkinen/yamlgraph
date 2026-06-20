---
type: feat
scope: examples
---
- **FR-541 DM v2 character state overlays**: A character's ORIGIN sheet is
  immutable (voice, backstory, who they were at the start), so the intent node read
  the same sheet in chapter 1 and chapter 7 and a character who died and returned
  still acted from their pre-death self (flat arcs in 10029-BC). A new
  `character_overlay` leaf derives a per-chapter CURRENT STATE overlay by accruing
  the committed `character_state_deltas` of prior chapters (deterministic,
  last-write-wins, additive — empty until a delta exists). The overlay REUSES
  `lifecycle_resolver`'s existing delta fold rather than duplicating it (one
  narrowing rule, two paths). `invoke_turn` carries the overlay in each cast bundle,
  and `character_intent.yaml` layers it as a CURRENT STATE block ALONGSIDE (never
  replacing) the ORIGIN sheet, so a chapter with no prior delta reproduces today's
  intent context exactly.
