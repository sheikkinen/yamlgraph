---
type: feat
scope: watcher
req: REQ-YG-276
---
- **FR-320 watcher2 retry-safe worktree setup cleanup**: Added retry-safe cleanup in `worktree_setup.sh` (stale worktree binding removal, stale directory cleanup, explicit local branch delete failure path, and best-effort remote branch delete) and updated `.chaplain/README.md` retry guidance to document automated cleanup with manual fallback commands. (REQ-YG-276)
