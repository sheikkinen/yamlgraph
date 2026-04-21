---
type: feat
scope: chaplain
req: REQ-YG-262
---
- **FR-261 Inquisitor into Watch Loop**: Remove fire-and-forget `inquisitor-background` post-commit hook from `.pre-commit-config.yaml` and integrate Inquisitor execution into `.chaplain/watch.sh` with `--propose` flag and `|| true` guard. Single orchestration point for all audit and enforcement activity. (REQ-YG-262)
