---
type: removal
scope: state
req: REQ-YG-024
---
- **FR-675 Remove dead top-level error field**: Removed phantom `error` field from `BASE_FIELDS` and `create_initial_state`; export now derives error summary from `errors[-1]` with JSON serialization. (REQ-YG-024)
