---
type: fix
scope: chaplain
---
- **Remove commit_plan step**: Plan artifacts are no longer committed in a separate step with pre-commit hooks. The `commit_plan` state, transitions, and action are removed. FR path is captured via lightweight `bash_context` at end of plan step. Fixes pipeline failures caused by RED acceptance tests failing pytest during plan commit.
