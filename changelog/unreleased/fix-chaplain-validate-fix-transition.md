---
type: fix
scope: chaplain
---
- **Chaplain pipeline**: add missing `validate_fix → failed` error transition in `watcher-pipeline-v2.yaml`; FSM no longer freezes silently on validate-session timeout
- **dependency_rationale.py**: skip gitignored module paths (e.g. `projects/`) in worktrees; eliminates false-positive stale-path failures during pre-commit
