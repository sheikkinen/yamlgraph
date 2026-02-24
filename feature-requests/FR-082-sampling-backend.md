# Feature Request: MCP Sampling Backend for Copilot Node

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** DROPPED
**Verdict:** OVERENGINEERING
**Judged:** 2026-02-24
**Implemented:** 2026-02-24 (then removed)
**Removed:** 2026-02-24
**Effort:** 2 days (wasted)
**Requested:** 2026-02-24
**FR:** FR-082
**Parent:** FR-081 (Copilot Node Type)

## Post-Mortem: Why Dropped

**Root cause:** Multi-node chains with sampling backend failed due to state serialization issues between LangGraph nodes. `CopilotResult` objects lose their `.output` attribute when passed between nodes, causing `{state.analysis.output}` to resolve to empty string.

**Value assessment:**
- Single-node sampling works (via loopback-poc)
- Multi-node chains are the actual use case
- `backend: cli` already solves the same problem with better testability
- Debugging MCP sampling is extremely difficult (separate process, no direct visibility)

**Lesson:** Before implementing, ask: "Does this add value beyond existing solutions?"

The CLI backend (`backend: cli`) works reliably for multi-node chains. Sampling was a solution seeking a problem.

## Summary

Implement the `_execute_sampling()` stub in `yamlgraph/node_factory/copilot_node.py` so that `backend: sampling` copilot nodes call `session.create_message()` via the MCP sampling protocol when running inside the YAMLGraph MCP server context.

## Problem

FR-081 delivered the copilot node type with two backends. The CLI backend (`backend: cli`) is fully implemented, but the sampling backend (`backend: sampling`) raises `NotImplementedError`. REQ-YG-088 requires:

> Copilot node executes via MCP sampling loopback when available; calls `session.create_message()` in MCP server context.

The loopback proof-of-concept (`scripts/loopback-poc/`) has validated the protocol pattern — `server.request_context.session.create_message()` works from within MCP tool handlers. What remains is threading the MCP session into the copilot node execution path and handling the sync→async boundary.

### Why it matters

1. **Zero API cost** — sampling uses the host LLM (Copilot/Claude); no API keys consumed on the server side
2. **No subprocess overhead** — eliminates `copilot` CLI process spawning
3. **Enables headless MCP deployments** — graphs with copilot nodes can run in MCP server mode without requiring `copilot` binary installed
4. **Completes REQ-YG-088** — the only deferred requirement from FR-081

## Proposed Solution

### Architecture: Context Variable Session Threading

Thread the MCP session from the tool handler through to the copilot node via `contextvars.ContextVar`. This avoids polluting graph state with infrastructure concerns.

```
MCP tool handler (async)
  │
  ├─ set _mcp_session ContextVar
  ├─ copy context
  │
  └─ run_in_executor(ctx.run, _invoke_graph, ...)
       │
       └─ copilot node (sync)
            │
            ├─ read _mcp_session from ContextVar
            └─ asyncio.run_coroutine_threadsafe(
                 session.create_message(...), loop
               ).result(timeout=...)
```

### 1. Session Context Module

New module `yamlgraph/mcp_context.py` (~20 lines):

```python
"""MCP session context for sampling backend (REQ-YG-088)."""
import asyncio
import contextvars

_mcp_session: contextvars.ContextVar = contextvars.ContextVar("_mcp_session", default=None)
_mcp_loop: contextvars.ContextVar = contextvars.ContextVar("_mcp_loop", default=None)

def set_mcp_context(session, loop: asyncio.AbstractEventLoop) -> None:
    _mcp_session.set(session)
    _mcp_loop.set(loop)

def get_mcp_context():
    return _mcp_session.get(), _mcp_loop.get()
```

### 2. MCP Server Integration

In `yamlgraph/mcp_server.py`, modify `_handle_run_graph()` to propagate the MCP session:

