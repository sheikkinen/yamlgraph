# Feature Request: SSE Streaming Chaos Testing & Error Resilience

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 2 days
**Requested:** 2026-02-20

## Summary

Add chaos testing infrastructure and error handling to `run_graph_streaming_native()` to discover and handle failure modes: LLM exceptions, timeouts, concurrent session races, and connection drops.

## Problem

FR-057–060 fixed **content bugs** (what data flows through the stream). The next class of bugs are **control bugs** (what happens when the stream breaks):

| Failure Mode | Current Behavior | Impact |
|--------------|------------------|--------|
| LLM exception mid-stream | Generator dies silently | Client sees incomplete response, no error signal |
| Slow LLM (>30s) | Connection hangs indefinitely | HTTP timeout at proxy/client, state unclear |
| Concurrent requests (same thread_id) | Undefined — possible interleaved checkpoints | Corrupted state, out-of-order tokens |
| LLM rate limit (429) | Exception propagates... somewhere | Unclear retry behavior, no backoff signal |
| Client disconnect | Generator continues, tokens lost | Wasted compute, orphaned state |
| Empty chunk flood | Yields nothing, but loops | Busy-wait consuming resources |

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
        state = await app.aget_state(config)
        if state and state.next and yield_events:
            interrupt_event = StreamEvent(
                type="interrupt",
                payload=_get_interrupt_payload(state),
            )

    # Yield interrupt event after try/finally completes
    if interrupt_event:
        yield interrupt_event


def _get_interrupt_payload(state: StateSnapshot) -> Any:
    """Extract interrupt payload from state snapshot."""
    if state.tasks and state.tasks[-1].interrupts:
        return state.tasks[-1].interrupts[-1].value
    return None
```

```python
# yamlgraph/models/streaming.py
from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class StreamEvent:
    """Control signal yielded during streaming."""
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

Add mock LLM fixtures that simulate failure modes:

```python
# tests/conftest.py
import asyncio
import random
from langchain_core.messages import AIMessageChunk


class SimulatedRateLimitError(Exception):
    """Mock rate limit for testing — real providers use different classes."""
    pass


@pytest.fixture
def chaos_llm_factory():
    """Factory for LLMs with controlled failure modes."""
    def create(
        fail_after_tokens: int | None = None,
        delay_per_token: float = 0,
        rate_limit_after: int | None = None,
        empty_chunk_probability: float = 0,
    ):
        class ChaosLLM:
            async def astream(self, messages):
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
async def test_streaming_handles_mid_stream_exception(chaos_llm_factory, monkeypatch):
    """Exception after 3 tokens yields error event, not silent death."""
    llm = chaos_llm_factory(fail_after_tokens=3)
    monkeypatch.setattr("yamlgraph.utils.llm_factory.create_llm", lambda **k: llm)

    events = [e async for e in run_graph_streaming_native("test.yaml", {})]

    tokens = [e for e in events if isinstance(e, str)]
    errors = [e for e in events if isinstance(e, StreamEvent) and e.type == "error"]

    assert len(tokens) == 3  # Got partial response
    assert len(errors) == 1  # Got error signal
    assert "Simulated LLM failure" in errors[0].error


@pytest.mark.asyncio
async def test_streaming_timeout_total(chaos_llm_factory, monkeypatch):
    """Stream exceeding total timeout yields timeout error."""
    llm = chaos_llm_factory(delay_per_token=0.5)  # 5 tokens × 0.5s = 2.5s
    monkeypatch.setattr("yamlgraph.utils.llm_factory.create_llm", lambda **k: llm)

    events = [e async for e in run_graph_streaming_native(
        "test.yaml", {}, timeout=1.0  # 1s total
    )]

    errors = [e for e in events if isinstance(e, StreamEvent) and e.type == "error"]
    assert len(errors) == 1
    assert errors[0].error_type == "TimeoutError"


@pytest.mark.asyncio
async def test_streaming_concurrent_session_race(redis_checkpointer):
    """Two concurrent streams to same thread_id: one succeeds, one fails cleanly."""
    config = {"configurable": {"thread_id": "race-test"}}

    async def stream_session(message: str):
        return [e async for e in run_graph_streaming_native(
            "interview.yaml", {"input": message}, config
        )]

    # Launch concurrent streams
    results = await asyncio.gather(
        stream_session("first"),
        stream_session("second"),
        return_exceptions=True,
    )

    # Expect: one succeeds (list of events), one fails with error event or exception
    # The key invariant: no state corruption, no interleaved tokens
    successes = [r for r in results if isinstance(r, list)]
    assert len(successes) >= 1, "At least one stream should complete"

    # If both completed, check neither has corrupted data
    for result in successes:
        errors = [e for e in result if isinstance(e, StreamEvent) and e.type == "error"]
        # Session race should surface as error event, not silent corruption
        if errors:
            assert "locked" in errors[0].error.lower() or "conflict" in errors[0].error.lower()


@pytest.mark.asyncio
async def test_streaming_rate_limit_error(chaos_llm_factory, monkeypatch):
    """Rate limit error surfaces as retriable error event."""
    llm = chaos_llm_factory(rate_limit_after=2)
    monkeypatch.setattr("yamlgraph.utils.llm_factory.create_llm", lambda **k: llm)

    events = [e async for e in run_graph_streaming_native("test.yaml", {})]

    errors = [e for e in events if isinstance(e, StreamEvent) and e.type == "error"]
    assert len(errors) == 1
    assert "429" in errors[0].error or "RateLimit" in errors[0].error_type


@pytest.mark.asyncio
async def test_streaming_empty_chunks_no_busywait(chaos_llm_factory, monkeypatch):
    """Empty chunks are filtered without busy-wait or yield."""
    llm = chaos_llm_factory(empty_chunk_probability=0.5)
    monkeypatch.setattr("yamlgraph.utils.llm_factory.create_llm", lambda **k: llm)

    events = [e async for e in run_graph_streaming_native("test.yaml", {})]

    tokens = [e for e in events if isinstance(e, str)]
    # Should get some tokens (not all filtered as empty)
    assert len(tokens) >= 1
    # No token should be empty string
    assert all(t.strip() for t in tokens)
```

