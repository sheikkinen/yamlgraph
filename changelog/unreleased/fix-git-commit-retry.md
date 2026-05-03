---
type: fix
scope: chaplain
---
- **FR-311 git_commit hook-fix retry**: `GitCommitAction` now retries commit after pre-commit hooks auto-fix files, re-staging with `git add -u` between attempts (max 3). Genuine failures still emit `error` immediately.
