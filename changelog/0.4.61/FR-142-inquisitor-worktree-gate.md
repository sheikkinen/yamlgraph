---
type: feat
scope: inquisitor
req: REQ-YG-142
---
- **FR-142 Inquisitor Worktree Gate**: Add worktree-detection gate to `inquisitor.sh` that suppresses audit and propose phases when running inside a git worktree (enforce pipeline). Detects via `-f "$REPO_ROOT/.git"`; `--force` bypasses. Placed before commit-delta gate (FR-131). (REQ-YG-142)
