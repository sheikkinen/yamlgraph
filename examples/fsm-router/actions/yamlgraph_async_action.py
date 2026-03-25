"""Fire-and-forget YAMLGraph action via asyncio.create_task.

Launches the YAMLGraph LLM pipeline as a background task so the FSM engine
event loop remains unblocked during the LLM call (which can take 2–30 s).

On first invocation: captures inputs from context, creates asyncio task,
sets guard key, returns None (engine polls at 50ms, stays in current state).

On re-invocation (before task completes): guard key set → returns None
immediately; no duplicate task launched.

On task completion: dispatches resolved event to engine's control socket
via AF_UNIX SOCK_DGRAM.

YAML usage:
    actions:
      classifying:
        - type: yamlgraph_async
          params:
            graph: graphs/classifier.yaml
            input_key: query
            output_key: classification
            event_key: classification
            event_map:
              goodbye: on_goodbye
              question: on_question
            success: simple
            failure: failed
"""

from __future__ import annotations

import asyncio
import json
import logging
import socket
import time
from pathlib import Path
from typing import Any

from langgraph.types import Command
from statemachine_engine.actions.base import BaseAction

logger = logging.getLogger(__name__)

_GUARD_PREFIX = "_graph_running_"
_SOCKET_PREFIX = "/tmp/statemachine-control"
_MAX_MSG = 4096


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _send_event(
    machine_name: str,
    event_type: str,
    payload: dict | None = None,
) -> None:
    """Send an event to the engine's control socket (AF_UNIX DGRAM)."""
    socket_path = f"{_SOCKET_PREFIX}-{machine_name}.sock"
    if not Path(socket_path).exists():
        raise FileNotFoundError(f"Control socket not found: {socket_path}")

    envelope = {"type": event_type, "payload": payload or {}}
    data = json.dumps(envelope).encode("utf-8")
    if len(data) > _MAX_MSG:
        raise ValueError(f"Message ({len(data)} bytes) exceeds {_MAX_MSG} byte limit")

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    try:
        sock.sendto(data, socket_path)
        logger.debug(
            "Sent event %s to %s (%d bytes)", event_type, socket_path, len(data)
        )
    finally:
        sock.close()


def _extract_event(raw: Any, event_map: dict[str, str]) -> str | None:
    """Extract FSM event from a result value using event_map.

    Handles plain strings and Pydantic models (one level deep).
    Returns the mapped event or None if no match.
    """
    if isinstance(raw, str):
        clean = raw.strip().lower()
        if clean in event_map:
            return event_map[clean]
        return None

    if hasattr(raw, "model_dump"):
        for field_val in raw.model_dump().values():
            if isinstance(field_val, str):
                clean = field_val.strip().lower()
                if clean in event_map:
                    return event_map[clean]

    return None


def _json_safe(value: Any) -> Any:
    """Convert values to JSON-serializable primitives for socket envelopes."""
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, list | tuple | set):
        return [_json_safe(v) for v in value]
    if hasattr(value, "model_dump"):
        return _json_safe(value.model_dump())
    return str(value)


def _resolve_context_value(
    value: Any,
    context: dict[str, Any],
    *,
    missing: Any | None = None,
) -> Any:
    """Resolve ``{key}`` placeholders from FSM context."""
    if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
        return context.get(value[1:-1], missing if missing is not None else value)
    return value


def _has_pending_next(state: Any) -> bool:
    """Return True when a checkpointed graph has pending interrupt targets."""
    next_nodes = getattr(state, "next", None)
    return bool(next_nodes)


# ---------------------------------------------------------------------------
# Background task
# ---------------------------------------------------------------------------


