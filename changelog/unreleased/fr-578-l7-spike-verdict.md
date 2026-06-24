---
type: feat
scope: examples
---
- **FR-578 L7 assign-affects spike — REVISE verdict**: Wired Mode 7
  (`run.py --mode assign-affects`), the L7 graph/prompt, and the `evaluate.py`
  L7 scorer (recall gate, precision over-emission detector C2, symmetric
  `toward` null-handling C3, informational open/close balance C1). Two-model
  spike: affect recall 4/33 (0.12) on `claude-haiku-4-5`, 3/33 (0.09) on
  `claude-sonnet-4-6`. Model-invariant kind-axis confusion (char/op correct,
  `kind` and relational `toward` wrong) → REVISE, not KILL (J:N2): the bottleneck
  is task framing, not model capability. L7 blocks the FR-579 merge node until a
  revised spike clears the 0.70 gate.
