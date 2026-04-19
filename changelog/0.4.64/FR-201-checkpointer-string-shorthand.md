---
type: feat
scope: storage
req: REQ-YG-197
---
- **FR-201 Checkpointer String Shorthand**: `get_checkpointer()` and `get_checkpointer_async()` now accept a plain string (e.g., `"memory"`) as shorthand for `{"type": "memory"}`, normalizing at the boundary. (REQ-YG-196)
