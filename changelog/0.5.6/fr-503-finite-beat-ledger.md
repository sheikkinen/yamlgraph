---
type: fix
scope: examples
---
- **FR-503 Finite beat ledger for the DM director**: The DM v2 director no longer
  judges chapter progress from a free-text summary with no anchor — chapter
  outlines now emit an ordered list of 3–6 key-event **beats**, the director
  selects the satisfied beats **by number** over that finite list, and `phase` /
  `scene_complete` are **computed** in Python from `k / N` (opening → rising →
  climax → resolved) rather than guessed by the model. The running scene surfaces
  the **beats still to portray** so both the characters and the director drive
  toward the next unsatisfied beat instead of looping a single struggle until the
  FR-501 turn cap fires. A chapter with no enumerated beats falls back to the
  FR-491 free-text path (no divide-by-zero). Fixes the cross-provider stall where
  chapters never left `"rising"` and most closed only via the cap.
