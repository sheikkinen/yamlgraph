---
type: removal
scope: node-factory
---
- **FR-635 Remove dead stream:true code**: Deleted `node_factory/streaming.py` and per-node `stream: true` early-return. Graph-level streaming via `--stream` / `run_graph_streaming_native()` is the correct approach.
