---
type: feat
scope: node
req: REQ-YG-233
---
- **FR-232 Race Node Type**: Added `type: race` node that fires the same prompt to N provider/model candidates concurrently via `ThreadPoolExecutor` and returns the first successful result. Includes `_race_winner` metadata in state, graph lint checks E301–E304, `on_error` policy support, and structured output support. (REQ-YG-233)
