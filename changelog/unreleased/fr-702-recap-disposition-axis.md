---
type: feat
scope: demos
req: REQ-YG-534
---
- **FR-702 Recap Disposition Axis**: workstreams in the recap demo now carry the verbatim FR `[Status: …]` at HEAD (anchored `git grep` tool, exit-1 normalized at the boundary, real errors still loud) — outcome, not just activity; rejected work reads as a deliverable. Orphan detection is mechanized out of the model via a deterministic `type: python` reference partition (case-insensitive `(FR|NC)-N`/`#N`), killing the mid-subject and lowercase-scope false-positive classes observed in field runs. (REQ-YG-534)
