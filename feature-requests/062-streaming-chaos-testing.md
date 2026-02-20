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

Wrap the streaming generator in `try/except` with explicit error events:

```python
async def run_graph_streaming_native(...) -> AsyncIterator[str | StreamEvent]:
    """Yields str tokens OR StreamEvent on control signals."""
    try:
        async for event in app.astream(...):
            # ... existing filter logic ...
            yield token
    except Exception as e:
        yield StreamEvent(type="error", error=str(e), error_type=type(e).__name__)
    finally:
        # Check for interrupt
        state = await app.aget_state(config)
        if state and state.next:
            yield StreamEvent(type="interrupt", payload=_get_interrupt_payload(state))
```

```python
@dataclass
class StreamEvent:
    type: Literal["error", "interrupt", "done"]
    error: str | None = None
    error_type: str | None = None
    payload: Any = None
```

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

```python
async def run_graph_streaming_native(
    ...,
    timeout: float | None = None,  # Total stream timeout in seconds
    token_timeout: float | None = None,  # Max gap between tokens
) -> AsyncIterator[str | StreamEvent]:

    start = time.monotonic()
    last_token = start

    async for event in app.astream(...):
        now = time.monotonic()
        if timeout and (now - start) > timeout:
            yield StreamEvent(type="error", error="Stream timeout exceeded", error_type="TimeoutError")
            return
        if token_timeout and (now - last_token) > token_timeout:
            yield StreamEvent(type="error", error="Token timeout exceeded", error_type="TokenTimeoutError")
            return
        # ... yield token ...
        last_token = now
```

### Phase 3: Chaos Testing Infrastructure

Add mock LLM fixtures that simulate failure modes:

```python
# tests/conftest.py

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
                        raise RateLimitError("429 Too Many Requests")
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
    """Two concurrent streams to same thread_id don't corrupt state."""
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

    # At least one should fail cleanly (not corrupt)
    # Exact behavior TBD — maybe second gets "session locked" error?
    assert not any(isinstance(r, Exception) for r in results), "Should handle race gracefully"


@pytest.mark.asyncio
async def test_streaming_rate_limit_retry(chaos_llm_factory, monkeypatch):
    """Rate limit error surfaces as retriable error event."""
    llm = chaos_llm_factory(rate_limit_after=2)
    monkeypatch.setattr("yamlgraph.utils.llm_factory.create_llm", lambda **k: llm)

    events = [e async for e in run_graph_streaming_native("test.yaml", {})]

    errors = [e for e in events if isinstance(e, StreamEvent) and e.type == "error"]
    assert len(errors) == 1
    assert "429" in errors[0].error or "RateLimit" in errors[0].error_type
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

**Breaking change consideration:**
Return type changes from `AsyncIterator[str]` to `AsyncIterator[str | StreamEvent]`. Existing consumers using `async for token in ...` will receive unexpected types. Options:
- **Option A:** New function `run_graph_streaming_native_v2()` — clean but duplicates
- **Option B:** Add `raw=True` parameter that preserves old behavior
- **Option C:** Require explicit opt-in via `yield_events=True` (default False)

Recommend **Option C** for backward compatibility:
```python
async def run_graph_streaming_native(
    ...,
    yield_events: bool = False,  # If True, yields StreamEvent on error/interrupt
) -> AsyncIterator[str] | AsyncIterator[str | StreamEvent]:
```

Existing code unchanged. New consumers opt into events.
