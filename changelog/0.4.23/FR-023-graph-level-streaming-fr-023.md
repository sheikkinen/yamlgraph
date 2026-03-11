---
type: feat
scope: graph-level
req: REQ-YG-048
---
- **Graph-level streaming (FR-023)** — New `run_graph_streaming()` async generator in `executor_async.py`. Runs non-LLM nodes (python, tool) first, then streams the LLM node token-by-token via `llm.astream()`. REQ-YG-048, REQ-YG-049. 7 new tests.
