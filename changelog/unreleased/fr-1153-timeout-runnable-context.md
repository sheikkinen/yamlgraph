---
type: fix
scope: compile
req: REQ-YG-078
---
- **FR-1153 `timeout:` keeps the runnable context**: a node with `timeout:` (python, tool, tool_call, agent, llm/router, and map sub-nodes) now runs with the caller's contextvars copied per invocation, so `langgraph.config.get_config()` inside it returns the run's config. Previously the timeout's worker thread started empty and `get_config()` raised `RuntimeError: Called get_config outside of a runnable context` (issue #708). Timeout values, error shapes, and the absence of cancellation are unchanged. (REQ-YG-078)
