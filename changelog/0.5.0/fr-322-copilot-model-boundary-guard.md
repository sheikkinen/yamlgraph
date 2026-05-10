---
type: fix
scope: watcher
---
- **FR-322 Copilot model name fix + boundary guard**: Corrected `claude-sonnet-4-6` (hyphen) to `claude-sonnet-4.6` (dot) in validate/sanity-check sessions. Added boundary guard in copilot_node to detect silent CLI failures (exit 0 + empty stdout + error in stderr).
