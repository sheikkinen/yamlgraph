---
type: fix
scope: fsm
---
- **FR-422 ActionConfig mapping hardening**: Strict `event_map` typing (non-dict raises `ValueError` instead of silently returning `{}`), `_STRIP_BEFORE_VALIDATE` applied to nested `params` branch in `execute()`, and `dict`/`list` variable coercion via `json.dumps`. (REQ-YG-319)
