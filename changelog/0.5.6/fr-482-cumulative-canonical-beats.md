---
type: feat
scope: examples
---
- **FR-482 DM v2 cumulative canonical beats**: The Dungeon Master director's
  `beats_satisfied` is now bound to the frozen key-scene's canonical `BEATS` and
  accumulated across turns. Each turn's free-text beat phrases are fuzzy-matched
  (difflib, with an acceptance floor and a runner-up margin) onto the scene's own
  beat vocabulary and unioned with prior turns, so the field is a stable,
  de-duplicated subset read in scene order — with a `k / N` progress count on the
  Director card. A phrase matching nothing is dropped, never invented.
