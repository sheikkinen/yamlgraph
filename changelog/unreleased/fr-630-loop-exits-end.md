---
type: fix
scope: graph
req: REQ-YG-093
---
- **FR-630 loop_exits END target**: Normalize YAML string "END" to LangGraph sentinel in edge compiler and router. Previously crashed at runtime despite linter accepting it.
