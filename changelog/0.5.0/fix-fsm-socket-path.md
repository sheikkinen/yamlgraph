---
type: fix
scope: fsm
---
- **Fix socket path and port conflicts in shared FSM bridge module**: Corrected `event_sender.py` to use `/tmp/` (matching statemachine-engine convention) instead of `tempfile.gettempdir()`. Updated fsm-router example ports to 3101/3102 to avoid conflicts. Fixed test mocks to inject `send_fn` parameter.
