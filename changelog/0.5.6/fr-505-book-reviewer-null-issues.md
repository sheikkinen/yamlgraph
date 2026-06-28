---
type: fix
scope: examples
---
- **book-reviewer: coerce null `issues` to empty list at provider boundary:** Azure returns `null` for `ChapterReview.issues` when no issues are found; add a `field_validator` to normalize `None → []` at the LLM output entry seam.
