---
type: fix
scope: worktree
---
- **FR-106 Worktree Pipeline**: Exclude `docs/diary.md` from clean working tree check
  - Inquisitor writes to diary after commits, which would block worktree creation
  - `validate_clean_working_tree(exclude_paths=["docs/diary.md"])` now allows diary changes
