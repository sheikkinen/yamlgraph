---
type: feat
scope: phantom
req: REQ-YG-145
---
- **FR-145 Phantom Requirement Detection**: `req_coverage.py --strict` rejects `@pytest.mark.req` markers referencing requirement IDs absent from `ALL_REQS` or `ARCHITECTURE.md`. (REQ-YG-145)
