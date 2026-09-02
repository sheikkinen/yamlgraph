---
type: feat
scope: copilot
req: REQ-YG-639
---
- **FR-959 `backend: claude` for the copilot node**: a fourth, closed backend value runs Claude Code CLI in print mode (`claude -p … --output-format json`) on the operator's Claude subscription. Typed Claude-only flags (`tools` = availability via `--tools`, `allowed_tools` = approval via `--allowedTools`, `max_turns`), a frozen argv order, a typed JSON envelope, and a per-invocation preflight that pins the CLI version (`2.1.255`) and refuses any non-subscription `claude auth status` before every call. Unknown backend values and malformed flags now fail at schema, compile, and lint instead of falling through to Copilot. (REQ-YG-639, REQ-YG-640, REQ-YG-641)
