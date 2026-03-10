---
type: feat
scope: linter
req: REQ-YG-113
---
- **FR-113 Linter W015**: Warn when cycle node has explicit `skip_if_exists: true` — the node will cache its first output and return stale results on every iteration. Only fires on explicit setting; runtime `apply_loop_node_defaults()` handles the default case. (REQ-YG-113)
