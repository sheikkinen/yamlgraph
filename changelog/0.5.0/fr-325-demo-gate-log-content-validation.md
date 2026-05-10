---
type: feat
scope: demo-gate
---
- **FR-325 demo-gate log content validation**: Added shared semantic validation for `demo-output.log` in CI and pre-commit, rejecting empty logs, fatal execution markers, and logs without success evidence while preserving changed-demo detection.
