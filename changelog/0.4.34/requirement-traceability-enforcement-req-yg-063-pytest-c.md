---
type: feat
scope: requirement
req: REQ-YG-063
---
- **Requirement traceability enforcement** (REQ-YG-063): `pytest_collection_modifyitems` hook in `tests/conftest.py` now **structurally enforces** ADR-001. Every test must have `@pytest.mark.req("REQ-YG-XXX")` or collection fails with `UsageError`. Implements Commandment #10.
