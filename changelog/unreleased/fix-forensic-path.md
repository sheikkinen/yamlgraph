---
type: fix
scope: watcher
---
- **Fix forensic graph path**: Use absolute path for watcher-forensic graph invocation to prevent "Prompt not found" errors when cwd changes to worktree.
