# FR-049: Interactive Tool Node Type

**Priority:** MEDIUM
**Type:** Feature
**Status:** Judged
**Effort:** 3-5 days (Phase 1: 2 days)
**Requested:** 2026-02-19
**Judged:** 2026-02-19

## Summary

A new `interactive_tool` node type for multi-turn stateful tool integration. Encapsulates the start → interrupt → step → loop → end pattern into a single declarative node, eliminating the need to inline 4+ nodes with manual edges.

## Problem

When a graph needs to integrate a **stateful external service that requires human input mid-execution**, the only current options are:

1. **Subgraph** — semantically correct, but `interrupt_output_mapping` via `__pregel_send` doesn't surface state through `astream(stream_mode="messages")`. Consumers using SSE token streaming never see the mapped values. Closed as "not a bug" (FR-039) because `stream_mode="values"` works — but SSE endpoints need `stream_mode="messages"` for OpenAI-compatible streaming.

2. **Inline nodes** — works, but explodes the parent graph with boilerplate. Each interactive tool requires 4+ nodes and 5+ edges that follow an identical pattern.

### Production evidence

Two independent cases in `questionnaire-api` required the same workaround (inlining):

**Case 1: Ninchat bot integration** — WebSocket chat with customer service bot

```
nc_create_session → nc_ask_user (interrupt) → nc_forward_to_bot → loop back / nc_close_session
```

4 nodes, 6 edges, 3 tools (`create_bot_session`, `send_to_bot`, `close_bot_session`).

**Case 2: Tunnistautuminen (strong authentication)** — SMS-based identity verification

```
check_phone → ask_phone (interrupt) → send_auth → inform_user → wait_auth (interrupt) → check_auth → loop / terminal states
```

10 nodes, 16 edges, 2 tools (`send_auth`, `check_auth`) — more complex because of multiple terminal states and retry logic.

Both were originally subgraphs. Both had to be inlined into the parent graph to work with SSE streaming. The core pattern is identical:

```
start()    → initial response (show to user)
continue() → user input → tool response (show to user, repeat)
end()      → final result (return to parent flow)
```

This is a **coroutine** — a tool that yields control back to the user mid-execution. YAMLGraph has no primitive for it.

## Proposed Solution

### Basic form — simple loop (Ninchat pattern)

```yaml
nodes:
  ninchat_chat:
    type: interactive_tool
    start: create_bot_session        # Called once on entry
    step: send_to_bot                # Called per user turn
    end: close_bot_session           # Called on exit
    resume_key: user_message         # State key for user input
    response_key: bot_response       # State key for tool output shown to user
    loop_until: "phase == 'completed' or phase == 'error'"
```

**Expansion**: the runtime generates the equivalent of:

```
[start tool] → [interrupt: resume_key] → [step tool] → condition → loop back / [end tool]
```

This replaces 4 hand-written nodes and 6 edges with 1 node.

### Extended form — with error/terminal branches (Auth pattern)

```yaml
nodes:
  authenticate:
    type: interactive_tool
    start: send_auth
    step: check_auth
    end: null                        # No cleanup needed
    resume_key: user_message
    response_key: response
    loop_until: "auth_status in ('finished', 'authenticated', 'expired', 'failed', 'aborted', 'error')"
    max_iterations: 5                # Default: 10. Routes to END on exhaustion.
    on_error: skip                   # Uses existing error handling pattern
```

### Implementation sketch

The `interactive_tool` node type compiles to a mini-subgraph at graph build time, but uses the **parent graph's checkpointer** — no cross-graph state mapping:

```python
def create_interactive_tool_node(config: InteractiveToolConfig):
    """Expand interactive_tool into inline nodes at compile time."""
    nodes = {}
    edges = []

    prefix = config.node_name

    # 1. Start node — calls start tool
    nodes[f"{prefix}__start"] = PythonNode(tool=config.start)

    # 2. Ask user — interrupt
    nodes[f"{prefix}__ask"] = InterruptNode(resume_key=config.resume_key)

    # 3. Step node — calls step tool
    nodes[f"{prefix}__step"] = PythonNode(tool=config.step)

    # 4. End node — calls end tool (if provided)
    if config.end:
        nodes[f"{prefix}__end"] = PythonNode(tool=config.end)

    # Edges: start → ask → step → (loop condition) → ask / end
    edges.append(Edge(f"{prefix}__start", f"{prefix}__ask",
                       condition=f"phase != 'error'"))
    if config.end:
        edges.append(Edge(f"{prefix}__start", f"{prefix}__end",
                           condition=f"phase == 'error'"))
    edges.append(Edge(f"{prefix}__ask", f"{prefix}__step"))
    edges.append(Edge(f"{prefix}__step", f"{prefix}__ask",
                       condition=f"not ({config.loop_until})"))
    target = f"{prefix}__end" if config.end else None  # None = next node in parent edges
    edges.append(Edge(f"{prefix}__step", target,
                       condition=config.loop_until))

    return nodes, edges
```

Key insight: **compile-time expansion, not runtime subgraph**. The generated nodes live in the parent graph's namespace and use its checkpointer. No `interrupt_output_mapping`. No `__pregel_send`. No stream mode coupling.

### Response surfacing

