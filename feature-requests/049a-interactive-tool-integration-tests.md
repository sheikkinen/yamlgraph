# FR-049a: Interactive Tool Integration Tests

**Parent:** FR-049 (Interactive Tool Node Type)
**Type:** Test Plan
**Status:** Judged
**Requested:** 2026-02-19
**Judged:** 2026-02-19

## Objective

Stand-alone integration tests proving FR-049's interactive_tool node type works end-to-end through the full `YAML → load → expand → compile → invoke → resume` pipeline with **all stream modes** and **all checkpointers**.

These tests close the two open acceptance criteria from FR-049:
- [ ] Works with all stream modes (`messages`, `values`, `updates`)
- [ ] Works with all checkpointers (memory, SQLite, Redis)

## Stub: Chatbot Tool

Inspired by the Ninchat bot pattern (`projects/ninchat/tools/inquiry.py`) but fully deterministic — no WebSocket, no LLM, no external dependencies. The stub simulates a stateful multi-turn chatbot session.

### Tool Functions (`tests/integration/stubs/chatbot_tool.py`)

All functions follow the `func(state: dict) → dict` convention.

```python
"""Stub chatbot tool for FR-049 interactive_tool integration tests.

Simulates a stateful multi-turn chatbot session.
No WebSocket, no LLM — pure deterministic state manipulation.
Inspired by projects/ninchat/tools/inquiry.py.
"""

from __future__ import annotations

# In-memory session store (reset between tests)
_sessions: dict[str, dict] = {}


def chatbot_start(state: dict) -> dict:
    """Start a new chatbot session. Returns greeting."""
    session_id = f"session-{len(_sessions) + 1}"
    _sessions[session_id] = {"turn": 0, "history": []}
    return {
        "session_id": session_id,
        "bot_response": "Hello! I'm a stub chatbot. How can I help?",
        "session_done": False,
    }


def chatbot_step(state: dict) -> dict:
    """Process user message. Returns bot response."""
    session_id = state.get("session_id", "")
    user_message = state.get("user_message", "")
    session = _sessions.get(session_id, {"turn": 0, "history": []})

    session["turn"] += 1
    session["history"].append(user_message)

    # Deterministic responses
    if "bye" in user_message.lower() or "quit" in user_message.lower():
        return {
            "bot_response": "Goodbye! Session complete.",
            "session_done": True,
        }

    if session["turn"] >= 5:
        return {
            "bot_response": f"Max turns reached (turn {session['turn']}). Ending.",
            "session_done": True,
        }

    return {
        "bot_response": f"Turn {session['turn']}: You said '{user_message}'",
        "session_done": False,
    }


def chatbot_end(state: dict) -> dict:
    """Close session. Returns summary."""
    session_id = state.get("session_id", "")
    session = _sessions.pop(session_id, {"turn": 0, "history": []})
    return {
        "session_summary": f"Session {session_id}: {session['turn']} turns",
    }


def reset_sessions():
    """Test helper: clear all sessions."""
    _sessions.clear()
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Deterministic responses | Tests must be repeatable without LLM |
| `session_done` flag | Maps naturally to `loop_until: "state.session_done == True"` |
| `_sessions` dict with reset | Simulates stateful external service; resettable per test |
| No end tool in variant B | Tests the optional `end` path (step exits directly) |
| `"bye"` trigger | Gives tests explicit control over loop termination |

## Graph Fixtures

### A: Full chatbot (`tests/integration/fixtures/interactive_tool/chatbot.yaml`)

All 4 hooks: start → ask → step → end.

```yaml
version: "1.0"
name: stub-chatbot
description: FR-049 integration test — interactive_tool with start/step/end

tools:
  chatbot_start:
    type: python
    module: tests.integration.stubs.chatbot_tool
    function: chatbot_start
    description: "Start chatbot session"
  chatbot_step:
    type: python
    module: tests.integration.stubs.chatbot_tool
    function: chatbot_step
    description: "Process user turn"
  chatbot_end:
    type: python
    module: tests.integration.stubs.chatbot_tool
    function: chatbot_end
    description: "Close chatbot session"

state:
  session_id: str
  user_message: str
  bot_response: str
  session_done: bool
  session_summary: str

nodes:
  chat:
    type: interactive_tool
    start: chatbot_start
    step: chatbot_step
    end: chatbot_end
    resume_key: user_message
    response_key: bot_response
    loop_until: "state.session_done == True"
    max_iterations: 10

edges:
  - from: START
    to: chat
  - from: chat
    to: END
