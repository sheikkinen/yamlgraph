---
type: feat
scope: examples
---
- **FR-538 DM v2 seam-entrance witness**: A deterministic `seam_entrance_gap`
  detector flags any **roster** character who acts in a chapter's final-cut prose
  but crossed the chapter seam with no on-page arrival — present in chapter N,
  neither on-page in N−1 nor staged arriving in N. The gating signal is prose
  establishment (an arrival/reposition token-run near the entrant, mirroring
  `seam_precondition_gap`'s bridge check), never a manifest lookup, so FR-539's
  `cast_entrances` cannot suppress a gap without narrating an arrival. Gaps are
  classified `new`/`returning`/`continuing` from prior on-page history plus the
  inherited `character_lifecycle`. The detector lives in a new leaf
  `seam_entrance.py` (a sibling of `gap_detectors`, which was at the 450-line
  ceiling) and is emitted as an additive, non-gating `seam_entrance` block in the
  continuity witness. Roster lens only: non-roster named NPCs are out of scope
  (they overlap the status/resurrection rail).
