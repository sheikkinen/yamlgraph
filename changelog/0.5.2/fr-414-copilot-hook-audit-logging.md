---
type: feat
scope: hooks
---
- **FR-414 Copilot Hook Audit Logging**: PreToolUse and PostToolUse hooks now log every tool invocation to append-only JSONL audit trail (`.github/hooks/logs/audit.jsonl`). Fail-closed parsing denies on malformed input. Supports both snake_case and camelCase VS Code payload formats. 43 tests validate enforcement and audit behavior.
