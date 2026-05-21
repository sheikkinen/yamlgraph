---
type: refactor
scope: hooks
---
- **FR-434 Hook scripts modular refactor**: split post-edit checks into `python-checks.sh`, `yaml-checks.sh`, and `fr-checks.sh` with shared parsing/logging helpers in `checks/common.sh`, per-script timeouts, and migrated split test suites with shared fixtures.
