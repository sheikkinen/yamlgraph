---
type: feat
scope: copilot
req: REQ-YG-141
---
- **FR-138 Copilot Session GC**: Shell script `scripts/copilot_session_gc.sh` prunes stale Copilot CLI sessions older than `--max-age` days (default 7). Supports `--dry-run` preview and protects the active session via `$COPILOT_SESSION_ID`. (REQ-YG-141)
