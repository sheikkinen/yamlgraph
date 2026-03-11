---
type: fix
scope: timeout
---
- **Timeout signal handler save/restore**: `_setup_timeout` / `_teardown_timeout` extracted as named functions; previous `SIGALRM` handler saved and restored in `finally`. Eliminates handler leak.
