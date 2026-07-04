---
type: feat
scope: graph
req: REQ-YG-511
---
- **FR-677 First-Class Verification (Move 1)**: Guards are now honored on all side-effect node types — shell `tool`, `python`, and `agent` — not just llm/router/copilot. `guards.pre` runs before execution (halt raises, skip returns a skip state, warn logs) and `guards.post` runs after (halt raises, retry re-executes bounded by `max_retries`, warn logs, pass returns output unchanged). Guard halts are never swallowed by `on_error: skip`. Declaring `guards:` on a node type that cannot honor them (map, race, subgraph, tool_call, passthrough, interrupt) now fails loud at compile time with `GraphConfigError`. Shared guard runtime relocated to `utils.guard_runtime` so Layer-3 tool factories share one contract without crossing import boundaries. (REQ-YG-511)
