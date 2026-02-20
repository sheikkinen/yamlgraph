"""Tests for FR-062: Streaming error propagation and chaos testing.

RED phase: these tests define the streaming contract for error/interrupt/timeout
handling. All should FAIL until executor_async.py is updated.
"""

import pytest
from pydantic import ValidationError

from yamlgraph.models.streaming import StreamEvent

CHAOS_GRAPH = "tests/fixtures/chaos_graph.yaml"


@pytest.mark.asyncio
@pytest.mark.req("REQ-YG-077")
async def test_stream_event_model():
    """StreamEvent is a Pydantic BaseModel with correct fields."""
    evt = StreamEvent(type="error", error="test", error_type="RuntimeError")
    assert evt.type == "error"
    assert evt.error == "test"
    assert evt.error_type == "RuntimeError"
    assert evt.payload is None

    # Model validation works
    evt2 = StreamEvent(type="interrupt", payload={"question": "name?"})
    assert evt2.type == "interrupt"
    assert evt2.error is None

    # Invalid type rejected
    with pytest.raises(ValidationError):
        StreamEvent(type="invalid")


@pytest.mark.asyncio
@pytest.mark.req("REQ-YG-077")
async def test_streaming_handles_exception(monkeypatch):
    """Exception during streaming yields error event, not silent death."""
    from yamlgraph.executor_async import run_graph_streaming_native

    monkeypatch.setenv("CHAOS_MODE", "fail")

    events = []
    async for item in run_graph_streaming_native(CHAOS_GRAPH, {}):
        events.append(item)

    errors = [e for e in events if isinstance(e, StreamEvent) and e.type == "error"]
    assert len(errors) == 1, f"Expected 1 error event, got {len(errors)}: {events}"
    assert "Simulated LLM failure" in errors[0].error
    assert errors[0].error_type == "RuntimeError"


@pytest.mark.asyncio
@pytest.mark.req("REQ-YG-077")
async def test_streaming_rate_limit_error(monkeypatch):
    """Rate limit error surfaces with identifiable error type."""
    from yamlgraph.executor_async import run_graph_streaming_native

    monkeypatch.setenv("CHAOS_MODE", "rate_limit")

    events = []
    async for item in run_graph_streaming_native(CHAOS_GRAPH, {}):
        events.append(item)

    errors = [e for e in events if isinstance(e, StreamEvent) and e.type == "error"]
    assert len(errors) == 1
    assert "SimulatedRateLimitError" in errors[0].error_type


@pytest.mark.asyncio
@pytest.mark.req("REQ-YG-077")
async def test_streaming_yield_events_false_raises(monkeypatch):
    """With yield_events=False, exceptions propagate to caller."""
    from yamlgraph.executor_async import run_graph_streaming_native

    monkeypatch.setenv("CHAOS_MODE", "fail")

    with pytest.raises(RuntimeError, match="Simulated"):
        async for _ in run_graph_streaming_native(CHAOS_GRAPH, {}, yield_events=False):
            pass


@pytest.mark.asyncio
@pytest.mark.req("REQ-YG-077")
async def test_streaming_timeout(monkeypatch):
    """Stream exceeding total timeout yields timeout error."""
    from yamlgraph.executor_async import run_graph_streaming_native

    monkeypatch.setenv("CHAOS_MODE", "slow")
    monkeypatch.setenv("CHAOS_DELAY", "5")

    events = []
    async for item in run_graph_streaming_native(CHAOS_GRAPH, {}, timeout=0.5):
        events.append(item)

    errors = [e for e in events if isinstance(e, StreamEvent) and e.type == "error"]
    assert len(errors) == 1
    assert errors[0].error_type == "TimeoutError"
    assert "0.5" in errors[0].error


@pytest.mark.asyncio
@pytest.mark.req("REQ-YG-077")
async def test_streaming_timeout_none_means_no_limit(monkeypatch):
    """timeout=None means no timeout — normal execution completes."""
    from yamlgraph.executor_async import run_graph_streaming_native

    monkeypatch.setenv("CHAOS_MODE", "normal")

    events = []
    async for item in run_graph_streaming_native(CHAOS_GRAPH, {}, timeout=None):
        events.append(item)

    errors = [e for e in events if isinstance(e, StreamEvent) and e.type == "error"]
    assert len(errors) == 0


@pytest.mark.asyncio
@pytest.mark.req("REQ-YG-077")
async def test_streaming_no_config_skips_interrupt_check(monkeypatch):
    """When no thread_id configured, interrupt detection is skipped (no crash)."""
    from yamlgraph.executor_async import run_graph_streaming_native

    monkeypatch.setenv("CHAOS_MODE", "normal")

    # No config, no thread_id — should not crash in finally block
    events = []
    async for item in run_graph_streaming_native(CHAOS_GRAPH, {}):
        events.append(item)

    errors = [e for e in events if isinstance(e, StreamEvent) and e.type == "error"]
    # No spurious errors from interrupt detection
    assert not any("aget_state" in (e.error or "") for e in errors)


@pytest.mark.asyncio
@pytest.mark.req("REQ-YG-077")
async def test_streaming_normal_yields_no_events(monkeypatch):
    """Normal execution with no errors yields no StreamEvents."""
    from yamlgraph.executor_async import run_graph_streaming_native

    monkeypatch.setenv("CHAOS_MODE", "normal")

    events = []
    async for item in run_graph_streaming_native(CHAOS_GRAPH, {}):
        events.append(item)

    stream_events = [e for e in events if isinstance(e, StreamEvent)]
    assert len(stream_events) == 0
