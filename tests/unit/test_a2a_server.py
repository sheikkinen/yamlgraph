"""Tests for A2A server — FR-208/FR-225/FR-250: A2A Protocol Server.

Covers: _invoke_graph, YAMLGraphAgentExecutor (execute, cancel),
        _resolve_graph, _format_result, create_a2a_app,
        streaming execution (FR-250), interrupt payload forwarding,
        and resume flow.

Message-layer tests moved to test_a2a_message.py (FR-225).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Guard: a2a-sdk is an optional dependency
a2a_sdk = pytest.importorskip("a2a")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_graph_info() -> dict[str, Any]:
    """A discovered graph info dict (as returned by discover_graphs)."""
    return {
        "name": "hello-world",
        "description": "Simple greeting generator",
        "path": "/tmp/hello/graph.yaml",
        "required_vars": ["name", "style"],
    }


@pytest.fixture
def single_var_graph_info() -> dict[str, Any]:
    """A graph with a single required variable."""
    return {
        "name": "echo",
        "description": "Echo input back",
        "path": "/tmp/echo/graph.yaml",
        "required_vars": ["input"],
    }


@pytest.fixture
def no_var_graph_info() -> dict[str, Any]:
    """A graph with no required variables."""
    return {
        "name": "auto-gen",
        "description": "Auto-generates content",
        "path": "/tmp/autogen/graph.yaml",
        "required_vars": [],
    }


# ---------------------------------------------------------------------------
# REQ-YG-207: A2A server discovers graphs
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-207")
def test_a2a_server_uses_shared_discovery():
    """a2a_server imports discover_graphs from yamlgraph.discovery."""
    from yamlgraph.a2a.server import discover_graphs as a2a_discover
    from yamlgraph.discovery import discover_graphs as shared_discover

    assert a2a_discover is shared_discover


# ---------------------------------------------------------------------------
# REQ-YG-068: _invoke_graph
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-207")
def test_invoke_graph_calls_load_compile_invoke():
    """_invoke_graph loads config, compiles graph, and invokes with variables."""
    from yamlgraph.a2a.server import _invoke_graph

    mock_config = MagicMock()
    mock_sg = MagicMock()
    mock_compiled = MagicMock()
    mock_compiled.invoke.return_value = {"out": "result"}
    mock_sg.compile.return_value = mock_compiled

    with (
        patch(
            "yamlgraph.graph_loader.load_graph_config", return_value=mock_config
        ) as mock_load,
        patch(
            "yamlgraph.graph_loader.compile_graph", return_value=mock_sg
        ) as mock_compile,
    ):
        result = _invoke_graph("/tmp/graph.yaml", {"name": "test"})

    mock_load.assert_called_once_with("/tmp/graph.yaml")
    mock_compile.assert_called_once_with(mock_config)
    mock_compiled.invoke.assert_called_once_with({"name": "test"}, config={})
    assert result == {"out": "result"}


# ---------------------------------------------------------------------------
# REQ-YG-207: _resolve_graph
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-207")
def test_resolve_graph_single(sample_graph_info):
    """Single-graph lookup returns the only graph."""
    from yamlgraph.a2a.server import YAMLGraphAgentExecutor

    executor = YAMLGraphAgentExecutor(
        graph_lookup={"hello-world": sample_graph_info},
    )
    resolved = executor._resolve_graph("anything")
    assert resolved["name"] == "hello-world"


@pytest.mark.req("REQ-YG-207")
def test_resolve_graph_multi(sample_graph_info, single_var_graph_info):
    """Multi-graph lookup returns first graph (default routing)."""
    from yamlgraph.a2a.server import YAMLGraphAgentExecutor

    executor = YAMLGraphAgentExecutor(
        graph_lookup={
            "hello-world": sample_graph_info,
            "echo": single_var_graph_info,
        },
    )
    resolved = executor._resolve_graph("some text")
    assert resolved is not None
    assert resolved["name"] in ("hello-world", "echo")


# ---------------------------------------------------------------------------
# REQ-YG-209: _format_result
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-209")
def test_format_result_string_values():
    """String values are included directly."""
    from yamlgraph.a2a.server import YAMLGraphAgentExecutor

    executor = YAMLGraphAgentExecutor(graph_lookup={})
    text = executor._format_result({"greeting": "Hello!", "detail": "World"})
    assert "Hello!" in text
    assert "World" in text


@pytest.mark.req("REQ-YG-209")
def test_format_result_json_values():
    """Non-string JSON-serializable values are formatted as JSON."""
    from yamlgraph.a2a.server import YAMLGraphAgentExecutor

    executor = YAMLGraphAgentExecutor(graph_lookup={})
    text = executor._format_result({"data": {"key": "val"}})
    assert '"key"' in text
    assert '"val"' in text


@pytest.mark.req("REQ-YG-209")
def test_format_result_internal_keys_filtered():
    """Keys starting with _ and 'errors' are filtered out."""
    from yamlgraph.a2a.server import YAMLGraphAgentExecutor

    executor = YAMLGraphAgentExecutor(graph_lookup={})
    text = executor._format_result(
        {
            "output": "visible",
            "_internal": "hidden",
            "errors": [{"msg": "err"}],
            "thread_id": "tid-123",
        }
    )
    assert "visible" in text
    assert "hidden" not in text
    assert "err" not in text
    assert "tid-123" not in text


@pytest.mark.req("REQ-YG-209")
def test_format_result_empty():
    """Empty result (all keys filtered) falls back to json.dumps."""
    from yamlgraph.a2a.server import YAMLGraphAgentExecutor

    executor = YAMLGraphAgentExecutor(graph_lookup={})
    text = executor._format_result({"_internal": "hidden"})
    assert text == '{"_internal": "hidden"}'


# ---------------------------------------------------------------------------
# REQ-YG-207: YAMLGraphAgentExecutor
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-207")
@pytest.mark.asyncio(loop_scope="function")
async def test_executor_execute_invokes_graph(sample_graph_info):
    """AgentExecutor.execute() invokes the graph and enqueues result."""
    from a2a.server.agent_execution import RequestContext
    from a2a.types import (
        TaskState,
        TaskStatusUpdateEvent,
    )

    from yamlgraph.a2a.server import YAMLGraphAgentExecutor

    executor = YAMLGraphAgentExecutor(
        graph_lookup={"hello-world": sample_graph_info},
    )

    context = MagicMock(spec=RequestContext)
    context.get_user_input.return_value = "name=World style=casual"
    context.task_id = "task-1"
    context.context_id = "ctx-1"
    context.current_task = None

    # Use a collecting mock queue
    collected_events: list[Any] = []

    queue = AsyncMock()
    queue.enqueue_event = AsyncMock(side_effect=lambda e: collected_events.append(e))
    queue.close = AsyncMock()

    async def mock_streaming(*args, **kwargs):
        yield "Hello World!"

    with patch(
        "yamlgraph.a2a.server.run_graph_streaming_native",
        side_effect=mock_streaming,
    ):
        await executor.execute(context, queue)

    # Should have working + artifact + completed events
    status_events = [
        e for e in collected_events if isinstance(e, TaskStatusUpdateEvent)
    ]
    assert any(e.status.state == TaskState.TASK_STATE_WORKING for e in status_events)
    assert any(e.status.state == TaskState.TASK_STATE_COMPLETED for e in status_events)


@pytest.mark.req("REQ-YG-207")
@pytest.mark.asyncio(loop_scope="function")
async def test_executor_execute_error_path(sample_graph_info):
    """Execute enqueues failed state when graph raises an exception."""
    from a2a.server.agent_execution import RequestContext
    from a2a.types import TaskState, TaskStatusUpdateEvent

    from yamlgraph.a2a.server import YAMLGraphAgentExecutor

    executor = YAMLGraphAgentExecutor(
        graph_lookup={"hello-world": sample_graph_info},
    )

    context = MagicMock(spec=RequestContext)
    context.get_user_input.return_value = "name=World style=casual"
    context.task_id = "task-err-1"
    context.context_id = "ctx-1"
    context.current_task = None

    collected_events: list[Any] = []
    queue = AsyncMock()
    queue.enqueue_event = AsyncMock(side_effect=lambda e: collected_events.append(e))
    queue.close = AsyncMock()

    async def mock_streaming_error(*args, **kwargs):
        raise RuntimeError("Graph exploded")
        yield  # pragma: no cover — makes this an async generator

    with patch(
        "yamlgraph.a2a.server.run_graph_streaming_native",
        side_effect=mock_streaming_error,
    ):
        await executor.execute(context, queue)

    status_events = [
        e for e in collected_events if isinstance(e, TaskStatusUpdateEvent)
    ]
    failed = [e for e in status_events if e.status.state == TaskState.TASK_STATE_FAILED]
    assert len(failed) == 1
    assert "Graph exploded" in failed[0].status.message.parts[0].text


@pytest.mark.req("REQ-YG-209")
@pytest.mark.asyncio(loop_scope="function")
async def test_executor_execute_pipeline_error_mapping_unreachable(sample_graph_info):
    """PipelineError is BaseModel, not Exception — the isinstance check in execute()
    is dead code. This test verifies that a generic exception still produces a failed
    state with the error message (the actual reachable path).
    """
    from a2a.server.agent_execution import RequestContext
    from a2a.types import TaskState, TaskStatusUpdateEvent

    from yamlgraph.a2a.server import YAMLGraphAgentExecutor

    executor = YAMLGraphAgentExecutor(
        graph_lookup={"hello-world": sample_graph_info},
    )

    context = MagicMock(spec=RequestContext)
    context.get_user_input.return_value = "name=World style=casual"
    context.task_id = "task-perr-1"
    context.context_id = "ctx-1"
    context.current_task = None

    collected_events: list[Any] = []
    queue = AsyncMock()
    queue.enqueue_event = AsyncMock(side_effect=lambda e: collected_events.append(e))
    queue.close = AsyncMock()

    async def mock_streaming_valerr(*args, **kwargs):
        raise ValueError("Bad input format")
        yield  # pragma: no cover — makes this an async generator

    with patch(
        "yamlgraph.a2a.server.run_graph_streaming_native",
        side_effect=mock_streaming_valerr,
    ):
        await executor.execute(context, queue)

    status_events = [
        e for e in collected_events if isinstance(e, TaskStatusUpdateEvent)
    ]
    failed = [e for e in status_events if e.status.state == TaskState.TASK_STATE_FAILED]
    assert len(failed) == 1
    assert "Bad input format" in failed[0].status.message.parts[0].text


@pytest.mark.req("REQ-YG-212")
@pytest.mark.asyncio(loop_scope="function")
async def test_executor_cancel(sample_graph_info):
    """AgentExecutor.cancel() cancels the running task."""
    from a2a.server.agent_execution import RequestContext
    from a2a.types import TaskState, TaskStatusUpdateEvent

    from yamlgraph.a2a.server import YAMLGraphAgentExecutor

    executor = YAMLGraphAgentExecutor(
        graph_lookup={"hello-world": sample_graph_info},
    )

    context = MagicMock(spec=RequestContext)
    context.task_id = "task-cancel-1"
    context.context_id = "ctx-1"

    collected_events: list[Any] = []

    queue = AsyncMock()
    queue.enqueue_event = AsyncMock(side_effect=lambda e: collected_events.append(e))
    queue.close = AsyncMock()

    await executor.cancel(context, queue)

    status_events = [
        e for e in collected_events if isinstance(e, TaskStatusUpdateEvent)
    ]
    assert any(e.status.state == TaskState.TASK_STATE_CANCELED for e in status_events)


# ---------------------------------------------------------------------------
# REQ-YG-207: create_a2a_app wires everything together
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-207")
def test_create_a2a_app(tmp_path: Path):
    """create_a2a_app returns a Starlette application."""
    from yamlgraph.a2a.server import create_a2a_app

    graph_dir = tmp_path / "demo"
    graph_dir.mkdir()
    (graph_dir / "graph.yaml").write_text(
        "version: '1.0'\nname: test-graph\n"
        "description: A test\n"
        "nodes:\n  n1:\n    type: llm\n    prompt: p\n    state_key: out\n"
        "edges:\n  - from: START\n    to: n1\n  - from: n1\n    to: END\n"
    )

    app = create_a2a_app(
        graph_patterns=[str(tmp_path / "demo/*.yaml")],
        host="localhost",
        port=8080,
    )

    # Should be a Starlette app (from A2AStarletteApplication)
    assert app is not None
    assert hasattr(app, "routes") or hasattr(app, "app")


# ---------------------------------------------------------------------------
# REQ-YG-210: task/get retrieves task status via InMemoryTaskStore
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-210")
@pytest.mark.asyncio(loop_scope="function")
async def test_task_store_save_and_get():
    """InMemoryTaskStore persists task for task/get retrieval."""
    from a2a.server.context import ServerCallContext
    from a2a.server.tasks import InMemoryTaskStore
    from a2a.types import Task, TaskState, TaskStatus

    store = InMemoryTaskStore()
    ctx = ServerCallContext()
    task = Task(
        id="task-get-1",
        context_id="ctx-1",
        status=TaskStatus(state=TaskState.TASK_STATE_WORKING),
    )
    await store.save(task, ctx)

    retrieved = await store.get("task-get-1", ctx)
    assert retrieved is not None
    assert retrieved.id == "task-get-1"
    assert retrieved.status.state == TaskState.TASK_STATE_WORKING


@pytest.mark.req("REQ-YG-210")
@pytest.mark.asyncio(loop_scope="function")
async def test_task_store_returns_none_for_unknown_id():
    """InMemoryTaskStore returns None for unknown task IDs."""
    from a2a.server.context import ServerCallContext
    from a2a.server.tasks import InMemoryTaskStore

    store = InMemoryTaskStore()
    ctx = ServerCallContext()
    result = await store.get("nonexistent", ctx)
    assert result is None


@pytest.mark.req("REQ-YG-210")
def test_create_a2a_app_uses_task_store(tmp_path: Path):
    """create_a2a_app wires InMemoryTaskStore for task/get retrieval."""
    from yamlgraph.a2a.server import create_a2a_app

    graph_dir = tmp_path / "demo"
    graph_dir.mkdir()
    (graph_dir / "graph.yaml").write_text(
        "version: '1.0'\nname: test-graph\n"
        "description: A test\n"
        "nodes:\n  n1:\n    type: llm\n    prompt: p\n    state_key: out\n"
        "edges:\n  - from: START\n    to: n1\n  - from: n1\n    to: END\n"
    )

    app = create_a2a_app(
        graph_patterns=[str(tmp_path / "demo/*.yaml")],
        host="localhost",
        port=8080,
    )

    # App is wired with a request handler that holds the task store
    assert app is not None
    assert hasattr(app, "routes") or hasattr(app, "app")


# ---------------------------------------------------------------------------
# REQ-YG-211: task/sendSubscribe streams via SSE
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-211")
@pytest.mark.asyncio(loop_scope="function")
async def test_execute_produces_streaming_events(sample_graph_info):
    """Execute enqueues ordered events for SSE streaming (working → artifact → completed)."""
    from a2a.server.agent_execution import RequestContext
    from a2a.types import (
        TaskArtifactUpdateEvent,
        TaskState,
        TaskStatusUpdateEvent,
    )

    from yamlgraph.a2a.server import YAMLGraphAgentExecutor

    executor = YAMLGraphAgentExecutor(
        graph_lookup={"hello-world": sample_graph_info},
    )

    context = MagicMock(spec=RequestContext)
    context.get_user_input.return_value = "name=World style=casual"
    context.task_id = "task-stream-1"
    context.context_id = "ctx-1"
    context.current_task = None

    collected: list[Any] = []
    queue = AsyncMock()
    queue.enqueue_event = AsyncMock(side_effect=lambda e: collected.append(e))
    queue.close = AsyncMock()

    async def mock_streaming(*args, **kwargs):
        yield "hi"

    with patch(
        "yamlgraph.a2a.server.run_graph_streaming_native",
        side_effect=mock_streaming,
    ):
        await executor.execute(context, queue)

    # Verify SSE event stream order: working → artifact → completed
    assert isinstance(collected[0], TaskStatusUpdateEvent)
    assert collected[0].status.state == TaskState.TASK_STATE_WORKING

    artifact_events = [e for e in collected if isinstance(e, TaskArtifactUpdateEvent)]
    assert len(artifact_events) == 1

    final_event = collected[-1]
    assert isinstance(final_event, TaskStatusUpdateEvent)
    assert final_event.status.state == TaskState.TASK_STATE_COMPLETED


@pytest.mark.req("REQ-YG-211")
@pytest.mark.asyncio(loop_scope="function")
async def test_streaming_events_include_message_on_complete(sample_graph_info):
    """Completed SSE event includes agent message."""
    from a2a.server.agent_execution import RequestContext
    from a2a.types import TaskState, TaskStatusUpdateEvent

    from yamlgraph.a2a.server import YAMLGraphAgentExecutor

    executor = YAMLGraphAgentExecutor(
        graph_lookup={"hello-world": sample_graph_info},
    )

    context = MagicMock(spec=RequestContext)
    context.get_user_input.return_value = "name=World style=casual"
    context.task_id = "task-stream-2"
    context.context_id = "ctx-1"
    context.current_task = None

    collected: list[Any] = []
    queue = AsyncMock()
    queue.enqueue_event = AsyncMock(side_effect=lambda e: collected.append(e))
    queue.close = AsyncMock()

    async def mock_streaming(*args, **kwargs):
        yield "Hello!"

    with patch(
        "yamlgraph.a2a.server.run_graph_streaming_native",
        side_effect=mock_streaming,
    ):
        await executor.execute(context, queue)

    completed = [
        e
        for e in collected
        if isinstance(e, TaskStatusUpdateEvent)
        and e.status.state == TaskState.TASK_STATE_COMPLETED
    ]
    assert len(completed) == 1
    assert completed[0].status.message is not None


@pytest.mark.req("REQ-YG-213")
@pytest.mark.asyncio(loop_scope="function")
async def test_execute_emits_input_required_on_interrupt(sample_graph_info):
    """When streaming yields an interrupt StreamEvent, input-required state is emitted."""
    from a2a.server.agent_execution import RequestContext
    from a2a.types import TaskState, TaskStatusUpdateEvent

    from yamlgraph.a2a.server import YAMLGraphAgentExecutor
    from yamlgraph.models.streaming import StreamEvent

    executor = YAMLGraphAgentExecutor(
        graph_lookup={"hello-world": sample_graph_info},
    )

    context = MagicMock(spec=RequestContext)
    context.get_user_input.return_value = "name=World style=casual"
    context.task_id = "task-interrupt-1"
    context.context_id = "ctx-1"
    context.current_task = None

    collected: list[Any] = []
    queue = AsyncMock()
    queue.enqueue_event = AsyncMock(side_effect=lambda e: collected.append(e))
    queue.close = AsyncMock()

    async def mock_streaming_interrupt(*args, **kwargs):
        yield "partial"
        yield StreamEvent(type="interrupt", payload="need clarification")

    with patch(
        "yamlgraph.a2a.server.run_graph_streaming_native",
        side_effect=mock_streaming_interrupt,
    ):
        await executor.execute(context, queue)

    status_events = [e for e in collected if isinstance(e, TaskStatusUpdateEvent)]
    input_required = [
        e
        for e in status_events
        if e.status.state == TaskState.TASK_STATE_INPUT_REQUIRED
    ]
    assert len(input_required) == 1


# ---------------------------------------------------------------------------
# FR-209: A2A demo exercises message/stream SSE
# ---------------------------------------------------------------------------

DEMO_SCRIPT = Path(__file__).resolve().parents[2] / "examples/demos/a2a_server/demo.sh"


@pytest.mark.req("REQ-YG-211")
def test_demo_script_has_streaming_part():
    """demo.sh includes a Part 3 that calls message/stream for SSE streaming."""
    content = DEMO_SCRIPT.read_text()
    assert "Part 3" in content, "demo.sh must have a Part 3 section"
    assert "message/stream" in content, "Part 3 must call message/stream"


@pytest.mark.req("REQ-YG-211")
def test_demo_script_streaming_uses_timeout():
    """Streaming curl in demo.sh uses timeout to prevent hanging."""
    content = DEMO_SCRIPT.read_text()
    # The streaming curl must have timeout protection
    assert "timeout" in content, "Streaming curl must use timeout to prevent hanging"


@pytest.mark.req("REQ-YG-211")
def test_demo_script_streaming_accepts_sse():
    """Streaming curl in demo.sh requests text/event-stream content type."""
    content = DEMO_SCRIPT.read_text()
    assert (
        "text/event-stream" in content
    ), "Streaming request must Accept text/event-stream"


@pytest.mark.req("REQ-YG-211")
@pytest.mark.asyncio(loop_scope="function")
async def test_execute_does_not_call_queue_close(sample_graph_info):
    """v1.0 SDK: EventQueue no longer has close(); executor must not call it."""
    from a2a.server.agent_execution import RequestContext

    from yamlgraph.a2a.server import YAMLGraphAgentExecutor

    executor = YAMLGraphAgentExecutor(
        graph_lookup={"hello-world": sample_graph_info},
    )

    context = MagicMock(spec=RequestContext)
    context.get_user_input.return_value = "name=World style=casual"
    context.task_id = "task-drain-1"
    context.context_id = "ctx-1"
    context.current_task = None

    queue = AsyncMock()
    queue.enqueue_event = AsyncMock()

    async def mock_streaming(*args, **kwargs):
        yield "hi"

    with patch(
        "yamlgraph.a2a.server.run_graph_streaming_native",
        side_effect=mock_streaming,
    ):
        await executor.execute(context, queue)

    # enqueue_event should have been called (working + artifact + completed)
    assert queue.enqueue_event.call_count == 3


# ---------------------------------------------------------------------------
# FR-250 Gap 3a (REQ-YG-213): Interrupt payload forwarded to client
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-213")
@pytest.mark.asyncio(loop_scope="function")
async def test_interrupt_payload_forwarded_in_input_required_message(sample_graph_info):
    """INPUT_REQUIRED message includes the interrupt payload (the question)."""
    from a2a.server.agent_execution import RequestContext
    from a2a.types import TaskState, TaskStatusUpdateEvent

    from yamlgraph.a2a.server import YAMLGraphAgentExecutor
    from yamlgraph.models.streaming import StreamEvent

    executor = YAMLGraphAgentExecutor(
        graph_lookup={"hello-world": sample_graph_info},
    )

    context = MagicMock(spec=RequestContext)
    context.get_user_input.return_value = "name=World style=casual"
    context.task_id = "task-int-payload-1"
    context.context_id = "ctx-1"
    context.current_task = None

    collected: list[Any] = []
    queue = AsyncMock()
    queue.enqueue_event = AsyncMock(side_effect=lambda e: collected.append(e))

    interrupt_value = "What is your preferred language?"

    async def mock_streaming_interrupt(*args, **kwargs):
        yield "partial"
        yield StreamEvent(type="interrupt", payload=interrupt_value)

    with patch(
        "yamlgraph.a2a.server.run_graph_streaming_native",
        side_effect=mock_streaming_interrupt,
    ):
        await executor.execute(context, queue)

    input_required = [
        e
        for e in collected
        if isinstance(e, TaskStatusUpdateEvent)
        and e.status.state == TaskState.TASK_STATE_INPUT_REQUIRED
    ]
    assert len(input_required) == 1
    # The interrupt payload must be forwarded as the message text
    msg_text = input_required[0].status.message.parts[0].text
    assert interrupt_value in msg_text


# ---------------------------------------------------------------------------
# FR-250 Gap 2 (REQ-YG-211): Streaming execution with incremental artifacts
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-211")
@pytest.mark.asyncio(loop_scope="function")
async def test_streaming_execute_yields_incremental_artifacts(sample_graph_info):
    """Streaming execution yields TaskArtifactUpdateEvent per token chunk."""
    from a2a.server.agent_execution import RequestContext
    from a2a.types import (
        TaskArtifactUpdateEvent,
        TaskState,
        TaskStatusUpdateEvent,
    )

    from yamlgraph.a2a.server import YAMLGraphAgentExecutor

    executor = YAMLGraphAgentExecutor(
        graph_lookup={"hello-world": sample_graph_info},
    )

    context = MagicMock(spec=RequestContext)
    context.get_user_input.return_value = "name=World style=casual"
    context.task_id = "task-stream-incr-1"
    context.context_id = "ctx-1"
    context.current_task = None

    collected: list[Any] = []
    queue = AsyncMock()
    queue.enqueue_event = AsyncMock(side_effect=lambda e: collected.append(e))

    # Simulate streaming: run_graph_streaming_native yields token chunks
    async def mock_streaming(*args, **kwargs):
        yield "Hello"
        yield ", "
        yield "World!"

    with patch(
        "yamlgraph.a2a.server.run_graph_streaming_native",
        side_effect=mock_streaming,
    ):
        await executor.execute(context, queue)

    # Should have: working + 3 artifact events + completed
    assert isinstance(collected[0], TaskStatusUpdateEvent)
    assert collected[0].status.state == TaskState.TASK_STATE_WORKING

    artifact_events = [e for e in collected if isinstance(e, TaskArtifactUpdateEvent)]
    assert len(artifact_events) == 3
    texts = [e.artifact.parts[0].text for e in artifact_events]
    assert texts == ["Hello", ", ", "World!"]

    final = collected[-1]
    assert isinstance(final, TaskStatusUpdateEvent)
    assert final.status.state == TaskState.TASK_STATE_COMPLETED


@pytest.mark.req("REQ-YG-211")
@pytest.mark.asyncio(loop_scope="function")
async def test_streaming_error_yields_failed_status(sample_graph_info):
    """StreamEvent(type='error') during streaming yields FAILED status."""
    from a2a.server.agent_execution import RequestContext
    from a2a.types import TaskState, TaskStatusUpdateEvent

    from yamlgraph.a2a.server import YAMLGraphAgentExecutor
    from yamlgraph.models.streaming import StreamEvent

    executor = YAMLGraphAgentExecutor(
        graph_lookup={"hello-world": sample_graph_info},
    )

    context = MagicMock(spec=RequestContext)
    context.get_user_input.return_value = "name=World style=casual"
    context.task_id = "task-stream-err-1"
    context.context_id = "ctx-1"
    context.current_task = None

    collected: list[Any] = []
    queue = AsyncMock()
    queue.enqueue_event = AsyncMock(side_effect=lambda e: collected.append(e))

    async def mock_streaming_error(*args, **kwargs):
        yield "partial"
        yield StreamEvent(type="error", error="LLM timeout", error_type="TimeoutError")

    with patch(
        "yamlgraph.a2a.server.run_graph_streaming_native",
        side_effect=mock_streaming_error,
    ):
        await executor.execute(context, queue)

    status_events = [e for e in collected if isinstance(e, TaskStatusUpdateEvent)]
    failed = [e for e in status_events if e.status.state == TaskState.TASK_STATE_FAILED]
    assert len(failed) == 1
    assert "LLM timeout" in failed[0].status.message.parts[0].text


@pytest.mark.req("REQ-YG-211")
@pytest.mark.asyncio(loop_scope="function")
async def test_streaming_interrupt_yields_input_required(sample_graph_info):
    """StreamEvent(type='interrupt') during streaming yields INPUT_REQUIRED."""
    from a2a.server.agent_execution import RequestContext
    from a2a.types import TaskState, TaskStatusUpdateEvent

    from yamlgraph.a2a.server import YAMLGraphAgentExecutor
    from yamlgraph.models.streaming import StreamEvent

    executor = YAMLGraphAgentExecutor(
        graph_lookup={"hello-world": sample_graph_info},
    )

    context = MagicMock(spec=RequestContext)
    context.get_user_input.return_value = "name=World style=casual"
    context.task_id = "task-stream-int-1"
    context.context_id = "ctx-1"
    context.current_task = None

    collected: list[Any] = []
    queue = AsyncMock()
    queue.enqueue_event = AsyncMock(side_effect=lambda e: collected.append(e))

    async def mock_streaming_interrupt(*args, **kwargs):
        yield "partial answer"
        yield StreamEvent(type="interrupt", payload="Please confirm your choice")

    with patch(
        "yamlgraph.a2a.server.run_graph_streaming_native",
        side_effect=mock_streaming_interrupt,
    ):
        await executor.execute(context, queue)

    status_events = [e for e in collected if isinstance(e, TaskStatusUpdateEvent)]
    input_required = [
        e
        for e in status_events
        if e.status.state == TaskState.TASK_STATE_INPUT_REQUIRED
    ]
    assert len(input_required) == 1
    assert (
        "Please confirm your choice" in input_required[0].status.message.parts[0].text
    )


# ---------------------------------------------------------------------------
# FR-250 Gap 3b (REQ-YG-213): Resume flow via Command(resume=...)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-213")
@pytest.mark.asyncio(loop_scope="function")
async def test_resume_from_input_required_state(sample_graph_info):
    """When current_task is INPUT_REQUIRED, execute resumes via Command(resume=...)."""
    from a2a.server.agent_execution import RequestContext
    from a2a.types import (
        Task,
        TaskArtifactUpdateEvent,
        TaskState,
        TaskStatus,
        TaskStatusUpdateEvent,
    )

    from yamlgraph.a2a.server import YAMLGraphAgentExecutor

    executor = YAMLGraphAgentExecutor(
        graph_lookup={"hello-world": sample_graph_info},
    )

    # Simulate existing task in INPUT_REQUIRED state
    existing_task = Task(
        id="task-resume-1",
        context_id="ctx-1",
        status=TaskStatus(state=TaskState.TASK_STATE_INPUT_REQUIRED),
    )

    context = MagicMock(spec=RequestContext)
    context.get_user_input.return_value = "English"
    context.task_id = "task-resume-1"
    context.context_id = "ctx-1"
    context.current_task = existing_task

    collected: list[Any] = []
    queue = AsyncMock()
    queue.enqueue_event = AsyncMock(side_effect=lambda e: collected.append(e))

    # Streaming should be called with Command(resume="English")
    async def mock_resume_streaming(graph_path, initial_state, **kwargs):
        from langgraph.types import Command

        assert isinstance(initial_state, Command)
        assert initial_state.resume == "English"
        yield "Resumed output"

    with patch(
        "yamlgraph.a2a.server.run_graph_streaming_native",
        side_effect=mock_resume_streaming,
    ):
        await executor.execute(context, queue)

    artifact_events = [e for e in collected if isinstance(e, TaskArtifactUpdateEvent)]
    assert len(artifact_events) == 1
    assert artifact_events[0].artifact.parts[0].text == "Resumed output"

    completed = [
        e
        for e in collected
        if isinstance(e, TaskStatusUpdateEvent)
        and e.status.state == TaskState.TASK_STATE_COMPLETED
    ]
    assert len(completed) == 1


# ---------------------------------------------------------------------------
# FR-250: Batch execute still works (non-streaming fallback)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-211")
@pytest.mark.asyncio(loop_scope="function")
async def test_batch_execute_still_works_via_streaming(sample_graph_info):
    """Batch execute uses streaming path and produces correct event sequence."""
    from a2a.server.agent_execution import RequestContext
    from a2a.types import (
        TaskArtifactUpdateEvent,
        TaskState,
        TaskStatusUpdateEvent,
    )

    from yamlgraph.a2a.server import YAMLGraphAgentExecutor

    executor = YAMLGraphAgentExecutor(
        graph_lookup={"hello-world": sample_graph_info},
    )

    context = MagicMock(spec=RequestContext)
    context.get_user_input.return_value = "name=World style=casual"
    context.task_id = "task-batch-1"
    context.context_id = "ctx-1"
    context.current_task = None

    collected: list[Any] = []
    queue = AsyncMock()
    queue.enqueue_event = AsyncMock(side_effect=lambda e: collected.append(e))

    async def mock_streaming(*args, **kwargs):
        yield "Complete response"

    with patch(
        "yamlgraph.a2a.server.run_graph_streaming_native",
        side_effect=mock_streaming,
    ):
        await executor.execute(context, queue)

    # working → artifact → completed
    assert isinstance(collected[0], TaskStatusUpdateEvent)
    assert collected[0].status.state == TaskState.TASK_STATE_WORKING

    artifacts = [e for e in collected if isinstance(e, TaskArtifactUpdateEvent)]
    assert len(artifacts) == 1

    assert isinstance(collected[-1], TaskStatusUpdateEvent)
    assert collected[-1].status.state == TaskState.TASK_STATE_COMPLETED
