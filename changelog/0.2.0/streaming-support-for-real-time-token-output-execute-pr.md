---
type: feat
scope: streaming
---
- **Streaming Support** for real-time token output
  - `execute_prompt_streaming()` - Async generator yielding chunks
  - `stream: true` node config for YAML-defined streaming
  - `create_streaming_node()` factory function
  - See [reference/streaming.md](reference/streaming.md)
