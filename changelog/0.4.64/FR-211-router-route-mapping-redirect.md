---
type: fix
scope: edge
req: REQ-YG-214
---
- **FR-211 Router Route Mapping Redirect**: Router conditional edges with `to: [list]` targets now correctly redirect interrupt node names to `{name}_prepare` (and subgraph interrupt targets to `{name}__run`) in the route mapping, while keeping original names as route labels for `make_router_fn` matching. Previously, list targets bypassed the FR-060 interrupt redirect logic, causing silent misrouting. (REQ-YG-214)
