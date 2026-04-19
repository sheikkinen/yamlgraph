"""YAMLGraph A2A Server — expose graphs as A2A agents.

FR-208 / CAP-81: A2A Protocol Server
FR-250: Complete protocol gaps (task/get, streaming, resume)
(REQ-YG-206, REQ-YG-207, REQ-YG-208, REQ-YG-209, REQ-YG-210,
 REQ-YG-211, REQ-YG-212, REQ-YG-213)

Usage:
    yamlgraph a2a serve examples/demos/hello/graph.yaml --port 8080
    yamlgraph a2a card examples/demos/hello/graph.yaml
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any

try:
    from a2a.server.agent_execution import AgentExecutor, RequestContext
    from a2a.server.events import InMemoryQueueManager
    from a2a.server.events.event_queue import EventQueue
    from a2a.server.request_handlers import DefaultRequestHandler
    from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
    from a2a.server.tasks import InMemoryTaskStore
    from a2a.types import (
        Artifact,
        Message,
        Part,
        Role,
        TaskArtifactUpdateEvent,
        TaskState,
        TaskStatus,
        TaskStatusUpdateEvent,
    )
except ImportError as exc:
    raise ImportError(
        "A2A SDK not installed. Install with: pip install yamlgraph[a2a]"
    ) from exc

from yamlgraph.a2a_message import (  # noqa: F401 (CONF-004) — re-exports
    _detect_interrupt,
    _extract_interrupt_payload,
    build_agent_card,
    extract_text_from_parts,
    map_pipeline_error,
    parse_a2a_message,
)
from yamlgraph.discovery import discover_graphs  # REQ-YG-206: shared discovery
from yamlgraph.executor_async import run_graph_streaming_native
from yamlgraph.models import PipelineError
from yamlgraph.models.streaming import StreamEvent

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# REQ-YG-068 (shared): Graph invocation
# ---------------------------------------------------------------------------


def _invoke_graph(graph_path: str, variables: dict[str, Any]) -> dict[str, Any]:
    """Load, compile, and invoke a graph synchronously.

    Args:
        graph_path: Absolute path to graph.yaml.
        variables: Input variables for the graph.

    Returns:
        Result dict from graph invocation.
    """
    from yamlgraph.graph_loader import compile_graph, load_graph_config

    config = load_graph_config(graph_path)
    sg = compile_graph(config)
    compiled = sg.compile()
    result = compiled.invoke(variables)
    return result


# ---------------------------------------------------------------------------
# REQ-YG-207, REQ-YG-209, REQ-YG-212: AgentExecutor
# ---------------------------------------------------------------------------


class YAMLGraphAgentExecutor(AgentExecutor):
    """A2A AgentExecutor that invokes YAMLGraph graphs.

    Maps A2A task lifecycle to graph compilation and execution.
    """

    def __init__(self, graph_lookup: dict[str, dict[str, Any]]) -> None:
        """Initialize with a lookup of discovered graphs.

        Args:
            graph_lookup: Dict mapping graph name to graph info dict.
        """
        self._graph_lookup = graph_lookup
        self._running_tasks: dict[str, asyncio.Task[Any]] = {}

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute a graph for an A2A task.

        FR-250: Uses streaming execution via run_graph_streaming_native()
        for both task/send and task/sendSubscribe. Supports resume from
        INPUT_REQUIRED state via Command(resume=...).
        """
        task_id = context.task_id or str(uuid.uuid4())
        context_id = context.context_id or str(uuid.uuid4())

        try:
            # Emit working status
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    task_id=task_id,
                    context_id=context_id,
                    status=TaskStatus(state=TaskState.TASK_STATE_WORKING),
                )
            )

            # Extract text from message
            text = context.get_user_input()

            # Find the target graph
            graph_info = self._resolve_graph(text)
            required_vars = graph_info.get("required_vars", [])

            # REQ-YG-213: Detect resume from INPUT_REQUIRED state
            is_resume = (
                context.current_task is not None
                and context.current_task.status.state
                == TaskState.TASK_STATE_INPUT_REQUIRED
            )

            if is_resume:
                from langgraph.types import Command

                initial_state = Command(resume=text)
            else:
                variables = parse_a2a_message(text, required_vars)
                initial_state = variables

            # REQ-YG-211: Stream execution via run_graph_streaming_native()
            config = {"configurable": {"thread_id": task_id}}

            async for chunk in run_graph_streaming_native(
                graph_info["path"],
                initial_state,
                config=config,
            ):
                if isinstance(chunk, StreamEvent):
                    if chunk.type == "error":
                        # Stream error → FAILED
                        await event_queue.enqueue_event(
                            TaskStatusUpdateEvent(
                                task_id=task_id,
                                context_id=context_id,
                                status=TaskStatus(
                                    state=TaskState.TASK_STATE_FAILED,
                                    message=Message(
                                        role=Role.ROLE_AGENT,
                                        parts=[
                                            Part(text=chunk.error or "Unknown error")
                                        ],
                                        message_id=str(uuid.uuid4()),
                                    ),
                                ),
                            )
                        )
                        return
                    elif chunk.type == "interrupt":
                        # Stream interrupt → INPUT_REQUIRED with payload
                        payload_text = (
                            str(chunk.payload)
                            if chunk.payload
                            else "Graph requires additional input"
                        )
                        await event_queue.enqueue_event(
                            TaskStatusUpdateEvent(
                                task_id=task_id,
                                context_id=context_id,
                                status=TaskStatus(
                                    state=TaskState.TASK_STATE_INPUT_REQUIRED,
                                    message=Message(
                                        role=Role.ROLE_AGENT,
                                        parts=[Part(text=payload_text)],
                                        message_id=str(uuid.uuid4()),
                                    ),
                                ),
                            )
                        )
                        return
                elif isinstance(chunk, str):
                    # Token chunk → incremental artifact event
                    await event_queue.enqueue_event(
                        TaskArtifactUpdateEvent(
                            task_id=task_id,
                            context_id=context_id,
                            artifact=Artifact(
                                artifact_id=str(uuid.uuid4()),
                                parts=[Part(text=chunk)],
                                name="graph_output",
                            ),
                        )
                    )

            # Emit completed status
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    task_id=task_id,
                    context_id=context_id,
                    status=TaskStatus(
                        state=TaskState.TASK_STATE_COMPLETED,
                        message=Message(
                            role=Role.ROLE_AGENT,
                            parts=[Part(text="Graph execution completed")],
                            message_id=str(uuid.uuid4()),
                        ),
                    ),
                )
            )

        except Exception as e:
            logger.error("Task %s failed: %s", task_id, e, exc_info=True)

            # Map PipelineError if applicable
            if isinstance(e, PipelineError):
                a2a_err = map_pipeline_error(e)
                error_msg = a2a_err.message or str(e)
            else:
                error_msg = str(e)

            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    task_id=task_id,
                    context_id=context_id,
                    status=TaskStatus(
                        state=TaskState.TASK_STATE_FAILED,
                        message=Message(
                            role=Role.ROLE_AGENT,
                            parts=[Part(text=error_msg)],
                            message_id=str(uuid.uuid4()),
                        ),
                    ),
                )
            )

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Cancel a running graph execution."""
        task_id = context.task_id or str(uuid.uuid4())
        context_id = context.context_id or str(uuid.uuid4())

        # Cancel any running asyncio task
        running = self._running_tasks.pop(task_id, None)
        if running and not running.done():
            running.cancel()

        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=task_id,
                context_id=context_id,
                status=TaskStatus(state=TaskState.TASK_STATE_CANCELED),
            )
        )

    def _resolve_graph(self, text: str) -> dict[str, Any]:
        """Resolve which graph to invoke.

        For single-graph servers, returns the only graph.
        For multi-graph, could be extended to route by skill.
        """
        if len(self._graph_lookup) == 1:
            return next(iter(self._graph_lookup.values()))

        # Default: return first graph
        return next(iter(self._graph_lookup.values()))

    def _format_result(self, result: dict[str, Any]) -> str:
        """Format graph result dict as readable text."""
        # Filter out internal keys
        output_parts: list[str] = []
        for key, value in result.items():
            if key.startswith("_") or key in ("thread_id", "errors"):
                continue
            if isinstance(value, str):
                output_parts.append(value)
            else:
                try:
                    output_parts.append(json.dumps(value, indent=2))
                except (TypeError, ValueError):
                    output_parts.append(str(value))

        return "\n\n".join(output_parts) if output_parts else json.dumps(result)


# ---------------------------------------------------------------------------
# REQ-YG-207: Server factory
# ---------------------------------------------------------------------------


def create_a2a_app(
    graph_patterns: list[str] | None = None,
    host: str = "localhost",
    port: int = 8080,
) -> Any:
    """Create an A2A Starlette application from discovered graphs.

    Args:
        graph_patterns: Glob patterns for graph discovery.
        host: Server hostname for Agent Card URL.
        port: Server port.

    Returns:
        Starlette application ready to be served.
    """
    from starlette.applications import Starlette

    from yamlgraph.discovery import DEFAULT_GRAPH_PATTERNS

    if graph_patterns is None:
        graph_patterns = DEFAULT_GRAPH_PATTERNS

    graphs = discover_graphs(graph_patterns)
    graph_lookup = {g["name"]: g for g in graphs}

    agent_card = build_agent_card(graphs=graphs, host=host, port=port)

    agent_executor = YAMLGraphAgentExecutor(graph_lookup=graph_lookup)
    task_store = InMemoryTaskStore()
    queue_manager = InMemoryQueueManager()

    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=task_store,
        agent_card=agent_card,
        queue_manager=queue_manager,
    )

    routes = create_jsonrpc_routes(
        request_handler, rpc_url="/"
    ) + create_agent_card_routes(agent_card)

    return Starlette(routes=routes)
