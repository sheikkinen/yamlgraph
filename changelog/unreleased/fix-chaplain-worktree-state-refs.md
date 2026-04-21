---
type: fix
scope: chaplain
---
- **Fix worktree state references in copilot graph**: Restore `state_key: worktree_result` on `create_worktree` node as required by FR-260 acceptance criteria. Fix `{state.worktree_result.worktree_dir}` → `{state.worktree_dir}` variable references.
