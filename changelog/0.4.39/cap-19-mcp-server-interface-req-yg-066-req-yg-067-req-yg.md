---
type: feat
scope: cap-19
req: REQ-YG-066
---
- **CAP-19: MCP Server Interface** (REQ-YG-066, REQ-YG-067, REQ-YG-068)
  - `yamlgraph/mcp_server.py`: Expose graphs as MCP tools via stdio transport
  - `yamlgraph_list_graphs`: Discover available graphs with descriptions and required vars
  - `yamlgraph_run_graph`: Invoke any graph by name with variables, returns structured JSON
  - Graph discovery scans `examples/demos/*/graph.yaml` and `examples/*/graph.yaml`
  - `.mcp.json` and `.vscode/mcp.json` workspace configs for MCP integration
  - `reference/mcp-server.md` documentation
  - 8 unit tests covering discovery, schema, invocation, error handling, timeout
