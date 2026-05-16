---
type: fix
scope: fsm
---
- **FR-392**: Strip `_race_winner` metadata in shared `run_and_dispatch()` before FSM payload assembly; log stripped winner metadata at INFO so framework-private race telemetry never crosses the FSM boundary.
