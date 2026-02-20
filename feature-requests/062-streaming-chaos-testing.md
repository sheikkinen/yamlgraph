# Feature Request: SSE Streaming Chaos Testing & Error Resilience

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-02-20
**Implemented:** 2026-02-20

## Summary

Add chaos testing infrastructure and error handling to `run_graph_streaming_native()` in `yamlgraph/executor_async.py` to discover and handle failure modes: LLM exceptions, timeouts, and connection drops.

## Problem

FR-057–060 fixed **content bugs** (what data flows through the stream). The next class of bugs are **control bugs** (what happens when the stream breaks):

| Failure Mode | Current Behavior | Impact |
|--------------|------------------|--------|
| LLM exception mid-stream | Generator dies silently | Client sees incomplete response, no error signal |
| Slow LLM (>30s) | Connection hangs indefinitely | HTTP timeout at proxy/client, state unclear |
| LLM rate limit (429) | Exception propagates... somewhere | Unclear retry behavior, no backoff signal |
| Client disconnect | Generator continues, tokens lost | Wasted compute, orphaned state |
| Empty chunk flood | Yields nothing, but loops | Busy-wait consuming resources |

*Concurrent session races (same thread_id) are a real concern but depend on checkpointer-specific locking semantics (Redis, SQLite) — deferred to a separate FR when checkpointer infrastructure is established.*

These can't be discovered by "using" the stream — they require "breaking" it deliberately.

## Proposed Solution

### Phase 1: Error Propagation (streaming contract)

Wrap the streaming generator in `try/except` with explicit error events.

**Note:** Cannot `yield` from `finally` block — store interrupt event and yield after:

```python
async def run_graph_streaming_native(
    ...,
    yield_events: bool = True,  # Yield StreamEvent on error/interrupt
) -> AsyncIterator[str | StreamEvent]:
    """Yields str tokens. If yield_events=True, also yields StreamEvent on error/interrupt."""
    app = await load_and_compile_async(graph_path)
    config = config or {}
    interrupt_event = None

    try:
        async for event in app.astream(...):
            # ... existing filter logic ...
            yield token
    except Exception as e:
        if yield_events:
            yield StreamEvent(type="error", error=str(e), error_type=type(e).__name__)
        else:
            raise  # Preserve original behavior if events disabled
    finally:
        # Check for interrupt (but don't yield here — invalid Python)
        # Only check state if a thread_id is configured (stateless graphs have no checkpoint)
        thread_id = (config.get("configurable") or {}).get("thread_id")
        if thread_id and yield_events:
            try:
                state = await app.aget_state(config)
                if state and state.next:
                    interrupt_event = StreamEvent(
                        type="interrupt",
                        payload=_get_interrupt_payload(state),
                    )
            except Exception:
                pass  # CONF-XXX: interrupt detection is best-effort; don't mask original error

    # Yield interrupt event after try/finally completes
    if interrupt_event:
        yield interrupt_event


# In yamlgraph/executor_async.py, alongside run_graph_streaming_native
def _get_interrupt_payload(state: StateSnapshot) -> Any:
    """Extract interrupt payload from state snapshot."""
    if state.tasks and state.tasks[-1].interrupts:
        return state.tasks[-1].interrupts[-1].value
    return None
```

```python
# yamlgraph/models/streaming.py
from pydantic import BaseModel, Field
from typing import Any, Literal


class StreamEvent(BaseModel):
    """Control signal yielded during streaming (Commandment 5: Pydantic for all typed data)."""
    type: Literal["error", "interrupt"]
    error: str | None = None
    error_type: str | None = None
    payload: Any = None

Consumer pattern:
```python
async for item in run_graph_streaming_native(...):
    if isinstance(item, str):
        yield f"data: {format_token(item)}\n\n"
    elif isinstance(item, StreamEvent):
        if item.type == "error":
            yield f"data: {format_error(item)}\n\n"
        elif item.type == "interrupt":
            yield f"data: {format_interrupt(item)}\n\n"
```

### Phase 2: Timeout Support

Use `asyncio.timeout()` to properly catch stalls *during* event waiting, not just between events:

```python
import asyncio

