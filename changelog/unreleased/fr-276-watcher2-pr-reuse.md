---
type: feat
scope: watcher
req: REQ-YG-276
---
- **FR-276 PR Reuse Functionality**: Enhanced watcher2 `create_pr.sh` to check for existing PRs before creation. When PR exists for the current branch, reuses it and updates title/body instead of failing. Fixes redundant PR creation attempts that caused pipeline failures. Fixed acceptance test architecture using PATH-based command mocking instead of subprocess mocking. (REQ-YG-276)
