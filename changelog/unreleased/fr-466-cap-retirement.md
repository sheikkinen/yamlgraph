---
type: feat
scope: registry
req: REQ-YG-428
---
- **FR-466 CAP Retirement Support**: CAP YAML files accept optional `status: retired` field. `req_coverage.py` excludes retired CAPs from coverage checks. `validate_capabilities.py` accepts retired files with relaxed validation. Tombstone `RETIRED_CAPS` dict preserved for deleted-file IDs. (REQ-YG-428)
