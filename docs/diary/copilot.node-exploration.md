# Copilot Node Implementation Exploration

## Key Findings

### Session ID Flow Architecture
1. **Extraction**: `_extract_session_id(stderr)` regex pattern matches "Session: <uuid>"
2. **Storage**: Extracted session ID stored in `CopilotResult.session_id` field
3. **Propagation**: State flows through graph edges; copilot nodes return `{state_key: CopilotResult}`
4. **Resume**: Next copilot node reads `{state.prev_result.session_id}` via `resolve_state_expression()`

### Core Files
- `copilot_node.py`: Factory for creating copilot nodes; handles CLI invocation, variable resolution, session ID extraction
- `node_compiler.py`: `_compile_copilot_node()` passes `effective_defaults` to factory
- `models/schemas.py`: `CopilotResult` with fields (output, exit_code, model, backend, session_id)
- `utils/expressions.py`: `resolve_state_expression()` handles nested attribute access on Pydantic models

### Resume Configuration
- `cli_flags.resume`: String or expression like `{state.prev_result.session_id}`
- Expression resolution happens in `_execute_cli()` before CLI invocation
- If expression contains `{state.`, calls `resolve_state_expression()`
- `cli_flags.continue_session`: Boolean flag for `--continue` without explicit session ID

### State Flow Pattern
```
Node 1 (copilot):
  └─ returns {enforce_result: CopilotResult(session_id="abc-123")}
            ↓
Node 2 (copilot):
  └─ cli_flags.resume: "{state.enforce_result.session_id}"
  └─ passes --resume abc-123 to CLI
  └─ returns {demo_result: CopilotResult(session_id="def-456")}
```

### Tests Cover
- CLI invocation with `subprocess.run()` (list-based, no shell injection)
- Variable resolution: simple (`{state.x}`) and nested (`{state.x.y}`)
- Session ID extraction from mock stderr
- Resume expression resolution with Pydantic model attributes
- Timeout configuration (default 300s)
- Model selection priority: `cli_flags.model > node.model > defaults.model`

### Requirements Addressed
- REQ-YG-087: CLI backend with configurable flags, injection safety
- REQ-YG-089: Composes with router/map/FSM patterns
- REQ-YG-105: Session continuations via `--resume` and `--continue`
- REQ-YG-265: Node-level model selection (FR-266)
- REQ-YG-268: State export with session_id round-trip
