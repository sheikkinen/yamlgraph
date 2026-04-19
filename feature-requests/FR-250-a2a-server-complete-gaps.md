# Feature Request: FR-250 A2A Server — Complete Protocol Gaps

**Priority:** HIGH
**Type:** Enhancement
**Status:** Approved
**Effort:** 3 days
**Requested:** 2026-04-19

## Summary

Implement the three remaining A2A protocol requirements left from FR-208: `task/get` retrieval (REQ-YG-210), `task/sendSubscribe` SSE streaming (REQ-YG-211), and full `input-required` resume flow (REQ-YG-213). Add an integration test proving end-to-end A2A streaming.

## Value Statement

A2A clients can retrieve task status, receive streamed responses, and participate in human-in-loop flows — making YAMLGraph a fully compliant A2A agent server instead of a fire-and-forget endpoint.

## Problem

FR-208 delivered ~70% of the A2A server. Three requirements remain unimplemented:

1. **No `task/get` (REQ-YG-210)**: Clients cannot poll task status. `InMemoryTaskStore` is wired (line 302 of `a2a_server.py`) but never queried. Clients that send a task and disconnect have no way to retrieve results later.

2. **No `task/sendSubscribe` (REQ-YG-211)**: Clients cannot receive streaming responses. The streaming infrastructure exists (`run_graph_streaming_native()` in `executor_async.py`), but no A2A endpoint wraps it. The Agent Card declares `streaming: true` unconditionally — a lie until this is implemented.

3. **Incomplete `input-required` (REQ-YG-213)**: Interrupt *detection* works (lines 142-158 of `a2a_server.py`), but there is no resume path. When a graph hits `__interrupt__`, the server emits `TASK_STATE_INPUT_REQUIRED` and returns — with no mechanism for the client to supply input and continue execution. The interrupt payload (the question/prompt) is also not forwarded to the client.

## Proposed Solution

### Gap 1: `task/get` via task store (REQ-YG-210)

The A2A SDK's `DefaultRequestHandler` already routes `task/get` JSON-RPC calls through `InMemoryTaskStore`. The store is created at app construction. The executor must persist task state after execution so the store can return it on `task/get`.

No new endpoint code is needed — the SDK handler delegates to the store. The fix is ensuring `execute()` saves final task state (status + artifacts) to the store.

### Gap 2: `task/sendSubscribe` via native streaming (REQ-YG-211)

Add a streaming execution path in `YAMLGraphAgentExecutor` that:

1. Calls `run_graph_streaming_native()` instead of `_invoke_graph()`
2. Maps yielded tokens → `TaskArtifactUpdateEvent` (incremental text parts)
3. Maps `StreamEvent(type="error")` → `TaskStatusUpdateEvent(FAILED)`
4. Maps `StreamEvent(type="interrupt")` → `TaskStatusUpdateEvent(INPUT_REQUIRED)` with payload
5. Emits `TASK_STATE_COMPLETED` after generator exhaustion

The A2A SDK's `DefaultRequestHandler` already distinguishes `task/send` from `task/sendSubscribe` and passes a streaming flag via `RequestContext`. The executor checks this flag to choose the sync vs streaming path.

```python
# Pseudocode for streaming path in execute()
async for chunk in run_graph_streaming_native(
    graph_info["path"], variables,
    config={"configurable": {"thread_id": task_id}},
):
    if isinstance(chunk, str):
        await event_queue.enqueue_event(
            TaskArtifactUpdateEvent(
                task_id=task_id,
                context_id=context_id,
                artifact=Artifact(parts=[Part(text=chunk)]),
            )
        )
    elif isinstance(chunk, StreamEvent) and chunk.type == "interrupt":
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=task_id,
                context_id=context_id,
                status=TaskStatus(
                    state=TaskState.TASK_STATE_INPUT_REQUIRED,
                    message=Message(
                        role=Role.ROLE_AGENT,
                        parts=[Part(text=str(chunk.payload))],
                        message_id=str(uuid.uuid4()),
                    ),
                ),
            )
        )
```

### Gap 3: `input-required` resume flow (REQ-YG-213)

Complete the interrupt cycle:

1. **Forward interrupt payload**: When `__interrupt__` is detected, extract the payload value (`result["__interrupt__"][0].value`) and include it in the `INPUT_REQUIRED` message so the client knows *what* to answer.

2. **Resume on subsequent `task/send`**: When `execute()` receives a `RequestContext` with an existing `task_id` that is in `INPUT_REQUIRED` state, invoke the graph with `Command(resume=user_input)` instead of fresh `initial_state`. This requires the checkpointer (task_id = thread_id).

3. **Require checkpointer**: Resumption requires a checkpointer. If the graph has no checkpointer configured, the interrupt detection should emit `TASK_STATE_FAILED` with an explanatory error instead of `INPUT_REQUIRED`.

```python
# Resume path in execute()
if task_in_input_required_state(task_id):
    from langgraph.types import Command
    result = await loop.run_in_executor(
        _executor, _invoke_graph, graph_info["path"],
        Command(resume=text),
        {"configurable": {"thread_id": task_id}},
    )
```

### Agent Card: conditional streaming capability

`build_agent_card()` currently hardcodes `streaming=True`. After this FR, streaming is genuinely supported, so this is correct. No change needed — the declaration becomes truthful.

## Acceptance Criteria

