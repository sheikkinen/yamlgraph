---
type: fix
scope: config
---
- **FR-432 Upward `.env` Search with Git Boundary**: `yamlgraph.config` now searches upward from the current working directory for `.env` and stops at `.git` directory boundaries. Worktree `.git` files no longer incorrectly terminate the search, allowing `.env` discovery at the main repo root.
