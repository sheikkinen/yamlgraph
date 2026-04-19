---
type: feat
scope: graph
req: REQ-YG-078
---
- **FR-069 Per-Node Timeout**: Optional `timeout: float` field on `NodeConfig` bounds individual node execution via `ThreadPoolExecutor`. Map branches honour timeout in `wrap_for_reducer`; non-map nodes (llm, tool_call, python, agent, race) via `_maybe_wrap_timeout` in `node_compiler`. New `TIMEOUT_ERROR` error type. Lint warning W203 for map+agent without timeout. (REQ-YG-078)
