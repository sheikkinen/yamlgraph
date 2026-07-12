"""Stream-event translation for native LangGraph token streaming (FR-716).

Extracted from run_graph_streaming_native (was CC 17): pure functions
that turn LangGraph ``stream_mode="messages"`` events into client-facing
tokens. The FR-057..060 streaming scar tissue lives here, isolated — the
next streaming incident's blast radius is this module.
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import AIMessageChunk

from yamlgraph.models.streaming import StreamEvent

logger = logging.getLogger(__name__)


def translate_message_event(
    event: Any,
    subgraphs: bool,
    node_filter: str | None = None,
) -> str | None:
    """LangGraph messages-mode event → token string, or None to drop.

    Event structure depends on the subgraphs flag:
    - subgraphs=False: ``(AIMessageChunk, metadata_dict)``
    - subgraphs=True: ``(namespace_tuple, (AIMessageChunk, metadata_dict))``

    Only AI message chunks with plain-string content and no tool calls
    become tokens (FR-058): agent nodes emit System/Human/Tool and
    intermediate AI messages; router nodes emit dict content — all
    filtered. node_filter drops tokens from other nodes.
    """
    if subgraphs:
        _namespace, payload = event
        chunk, metadata = payload
    else:
        chunk, metadata = event

    if node_filter and metadata.get("langgraph_node") != node_filter:
        return None

    if (
        isinstance(chunk, AIMessageChunk)
        and chunk.content
        and isinstance(chunk.content, str)
        and not chunk.tool_calls
    ):
        return chunk.content
    return None


def _get_interrupt_payload(state) -> object:  # noqa: ANN001 — StateSnapshot type
    """Extract interrupt payload from state snapshot.

    Args:
        state: LangGraph StateSnapshot from aget_state()

    Returns:
        Interrupt payload value, or None if no interrupts pending.
    """
    if state.tasks and state.tasks[-1].interrupts:
        return state.tasks[-1].interrupts[-1].value
    return None


async def check_interrupt(app: Any, config: dict) -> StreamEvent | None:
    """Post-stream interrupt detection — only when a thread_id is configured."""
    if not config.get("configurable", {}).get("thread_id"):
        return None
    try:
        state = await app.aget_state(config)
        interrupt_payload = _get_interrupt_payload(state)
        if interrupt_payload is not None:
            return StreamEvent(type="interrupt", payload=interrupt_payload)
    except Exception:
        logger.debug("Could not check interrupt state", exc_info=True)
    return None


__all__ = ["translate_message_event", "check_interrupt"]
