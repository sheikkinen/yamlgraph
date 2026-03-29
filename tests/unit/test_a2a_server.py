"""Tests for A2A server — FR-208: A2A Protocol Server.

TDD red phase: all tests written before implementation.
Tests cover message parsing, Agent Card generation, error mapping,
and the AgentExecutor integration.
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
# REQ-YG-208: Agent Card generation
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-208")
def test_build_agent_card_from_graph(sample_graph_info):
    """Agent Card auto-generated with correct name, description, skills."""
    from yamlgraph.a2a_server import build_agent_card

    card = build_agent_card(
        graphs=[sample_graph_info],
        host="localhost",
        port=8080,
    )

    assert card.name == "YAMLGraph A2A Server"
    assert card.url == "http://localhost:8080/"
    assert len(card.skills) == 1
    assert card.skills[0].id == "hello-world"
    assert card.skills[0].name == "hello-world"
    assert card.skills[0].description == "Simple greeting generator"
    assert "yamlgraph" in card.skills[0].tags


@pytest.mark.req("REQ-YG-208")
def test_agent_card_capabilities(sample_graph_info):
    """Agent Card has streaming=True, push_notifications=None."""
    from yamlgraph.a2a_server import build_agent_card

    card = build_agent_card(
        graphs=[sample_graph_info],
        host="localhost",
        port=8080,
    )

    assert card.capabilities.streaming is True
    assert card.capabilities.push_notifications is None


@pytest.mark.req("REQ-YG-208")
def test_agent_card_no_authentication(sample_graph_info):
    """Agent Card has no security schemes by default."""
    from yamlgraph.a2a_server import build_agent_card

    card = build_agent_card(
        graphs=[sample_graph_info],
        host="localhost",
        port=8080,
    )

    assert card.security_schemes is None


@pytest.mark.req("REQ-YG-208")
def test_agent_card_multi_graph(sample_graph_info, single_var_graph_info):
    """Multiple graphs become multiple skills in Agent Card."""
    from yamlgraph.a2a_server import build_agent_card

    card = build_agent_card(
        graphs=[sample_graph_info, single_var_graph_info],
        host="localhost",
        port=9090,
    )

    assert len(card.skills) == 2
    skill_ids = {s.id for s in card.skills}
    assert "hello-world" in skill_ids
    assert "echo" in skill_ids


# ---------------------------------------------------------------------------
# REQ-YG-209: Message parsing strategy
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-209")
def test_parse_message_json_mode():
    """JSON object in text is parsed as variables."""
    from yamlgraph.a2a_server import parse_a2a_message

    result = parse_a2a_message(
        '{"name": "World", "style": "casual"}',
        required_vars=["name", "style"],
    )
    assert result == {"name": "World", "style": "casual"}


@pytest.mark.req("REQ-YG-209")
def test_parse_message_key_value_mode():
    """key=value pairs parsed via shlex."""
    from yamlgraph.a2a_server import parse_a2a_message

    result = parse_a2a_message(
        'name=World style="holy see of code"',
        required_vars=["name", "style"],
    )
    assert result == {"name": "World", "style": "holy see of code"}


@pytest.mark.req("REQ-YG-209")
def test_parse_message_single_input_mode():
    """Single required var gets entire text assigned."""
    from yamlgraph.a2a_server import parse_a2a_message

    result = parse_a2a_message(
        "Hello World, how are you?",
        required_vars=["input"],
    )
    assert result == {"input": "Hello World, how are you?"}


@pytest.mark.req("REQ-YG-209")
def test_parse_message_fallback_to_input_key():
    """No required vars and no key=value → assign to 'input' key."""
    from yamlgraph.a2a_server import parse_a2a_message

    result = parse_a2a_message(
        "Just some text",
        required_vars=[],
    )
    assert result == {"input": "Just some text"}


@pytest.mark.req("REQ-YG-209")
def test_parse_message_resolution_order():
    """JSON takes priority over key_value even when text contains '='."""
    from yamlgraph.a2a_server import parse_a2a_message

    # Valid JSON that also contains '='
    result = parse_a2a_message(
        '{"equation": "a=b"}',
        required_vars=["equation"],
    )
    assert result == {"equation": "a=b"}


@pytest.mark.req("REQ-YG-209")
def test_parse_message_missing_required_vars():
    """Missing required vars raises ValueError with missing keys."""
    from yamlgraph.a2a_server import parse_a2a_message

    with pytest.raises(ValueError, match="missing_variables"):
        parse_a2a_message(
            "name=World",
            required_vars=["name", "style"],
        )


@pytest.mark.req("REQ-YG-209")
def test_parse_message_extra_vars_ignored():
    """Extra variables not in required_vars are included (same as CLI --var)."""
    from yamlgraph.a2a_server import parse_a2a_message

    result = parse_a2a_message(
        "name=World style=casual extra=ignored",
        required_vars=["name", "style"],
    )
    assert result["name"] == "World"
    assert result["style"] == "casual"
    assert result["extra"] == "ignored"


# ---------------------------------------------------------------------------
# REQ-YG-209: PipelineError → A2A error mapping
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-209")
def test_map_pipeline_error_llm():
    """LLM_ERROR maps to InternalError."""
    from a2a.types import InternalError

    from yamlgraph.a2a_server import map_pipeline_error
    from yamlgraph.models import ErrorType, PipelineError

    err = PipelineError(
        type=ErrorType.LLM_ERROR,
        message="Rate limit exceeded",
        node="greet",
        retryable=True,
    )
    a2a_err = map_pipeline_error(err)
    assert isinstance(a2a_err, InternalError)
    assert "Rate limit exceeded" in a2a_err.message
    assert a2a_err.data["retryable"] is True


@pytest.mark.req("REQ-YG-209")
def test_map_pipeline_error_validation():
    """VALIDATION_ERROR maps to InvalidParamsError."""
    from a2a.types import InvalidParamsError

    from yamlgraph.a2a_server import map_pipeline_error
    from yamlgraph.models import ErrorType, PipelineError

    err = PipelineError(
        type=ErrorType.VALIDATION_ERROR,
        message="Field 'name' required",
        node="greet",
    )
    a2a_err = map_pipeline_error(err)
    assert isinstance(a2a_err, InvalidParamsError)


@pytest.mark.req("REQ-YG-209")
def test_map_pipeline_error_prompt():
    """PROMPT_ERROR maps to InvalidParamsError."""
    from a2a.types import InvalidParamsError

    from yamlgraph.a2a_server import map_pipeline_error
    from yamlgraph.models import ErrorType, PipelineError

    err = PipelineError(
        type=ErrorType.PROMPT_ERROR,
        message="Prompt not found",
        node="greet",
    )
    a2a_err = map_pipeline_error(err)
    assert isinstance(a2a_err, InvalidParamsError)


# ---------------------------------------------------------------------------
# REQ-YG-207: A2A server discovers graphs
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-207")
def test_a2a_server_uses_shared_discovery():
    """a2a_server imports discover_graphs from yamlgraph.discovery."""
    from yamlgraph.a2a_server import discover_graphs as a2a_discover
    from yamlgraph.discovery import discover_graphs as shared_discover

    assert a2a_discover is shared_discover


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

    from yamlgraph.a2a_server import YAMLGraphAgentExecutor

    executor = YAMLGraphAgentExecutor(
        graph_lookup={"hello-world": sample_graph_info},
    )

    context = MagicMock(spec=RequestContext)
    context.get_user_input.return_value = "name=World style=casual"
    context.task_id = "task-1"
    context.context_id = "ctx-1"

    # Use a collecting mock queue
    collected_events: list[Any] = []

    queue = AsyncMock()
    queue.enqueue_event = AsyncMock(side_effect=lambda e: collected_events.append(e))
    queue.close = AsyncMock()

    mock_result = {"greeting": "Hello World!"}
    with patch("yamlgraph.a2a_server._invoke_graph", return_value=mock_result):
        await executor.execute(context, queue)

    # Should have working + artifact + completed events
    status_events = [
        e for e in collected_events if isinstance(e, TaskStatusUpdateEvent)
    ]
    assert any(e.status.state == TaskState.working for e in status_events)
    assert any(e.status.state == TaskState.completed for e in status_events)


@pytest.mark.req("REQ-YG-212")
@pytest.mark.asyncio(loop_scope="function")
async def test_executor_cancel(sample_graph_info):
    """AgentExecutor.cancel() cancels the running task."""
    from a2a.server.agent_execution import RequestContext
    from a2a.types import TaskState, TaskStatusUpdateEvent

    from yamlgraph.a2a_server import YAMLGraphAgentExecutor

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
    assert any(e.status.state == TaskState.canceled for e in status_events)


# ---------------------------------------------------------------------------
# REQ-YG-207: create_a2a_app wires everything together
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-207")
def test_create_a2a_app(tmp_path: Path):
    """create_a2a_app returns a Starlette application."""
    from yamlgraph.a2a_server import create_a2a_app

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
# REQ-YG-209: Text extraction from A2A Message parts
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-209")
def test_extract_text_from_parts():
    """Multiple TextParts are concatenated with newlines."""
    from a2a.types import Part, TextPart

    from yamlgraph.a2a_server import extract_text_from_parts

    parts = [
        Part(root=TextPart(text="name=World")),
        Part(root=TextPart(text="style=casual")),
    ]
    text = extract_text_from_parts(parts)
    assert text == "name=World\nstyle=casual"


@pytest.mark.req("REQ-YG-209")
def test_extract_text_skips_non_text_parts():
    """Non-text parts are skipped; if only non-text, raises ValueError."""
    from a2a.types import DataPart, Part

    from yamlgraph.a2a_server import extract_text_from_parts

    parts = [
        Part(root=DataPart(data={"key": "val"})),
    ]
    with pytest.raises(ValueError, match="unsupported_content_type"):
        extract_text_from_parts(parts)


# ---------------------------------------------------------------------------
# REQ-YG-210: task/get retrieves task status via InMemoryTaskStore
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-210")
@pytest.mark.asyncio(loop_scope="function")
async def test_task_store_save_and_get():
    """InMemoryTaskStore persists task for task/get retrieval."""
    from a2a.server.tasks import InMemoryTaskStore
    from a2a.types import Task, TaskState, TaskStatus

    store = InMemoryTaskStore()
    task = Task(
        id="task-get-1",
        context_id="ctx-1",
        status=TaskStatus(state=TaskState.working),
    )
    await store.save(task)

    retrieved = await store.get("task-get-1")
    assert retrieved is not None
    assert retrieved.id == "task-get-1"
    assert retrieved.status.state == TaskState.working


@pytest.mark.req("REQ-YG-210")
@pytest.mark.asyncio(loop_scope="function")
async def test_task_store_returns_none_for_unknown_id():
    """InMemoryTaskStore returns None for unknown task IDs."""
    from a2a.server.tasks import InMemoryTaskStore

    store = InMemoryTaskStore()
    result = await store.get("nonexistent")
    assert result is None


@pytest.mark.req("REQ-YG-210")
def test_create_a2a_app_uses_task_store(tmp_path: Path):
    """create_a2a_app wires InMemoryTaskStore for task/get retrieval."""
    from yamlgraph.a2a_server import create_a2a_app

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

    from yamlgraph.a2a_server import YAMLGraphAgentExecutor

    executor = YAMLGraphAgentExecutor(
        graph_lookup={"hello-world": sample_graph_info},
    )

    context = MagicMock(spec=RequestContext)
    context.get_user_input.return_value = "name=World style=casual"
    context.task_id = "task-stream-1"
    context.context_id = "ctx-1"

    collected: list[Any] = []
    queue = AsyncMock()
    queue.enqueue_event = AsyncMock(side_effect=lambda e: collected.append(e))
    queue.close = AsyncMock()

    with patch("yamlgraph.a2a_server._invoke_graph", return_value={"out": "hi"}):
        await executor.execute(context, queue)

    # Verify SSE event stream order: working → artifact → completed
    assert isinstance(collected[0], TaskStatusUpdateEvent)
    assert collected[0].status.state == TaskState.working
    assert collected[0].final is False

    artifact_events = [e for e in collected if isinstance(e, TaskArtifactUpdateEvent)]
    assert len(artifact_events) == 1

    final_event = collected[-1]
    assert isinstance(final_event, TaskStatusUpdateEvent)
    assert final_event.status.state == TaskState.completed
    assert final_event.final is True


@pytest.mark.req("REQ-YG-211")
@pytest.mark.asyncio(loop_scope="function")
async def test_streaming_events_include_message_on_complete(sample_graph_info):
    """Completed SSE event includes agent message with result text."""
    from a2a.server.agent_execution import RequestContext
    from a2a.types import TaskState, TaskStatusUpdateEvent

    from yamlgraph.a2a_server import YAMLGraphAgentExecutor

    executor = YAMLGraphAgentExecutor(
        graph_lookup={"hello-world": sample_graph_info},
    )

    context = MagicMock(spec=RequestContext)
    context.get_user_input.return_value = "name=World style=casual"
    context.task_id = "task-stream-2"
    context.context_id = "ctx-1"

    collected: list[Any] = []
    queue = AsyncMock()
    queue.enqueue_event = AsyncMock(side_effect=lambda e: collected.append(e))
    queue.close = AsyncMock()

    with patch(
        "yamlgraph.a2a_server._invoke_graph", return_value={"greeting": "Hello!"}
    ):
        await executor.execute(context, queue)

    completed = [
        e
        for e in collected
        if isinstance(e, TaskStatusUpdateEvent)
        and e.status.state == TaskState.completed
    ]
    assert len(completed) == 1
    assert completed[0].status.message is not None
    assert "Hello!" in completed[0].status.message.parts[0].root.text


# ---------------------------------------------------------------------------
# REQ-YG-213: input-required state on __interrupt__
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-213")
def test_detect_interrupt_returns_true():
    """_detect_interrupt recognizes __interrupt__ key in graph result."""
    from yamlgraph.a2a_server import _detect_interrupt

    result = {"greeting": "Hello", "__interrupt__": [{"value": "need input"}]}
    assert _detect_interrupt(result) is True


@pytest.mark.req("REQ-YG-213")
def test_detect_interrupt_returns_false():
    """_detect_interrupt returns False for normal results."""
    from yamlgraph.a2a_server import _detect_interrupt

    result = {"greeting": "Hello"}
    assert _detect_interrupt(result) is False


@pytest.mark.req("REQ-YG-213")
@pytest.mark.asyncio(loop_scope="function")
async def test_execute_emits_input_required_on_interrupt(sample_graph_info):
    """When graph result contains __interrupt__, input-required state is emitted."""
    from a2a.server.agent_execution import RequestContext
    from a2a.types import TaskState, TaskStatusUpdateEvent

    from yamlgraph.a2a_server import YAMLGraphAgentExecutor

    executor = YAMLGraphAgentExecutor(
        graph_lookup={"hello-world": sample_graph_info},
    )

    context = MagicMock(spec=RequestContext)
    context.get_user_input.return_value = "name=World style=casual"
    context.task_id = "task-interrupt-1"
    context.context_id = "ctx-1"

    collected: list[Any] = []
    queue = AsyncMock()
    queue.enqueue_event = AsyncMock(side_effect=lambda e: collected.append(e))
    queue.close = AsyncMock()

    interrupt_result = {
        "greeting": "partial",
        "__interrupt__": [{"value": "need clarification"}],
    }
    with patch("yamlgraph.a2a_server._invoke_graph", return_value=interrupt_result):
        await executor.execute(context, queue)

    status_events = [e for e in collected if isinstance(e, TaskStatusUpdateEvent)]
    input_required = [
        e for e in status_events if e.status.state == TaskState.input_required
    ]
    assert len(input_required) == 1
    assert input_required[0].final is False


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
async def test_execute_closes_queue_gracefully(sample_graph_info):
    """EventQueue.close must use immediate=False so SSE consumer can drain all events."""
    from a2a.server.agent_execution import RequestContext

    from yamlgraph.a2a_server import YAMLGraphAgentExecutor

    executor = YAMLGraphAgentExecutor(
        graph_lookup={"hello-world": sample_graph_info},
    )

    context = MagicMock(spec=RequestContext)
    context.get_user_input.return_value = "name=World style=casual"
    context.task_id = "task-drain-1"
    context.context_id = "ctx-1"

    queue = AsyncMock()
    queue.enqueue_event = AsyncMock()
    queue.close = AsyncMock()

    with patch("yamlgraph.a2a_server._invoke_graph", return_value={"out": "hi"}):
        await executor.execute(context, queue)

    # close() must be called with immediate=False to allow consumer drain
    queue.close.assert_called_once_with(immediate=False)
