---
type: feat
scope: examples
---
- **FR-573 L1 extract agents spike**: LLM-validator-retry graph extracts
  agents, initial world state, and initial beliefs from prose synopsis.
  `validate_agents` checks structure, agent references, alive predicates.
  Tolerant matching (C1: normalize + contains/prefix). Agent recall 22/24
  (0.92). Verdict: **GO**.
