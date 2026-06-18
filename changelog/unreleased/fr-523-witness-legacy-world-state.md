---
type: fix
scope: examples
---
- **FR-523 DM witness tolerates legacy world_state**: `seam_precondition_gap` now normalizes the carried `world_state` at the boundary via `parse_world_state`, so scanning older books (pre-FR-499A) that store `world_state` as a free-prose string no longer crashes with `AttributeError`.
