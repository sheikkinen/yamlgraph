---
type: fix
scope: examples
---
- **FR-555 Reversal-gate the state-aware re-outline boundary**: `outline_ops.reoutline_chapter_beats` now gates its re-authored beats with the same `reversal_pack_gap` detector and bounded `_reversal_feedback` retry-then-raise discipline as the partition gate (`outline_chapters`, FR-525). A re-outline that re-packs an actor's removal-and-return into one chapter (the 10036-BC Ch3 Arnulf early-reveal: frozen summary "presumed dead" + a beat asserting he is "alive") is now re-rolled with feedback and, if still packed after `_OUTLINE_MAX_ATTEMPTS`, raised -- never committed. Closes the second, previously ungated authoring boundary the FR-523 re-outline introduced.
