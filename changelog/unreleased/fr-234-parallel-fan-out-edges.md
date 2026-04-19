---
type: feat
scope: graph
req: REQ-YG-237
---
- **FR-234 Parallel Fan-Out Edges**: `to: [a, b, c]` without `type: conditional` compiles as parallel fan-out — all targets execute concurrently. Handles interrupt node redirect, map node targets, and START fan-out. (REQ-YG-235)