async def run_graph_streaming_native(
    ...,
    timeout: float | None = None,  # Total stream timeout in seconds
    yield_events: bool = True,
) -> AsyncIterator[str | StreamEvent]:
    """
    Args:
        timeout: Max total duration for the stream. If exceeded, yields
            StreamEvent(type="error", error_type="TimeoutError").
    """
    app = await load_and_compile_async(graph_path)
    config = config or {}

    try:
        # asyncio.timeout wraps the entire iteration — catches stalls mid-await
        async with asyncio.timeout(timeout):
            async for event in app.astream(
                initial_state, config, stream_mode="messages", subgraphs=subgraphs
            ):
                # ... filter and yield tokens ...
                yield token
    except asyncio.TimeoutError:
        if yield_events:
            yield StreamEvent(
                type="error",
                error=f"Stream timeout exceeded ({timeout}s)",
                error_type="TimeoutError",
            )
        else:
            raise
    except Exception as e:
        if yield_events:
            yield StreamEvent(type="error", error=str(e), error_type=type(e).__name__)
        else:
            raise
```

**Why `asyncio.timeout()` instead of post-yield check:**
- Post-yield check (`if now - start > timeout`) only triggers *after* an event arrives
- If LLM blocks for 60s on one token, the check never runs
- `asyncio.timeout()` raises during the `async for` await, catching true stalls

### Phase 3: Chaos Testing Infrastructure

Add a minimal chaos graph YAML + chaos tool that simulates failure modes.

**Approach:** Inject chaos at the graph level, not by monkeypatching `create_llm`. The streaming
pipeline goes `graph YAML → compile → app.astream(stream_mode="messages")`. Monkeypatching
`create_llm` alone doesn't guarantee the ChaosLLM's `.astream()` is what `app.astream()`
calls — the compiled graph sits between them. Instead: use a real graph YAML with a
`type: python` chaos node that raises/delays/returns empty, and stream through the
normal compilation pipeline.

```yaml
# tests/fixtures/chaos_graph.yaml
metadata:
  name: chaos-test
  description: Graph for streaming chaos testing
  provider: anthropic

nodes:
  chaos_node:
    type: python
    module: tests.chaos_tools
    function: chaos_respond
    state_key: response

edges:
  - from: START
    to: chaos_node
  - from: chaos_node
    to: END
```

```python
# tests/chaos_tools.py
"""Chaos tool for streaming fault injection tests."""
import asyncio
import os


class SimulatedRateLimitError(Exception):
    """Mock rate limit for testing — real providers use different classes."""
    pass


def chaos_respond(state: dict) -> dict:
    """Python node that simulates various failure modes based on env vars."""
    mode = os.environ.get("CHAOS_MODE", "normal")

    if mode == "fail":
        raise RuntimeError("Simulated LLM failure")
    elif mode == "rate_limit":
        raise SimulatedRateLimitError("429 Too Many Requests")
    elif mode == "slow":
        import time
        time.sleep(float(os.environ.get("CHAOS_DELAY", "5")))
        return {"response": "delayed response"}
    else:
        return {"response": "normal response"}
```

**Note:** Streaming chaos (mid-token failure, empty chunks) requires an LLM node, not
a python node. For those tests, use the existing `mock_llm` fixture pattern from
`tests/conftest.py` — patch the LLM instance *after* graph compilation via
`app.nodes[node_name].llm = chaos_llm`. This injects at the right layer.

```python
# tests/conftest.py — add to existing fixtures
import asyncio
import random
from langchain_core.messages import AIMessageChunk


