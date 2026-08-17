---
type: fix
scope: observability
req: REQ-YG-570
---
- **FR-813 None checkpoint input**: Preserve `None` through `run_graph_async` checkpoint retries and hash it as canonical JSON `null` for OTel evidence. (REQ-YG-570)
