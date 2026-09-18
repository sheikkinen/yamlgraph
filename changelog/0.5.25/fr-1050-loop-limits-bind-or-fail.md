---
type: fix
scope: compile
req: REQ-YG-683
---
- **FR-1050 `loop_limits` binds or fails compilation**: a `loop_limits` entry naming no node, or naming a node whose type never consults `check_loop_limit` (agent, map, tool_call, interrupt, subgraph, copilot, verify, interactive_tool, pipeline), now raises `GraphConfigError` at load time instead of sitting inert. Standalone `race` nodes enforce their limit before firing candidates. Inert entries removed from the `multi-turn` and `book-summary` demos. (REQ-YG-683)
