# Feature Request: Copilot Node Session Continuations

**ID:** FR-105
**Priority:** MEDIUM
**Type:** Enhancement
**Status:** ✅ Implemented
**Effort:** 2 days
**Requested:** 2026-02-27
**Judged:** 2026-02-27
**Completed:** 2026-02-27

## Summary

Extend the copilot node type to support session resumption (`--resume`, `--continue`) so that a multi-node graph can continue work within the same Copilot CLI session across sequential tasks.

## Value Statement

Graph authors can chain multiple copilot nodes that share a single Copilot session, enabling multi-task workflows (e.g., TDD enforcement → example implementation → demo execution) without losing session context between steps.

## Problem

Today each copilot node invocation spawns an independent CLI process with `-p` (non-interactive prompt mode). The Copilot CLI supports `--resume <sessionId>` and `--continue` flags that allow a new prompt to be executed within an existing session's context — retaining file edits, tool state, and conversation history.

**Current limitation:** A graph like `enforce_tdd → implement_example → run_demo` requires three separate copilot nodes. Each starts from scratch with no knowledge of what previous nodes did. The user's inbox topic describes exactly this: "started with one task and then continued with another."

**What the CLI already supports:**
- `--resume <sessionId>` — resume a specific session by UUID
- `--continue` — resume the most recent session
- `--resume` (no arg) — interactive session picker (not useful for automation)

These flags compose with `-p` for non-interactive continuation:
```bash
copilot --resume <session-id> -p "Now implement the example" --allow-all-tools
```

## Proposed Solution

### 1. New `cli_flags` options

Add two new flags to the copilot node's `cli_flags` configuration:

```yaml
cli_flags:
  resume: "{state.session_id}"    # --resume <sessionId> (from state or literal)
  continue_session: true           # --continue (resume most recent)
```

Only one of `resume` or `continue_session` may be set. Validation at lint time.

### 2. Capture `session_id` in `CopilotResult`

Extend `CopilotResult` to capture the session ID so downstream nodes can reference it:

```python
class CopilotResult(BaseModel):
    output: str
    exit_code: int
    model: str | None
    backend: str
    session_id: str | None = Field(default=None, description="Copilot session ID for resumption")
```

The session ID can be extracted from the Copilot CLI's stderr or log output (the CLI reports the session ID on startup). If extraction fails, `session_id` remains `None` — no silent fallback to a wrong value.

### 3. Variable resolution for `resume`

The `resume` flag supports state expression resolution like other variables:

```yaml
nodes:
  plan:
    type: copilot
    prompt: plan
    cli_flags:
      allow_all_tools: true
    state_key: plan_result
    timeout: 500

  implement:
    type: copilot
    prompt: implement
    cli_flags:
      allow_all_tools: true
      resume: "{state.plan_result.session_id}"   # Continue in same session
    state_key: implement_result
    timeout: 500

  demo:
    type: copilot
    prompt: demo
    cli_flags:
      allow_all_tools: true
      resume: "{state.plan_result.session_id}"   # Same session still
    state_key: demo_result
    timeout: 300
```

### 4. Implementation changes

**`copilot_node.py` — `_execute_cli()`:**

```python
# Add resume/continue flags
if resume_id := cli_flags.get("resume"):
    # Resolve state expressions if needed
    cmd.extend(["--resume", str(resume_id)])
elif cli_flags.get("continue_session"):
    cmd.append("--continue")

# ... existing -p prompt append ...
```

**`copilot_node.py` — session ID extraction:**

```python
# After subprocess.run, extract session_id from stderr
session_id = _extract_session_id(result.stderr)

copilot_result = CopilotResult(
    output=result.stdout,
    exit_code=result.returncode,
    model=cli_flags.get("model"),
    backend="cli",
    session_id=session_id,
)
```

**`_extract_session_id()`** — parse stderr for the UUID pattern the CLI emits on session start. If not found, return `None` and log a warning. Never guess.

### 5. Linter rule

Add a lint check in `yamlgraph/linter/patterns/`:
- **E-COPILOT-RESUME**: Error if both `resume` and `continue_session` are set on the same node.
- **W-COPILOT-SESSION**: Warning if `resume` references a state key that doesn't come from a copilot node's `state_key`.

## Acceptance Criteria

- [x] `cli_flags.resume` passes `--resume <value>` to the copilot CLI command
- [x] `cli_flags.continue_session: true` passes `--continue` to the copilot CLI command
- [x] State expression resolution works for `resume` (e.g., `{state.plan_result.session_id}`)
- [x] `CopilotResult.session_id` is populated when extractable from CLI output
- [x] `CopilotResult.session_id` is `None` (not fabricated) when extraction fails
- [x] Linter raises error when both `resume` and `continue_session` are set
- [x] Unit tests cover: resume flag injection, continue flag injection, session ID extraction, mutual exclusion validation
- [x] Existing copilot node tests continue to pass (no regression)
- [x] Example graph in `examples/copilot/` updated with a multi-task continuation demo
- [x] Documentation in `reference/graph-yaml.md` updated with new `cli_flags` options

## Alternatives Considered

1. **Explicit `session_name` field** — The Copilot CLI does not support named sessions (only UUIDs). A naming abstraction would add complexity without CLI support. Rejected.

2. **Always `--continue` between copilot nodes** — Fragile: depends on execution order being the only thing touching copilot sessions. Breaks if the user runs copilot manually between graph steps. Rejected.

3. **Use `--resume` with a user-provided UUID** — Supported as a literal string in `resume`, but the primary use case is chaining within a single graph run via state propagation.

4. **Session management at the framework level (FR-005)** — FR-005 addresses LangGraph checkpointer-based sessions, not Copilot CLI sessions. These are orthogonal: FR-005 manages graph state persistence; this FR manages Copilot CLI process continuity. Both can coexist.

## Related

- `yamlgraph/node_factory/copilot_node.py` — Implementation target
- `yamlgraph/models/schemas.py` — `CopilotResult` model
- `feature-requests/005-session-manager.md` — Orthogonal graph-level session management (deferred)
- `examples/copilot/graph.yaml` — Existing copilot example to extend
- FR-081 — Original copilot node type implementation

## Judgement Notes

**Verdict:** APPROVE — Scope is clear, minimal, and internally consistent. Authority granted.

**Notes for implementer:**

1. **Session ID extraction pattern**: Empirically verify the Copilot CLI stderr format during implementation. The defensive `None` fallback is correct — never fabricate.
2. **State expression resolution for `cli_flags`**: Currently `cli_flags` values are static (used directly). Extending `_resolve_variables()` or adding a dedicated pass for `cli_flags.resume` is prerequisite work — small but necessary.
3. **Invalid resume ID behavior**: When `--resume <invalid-uuid>` is passed, the CLI will exit non-zero. Verify existing error handling covers this in integration tests.
