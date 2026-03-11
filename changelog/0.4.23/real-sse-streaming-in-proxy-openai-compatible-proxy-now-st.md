---
type: feat
scope: real
---
- **Real SSE streaming in proxy** — OpenAI-compatible proxy now streams LLM tokens in real-time via `run_graph_streaming()`, replacing the previous fake word-splitting approach. TTFT reduced from full-generation time to ~200ms.
