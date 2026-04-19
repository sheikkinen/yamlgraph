---
type: feat
scope: native
---
- **FR-029 Native LangGraph Streaming** (REQ-YG-065): New `run_graph_streaming_native()` uses LangGraph's `astream(stream_mode="messages")` to stream tokens from ALL LLM nodes (not just first found). Supports `node_filter` parameter.
