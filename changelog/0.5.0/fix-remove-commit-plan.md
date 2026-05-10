---
type: fix
scope: chaplain
---
- **Remove commit_plan step**: Plan artifacts are no longer committed in a separate step with pre-commit hooks. The `commit_plan` state is replaced by a lightweight `capture_fr` state using `bash_context` to find the FR path. Fixes pipeline failures caused by RED acceptance tests failing pytest during plan commit.