@pytest.fixture
def chaos_llm_factory():
    """Factory for mock LLMs with controlled failure modes.

    Usage: patch into a compiled graph's node, NOT via create_llm monkeypatch.
    The compiled graph's app.astream() dispatches to node-level LLMs.
    """
    def create(
        fail_after_tokens: int | None = None,
        delay_per_token: float = 0,
        rate_limit_after: int | None = None,
        empty_chunk_probability: float = 0,
    ):
        class ChaosLLM:
            """Mock LLM that simulates failure modes during streaming."""
            async def astream(self, messages, **kwargs):
                tokens_yielded = 0
                for word in "This is a test response".split():
                    if fail_after_tokens and tokens_yielded >= fail_after_tokens:
                        raise RuntimeError("Simulated LLM failure")
                    if rate_limit_after and tokens_yielded >= rate_limit_after:
                        raise SimulatedRateLimitError("429 Too Many Requests")
                    if delay_per_token:
                        await asyncio.sleep(delay_per_token)
                    if random.random() < empty_chunk_probability:
                        yield AIMessageChunk(content="")
                        continue
                    yield AIMessageChunk(content=word + " ")
                    tokens_yielded += 1
        return ChaosLLM()
    return create
```

Test cases:
```python
@pytest.mark.asyncio
@pytest.mark.req("REQ-YG-XXX")
async def test_streaming_handles_exception(monkeypatch):
    """Exception during streaming yields error event, not silent death."""
    events = [e async for e in run_graph_streaming_native(
        "tests/fixtures/chaos_graph.yaml", {},
    )]
    # chaos_respond raises RuntimeError when CHAOS_MODE=fail
    # Here we test the error propagation contract
    errors = [e for e in events if isinstance(e, StreamEvent) and e.type == "error"]
    assert len(errors) == 1
    assert "Simulated" in errors[0].error


@pytest.mark.asyncio
@pytest.mark.req("REQ-YG-XXX")
async def test_streaming_timeout_total():
    """Stream exceeding total timeout yields timeout error."""
    # chaos_graph with CHAOS_MODE=slow, CHAOS_DELAY=5
    events = [e async for e in run_graph_streaming_native(
        "tests/fixtures/chaos_graph.yaml", {}, timeout=0.5
    )]

    errors = [e for e in events if isinstance(e, StreamEvent) and e.type == "error"]
    assert len(errors) == 1
    assert errors[0].error_type == "TimeoutError"


@pytest.mark.asyncio
@pytest.mark.req("REQ-YG-XXX")
async def test_streaming_rate_limit_error():
    """Rate limit error surfaces with identifiable error type."""
    # chaos_graph with CHAOS_MODE=rate_limit
    events = [e async for e in run_graph_streaming_native(
        "tests/fixtures/chaos_graph.yaml", {},
    )]

    errors = [e for e in events if isinstance(e, StreamEvent) and e.type == "error"]
    assert len(errors) == 1
    assert "SimulatedRateLimitError" in errors[0].error_type


@pytest.mark.asyncio
@pytest.mark.req("REQ-YG-XXX")
async def test_streaming_yield_events_false_raises():
    """With yield_events=False, exceptions propagate to caller."""
    with pytest.raises(RuntimeError, match="Simulated"):
        async for _ in run_graph_streaming_native(
            "tests/fixtures/chaos_graph.yaml", {}, yield_events=False,
        ):
            pass


@pytest.mark.asyncio
@pytest.mark.req("REQ-YG-XXX")
async def test_streaming_no_config_skips_interrupt_check():
    """When no thread_id configured, interrupt detection is skipped (no crash)."""
    # Normal graph without config — should not crash in finally block
    events = [e async for e in run_graph_streaming_native(
        "tests/fixtures/chaos_graph.yaml", {},  # No config, no thread_id
    )]
    # Should complete without interrupt-related crash
    errors = [e for e in events if isinstance(e, StreamEvent) and e.type == "error"]
    # No spurious errors from interrupt detection
    assert not any("aget_state" in (e.error or "") for e in errors)
```

*Concurrent session race test deferred — requires Redis checkpointer fixture and
checkpointer-specific locking semantics that are currently unspecified.*

### Phase 4: Consumer Updates (deferred)

Consumer updates (`openai_proxy`, `questionnaire-api`) are separate commits — they are
consumer concerns, not framework features. Each consumer handles `StreamEvent` in its
own SSE format. Pattern documented here for reference:

```python
# Consumer pattern — NOT part of this FR's implementation scope
async def stream_response():
    async for item in run_graph_streaming_native(graph_path, initial_state, config):
        if isinstance(item, str):
            yield f"data: {format_token_chunk(item)}\n\n"
        elif isinstance(item, StreamEvent):
            if item.type == "error":
                yield f"data: {format_error_chunk(item)}\n\n"
            elif item.type == "interrupt":
                yield f"data: {format_interrupt_chunk(item)}\n\n"
    yield "data: [DONE]\n\n"
