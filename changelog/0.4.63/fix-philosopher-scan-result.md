---
type: fix
scope: philosopher
---
- **Philosopher scan_result wrapping**: Fixed `scan_diary_markers()` to wrap return in `{"scan_result": {...}}` so downstream nodes can reference `state.scan_result`. Python nodes that return dicts have keys merged directly (state_key is ignored for dict returns).
