---
type: feat
scope: examples
---
- **FR-574 L2 extract goals spike**: LLM-validator-retry graph extracts story
  goals as typed Fluent predicates from synopsis + agent list. `validate_goals`
  checks predicate vocabulary, agent references, duplicates. Order-insensitive
  matching for symmetric predicates (C3). Goal recall 13/18 (0.72). Verdict:
  **REVISE** — inherent goal-inference ambiguity; spike measured + recorded (C4).
