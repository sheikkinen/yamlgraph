---
type: fix
scope: condition
---
- **Condition evaluation `state.` prefix**: `resolve_value()` in `conditions.py` now strips the `state.` prefix from paths (e.g. `state.session_done == True`), fixing `loop_until` routing that silently resolved to `None`
