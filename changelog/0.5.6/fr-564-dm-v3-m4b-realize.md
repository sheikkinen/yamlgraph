---
type: feat
scope: examples
---
- **FR-564 DM v3 M4b -- realize (beat-driven turn instruction)**: closes the v3 plot lane.
  `plot.realize.beat_instruction(plan, chapter) -> str` renders authored beat(s) at a chapter
  into a turn instruction, focalized on belief (never world-truth). A chapter carrying no beat
  returns `''` (byte-for-byte passthrough). `plot.project.belief_at(plan, chapter)` exposes the
  observer-dimensioned belief timeline that `exclusion_set` collapses; realize focalizes grief
  from `believes(clan, not alive(Arnulf))` while world-truth stays untouched.  Additive wiring
  inside `invoke_turn` (turn_ops.py) merges the beat directive into the stage instruction, gated
  on `attached_plot_plan(doc)` -- no plan attached means byte-for-byte v2 passthrough (dormancy
  invariant). Milestone closure: author (M4a) -> attach (M4a) -> validate (M0-M3) -> exclude
  (M1) -> realize (M4b), end-to-end.
