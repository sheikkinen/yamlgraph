---
type: fix
scope: empty
---
- **Empty YAML error handling** - `load_graph_config()` now raises `ValueError("Empty or invalid YAML file")` instead of `AttributeError` when YAML file is empty or contains only comments/null
