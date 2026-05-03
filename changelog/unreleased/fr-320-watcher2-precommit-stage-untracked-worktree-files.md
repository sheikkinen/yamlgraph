---
type: feat
scope: watcher
---
- **FR-320**: Stage all worktree changes with `git add -A` before `pre-commit run --all-files`, and use the same full restage on retry so untracked artifacts are included in watcher2 precommit remediation.
