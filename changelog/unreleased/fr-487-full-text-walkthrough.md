---
type: feat
scope: examples
---
- **FR-487 DM v2 full-text walkthrough (the rendered finish)**: A `walkthrough`
  terminal leaf that renders the **full text** of each played turn — the scene as
  it could be read aloud or performed — by composing three already-authored layers:
  the FR-485 cut spine (structural order + emphasis), the FR-486 per-character
  performance (spoken `dialogue`, visible `expression`, acted `intent`), and a new
  whole-arc director-staging pass (a curtain-up `setting` plus per-turn
  location/blocking deltas that carry cross-turn continuity). The render is a
  per-turn map — global de-repetition and climax weight already ride in on the cut
  spine — validated 1:1 against the played turns by the **reused**
  `validate_cut_turns` (no new alignment contract; alignment composes because the
  spine is itself 1:1 to the played arc). The private `thinking` is dropped at the
  assembly boundary and never reaches the page. Additive `doc["walkthrough"] =
  {setting, turns:[{n, text}]}`, gated on the scene being complete **and** the
  FR-485 cut being present; the recaps, both Final Cuts, and the per-turn
  performance stay byte-for-byte immutable.