The `response_key` field specifies which state key holds the user-visible output. After `start` and `step` calls, the runtime checks `state[response_key]` and surfaces it through the interrupt's `message` field:

```yaml
# Generated interrupt node includes message mapping:
{prefix}__ask:
  type: interrupt
  message: "{{ state.{response_key} }}"
  resume_key: "{resume_key}"
```

This ensures SSE consumers see the bot/tool response regardless of stream mode.

## Judgment Constraints

1. **Tool resolution via `callable_registry`** — `start`, `step`, `end` must be Python tool references resolved through the same registry as `type: python` nodes. Not YAML tool names.
2. **Expression evaluator reuse** — `loop_until` must use `yamlgraph/utils/expression.py`, not a new evaluator.
3. **No `__` in user node names** — generated internal names use `{prefix}__start`, `{prefix}__ask`, etc. Linter must reject user-defined node names containing `__`.
4. **Phase 1 excludes `on_error.output`** — custom output dicts on error are a new concept. Use existing `on_error: skip|retry|fail|fallback` pattern. Defer custom output to Phase 2.
5. **`end` tool output mapping** — when `end` tool returns state updates, they must map to parent graph state keys. Follow `subgraph_nodes.py` output mapping pattern.
6. **`max_iterations` default: 10** — on exhaustion, route to END (or `end` tool if defined). No custom output in Phase 1.
7. **REQ-YG-073** — new requirement ID for this capability.

## Phase 1 Scope (Frozen)

- `start`, `step`, `end` (optional) tool hooks via `callable_registry`
- `resume_key` and `response_key` state key mapping
- `loop_until` via existing expression evaluator
- `max_iterations` (default: 10) with fallback to END
- Compile-time expansion to inline nodes in `node_compiler.py`
- Stream mode agnostic (tested with `messages`, `values`, `updates`)
- Works with all checkpointers (memory, SQLite, Redis)
- Linter/validator support for the new node type
- 8-10 unit tests tagged `@pytest.mark.req("REQ-YG-073")`

### Deferred to Phase 2

- `on_error.output` custom error output mapping
- `on_max_iterations.output` custom exhaustion output
- Nested interactive tools (interactive_tool inside map)
- Dynamic `loop_until` conditions based on LLM decisions

## Use Cases Beyond Ninchat/Auth

| Use Case | start | step | end |
|----------|-------|------|-----|
| **Chat with external bot** | Connect to bot, get greeting | Forward message, get reply | Disconnect |
| **Strong authentication** | Send SMS/email challenge | Check verification status | — |
| **Document upload flow** | Request document | Validate + request corrections | Confirm acceptance |
| **Multi-step form wizard** | Show first section | Validate section, show next | Submit form |
| **Payment flow** | Create payment intent | Check payment status | Confirm receipt |
| **Guided troubleshooting** | Run initial diagnostic | Run next check based on input | Generate report |

The pattern is universal: any external service with a stateful session that requires human interaction in the loop.

## Acceptance Criteria (Phase 1)

- [ ] `NodeType.INTERACTIVE_TOOL` added to enum
- [ ] Compile-time expansion in `node_compiler.py` (new elif branch)
- [ ] `start`, `step`, `end` tool hooks via `callable_registry`
- [ ] `resume_key` and `response_key` state mapping
- [ ] `loop_until` via existing expression evaluator
- [ ] `max_iterations` (default 10) with route to END
- [ ] Existing `on_error` pattern (skip/retry/fail/fallback) — no custom output
- [ ] Works with all stream modes (`messages`, `values`, `updates`)
- [ ] Works with all checkpointers (memory, SQLite, Redis)
- [ ] Linter rejects node names containing `__`
- [ ] Lint/validate support for `interactive_tool` fields
- [ ] 8-10 unit tests tagged `@pytest.mark.req("REQ-YG-073")`
- [ ] Documentation with Ninchat and Auth examples

## Alternatives Considered

### Subgraph with `mode=invoke` (current)

Works with `ainvoke()` and `stream_mode="values"`, but not with `stream_mode="messages"` which SSE endpoints need for OpenAI-compatible token streaming. Requires `interrupt_output_mapping` which doesn't surface through all stream modes. Two production cases had to abandon this approach.

### A2A protocol (FR-045)

Correct for cross-framework agent interop, but massive overkill for "call a Python function that needs user input." Requires HTTP server, Agent Card, protocol negotiation, task lifecycle — for what is essentially a coroutine. A2A solves a different problem (agent discovery and collaboration across network boundaries).

### Manual inlining (current workaround)

Works but doesn't scale. Each interactive tool adds 4-10 nodes and 5-16 edges of boilerplate to the parent graph. The pattern is identical every time — it should be a primitive.

## Related

- FR-039: `async interrupt_output_mapping` (closed, not a bug — stream mode behavior)
- FR-045: A2A protocol brainstorm (separate concern — inter-agent interop)
- FR-045b: A2A consumer `a2a_call` node (network-level, heavyweight)
- `questionnaire-api` commit `900b6cb`: ninchat inlining workaround
- `questionnaire-api` navigator `graph.yaml`: lines 310-340 (ninchat), 340-420 (tunnistautuminen)
- `questionnaire-api` `src/questionnaire/handlers/ninchat_inquiry.py`: production tool functions
