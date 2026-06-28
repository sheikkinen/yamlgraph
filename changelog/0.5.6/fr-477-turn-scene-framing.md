---
type: fix
scope: examples
---
- **FR-477 DM turn scene framing**: Fix the play loop replaying the scene's
  aftermath instead of starting from the opening. The key scene is a plan
  (SUMMARY/BEATS/END describe the intended arc, not events that have happened);
  `running_scene` now labels the plan apart from what has actually happened, and
  the turn prompts act from the current moment so turn 1 begins at the START.
