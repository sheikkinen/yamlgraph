---
type: removal
scope: mcp
---
- **FR-910 Retire the MCP server surface**: Deleted `yamlgraph/export/mcp.py`, the `.vscode/mcp.json` registration, the `mcp` optional extra, `reference/mcp-server.md`, and the MCP-only test modules. CAP-19 and CAP-136 are retired; agents reach graphs through the CLI adapters (`yamlgraph graph list`) instead.
