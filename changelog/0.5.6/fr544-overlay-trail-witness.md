---
type: feat
scope: examples
---
- **FR-544 Overlay-Trail Witness**: Persist the FR-541 derived character overlay
  as an `overlay_trail` block in `continuity_witness.json`. `overlay_trail_summary`
  reuses `character_overlay.derive_overlay` (no duplicated accrual) to recompute,
  per chapter, the CURRENT STATE each roster character entered from; characters with
  an empty overlay are omitted (sparse-is-truth). Visibility-not-gate; `story.json`
  is unchanged (the overlay stays a derived projection, never authored state).
