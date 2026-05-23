---
type: feat
scope: node-factory
req: REQ-YG-223
---
- **FR-223 Refactor create_node_function**: Decomposed monolithic `create_node_function` (C901=35) and nested `node_fn` (C901=26) into 6 composable, independently testable phase functions — each below C901=10. (REQ-YG-223)
