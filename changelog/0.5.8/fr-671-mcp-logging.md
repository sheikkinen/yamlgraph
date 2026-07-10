---
type: fix
scope: mcp
---
- **FR-671 MCP graph execution logging**: `_handle_run_graph` now logs with `exc_info=True` on graph execution failure and logs timeout errors, matching the outer tool handler's behavior.
