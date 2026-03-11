---
type: removal
scope: rungraphstreaming
---
- **`run_graph_streaming()`**: Deprecated legacy function removed. Use `run_graph_streaming_native()` instead. The native version streams from ALL LLM nodes using LangGraph's native streaming (was: passthrough hack for first node only).