### Phase 4: Integration with openai_proxy

Update the SSE formatter to handle `StreamEvent`:

```python
async def stream_response():
    async for item in run_graph_streaming_native(graph_path, initial_state, config):
        if isinstance(item, str):
            yield f"data: {format_token_chunk(item)}\n\n"
        elif isinstance(item, StreamEvent):
            if item.type == "error":
                # OpenAI format: finish_reason: "error" with error details
                yield f"data: {format_error_chunk(item)}\n\n"
            elif item.type == "interrupt":
                # Custom: finish_reason: "interrupted"
                yield f"data: {format_interrupt_chunk(item)}\n\n"
    yield "data: [DONE]\n\n"
```

## Acceptance Criteria

- [ ] `run_graph_streaming_native` yields `StreamEvent(type="error")` on exceptions
- [ ] `StreamEvent(type="interrupt")` yielded when graph pauses (not just ends)
- [ ] `timeout` parameter enforces total stream duration
- [ ] `token_timeout` parameter detects stalled LLM
- [ ] Chaos LLM fixture in `conftest.py` for controlled failures
- [ ] Test: mid-stream exception yields partial tokens + error event
- [ ] Test: timeout exceeded yields timeout error
- [ ] Test: empty chunks don't cause busy-wait
- [ ] Test: rate limit error surfaces with retriable signal
- [ ] openai_proxy updated to format error/interrupt events
- [ ] Documentation in `reference/streaming.md`

## Alternatives Considered

1. **Consumer-side timeout via `asyncio.timeout()`** — Works but doesn't give clean error event; raises exception to caller.

2. **Separate error channel (websocket pattern)** — Overcomplicated for SSE; single-channel with tagged events is simpler.

3. **Retry inside the generator** — Violates separation of concerns; the consumer decides retry policy, not the streaming primitive.

4. **Session locking via Redis** — Could prevent concurrent races but adds latency; better to detect and error than to block.

## Related

- `yamlgraph/executor_async.py` L300-392 — current streaming implementation
- `examples/openai_proxy/api/app.py` L115-155 — SSE consumer
- FR-057, FR-058, FR-059, FR-060 — content bugs this builds on
- Diary entry "The Next Four Bugs" — predictive analysis this implements
- `reference/streaming.md` — needs update for error events

## Implementation Notes

**Phase ordering:**
1. Phase 1 (error propagation) is foundational — all other phases depend on it
2. Phase 3 (chaos fixtures) enables testing Phases 1, 2, and 4
3. Phase 2 (timeouts) and Phase 4 (proxy integration) can parallelize

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
