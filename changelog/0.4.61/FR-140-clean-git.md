---
type: feat
scope: clean
req: REQ-YG-140
---
- **FR-140 Clean GIT_* Test Fixture**: Session-scoped autouse pytest fixture strips `GIT_*` env vars injected by pre-commit, preventing subprocess bleed into `tmp_path`-based test repos. Closes the `--no-verify` bypass loophole. (REQ-YG-140)
