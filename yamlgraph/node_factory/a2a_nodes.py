"""A2A call node factory — FR-240, FR-248.

Creates LangGraph nodes that invoke external A2A agents via HTTP JSON-RPC.
FR-248 adds Agent Card discovery, skill selection, and SSE streaming.
"""

import asyncio
import logging
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from contextvars import ContextVar
from typing import Any

import httpx

from yamlgraph.constants import ErrorHandler
from yamlgraph.models import PipelineError
from yamlgraph.node_factory.base import GraphState
from yamlgraph.utils.expressions import resolve_node_variables

logger = logging.getLogger(__name__)

# Per-invocation Agent Card cache (FR-248).
# Each ContextVar context starts with an empty dict; no explicit clear needed.
_agent_card_cache: ContextVar[dict[str, Any]] = ContextVar("agent_card_cache")


def _render_message(template: str, variables: dict[str, Any]) -> str:
    """Render a Jinja2 message template with variables.

    Args:
        template: Jinja2 template string.
        variables: Variables to render into the template.

    Returns:
        Rendered message string.
    """
    from jinja2 import Template

    tmpl = Template(template)
    return tmpl.render(**variables)


def _extract_text_from_result(result: dict[str, Any]) -> str:
    """Extract text from A2A task result.

    Collects text from artifacts first, falls back to status message.

    Args:
        result: A2A JSON-RPC result dict.

    Returns:
        Extracted text content.
    """
    texts: list[str] = []

    # Extract from artifacts
    for artifact in result.get("artifacts") or []:
        for part in artifact.get("parts", []):
            if "text" in part and part["text"]:
                texts.append(part["text"])

    if texts:
        return "\n".join(texts)

    # Fallback to status message
    status = result.get("status", {})
    message = status.get("message", {})
    for part in message.get("parts", []):
        if "text" in part and part["text"]:
            texts.append(part["text"])

    return "\n".join(texts) if texts else ""


def _send_a2a_message(
    *,
    agent_url: str,
    message: str,
    timeout: int = 120,
) -> str:
    """Send a message to an A2A agent and return the response text.

    Sends a JSON-RPC ``message/send`` request and extracts text from
    the completed task's artifacts.

    Args:
        agent_url: Base URL of the A2A agent server.
        message: Text message to send.
        timeout: Request timeout in seconds.

    Returns:
        Extracted text from the agent's response.

    Raises:
        RuntimeError: If the A2A task fails or returns an error.
    """
    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "messageId": str(uuid.uuid4()),
                "parts": [{"text": message}],
            },
        },
    }

    response = httpx.post(
        agent_url,
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()

    data = response.json()

    # Check for JSON-RPC error
    if "error" in data:
        err = data["error"]
        raise RuntimeError(f"A2A JSON-RPC error: {err.get('message', str(err))}")

    result = data.get("result", {})
    state = result.get("status", {}).get("state", "")

    if state == "failed":
        task_id = result.get("id", "unknown")
        raise RuntimeError(f"A2A task failed: {task_id}")

    return _extract_text_from_result(result)


def _fetch_agent_card(agent_url: str, timeout: float = 30) -> Any:
    """Fetch Agent Card from the well-known endpoint.

    Args:
        agent_url: Base URL of the A2A agent.
        timeout: HTTP request timeout in seconds.

    Returns:
        Parsed AgentCard object.

    Raises:
        httpx.HTTPStatusError: On non-2xx responses.
    """
    from a2a.types import AgentCard
    from google.protobuf.json_format import ParseDict

    card_url = f"{agent_url.rstrip('/')}/.well-known/agent.json"
    response = httpx.get(card_url, timeout=timeout)
    response.raise_for_status()
    return ParseDict(response.json(), AgentCard())


def _get_agent_card(agent_url: str, timeout: float = 30) -> Any:
    """Get Agent Card, using ContextVar-scoped cache.

    Cache is scoped per graph invocation context via ContextVar.
    Each context starts fresh; no TTL needed for short-lived invocations.

    Args:
        agent_url: Base URL of the A2A agent.
        timeout: HTTP request timeout in seconds.

    Returns:
        Cached or freshly fetched AgentCard object.
    """
    # .get({}) creates a new dict only on first access per context
    cache = _agent_card_cache.get({})
    if agent_url in cache:
        return cache[agent_url]
    card = _fetch_agent_card(agent_url, timeout)
    cache[agent_url] = card
    _agent_card_cache.set(cache)
    return card


def _validate_skill(skill_id: str, card: Any) -> None:
    """Validate a skill ID exists in the Agent Card.

    Args:
        skill_id: Requested skill identifier.
        card: AgentCard with skills list.

    Raises:
        ValueError: If skill not found, listing available skills.
    """
    if not card.skills:
        raise ValueError(f"Skill '{skill_id}' requested but agent has no skills")
    available_ids = [s.id for s in card.skills]
    if skill_id not in available_ids:
        raise ValueError(
            f"Skill '{skill_id}' not found on agent. "
            f"Available skills: {available_ids}"
        )


def _extract_text_from_streaming_events(events: list[Any]) -> str:
    """Extract text from collected A2A streaming events.

    Collects text from TaskArtifactUpdateEvent artifacts.

    Args:
        events: List of streaming events from A2AClient.

    Returns:
        Concatenated text from artifact parts.
    """
    from a2a.types import TaskArtifactUpdateEvent

    texts: list[str] = []
    for event in events:
        if isinstance(event, TaskArtifactUpdateEvent) and event.artifact:
            for part in event.artifact.parts or []:
                if part.WhichOneof("content") == "text" and part.text:
                    texts.append(part.text)
    return "\n".join(texts) if texts else ""


def _send_streaming(
    *,
    agent_url: str,
    message: str,
    timeout: int = 120,
) -> str:
    """Send streaming A2A message via A2AClient in a dedicated thread.

    Runs asyncio.run() in a separate thread to avoid event loop conflicts
    under graph.ainvoke(). See FR-248 Design Decisions.

    Args:
        agent_url: Base URL of the A2A agent.
        message: Rendered message text.
        timeout: Request timeout in seconds.

    Returns:
        Extracted text from streaming events.
    """
    from a2a.client import Client
    from a2a.types import (
        Message,
        Part,
        SendMessageRequest,
    )

    def _run() -> str:
        async def _stream() -> str:
            async with httpx.AsyncClient(timeout=timeout) as http_client:
                client = Client(httpx_client=http_client, url=agent_url)
                request = SendMessageRequest(
                    message=Message(
                        role="user",
                        message_id=str(uuid.uuid4()),
                        parts=[Part(text=message)],
                    ),
                )
                collected: list[Any] = []
                async for event in client.send_message(request):
                    logger.debug("A2A streaming event: %s", type(event).__name__)
                    collected.append(event)
                return _extract_text_from_streaming_events(collected)

        return asyncio.run(_stream())

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_run)
        return future.result()


