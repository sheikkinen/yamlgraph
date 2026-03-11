---
type: fix
scope: commit-msg
---
- **FR-083 Commit-Msg Hook Bug** Fix `bash -c` positional argument bug in both `feat-requires-fr` and `changelog-required` pre-commit hooks. Added `_` placeholder to both hook entries so the commit message file properly becomes `$1`. Removed stale `backend: sampling` CHANGELOG entry for FR-081 (was deleted in FR-082 teardown). Added 19 integration tests for commit-msg hook behavior.