```

**Expected expansion** (5 nodes, 7 edges):
- `chat__start` (python) → `chat__ask` (interrupt, idempotent=False) → `chat__step` (python, loop_limit=10)
- If `session_done == True` → `chat__end` (python) → END
- If `session_done != True` → `chat__ask` (loop back)

### B: No-end chatbot (`tests/integration/fixtures/interactive_tool/chatbot_no_end.yaml`)

3 hooks only: start → ask → step (no end tool).

```yaml
version: "1.0"
name: stub-chatbot-no-end
description: FR-049 integration test — interactive_tool without end tool

tools:
  chatbot_start:
    type: python
    module: tests.integration.stubs.chatbot_tool
    function: chatbot_start
    description: "Start chatbot session"
  chatbot_step:
    type: python
    module: tests.integration.stubs.chatbot_tool
    function: chatbot_step
    description: "Process user turn"

state:
  session_id: str
  user_message: str
  bot_response: str
  session_done: bool

nodes:
  chat:
    type: interactive_tool
    start: chatbot_start
    step: chatbot_step
    resume_key: user_message
    response_key: bot_response
    loop_until: "state.session_done == True"
    max_iterations: 5

edges:
  - from: START
    to: chat
  - from: chat
    to: END
```

**Expected expansion** (3 nodes, 5 edges):
- `chat__start` → `chat__ask` → `chat__step`
- If `session_done == True` → END (edge from step with condition)
- If `session_done != True` → `chat__ask` (loop back)

## Integration Test Matrix

### File: `tests/integration/test_interactive_tool.py`

All tests tagged `@pytest.mark.req("REQ-YG-075")`.

### Test Cases

#### T1: Basic 3-Turn Conversation (MemorySaver, sync)

**Pattern:** sync `load_graph_config()` + `compile_graph()` + `graph.compile(checkpointer=MemorySaver())`

```
invoke({}) → interrupt (greeting)
  assert bot_response == "Hello! I'm a stub chatbot..."
  assert "__interrupt__" in result

invoke(Command(resume="hello")) → interrupt (turn 1)
  assert "You said 'hello'" in bot_response

invoke(Command(resume="bye")) → complete (session closed)
  assert session_summary contains "2 turns"
  assert "__interrupt__" not in result
```

Tests: start→ask→step loop, end tool, condition routing, 3 interrupt/resume cycles.

#### T2: Max Iterations Exhaustion (MemorySaver, sync)

Same graph, but never say "bye" — let `max_iterations` (or stub's turn≥5) trigger exit.

```
invoke({}) → interrupt
invoke(Command(resume="msg1")) → interrupt
invoke(Command(resume="msg2")) → interrupt
... repeat until max_iterations or session_done
assert final result has session_summary  # end tool ran
```

Tests: `loop_limit` enforcement on step node.

#### T3: No-End Variant (MemorySaver, sync)

Uses `chatbot_no_end.yaml`. Step exits directly to END when `loop_until` fires.

```
invoke({}) → interrupt
invoke(Command(resume="bye")) → complete
assert "session_summary" not in result  # no end tool
assert session_done == True
```

Tests: the optional end tool path.

#### T4: Async Multi-Turn (MemorySaver, async)

**Pattern:** `load_and_compile_async()` + `run_graph_async()` + `Command(resume=...)`

Same flow as T1, but async. Validates the async compilation path correctly handles expanded interactive_tool nodes.

#### T5: SqliteSaver In-Memory (sync)

**Pattern:** Override checkpointer after compilation.

```python
from langgraph.checkpoint.sqlite import SqliteSaver
checkpointer = SqliteSaver.from_conn_string(":memory:")
```

Same flow as T1. Validates checkpointer-agnostic behavior.

#### T6: Stream Mode — `values` (MemorySaver, sync)

**Pattern:** `graph.stream(input, config, stream_mode="values")`

```python
chunks = list(graph.stream({}, config, stream_mode="values"))
# First chunk should be initial state
# Last chunk before interrupt should contain bot_response

# Resume
chunks = list(graph.stream(Command(resume="hello"), config, stream_mode="values"))
# Should contain updated bot_response
```

Tests: interrupt/resume cycle works through `.stream()` with `values` mode.

#### T7: Stream Mode — `updates` (MemorySaver, sync)

**Pattern:** `graph.stream(input, config, stream_mode="updates")`

```python
chunks = list(graph.stream({}, config, stream_mode="updates"))
# Should see per-node updates: chat__start, then interrupt
for node_name, update in chunks:
    assert node_name in ("chat__start", "__interrupt__", ...)
```

Tests: each expanded sub-node emits its own update chunk.

#### T8: Stream Mode — `messages` (MemorySaver, async)

**Pattern:** `graph.astream(input, config, stream_mode="messages")`

```python
messages = []
async for msg, metadata in graph.astream(Command(resume="hello"), config, stream_mode="messages"):
    messages.append(msg)