def create_a2a_call_node(
    node_name: str,
    node_config: dict[str, Any],
) -> Callable[[GraphState], dict]:
    """Create an a2a_call node function from YAML config.

    An a2a_call node sends a message to an external A2A agent and
    stores the response in graph state.

    Args:
        node_name: Name of the node in the graph.
        node_config: Node configuration from YAML.

    Returns:
        Node function compatible with LangGraph.
    """
    agent_url = node_config["agent_url"]
    message_template = node_config["message"]
    state_key = node_config.get("state_key", node_name)
    timeout = node_config.get("timeout", 120)
    on_error = node_config.get("on_error", "fail")
    variable_templates = node_config.get("variables", {})
    skill = node_config.get("skill")
    streaming = node_config.get("streaming", False)

    def node_fn(state: dict) -> dict:
        """A2A call node: send message to external agent."""
        loop_counts = dict(state.get("_loop_counts") or {})
        current_count = loop_counts.get(node_name, 0)
        loop_counts[node_name] = current_count + 1

        # Resolve variable templates from state
        variables = resolve_node_variables(variable_templates, state)

        # Merge state into variables for template rendering
        render_vars = {**state, **variables}

        # Render message template
        rendered_message = _render_message(message_template, render_vars)

        try:
            # Skill validation requires Agent Card (FR-248)
            if skill:
                card = _get_agent_card(agent_url)
                _validate_skill(skill, card)

            if streaming:
                # Streaming requires Agent Card capability check (FR-248)
                card = _get_agent_card(agent_url)
                if not (card.capabilities and card.capabilities.streaming):
                    raise ValueError(
                        f"Agent at {agent_url} does not support streaming. "
                        f"Remove 'streaming: true' or use a streaming-capable agent."
                    )
                result_text = _send_streaming(
                    agent_url=agent_url,
                    message=rendered_message,
                    timeout=timeout,
                )
            else:
                result_text = _send_a2a_message(
                    agent_url=agent_url,
                    message=rendered_message,
                    timeout=timeout,
                )

            return {
                state_key: result_text,
                "current_step": node_name,
                "_loop_counts": loop_counts,
            }

        except Exception as e:
            logger.error("a2a_call node %s failed: %s", node_name, e, exc_info=True)

            if on_error == ErrorHandler.SKIP:
                return {
                    state_key: None,
                    "current_step": node_name,
                    "_loop_counts": loop_counts,
                    "errors": [PipelineError.from_exception(e, node=node_name)],
                }

            raise

    node_fn.__name__ = f"{node_name}_a2a_call_node"
    return node_fn


__all__ = ["create_a2a_call_node"]
