---
type: feat
scope: copilot
---
- **FR-105 Copilot Session Continuations** (CAP-30, REQ-YG-105): Enable multi-task workflows where sequential copilot nodes share a session
  - `cli_flags.resume`: Resume a specific session by ID (`--resume <id>`)
  - `cli_flags.continue_session`: Resume most recent session (`--continue`)
  - `CopilotResult.session_id`: Extracted from CLI stderr for downstream nodes
  - State expression support: `{state.prev_result.session_id}` in resume
  - Linter rules: `E-COPILOT-RESUME` (mutual exclusion), `W-COPILOT-SESSION` (pattern warning)
  - Updated example in `examples/copilot/graph.yaml` with session continuation
