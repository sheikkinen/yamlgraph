---
type: feat
scope: ci
---
- **FR-918 CI Python Matrix Refresh**: `test` matrix moves from 3.11/3.12 to 3.11/3.13 (floor + ceiling bracket policy); `core-test`, `security`, and release `build` jobs move to 3.13; `requires-python` narrows to `>=3.11,<3.14` so no install-allowed interpreter sits outside the tested bracket.
