---
type: feat
scope: examples
---
- **FR-530 DM v2 continuity witness (Stage 1)**: `generate_and_review.sh` now emits a per-run, machine-readable continuity witness (`continuity_witness.json` with the reviewer's `Continuity` score and break count) after review. Strictly non-blocking (visibility, not a gate -- FR-522 posture): a missing review or low score never fails the run. The JSON is the join key for FR-531's continuity report. Stage 2 (per-seam corrective re-roll) remains out of scope.
