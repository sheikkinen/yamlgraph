---
type: fix
scope: examples
---
- **FR-523 DM v2 state-aware chapter re-outline**: The chapter outliner was
  state-blind — it wrote every chapter's beats from the synopsis alone, before any
  chapter played, so a lethal beat ("Arnulf is swept away by the flood") could land
  on an actor the prior chapter left safe on the higher bank with no beat bridging
  the two. The generator then teleported the actor to satisfy the beat and the
  director was blamed at play time for a contradiction the planner authored. After a
  chapter closes and commits its `world_state`/`seam_packet`, the next unplayed
  chapter's beats are now re-authored from that carried physical state
  (`chapter_reoutline.yaml`), so a hazard death/exit is bridged by a reposition beat
  that first moves the character into reach — killing the seam-teleport in the spec
  (the One Law: normalize at the outliner boundary, not downstream in the prose).
  Beats-only: title and summary stay frozen. Condemned first by the deterministic
  `witness_metrics.seam_precondition_gap` witness and its fixture (RED), then cleared
  by the re-outline (GREEN, mocked-graph gate with a non-vacuity negative control).
