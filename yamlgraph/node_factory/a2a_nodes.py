"""A2A call node factory — FR-240.

Creates LangGraph nodes that invoke external A2A agents via HTTP JSON-RPC.
"""

import logging
import uuid
from collections.abc import Callable
from typing import Any

import httpx

from yamlgraph.constants import ErrorHandler
from yamlgraph.models import PipelineError
from yamlgraph.node_factory.base import GraphState
from yamlgraph.utils.expressions import resolve_node_variables

logger = logging.getLogger(__name__)


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
            if part.get("kind") == "text" and part.get("text"):
                texts.append(part["text"])

    if texts:
        return "\n".join(texts)

    # Fallback to status message
    status = result.get("status", {})
    message = status.get("message", {})
    for part in message.get("parts", []):
        if part.get("kind") == "text" and part.get("text"):
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
                "parts": [{"kind": "text", "text": message}],
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