```

Note: `messages` mode only works with LLM nodes that produce AIMessage/HumanMessage. Since our stub uses `type: python` (not `type: llm`), **this test verifies the graph doesn't crash** rather than asserting message content. The key validation is that interrupt/resume still works through this stream mode.

#### T9: Redis Checkpointer (async, optional)

**Pattern:** Skip if Redis unavailable.

```python
import pytest

@pytest.mark.skipif(not redis_available(), reason="Redis not available")
@pytest.mark.asyncio
async def test_redis_checkpointer():
    ...
```

Same flow as T4, but with Redis checkpointer. Validates that the expanded nodes' state serializes correctly through Redis (FR-048 BaseModel serialization).

### Test Count Summary

| ID | Test Name | Checkpointer | Mode | Sync/Async | Graph |
|----|-----------|-------------|------|-----------|-------|
| T1 | basic_3_turn | MemorySaver | invoke | sync | chatbot.yaml |
| T2 | max_iterations | MemorySaver | invoke | sync | chatbot.yaml |
| T3 | no_end_variant | MemorySaver | invoke | sync | chatbot_no_end.yaml |
| T4 | async_multi_turn | MemorySaver | invoke | async | chatbot.yaml |
| T5 | sqlite_checkpointer | SqliteSaver(:memory:) | invoke | sync | chatbot.yaml |
| T6 | stream_values | MemorySaver | values | sync | chatbot.yaml |
| T7 | stream_updates | MemorySaver | updates | sync | chatbot.yaml |
| T8 | stream_messages | MemorySaver | messages | async | chatbot.yaml |
| T9 | redis_checkpointer | Redis | invoke | async | chatbot.yaml |

**Total: 9 tests** (8 always-run + 1 skip-if-no-Redis)

## File Structure

```
tests/
  integration/
    stubs/
      __init__.py
      chatbot_tool.py          # Stub tool functions
    fixtures/
      interactive_tool/
        chatbot.yaml            # Full chatbot graph (start/step/end)
        chatbot_no_end.yaml     # No-end variant
    test_interactive_tool.py    # 9 integration tests
```

## Dependencies

- No LLM API keys required (all nodes are `type: python` or `type: interrupt`)
- No external services
- Redis optional (T9 skips gracefully)
- SQLite via langgraph built-in (`langgraph-checkpoint-sqlite`)

## Acceptance Criteria

After implementation:
- [ ] All 9 tests pass with `pytest tests/integration/test_interactive_tool.py -v`
- [ ] All tests tagged `@pytest.mark.req("REQ-YG-075")`
- [ ] `pytest tests/ -q` still passes (no regressions)
- [ ] `ruff check` clean
- [ ] FR-049 acceptance criteria updated to checked

## Notes

- The stub chatbot is intentionally simple. No mocking framework needed — regular Python functions with deterministic output.
- The `_sessions` dict simulates external state (like Ninchat's WebSocket connection). The `reset_sessions()` helper should be called in a pytest fixture's `yield` teardown.
- Stream mode `messages` (T8) is the trickiest. Since `type: python` nodes don't emit LangChain messages, we primarily verify the graph doesn't error and that interrupt/resume still works. Real `messages` streaming requires `type: llm` nodes, which would need API keys and defeat the purpose of standalone tests.
- The `idempotent=False` flag on `chat__ask` is critical: each loop iteration must re-generate the interrupt payload from the *updated* `bot_response`, not cache the first one.

---

## Judge Verdict (2026-02-19)

**Decision: APPROVED with 1 blocker + 4 corrections**

The plan is clear, minimal, and well-structured. The stub chatbot design is sound — deterministic, no external deps, idiomatic `func(state) → dict` convention. The test matrix covers the right dimensions. However, code audit against the actual routing implementation reveals one incorrect assertion and several precision issues.

### Blocker 1: T2 `session_summary` assertion is wrong when `_loop_limit_reached` fires

**Root cause:** When `loop_limit` is reached on `chat__step`, `create_python_node()` returns `{"_loop_limit_reached": True}` without executing the tool. The router `make_expr_router_fn()` ([routing.py#L68](yamlgraph/routing.py#L68)) checks `_loop_limit_reached` **before** evaluating conditions and returns `END` directly — bypassing `chat__end`. The end tool never runs.

```python
# routing.py line 68
if state.get("_loop_limit_reached"):
    return END  # ← bypasses chat__end, goes straight to graph END
