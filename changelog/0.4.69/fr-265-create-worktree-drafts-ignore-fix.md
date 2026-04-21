---
type: fix
scope: worktree
---
- **FR-265 create_worktree drafts ignore fix**: Fix Chaplain pipeline failure where `create_worktree()` ran `git add` on drafts under `.chaplain/drafts/` (excluded by `.gitignore`). Now uses `git add --force` and treats "nothing to commit" as success.
