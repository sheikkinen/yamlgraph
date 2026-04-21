---
type: fix
scope: chaplain
---
- **Fix worktree state references in copilot graph**: Python nodes returning dicts merge keys directly into state — `state_key` is decorative for dict returns. Fixed `{state.worktree_result.worktree_dir}` → `{state.worktree_dir}`.
