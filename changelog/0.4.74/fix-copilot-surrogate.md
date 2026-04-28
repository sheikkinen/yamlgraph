---
type: fix
scope: copilot
---
- **Fix UTF-8 surrogate crash**: Normalize copilot CLI subprocess output at boundary with `errors='replace'`, fix surrogate pair emoji in helpers.py. Prevents `--full` display crash when output is piped.
