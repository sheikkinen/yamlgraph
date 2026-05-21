---
type: fix
scope: fsm
---
- **FR-416 Judge Event Key Mismatch**: Fixed `extract_event()` to match first-line verdict tokens in multiline judge output (e.g., `"APPROVE\n\nRationale: ..."`); added `event_key: judge_result` to watcher-pipeline-v2.yaml judge action to resolve key mismatch between FSM config and graph state. (REQ-YG-319)
