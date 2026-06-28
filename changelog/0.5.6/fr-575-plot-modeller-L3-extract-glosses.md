---
type: feat
scope: examples
---
- **FR-575 L3 extract glosses spike**: LLM-validator-retry graph decomposes
  prose synopsis into 7–12 discrete story beats (id, gloss, chapter).
  `validate_glosses` checks sequential IDs, word count, non-decreasing chapters.
  Many-to-one beat matching (C5), stopword-stripped Jaccard calibrated at 0.15
  threshold (C6). Beat recall 42/48 (0.88). Verdict: **GO**.
