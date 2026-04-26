---
type: feat
scope: pre-commit
req: REQ-YG-275
---
- **FR-286**: Exclude slow-marked unit tests from the root pre-commit pytest hook by adding `-m "not slow"` while preserving explicit slow-test execution outside pre-commit. (REQ-YG-275)
