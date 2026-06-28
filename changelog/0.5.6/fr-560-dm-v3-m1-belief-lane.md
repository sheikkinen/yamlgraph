---
type: feat
scope: examples
---
- **FR-560 DM v3 M1 belief lane**: Graduated the floodmark plot-model spike into a typed
  `examples/dungeon_master/api/plot/` leaf package (`schema`/`up_model`/`validate`/`project`/
  `report`). Added pure belief-lane projections (`chapter_cast`/`exclusion_set`/`protected_set`),
  an ungrounded-reveal grounding check, and an additive plan-optional exclusion seam in
  `compile_opening_onepager` (byte-identical when no plan is attached). `unified-planning` stays
  optional -- projection, grounding, the seam, and the report run pure.
