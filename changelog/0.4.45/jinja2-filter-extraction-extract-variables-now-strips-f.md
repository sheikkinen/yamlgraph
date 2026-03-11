---
type: fix
scope: jinja2
---
- **Jinja2 filter extraction**: `extract_variables()` now strips filter expressions (`|length`, `|join` etc.) before parsing — fixes false "missing variable" errors
