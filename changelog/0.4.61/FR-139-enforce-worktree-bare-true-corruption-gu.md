---
type: fix
scope: enforce
---
- **FR-139 Enforce Worktree bare=true Corruption Guard**: Add three-layer defense against `.git/config` corruption (env sanitization, cleanup trap restoration, post-run assertion) that can set `bare = true` after worktree operations. (REQ-YG-UTIL)
