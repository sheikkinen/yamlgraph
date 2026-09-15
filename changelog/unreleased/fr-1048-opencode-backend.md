---
type: feat
scope: copilot
req: REQ-YG-679
---
- **FR-1048 opencode CLI backend**: `backend: opencode` delegates a `type: copilot` node to `opencode run <prompt> --format json` as a subprocess, reusing the FR-959 CLI-backend seam with no new dependency, no server lifecycle, and no `CopilotResult` field change. The resolved `provider/model` is a compile-time fail-closed requirement (missing, empty, or malformed values fail before any subprocess); `resume` maps to `--session` with fail-closed state-expression resolution; `continue_session` is deliberately absent (opencode's `--continue` is directory-scoped and silently starts a new session). stdout crosses a typed, fail-closed JSONL state machine (`step_start`/`text`/`tool_use`/`step_finish`/`error`; `step_finish.reason ∈ {stop, tool-calls}`; `stop` is the sole terminal success) into the frozen `CopilotResult(backend="opencode")`. An exact-whole-banner version probe runs before every invocation; the child environment keeps provider credentials (they are the payer, the inverse of Claude's subscription boundary) and never logs them. (REQ-YG-679)
