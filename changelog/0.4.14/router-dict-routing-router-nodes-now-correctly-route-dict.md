---
type: fix
scope: router
---
- **Router dict routing** - Router nodes now correctly route dict outputs (e.g., `parse_json: true`) by checking `isinstance(result, dict)` and using `.get()` instead of `getattr()`
