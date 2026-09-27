---
type: removal
scope: error
req: REQ-YG-715
---
- **FR-1124 LLM record-and-continue default removed**: A top-level `llm` node without `on_error` no longer records the failure and continues with an absent `state_key`; the original exception now propagates (`fail`). Graphs that relied on continuation declare `on_error: skip` on the node or `defaults.on_error: skip`. (REQ-YG-715)
