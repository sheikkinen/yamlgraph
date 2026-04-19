---
type: feat
scope: graph
req: REQ-YG-257
---
- **FR-255 Extract Shared invoke_graph**: `invoke_graph()` in `graph_loader.py` provides a single entry point for synchronous graph invocation, replacing duplicated code in `mcp_server.py` and `a2a_server.py`. (REQ-YG-257)
