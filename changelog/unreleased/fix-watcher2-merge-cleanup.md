---
type: fix
scope: watcher
---
- **Fix watcher2 post-merge cleanup**: Remove `--delete-branch` from `gh pr merge` to prevent false failure when `main` is already checked out in the main worktree. Add merge state verification fallback. Move remote branch deletion to `worktree_teardown`.
