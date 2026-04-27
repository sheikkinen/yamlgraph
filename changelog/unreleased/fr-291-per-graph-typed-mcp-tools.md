---
type: feat
scope: mcp
req: REQ-YG-310
---
- **FR-291 Per-Graph Typed MCP Tools**: Each discovered graph is now exposed as its own named MCP tool with typed JSON Schema derived from the graph's `state:` block. Input/output separation via `state_key` exclusion. Tool names normalized (hyphens/spaces → underscores). Collision detection at startup. Mastra (TypeScript) integration example proves cross-runtime discovery and execution. (REQ-YG-310, REQ-YG-311, REQ-YG-312, REQ-YG-313, REQ-YG-314)
