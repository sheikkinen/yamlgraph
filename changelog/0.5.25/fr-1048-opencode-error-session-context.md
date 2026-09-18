---
type: fix
scope: copilot
req: REQ-YG-679
---
- **FR-1048 opencode error names the attempted session id**: the non-zero-exit error from `backend: opencode` now appends `(attempted --session <id>)` to the bounded stderr tail, because opencode's own `Session not found` message does not echo the id. Closes the AC-17 assertion that the invalid-session failure names both `Session not found` and the attempted id. (REQ-YG-679)