```python
async def _handle_run_graph(arguments, graph_lookup):
    # ... existing validation ...

    # NEW: Propagate MCP session to graph execution context
    from yamlgraph.mcp_context import set_mcp_context
    session = server.request_context.session
    loop = asyncio.get_running_loop()
    set_mcp_context(session, loop)

    # Copy context so thread inherits the ContextVars
    ctx = contextvars.copy_context()
    result = await asyncio.wait_for(
        loop.run_in_executor(_executor, ctx.run, _invoke_graph, graph_path, variables),
        timeout=INVOKE_TIMEOUT,
    )
```

### 3. Sampling Backend Implementation

Replace the `NotImplementedError` in `_execute_sampling()`:

```python
def _execute_sampling(node_name: str, prompt: str, state_key: str) -> dict:
    """REQ-YG-088: Calls session.create_message() when in MCP server context."""
    from yamlgraph.mcp_context import get_mcp_context

    session, loop = get_mcp_context()
    if session is None or loop is None:
        raise RuntimeError(
            f"Sampling backend for node '{node_name}' requires MCP server context. "
            f"Run the graph via the YAMLGraph MCP server, or use backend='cli'."
        )

    import mcp.types as types

    coro = session.create_message(
        messages=[
            types.SamplingMessage(
                role="user",
                content=types.TextContent(type="text", text=prompt),
            )
        ],
        max_tokens=4096,
    )

    future = asyncio.run_coroutine_threadsafe(coro, loop)
    result = future.result(timeout=DEFAULT_TIMEOUT)

    # Extract response text
    if hasattr(result.content, "text"):
        response_text = result.content.text
    else:
        response_text = str(result.content)

    model_used = getattr(result, "model", None)

    return {
        state_key: CopilotResult(
            output=response_text,
            exit_code=0,
            model=model_used,
            backend="sampling",
        ),
        "current_step": node_name,
    }
```

### YAML Usage

```yaml
nodes:
  analyze:
    type: copilot
    prompt: prompts/analyze.yaml
    state_key: analysis
    backend: sampling          # Uses host LLM via MCP sampling
    variables:
      topic: "{state.topic}"
```

## Acceptance Criteria

- [ ] `_execute_sampling()` calls `session.create_message()` and returns `CopilotResult` with `backend="sampling"`
- [ ] `RuntimeError` raised with clear message when sampling is called outside MCP server context (no session available)
- [ ] MCP session propagated from tool handler to graph execution via `contextvars.ContextVar`
- [ ] Context properly copied to thread pool executor via `contextvars.copy_context()`
- [ ] Response text extracted from `result.content` (handles both `TextContent` and fallback `str()`)
- [ ] Existing CLI backend behavior unchanged
- [ ] Existing `NotImplementedError` test replaced with proper unit tests
- [ ] Unit tests mock the MCP session (no real MCP connection required)
- [ ] Tests tagged with `@pytest.mark.req("REQ-YG-088")`
- [ ] `mcp_context.py` module created with `set_mcp_context()` / `get_mcp_context()`
- [ ] `mcp` import is lazy (inside function body) to avoid hard dependency for non-MCP usage
- [ ] Timeout respects node-level `timeout` config (default `DEFAULT_TIMEOUT`)

## Implementation Steps

1. **Red:** Write unit tests for `_execute_sampling()` with mocked MCP session. Test success path, missing context error, and response extraction. Tag with `@pytest.mark.req("REQ-YG-088")`.
2. **Green:** Create `yamlgraph/mcp_context.py`. Implement `_execute_sampling()` in `copilot_node.py`. Modify `mcp_server.py` to propagate session context.
3. **Red:** Write integration test verifying context propagation from MCP handler through thread pool to copilot node (mocked session, real threading).
4. **Green:** Wire `contextvars.copy_context()` in `_handle_run_graph()`.
5. **Refactor:** Run ruff, vulture, radon. Ensure `mcp_context.py` stays under 30 lines.
6. **Reflect:** Log diary entry.