async def _run_and_dispatch(
    graph_path: str,
    initial_state: dict[str, Any],
    input_key: str,
    output_key: str,
    event_key: str,
    event_map: dict[str, str],
    success_event: str,
    failure_event: str,
    machine_name: str,
    thread_id: str | None = None,
    context: dict[str, Any] | None = None,
    guard_key: str | None = None,
) -> None:
    """Background task: run YAMLGraph pipeline and dispatch result event."""
    started = time.perf_counter()
    try:
        from yamlgraph.executor_async import load_and_compile_async, run_graph_async

        app = await load_and_compile_async(graph_path)
        run_config = {"configurable": {"thread_id": thread_id}} if thread_id else None
        graph_input: dict[str, Any] | Command = initial_state

        if run_config:
            before_state = await app.aget_state(run_config)
            if _has_pending_next(before_state):
                graph_input = Command(resume=initial_state.get(input_key))

        if run_config:
            result = await run_graph_async(app, graph_input, run_config)
        else:
            result = await run_graph_async(app, graph_input)

        # Event resolution: event_map → route → success
        event = success_event
        payload: dict[str, Any] = {}

        if isinstance(result, dict) and output_key and output_key in result:
            payload[output_key] = _json_safe(result[output_key])

        interrupt_event_resolved = False
        if run_config:
            after_state = await app.aget_state(run_config)
            if _has_pending_next(after_state):
                event = event_map.get("continue", success_event)
                interrupt_event_resolved = True
            elif done_event := event_map.get("done"):
                event = done_event
                interrupt_event_resolved = True

        if (
            not interrupt_event_resolved
            and event_map
            and event_key
            and isinstance(result, dict)
        ):
            raw = result.get(event_key)
            mapped = _extract_event(raw, event_map)
            if mapped:
                logger.info("🗺️ event_map: %s → %s", raw, mapped)
                event = mapped
        elif not interrupt_event_resolved and isinstance(result, dict):
            route = result.get("_route") or result.get("route")
            if route:
                logger.info("🔀 route: %s", route)
                event = route

        elapsed_ms = int((time.perf_counter() - started) * 1000)
        logger.info(
            "✅ yamlgraph_async completed: event=%s elapsed_ms=%s", event, elapsed_ms
        )
        _send_event(machine_name, event, payload or None)

    except Exception as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        logger.error("❌ yamlgraph_async failed: %s (elapsed_ms=%s)", exc, elapsed_ms)
        _send_event(machine_name, failure_event)
    finally:
        if context is not None and guard_key:
            context.pop(guard_key, None)


# ---------------------------------------------------------------------------
# Action class
# ---------------------------------------------------------------------------


class YamlgraphAsyncAction(BaseAction):
    """Fire-and-forget YAMLGraph pipeline via asyncio.create_task."""

    async def execute(self, context: dict[str, Any]) -> str | None:
        """Launch LLM graph as background task; return None immediately."""
        params = self.config.get("params", {})
        current_state = context.get("current_state", "unknown")
        guard_key = f"{_GUARD_PREFIX}{current_state}"

        # Clear stale guards from other states
        stale = [
            k for k in list(context) if k.startswith(_GUARD_PREFIX) and k != guard_key
        ]
        for k in stale:
            del context[k]

        # Guard hit — task already running, engine keeps polling
        if context.get(guard_key):
            return None

        graph_path = params.get("graph")
        if not graph_path:
            logger.error("yamlgraph_async: no graph specified in params")
            return params.get("failure", "failed")

        input_key = params.get("input_key", "input")
        input_value = _resolve_context_value(
            params.get("input_value") or context.get(input_key, ""),
            context,
            missing="",
        )
        output_key = params.get("output_key", "yamlgraph_result")
        event_key = params.get("event_key") or output_key
        event_map = params.get("event_map", {})
        success_event = params.get("success", "completed")
        failure_event = params.get("failure", "failed")
        thread_id = _resolve_context_value(params.get("thread_id"), context)

        # Resolve graph path relative to project root
        action_dir = Path(__file__).resolve().parent.parent
        resolved = action_dir / graph_path
        if not resolved.exists():
            resolved = Path(graph_path)

        # Build initial state
        initial_state: dict[str, Any] = {input_key: input_value}
        for key, value in params.get("variables", {}).items():
            initial_state[key] = _resolve_context_value(value, context)

        machine_name = context.get("machine_name", "unknown")

        logger.info(
            "🚀 yamlgraph_async: launching %s in state %s", resolved, current_state
        )
        asyncio.create_task(
            _run_and_dispatch(
                graph_path=str(resolved),
                initial_state=initial_state,
                input_key=input_key,
                output_key=output_key,
                event_key=event_key,
                event_map=event_map,
                success_event=success_event,
                failure_event=failure_event,
                machine_name=machine_name,
                thread_id=thread_id,
                context=context,
                guard_key=guard_key,
            )
        )

        context[guard_key] = True
        return None
