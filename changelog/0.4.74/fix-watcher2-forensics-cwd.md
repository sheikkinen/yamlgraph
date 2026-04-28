---
type: fix
scope: watcher
---
- **Fix watcher2 failure forensics**: Preserve worktree and move topic to `.chaplain/failed/` on failure instead of destroying evidence. Pass absolute worktree path to copilot plan prompt to prevent writing to main repo.
