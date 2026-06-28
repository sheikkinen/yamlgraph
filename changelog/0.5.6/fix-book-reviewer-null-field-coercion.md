---
type: fix
scope: book-reviewer
---
- **Book reviewer null-field coercion**: Review model before-validators coerce a
  null or non-list `criteria`/`breaks` from the LLM provider into an empty list at
  the schema boundary, so a malformed provider response normalizes rather than
  raising downstream.
