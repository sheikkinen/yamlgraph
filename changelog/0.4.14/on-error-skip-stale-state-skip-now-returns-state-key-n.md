---
type: fix
scope: onerror
---
- **on_error: skip stale state** - Skip now returns `{state_key: None, "_skipped": True, "_skip_reason": "error"}` to prevent downstream nodes from using stale data