```

## Acceptance Criteria

- [ ] `run_graph_streaming_native` yields `StreamEvent(type="error")` on exceptions
- [ ] `StreamEvent(type="interrupt")` yielded when graph pauses (only with `thread_id`)
- [ ] `timeout` parameter enforces total stream duration via `asyncio.timeout()`
- [ ] Chaos graph fixture in `tests/fixtures/` for controlled failures
- [ ] `chaos_llm_factory` fixture for mid-stream token-level failures
- [ ] Test: exception yields error event (not silent death)
- [ ] Test: timeout exceeded yields `TimeoutError` event
- [ ] Test: rate limit error surfaces with identifiable error type
- [ ] Test: `yield_events=False` re-raises exceptions to caller
- [ ] Test: no `thread_id` → interrupt detection skipped (no crash)
- [ ] `StreamEvent` uses Pydantic `BaseModel` (Commandment 5)
- [ ] `_get_interrupt_payload()` in `executor_async.py`
- [ ] Documentation in `reference/streaming.md`

## Alternatives Considered

1. **Consumer-side timeout via `asyncio.timeout()`** — Works but doesn't give clean error event; raises exception to caller.

2. **Separate error channel (websocket pattern)** — Overcomplicated for SSE; single-channel with tagged events is simpler.

3. **Retry inside the generator** — Violates separation of concerns; the consumer decides retry policy, not the streaming primitive.

4. **Session locking via Redis** — Could prevent concurrent races but adds latency and depends on checkpointer-specific semantics. Deferred to separate FR.

## Related

- `yamlgraph/executor_async.py` L300-392 — current streaming implementation
- `examples/openai_proxy/api/app.py` L115-155 — SSE consumer
- FR-057, FR-058, FR-059, FR-060 — content bugs this builds on
- Diary entry "The Next Four Bugs" — predictive analysis this implements
- `reference/streaming.md` — needs update for error events

## Implementation Notes

**Phase ordering:**
1. Phase 1 (error propagation + `StreamEvent` model) is foundational
2. Phase 3 (chaos fixtures) enables testing Phases 1 and 2
3. Phase 2 (timeouts) builds on Phase 1's error handling
4. Phase 4 (consumer updates) is out of scope — separate commits per consumer

**Breaking change: `yield_events` defaults to `True`**

Return type changes from `AsyncIterator[str]` to `AsyncIterator[str | StreamEvent]`.

**Rationale:** The whole point of FR-062 is to stop silent failures. Defaulting to `False` means existing consumers *still* get silent failures — defeating the purpose. Better to fix all consumers now than propagate the bug.

**Migration for existing consumers:**
```python
# Before: assumes only strings
async for token in run_graph_streaming_native("graph.yaml", state):
    print(token, end="")

# After: handle both types
async for item in run_graph_streaming_native("graph.yaml", state):
    if isinstance(item, str):
        print(item, end="")
    elif isinstance(item, StreamEvent) and item.type == "error":
        print(f"\nError: {item.error}")

# Or: opt out explicitly
async for token in run_graph_streaming_native("graph.yaml", state, yield_events=False):
    print(token, end="")  # Exceptions propagate as before
```

**Affected consumers:**
- `examples/openai_proxy/api/app.py` — update to handle `StreamEvent`
- `questionnaire-api` SSE routes — update to format error/interrupt events
- Any direct callers — check for `StreamEvent` type

**CHANGELOG entry:**
```markdown
### Breaking Changes
- `run_graph_streaming_native()` now yields `StreamEvent` on error/interrupt by default.
  Pass `yield_events=False` to restore previous behavior (silent failures).
```
