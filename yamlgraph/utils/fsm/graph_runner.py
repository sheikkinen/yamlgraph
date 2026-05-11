"""Run YAMLGraph asynchronously and dispatch FSM events."""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from importlib import import_module
from typing import Any

from langgraph.types import Command

from yamlgraph.utils.fsm.event_sender import send_event
from yamlgraph.utils.fsm.helpers import extract_event, has_pending_next, json_safe
from yamlgraph.utils.fsm.snapshot import SnapshotParams

logger = logging.getLogger(__name__)

LoadFn = Callable[[str], Awaitable[Any]]
RunFn = Callable[..., Awaitable[Any]]
SendFn = Callable[..., None]
PreDispatchFn = Callable[
    [SnapshotParams | None, str, dict[str, Any] | None, dict[str, Any] | None], bool
]
OnSuccessFn = Callable[[SnapshotParams | None, str, int, dict[str, Any] | None], None]
OnErrorFn = Callable[
    [SnapshotParams | None, Exception, int, dict[str, Any] | None], None
]


def _should_dispatch(
    pre_dispatch_fn: PreDispatchFn | None,
    *,
    snapshot: SnapshotParams | None,
    event: str,
    payload: dict[str, Any] | None,
    context: dict[str, Any] | None,
) -> bool:
    """Return True when dispatch should proceed."""
    should_dispatch = True
    if pre_dispatch_fn is not None:
        should_dispatch = pre_dispatch_fn(snapshot, event, payload, context)
    return should_dispatch


def _handle_success_dispatch(
    *,
    send_fn: SendFn,
    machine_name: str,
    event: str,
    payload: dict[str, Any] | None,
    snapshot: SnapshotParams | None,
    elapsed_ms: int,
    context: dict[str, Any] | None,
    pre_dispatch_fn: PreDispatchFn | None,
    on_success_fn: OnSuccessFn | None,
) -> None:
    """Invoke success hooks and dispatch if allowed."""
    if on_success_fn is not None:
        on_success_fn(snapshot, event, elapsed_ms, context)

    should_dispatch = _should_dispatch(
        pre_dispatch_fn,
        snapshot=snapshot,
        event=event,
        payload=payload,
        context=context,
    )
    if should_dispatch:
        send_fn(machine_name, event, payload)
    else:
        logger.info("🛑 yamlgraph_async dispatch suppressed: event=%s", event)


def _handle_error_dispatch(
    *,
    send_fn: SendFn,
    machine_name: str,
    failure_event: str,
    snapshot: SnapshotParams | None,
    exc: Exception,
    elapsed_ms: int,
    context: dict[str, Any] | None,
    pre_dispatch_fn: PreDispatchFn | None,
    on_error_fn: OnErrorFn | None,
) -> None:
    """Invoke error hooks and dispatch failure event if allowed."""
    if on_error_fn is not None:
        on_error_fn(snapshot, exc, elapsed_ms, context)

    should_dispatch = _should_dispatch(
        pre_dispatch_fn,
        snapshot=snapshot,
        event=failure_event,
        payload=None,
        context=context,
    )
    if should_dispatch:
        send_fn(machine_name, failure_event)
    else:
        logger.info("🛑 yamlgraph_async dispatch suppressed: event=%s", failure_event)


def _resolve_event(
    result: Any,
    *,
    event_key: str,
    event_map: dict[str, str],
    success_event: str,
    interrupt_pending: bool | None,
) -> str:
    """Resolve completion event with the documented cascade order."""
    if interrupt_pending is True:
        return event_map.get("continue", success_event)
    if interrupt_pending is False and "done" in event_map:
        return event_map["done"]

    if event_map and event_key and isinstance(result, dict):
        mapped = extract_event(result.get(event_key), event_map)
        if mapped:
            logger.info("🗺️ event_map: %s → %s", result.get(event_key), mapped)
            return mapped

    if isinstance(result, dict):
        route = result.get("_route") or result.get("route")
        if isinstance(route, str) and route:
            logger.info("🔀 route: %s", route)
            return route

    return success_event


async def run_and_dispatch(
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
    *,
    load_fn: LoadFn | None = None,
    run_fn: RunFn | None = None,
    send_fn: SendFn = send_event,
    snapshot: SnapshotParams | None = None,
    pre_dispatch_fn: PreDispatchFn | None = None,
    on_success_fn: OnSuccessFn | None = None,
    on_error_fn: OnErrorFn | None = None,
) -> None:
    """Execute a graph in the background and send the resulting FSM event."""
    started = time.perf_counter()

    try:
        if load_fn is None or run_fn is None:
            executor_async = import_module("yamlgraph.executor_async")

            load_fn = load_fn or executor_async.load_and_compile_async
            run_fn = run_fn or executor_async.run_graph_async

        app = await load_fn(graph_path)
        run_config = {"configurable": {"thread_id": thread_id}} if thread_id else None
        graph_input: dict[str, Any] | Command = initial_state

        if run_config:
            before_state = await app.aget_state(run_config)
            if has_pending_next(before_state):
                graph_input = Command(resume=initial_state.get(input_key))

        if run_config:
            result = await run_fn(app, graph_input, run_config)
            after_state = await app.aget_state(run_config)
            interrupt_pending: bool | None = has_pending_next(after_state)
        else:
            result = await run_fn(app, graph_input)
            interrupt_pending = None

        payload: dict[str, Any] = {}
        if isinstance(result, dict) and output_key and output_key in result:
            payload[output_key] = json_safe(result[output_key])

        event = _resolve_event(
            result,
            event_key=event_key,
            event_map=event_map,
            success_event=success_event,
            interrupt_pending=interrupt_pending,
        )
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        logger.info(
            "✅ yamlgraph_async completed: event=%s elapsed_ms=%s", event, elapsed_ms
        )
        _handle_success_dispatch(
            send_fn=send_fn,
            machine_name=machine_name,
            event=event,
            payload=payload or None,
            snapshot=snapshot,
            elapsed_ms=elapsed_ms,
            context=context,
            pre_dispatch_fn=pre_dispatch_fn,
            on_success_fn=on_success_fn,
        )
    except Exception as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        logger.error("❌ yamlgraph_async failed: %s (elapsed_ms=%s)", exc, elapsed_ms)
        _handle_error_dispatch(
            send_fn=send_fn,
            machine_name=machine_name,
            failure_event=failure_event,
            snapshot=snapshot,
            exc=exc,
            elapsed_ms=elapsed_ms,
            context=context,
            pre_dispatch_fn=pre_dispatch_fn,
            on_error_fn=on_error_fn,
        )
    finally:
        if context is not None and guard_key:
            context.pop(guard_key, None)
