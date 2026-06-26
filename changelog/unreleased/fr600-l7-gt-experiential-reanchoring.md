---
type: fix
scope: plot-modeller
req: REQ-YG-020
---
- **FR-600 L7 Affect Experiential Re-Anchoring**: Corrected 12 mis-anchored L7 ground-truth
  affect deltas from FR-599's UNLICENSED bucket against a human-confirmed frozen fixture —
  7 re-anchored one beat forward to the experiential beat, 5 dropped as inferred-from-arc.
  The frozen FR-578 gate is untouched. Recall 0.061→0.107, but the model-skill-only gain
  (denominator held at 33) is 0.061→0.091; the rest is the denominator shrinking by 5 drops.
  The (e)=12 bucket re-partitions to 1 HIT / 5 ABSENT / 1 KIND-WRONG / 0 (e), confirming the
  MULTI-CAUSE verdict. (REQ-YG-020)
