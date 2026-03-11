---
type: fix
scope: dead
---
- **Dead code removed**: `DEFAULT_MAX_TOKENS = 4096` constant deleted from `config.py` — was never wired (superseded by explicit `max_tokens` parameter in v0.4.31).
