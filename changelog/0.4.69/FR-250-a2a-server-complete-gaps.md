---
type: feat
scope: a2a
---
- **FR-250 A2A Server — Complete Protocol Gaps**: Implement task/get retrieval (REQ-YG-210), task/sendSubscribe SSE streaming via `run_graph_streaming_native` (REQ-YG-211), and full input-required resume flow with `Command(resume=...)` (REQ-YG-213). Adds interrupt detection helpers and streaming artifact events for incremental token delivery.