- [ ] **REQ-YG-210**: `task/get` returns task status and artifacts for previously submitted tasks
- [ ] **REQ-YG-211**: `task/sendSubscribe` streams graph execution via `run_graph_streaming_native()`, yielding `TaskArtifactUpdateEvent` per token chunk and proper status transitions
- [ ] **REQ-YG-213**: Interrupt payload forwarded to client in `INPUT_REQUIRED` message; subsequent `task/send` with same `task_id` resumes graph via `Command(resume=...)`
- [ ] Integration test: A2A client → hello graph → streamed response received with correct event sequence (working → artifact chunks → completed)
- [ ] Unit tests for `task/get` retrieval, streaming event mapping, and resume flow
- [ ] `reference/a2a-server.md` updated with `task/get`, streaming, and interrupt/resume documentation
- [ ] Existing tests pass (no regressions)

## Implementation Approach

### Phase 1: `task/get` (0.5 day)

1. RED: Test that `task/get` returns stored task state after `task/send`
2. GREEN: Ensure executor persists task state to `InMemoryTaskStore` after execution
3. Verify via existing A2A SDK handler routing

### Phase 2: `task/sendSubscribe` (1.5 days)

1. RED: Test that streaming execution yields incremental artifact events
2. GREEN: Add streaming branch in `execute()` gated on `RequestContext` streaming flag
3. RED: Test error and interrupt events during streaming
4. GREEN: Map `StreamEvent` types to A2A event types
5. Integration test with hello graph

### Phase 3: `input-required` resume (0.5 day)

1. RED: Test that interrupt payload is included in `INPUT_REQUIRED` message
2. GREEN: Extract `result["__interrupt__"][0].value` and forward as message text
3. RED: Test that `task/send` with existing interrupted task_id resumes via `Command(resume=...)`
4. GREEN: Detect `INPUT_REQUIRED` state in task store, switch to resume invocation path

### Phase 4: Docs + diary (0.5 day)

1. Update `reference/a2a-server.md` with all three capabilities
2. Update FR-208 acceptance criteria to mark REQ-YG-210/211/213 complete
3. Diary entry

## Alternatives Considered

1. **External SSE adapter**: Wrap the existing `task/send` in an SSE proxy outside YAMLGraph. Rejected — defeats the purpose of native A2A streaming support and duplicates event mapping logic.

2. **Polling-only for task status**: Skip `task/sendSubscribe` and rely on `task/get` polling. Rejected — polling is wasteful and the streaming infrastructure already exists.

3. **Skip resume flow**: Implement `INPUT_REQUIRED` as terminal (no continuation). Rejected — half-implemented interrupts are worse than none; clients see "input required" but cannot supply it.

## Judgement

**Verdict: APPROVE — Scope frozen, authority granted.**

**Analysis:**

1. **Scope is clear and minimal.** Three concrete, well-defined gaps completing FR-208's A2A protocol. Each maps to a specific requirement (REQ-YG-210/211/213). No speculative features.

2. **No contradictions.** Claims verified against code:
   - `InMemoryTaskStore` wired (line 302) but never queried — confirmed.
   - `_detect_interrupt()` exists (line 143) but emits generic message, no resume — confirmed.
   - Streaming infra (`run_graph_streaming_native()`, `StreamEvent`) fully available — confirmed.
   - `run_graph_streaming_native()` already accepts `Command` as `initial_state` and yields `StreamEvent(type="interrupt", payload=...)` in its finally block — the infrastructure already supports the proposed design.

3. **Acceptance criteria are measurable** — each maps to a testable behavior with specific event types and states.

4. **Feasibility confirmed.** The A2A SDK, streaming generator, and `Command(resume=...)` pattern all exist. The implementation extends `execute()` with branching logic, not new abstractions.

5. **Single responsibility preserved.** All three gaps complete one protocol implementation (FR-208) in one module (`a2a_server.py`). Splitting would add overhead without architectural benefit — Gap 1 is 0.5 days.

**Implementation notes (non-blocking):**

- **Gap 1 persistence mechanism:** Verify whether `DefaultRequestHandler` auto-persists task state from events to `InMemoryTaskStore`, or if `execute()` must explicitly call `store.save()`. The SDK may already handle this; if so, Gap 1 reduces to a verification test.
- **Existing REQ-YG-211 tests:** Current tests tagged REQ-YG-211 verify batch event ordering (working → artifact → completed), not actual `task/sendSubscribe` streaming. These tests remain valid for the batch path. New streaming tests should exercise the `run_graph_streaming_native()` integration path distinctly.
- **Checkpointer detection (Gap 3):** The FR states "emit FAILED if no checkpointer configured." Clarify detection mechanism during implementation — likely checking `config.get("configurable", {}).get("thread_id")` presence or attempting `aget_state()`.

## Related

- **FR-208**: Original A2A server feature request (`feature-requests/FR-208-a2a-graph-support.md`)
- **REQ-YG-210/211/213**: Requirements in `ARCHITECTURE.md` (lines 1022-1025)
- **CAP-81**: A2A server capability (`capabilities/CAP-81-a2a-server.yaml`)
- **Streaming infra**: `run_graph_streaming_native()` in `yamlgraph/executor_async.py`
- **Interrupt pattern**: `reference/interrupt-nodes.md`
- **A2A server code**: `yamlgraph/a2a_server.py`, `yamlgraph/a2a_message.py`
- **Existing tests**: `tests/unit/test_a2a_server.py`
