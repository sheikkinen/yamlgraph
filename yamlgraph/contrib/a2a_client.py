"""A2A consumer client for type: python nodes — FR-253.

Sends messages to external A2A agents via HTTP JSON-RPC. Replaces the
dedicated ``type: a2a_call`` node type with a contrib function invoked
via ``type: python``. Preserves Agent Card discovery, skill validation,
and streaming support from FR-240/FR-248.

Usage in graph YAML::

    tools:
      a2a_send:
        type: python
        module: yamlgraph.contrib.a2a_client
        function: send_a2a_message

    nodes:
      ask_agent:
        type: python
        tool: a2a_send
        state_key: agent_response
        variables:
          agent_url: "http://localhost:9240/"
          message: "name={{ name }} style={{ style }}"
"""

import asyncio
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextvars import ContextVar
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Per-invocation Agent Card cache.
# Each ContextVar context starts with an empty dict; no explicit clear needed.
_agent_card_cache: ContextVar[dict[str, Any]] = ContextVar("agent_card_cache")


def _render_template(template: str, state: dict[str, Any]) -> str:
    """Render Jinja2 template with state variables."""
    from jinja2 import Template

    return Template(template).render(**state)


def _extract_text_from_result(result: dict[str, Any]) -> str:
    """Extract text from A2A task result artifacts or status message."""
    texts: list[str] = []

    for artifact in result.get("artifacts") or []:
        for part in artifact.get("parts", []):
            if "text" in part and part["text"]:
                texts.append(part["text"])

    if texts:
        return "\n".join(texts)

    status = result.get("status", {})
    message = status.get("message", {})
    for part in message.get("parts", []):
        if "text" in part and part["text"]:
            texts.append(part["text"])

    return "\n".join(texts) if texts else ""


def _fetch_agent_card(agent_url: str, timeout: float = 30) -> Any:
    """Fetch Agent Card from well-known endpoint.

    Args:
        agent_url: Base URL of the A2A agent.
        timeout: HTTP request timeout in seconds.

    Returns:
        Parsed AgentCard protobuf object.
    """
    from a2a.types import AgentCard
    from google.protobuf.json_format import ParseDict

    card_url = f"{agent_url.rstrip('/')}/.well-known/agent.json"
    response = httpx.get(card_url, timeout=timeout)
    response.raise_for_status()
    return ParseDict(response.json(), AgentCard())


def _get_agent_card(agent_url: str, timeout: float = 30) -> Any:
    """Get Agent Card with ContextVar-scoped cache.

    Cache is scoped per graph invocation via ContextVar.
    Each context starts fresh; no TTL needed.
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
    """Validate skill ID exists in Agent Card.

    Raises:
        ValueError: If skill not found, listing available skills.
    """
    if not card.skills:
        raise ValueError(f"Skill '{skill_id}' requested but agent has no skills")
    available_ids = [s.id for s in card.skills]
    if skill_id not in available_ids:
        raise ValueError(
            f"Skill '{skill_id}' not found on agent. Available skills: {available_ids}"
        )


def _extract_text_from_streaming_events(events: list[Any]) -> str:
    """Extract text from collected A2A streaming events."""
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
    """
    from a2a.client import Client
    from a2a.types import Message, Part, SendMessageRequest

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


def send_a2a_message(state: dict[str, Any]) -> dict[str, Any]:
    """Send message to an external A2A agent.

    Reads configuration from state keys (injected via ``variables:``
    on the ``type: python`` node):

    - ``agent_url`` (required): Base URL of the A2A agent server
    - ``message`` (required unless ``message_template`` set): Message text
    - ``message_template`` (optional): Jinja2 template rendered with state
    - ``skill`` (optional): Target skill ID on the remote agent
    - ``streaming`` (optional): Use SSE streaming transport
    - ``timeout`` (optional, default 120): Request timeout in seconds

    Returns:
        ``{"response": extracted_text}``

    Raises:
        ValueError: If required fields are missing or skill/streaming
            validation fails.
        RuntimeError: If the A2A task fails or returns a JSON-RPC error.
    """
    agent_url = state.get("agent_url")
    if not agent_url:
        raise ValueError("send_a2a_message: 'agent_url' required in state")

    # Resolve message: direct message or Jinja2 template
    message = state.get("message")
    message_template = state.get("message_template")
    if not message and not message_template:
        raise ValueError(
            "send_a2a_message: 'message' or 'message_template' required in state"
        )
    if message_template:
        message = _render_template(message_template, state)

    timeout = int(state.get("timeout", 120))
    skill = state.get("skill")
    streaming = state.get("streaming")

    # Skill validation requires Agent Card
    if skill:
        card = _get_agent_card(agent_url)
        _validate_skill(skill, card)

    # Streaming path
    if streaming:
        card = _get_agent_card(agent_url)
        if not (card.capabilities and card.capabilities.streaming):
            raise ValueError(
                f"Agent at {agent_url} does not support streaming. "
                f"Remove 'streaming' or use a streaming-capable agent."
            )
        result_text = _send_streaming(
            agent_url=agent_url, message=message, timeout=timeout
        )
        return {"response": result_text}

    # Sync path — raw httpx.post with JSON-RPC
    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "SendMessage",
        "params": {
            "message": {
                "role": "ROLE_USER",
                "messageId": str(uuid.uuid4()),
                "parts": [{"text": message}],
            },
        },
    }

    response = httpx.post(
        agent_url,
        json=payload,
        timeout=timeout,
        headers={"A2A-Version": "1.0"},
    )
    response.raise_for_status()

    data = response.json()

    if "error" in data:
        err = data["error"]
        raise RuntimeError(f"A2A JSON-RPC error: {err.get('message', str(err))}")

    result = data.get("result", {})
    task_state = result.get("status", {}).get("state", "")

    if task_state == "failed":
        task_id = result.get("id", "unknown")
        raise RuntimeError(f"A2A task failed: {task_id}")

    return {"response": _extract_text_from_result(result)}


__all__ = ["send_a2a_message"]
