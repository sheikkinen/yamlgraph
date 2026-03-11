---
type: fix
scope: agent
---
- **Agent prompt formatting** - Now uses `format_prompt()` instead of regex, supporting Jinja2 templates (`{{ state.topic }}`) and dot notation variables
