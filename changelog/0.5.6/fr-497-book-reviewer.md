---
type: feat
scope: book-reviewer
---
- **FR-497 Book Reviewer example**: A stand-alone YAMLGraph example that critiques
  a book-shaped Markdown manuscript with a decomposed `map → reduce` pipeline — the
  deliberate opposite of a single "almighty prompt". No LLM call sees the whole
  book (one chapter per review, two adjacent chapters per continuity check,
  summaries-only for synopsis delivery), and no LLM emits a number: every score in
  the final review is computed by a deterministic Python reduce, with the model
  writing only a one-line prose verdict. Includes pure parse/lint/reduce tests, a
  fully mocked graph run, a tested K4 prompt-scope gate, and an import-purity check.