### File Changes

| File | Change |
|------|--------|
| `yamlgraph/mcp_context.py` | New — ContextVar-based MCP session threading |
| `yamlgraph/node_factory/copilot_node.py` | Replace `NotImplementedError` in `_execute_sampling()` |
| `yamlgraph/mcp_server.py` | Set MCP context before graph invocation; copy context to executor |
| `tests/unit/test_copilot_node.py` | Replace deferred test with proper sampling tests |

## Alternatives Considered

### 1. Pass session through graph state

Inject `_mcp_session` into the graph's input variables dict. Rejected: pollutes the TypedDict state with infrastructure concerns; session object is not serializable (breaks checkpointing); violates separation between graph state and execution context.

### 2. Module-level global variable

Store session in a module-level variable instead of `ContextVar`. Rejected: not thread-safe. Although the current thread pool has `max_workers=1`, this is an implementation detail that could change. `ContextVar` is the correct primitive for per-execution context.

### 3. Make copilot node async

Convert `copilot_fn` to an async function and await `session.create_message()` directly. Rejected: LangGraph's `StateGraph` expects sync node functions in the standard path. The codebase follows sync-first with async wrappers (per CLAUDE.md). Using `run_coroutine_threadsafe` from the sync thread is the established pattern.

### 4. Separate sampling node type

Create `type: copilot_sampling` as a distinct node type. Rejected: the backend distinction is a deployment concern, not a semantic one. The same graph should be deployable with either backend by changing one config line.

## Judgement

**Verdict: APPROVE** — Scope frozen. Authority granted to implement.

### Evaluation

| Criterion | Assessment |
|-----------|------------|
| Scope clear and minimal | ✅ 4 files, single stub completion, well-bounded by parent FR-081 |
| No contradictions | ✅ Minor note below, not blocking |
| Acceptance criteria measurable | ✅ All 12 criteria are specific and testable |
| Implementation feasible | ✅ PoC validated, patterns established, changes minimal |
| Architecture alignment | ✅ Sync-first, ContextVar, lazy imports, no state pollution |

### Verified Claims

All claims verified against codebase:
- `_execute_sampling()` stub exists at line 256, raises `NotImplementedError` ✅
- `REQ-YG-088` defined in `ARCHITECTURE.md` ✅
- `_handle_run_graph()` already uses `run_in_executor` with `_executor` and `INVOKE_TIMEOUT` ✅
- `scripts/loopback-poc/` validates `session.create_message()` pattern ✅
- `CopilotResult` in `models/schemas.py` has correct fields including `backend: str` ✅
- Deferred test exists in `test_copilot_node.py` at `TestCopilotNodeSampling` ✅

### Implementation Note: Timeout Parameter

The proposed code sample uses `future.result(timeout=DEFAULT_TIMEOUT)` (module constant), but acceptance criterion #12 requires node-level timeout config. The call site (line 168) currently does not pass `timeout` to `_execute_sampling()`, though it does for `_execute_cli()` (line 165). During implementation:
1. Add `timeout` parameter to `_execute_sampling()` signature
2. Pass `timeout` from the call site at line 168, matching the CLI backend pattern

The proposed code is illustrative; the acceptance criteria are the specification.

### Note: `max_tokens` Hardcoded

The proposed code hardcodes `max_tokens=4096`. This is acceptable as a default for initial implementation. If configurability is needed later, it can be added via node config without architectural changes.

## Related

- FR-081: Copilot Node Type (parent FR — deferred REQ-YG-088)
- `yamlgraph/node_factory/copilot_node.py` — Existing stub at `_execute_sampling()`
- `scripts/loopback-poc/mcp_server.py` — Proven sampling pattern
- `yamlgraph/mcp_server.py` — MCP server (CAP-19, REQ-YG-066–068)
- `ARCHITECTURE.md` — REQ-YG-088 definition
- `tests/unit/test_copilot_node.py` — Existing deferred test at line 283
