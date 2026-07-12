---
type: feat
scope: models
req: REQ-YG-544
---
- **FR-716 Pre-emptive Module Splits**: `graph_schema.py` (448 lines, 2 from the size gate) bisected at the node/graph seam — node-config models now live in `models/node_schema.py` (336 lines), graph-level models stay (138 lines); public re-exports from `yamlgraph.models` unchanged. The stream-event translation extracted from `run_graph_streaming_native` (CC 17 → 8) into `streaming_events.py` as pure functions (`translate_message_event`, `check_interrupt`) — the FR-057…060 streaming scar tissue isolated in one small module; `executor_async.py` back under the 400 warn line. Seams chosen calmly instead of under deadline pressure at the 450 gate. (REQ-YG-544)
