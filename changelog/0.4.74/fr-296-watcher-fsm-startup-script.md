---
type: feat
scope: fsm
req: REQ-YG-315
---
- **FR-296 Watcher FSM Startup Script**: Single `start-system.sh` starts the full watcher FSM system (UI, diagrams, dispatcher) with proper sequencing, health checks, signal-based teardown, and `--inbox DIR` override. (REQ-YG-315)
