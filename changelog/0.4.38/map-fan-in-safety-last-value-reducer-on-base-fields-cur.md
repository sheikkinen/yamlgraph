---
type: fix
scope: map
---
- **Map fan-in safety**: `last_value` reducer on BASE_FIELDS (`current_step`, `error`, `_loop_counts`, etc.) prevents `INVALID_CONCURRENT_GRAPH_UPDATE` when parallel map branches write to shared tracking fields.
