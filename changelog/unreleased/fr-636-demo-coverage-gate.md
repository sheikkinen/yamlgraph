---
type: feat
scope: demo
req: REQ-YG-065
---
- **FR-636 Demo Coverage Gate**: Phase 1 CI gate (`scripts/node_type_coverage.py`) verifies all NodeTypes have demo coverage; Phase 2 advisory (`scripts/demo_coverage.sh`) runs 13 demos under `coverage` proving 44% framework reachability. New `tool-call` demo added. Fixed `tool_call` doc field names in `reference/graph-yaml.md`. (REQ-YG-065)
