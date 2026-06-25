---
type: feat
scope: examples
req: REQ-YG-020
---
- **FR-589 Abstraction-span example**: Standalone graph-native example
  (`examples/abstraction_span/`) that LLM-scores a prompt's abstraction-span (count
  of distinct kinds of cognitive operation) via a `map` node and gates the score
  with a deterministic `separation_verdict` Python tool. Gate 1 passed: the metric
  reproduces the hand monolith/clean labels on `claude-haiku-4-5`. No linter
  integration (the `linter-llm-free` contract stands). (REQ-YG-020)
