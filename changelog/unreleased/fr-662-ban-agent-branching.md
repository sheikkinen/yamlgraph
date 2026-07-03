---
type: feat
scope: hooks
---
- **FR-662 Ban Agent Branching**: pre-command-guard blocks `git checkout -b`, `git switch -c`, and `git branch <name>` in the main worktree. Agents must use chaplain worktrees for isolation.
