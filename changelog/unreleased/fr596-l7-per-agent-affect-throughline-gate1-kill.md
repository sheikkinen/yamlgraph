---
type: fix
scope: plot-modeller
req: REQ-YG-020
---
- **FR-596 L7 per-agent affect throughline (Gate-1 KILL)**: Added the pure
  `combine_affects` + `affect_balance` helpers (per-beat union of feeler-owned
  affect deltas, no dedup), the `affect_throughline` / `encode_affect` decomposition
  prompts, and the `spike_affect.py` Gate-1 harness (maps over the GT agent roster,
  reports detection / kind-given-detection / toward-given-relational sub-axes and
  the agent-coverage ceiling). Gate 1 KILLed the full-cast decomposition: the L7
  ground truth authors affect as a single protagonist's throughline (every fixture's
  deltas sit on one character), so mapping over the whole cast over-generates ~N×
  and collapses precision (0.03) while affect_recall stays 0.09. The frozen FR-578
  evaluator gate was not modified. (REQ-YG-020)
