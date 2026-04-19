---
type: feat
scope: philosopher
---
- **FR-197 Philosopher Distill Node**: Added `distill` copilot node and `unwrap_distill` Python node to the philosopher graph for ranked prioritization. The distill prompt evaluates graduation candidates on recency, severity, evidence spread, and specificity to select the single strongest candidate. Conditional routing skips `propose` when no candidate survives. (REQ-YG-193)