```

**Consequence:** T2 says "assert final result has `session_summary`" — this is false when `_loop_limit_reached` triggers. The end tool is skipped.

**However:** The stub's internal `turn >= 5` check sets `session_done = True` *before* `loop_limit` (10) fires. So the condition routing (`state.session_done == True`) triggers normally, routing to `chat__end` correctly. T2 actually tests stub natural termination, not `max_iterations` enforcement.

**Fix:** Split T2 into two tests:
- **T2a** (natural exit): Use `chatbot.yaml` (max_iterations=10). Send 5 non-"bye" messages. Stub sets `session_done=True` at turn 5. Assert: `session_summary` exists (end tool ran via condition routing).
- **T2b** (loop_limit exit): Use `chatbot_no_end.yaml` with `max_iterations: 2`. Send 2 non-"bye" messages. On turn 3, step hits `loop_limit` → `_loop_limit_reached=True` → router exits to END. Assert: graph terminated, `session_done` is still `False`.

### Correction 1: SqliteSaver instantiation pattern

The plan uses `SqliteSaver.from_conn_string(":memory:")` — this API doesn't exist in the codebase. The actual pattern ([checkpointer_factory.py#L87-L89](yamlgraph/storage/checkpointer_factory.py#L87)):

```python
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
conn = sqlite3.connect(":memory:", check_same_thread=False)
checkpointer = SqliteSaver(conn)
```

### Correction 2: Missing `__init__.py` files

The plan lists `tests/integration/stubs/__init__.py` in the file structure — correct. But it also needs `tests/integration/fixtures/__init__.py` (new directory) and `tests/integration/fixtures/interactive_tool/` doesn't need one (not a Python package — just YAML files). Explicit list of required `__init__.py` files:
- `tests/integration/stubs/__init__.py` ← **must create**

### Correction 3: Sync `.stream()` is uncharted territory

T6 and T7 use sync `graph.stream(input, config, stream_mode=...)` — there are **zero** existing sync `.stream()` tests in the codebase. All streaming tests use async `astream()` via `run_graph_streaming_native()`. The API is LangGraph-native and should work, but:
- If sync `.stream()` doesn't properly yield chunks before an interrupt, these tests may behave unexpectedly.
- Add a brief comment in T6 noting this is the first sync `.stream()` test.
- If sync `.stream()` proves problematic, fallback to async `astream()`.

### Correction 4: T2b needs its own fixture or parametrize

T2b (loop_limit enforcement) requires `max_iterations: 2` but `chatbot.yaml` has `max_iterations: 10`. Options:
- (a) Create a third fixture `chatbot_low_limit.yaml` with `max_iterations: 2`
- (b) Use `chatbot_no_end.yaml` (already has `max_iterations: 5`) and send 5+ messages — but the stub exits at turn 5, same problem
- (c) ✅ **Best:** Override `max_iterations` to 2 at the config dict level after `load_graph_config()` but before `compile_graph()` — no extra fixture needed

### Constraints (for Enforce phase)

1. T2 must be split: T2a (condition routing, end tool runs) + T2b (loop_limit, no end tool)
2. SqliteSaver via `sqlite3.connect(":memory:") → SqliteSaver(conn)`, not `from_conn_string`
3. Must create `tests/integration/stubs/__init__.py`
4. T6/T7: add comment noting first-ever sync `.stream()` test; fallback to async if broken
5. All 10 tests (was 9, now +1 from T2 split) tagged `@pytest.mark.req("REQ-YG-075")`
6. Stub's `reset_sessions()` must be called in a pytest fixture teardown
7. `chatbot_start()` MUST return `bot_response` key (critical: `{bot_response}` template in `__ask` node would `KeyError` otherwise)
8. T8 (`messages` mode): assert "doesn't crash" + interrupt/resume works — no message content assertions (python nodes don't emit LangChain messages)

### Approved Test Matrix (10 tests)

| ID | Test Name | Checkpointer | Mode | Sync/Async | Graph |
|----|-----------|-------------|------|-----------|-------|
| T1 | basic_3_turn | MemorySaver | invoke | sync | chatbot.yaml |
| T2a | natural_exit_5_turns | MemorySaver | invoke | sync | chatbot.yaml |
| T2b | loop_limit_exit | MemorySaver | invoke | sync | chatbot.yaml (patched max=2) |
| T3 | no_end_variant | MemorySaver | invoke | sync | chatbot_no_end.yaml |
| T4 | async_multi_turn | MemorySaver | invoke | async | chatbot.yaml |
| T5 | sqlite_checkpointer | SqliteSaver(:memory:) | invoke | sync | chatbot.yaml |
| T6 | stream_values | MemorySaver | values | sync | chatbot.yaml |
| T7 | stream_updates | MemorySaver | updates | sync | chatbot.yaml |
| T8 | stream_messages | MemorySaver | messages | async | chatbot.yaml |
| T9 | redis_checkpointer | Redis | invoke | async | chatbot.yaml |

Scope frozen. Authority granted to Enforce.
