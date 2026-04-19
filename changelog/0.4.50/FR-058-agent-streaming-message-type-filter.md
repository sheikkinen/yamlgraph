---
type: fix
scope: agent
---
- **FR-058 Agent streaming message type filter** (REQ-YG-065): `run_graph_streaming_native` now yields only `AIMessageChunk` content without `tool_calls`. Previously, `hasattr(chunk, "content")` duck-type check leaked SystemMessage (prompt text), HumanMessage (echoed input), ToolMessage (raw tool data), and intermediate AIMessage with tool_calls to clients. Replaced with `isinstance(chunk, AIMessageChunk)` + `not chunk.tool_calls` guard. Five new tests.
