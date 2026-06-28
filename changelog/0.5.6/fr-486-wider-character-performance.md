---
type: feat
scope: examples
---
- **FR-486 DM v2 wider per-turn character performance**: Each character's per-turn
  `character_intent` output widens from `{thinking, intent}` to
  `{thinking, intent, dialogue, expression}` — a captured **side-channel the arc
  never reads**. `intent` stays first and explicitly singular (one decisive
  action), `thinking` stays private, `expression` is its only public projection
  (the visible facial/bodily tell), and `dialogue` is the spoken line. The turn
  director and recap are untouched, so the played arc still converges on `intent`
  alone; a mandatory seam-freeze test asserts `dialogue`/`expression` appear in
  neither `turn_direct` nor `turn_recap`. Missing performance keys on older turns
  default to `""` (a benign normalization, the deliberate asymmetry against
  FR-485's alignment validator which raises). The turn card surfaces "Says"/"Shows"
  rows when present. This authors the performance layer that FR-487's full-text
  walkthrough renders, rather than inventing it at render time.
