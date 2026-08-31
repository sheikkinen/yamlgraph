---
type: fix
scope: research
---
- **FR-937 Research Precedent Vocabulary Drift**: The brief preflight and the
  route reducer implemented the same precedent contract twice and drifted apart.
  The preflight rejected the honest-miss marker the reducer accepts, matched
  markers by naive substring so a row merely *mentioning* `none-retrieved` in
  prose passed, accepted a classification claim anywhere in the cell rather than
  as the leading token, and reported every closure failure as
  "remove solution-shaped sections" regardless of cause. Marker recognition is
  now a single shared predicate — a marker counts only as the whole cell or as a
  leading `marker:` prefix — `none-retrieved` is accepted only when retrieval
  came back empty, the retired `brief-echo` marker is rejected outright, and the
  wrapper reports the violations it actually found. The five research-route
  persona prompts were re-authored through the authoring route to teach the
  accepted vocabulary. (REQ-YG-623)
