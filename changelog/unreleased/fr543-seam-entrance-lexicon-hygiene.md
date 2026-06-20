---
type: fix
scope: examples
---
- **FR-543 Seam-entrance lexicon hygiene**: The DM v2 seam-entrance witness
  (`seam_entrance.seam_entrance_gap`) no longer clears an unbridged entrance with
  an exit/fall sentence. The arrival lexicon (`_ESTABLISH_TOKENS`) had borrowed the
  exit-edge reposition tokens (`into the water`, `slips`, `loses footing`,
  `down the bank`, `goes back`, `back for`), so a character's later death-fall
  wrongly counted as their arrival. Those inversion-prone tokens are purged; the
  establish set now contains only unambiguous arrival verbs.
