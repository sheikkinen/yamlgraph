"""Typed snapshot contract for shared FSM bridge execution."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from yamlgraph.utils.fsm.helpers import resolve_context_ref


@dataclass
class SnapshotParams:
    """Normalized action execution snapshot passed to runner hooks."""

    graph_path: str
    initial_state: dict[str, Any]
    input_key: str
    output_key: str
    event_key: str
    event_map: dict[str, str]
    success_event: str
    failure_event: str
    thread_id: str | None
    phase: str
    payload_keys: list[str] | None


def snapshot_params(
    params: dict[str, Any],
    context: dict[str, Any],
    *,
    project_root: str | Path | None = None,
) -> SnapshotParams:
    """Build typed snapshot params from FSM action config and runtime context."""
    graph_path = params.get("graph")
    if not graph_path:
        raise ValueError("yamlgraph_async: no graph specified in params")

    input_key = params.get("input_key", "input")
    input_value = resolve_context_ref(
        params.get("input_value") or context.get(input_key, ""),
        context,
        missing="",
    )
    output_key = params.get("output_key", "yamlgraph_result")
    event_key = params.get("event_key") or output_key
    event_map = dict(params.get("event_map", {}))
    success_event = params.get("success", "completed")
    failure_event = params.get("failure", "failed")
    thread_id = resolve_context_ref(params.get("thread_id"), context)
    phase = params.get("phase", "graph")
    payload_keys = params.get("payload_keys")

    initial_state: dict[str, Any] = {input_key: input_value}
    for key, value in params.get("variables", {}).items():
        initial_state[key] = resolve_context_ref(value, context)

    resolved_graph = str(graph_path)
    graph_candidate = Path(resolved_graph)
    if project_root is not None and not graph_candidate.is_absolute():
        candidate = Path(project_root) / graph_candidate
        if candidate.exists():
            resolved_graph = str(candidate)

    return SnapshotParams(
        graph_path=resolved_graph,
        initial_state=initial_state,
        input_key=input_key,
        output_key=output_key,
        event_key=event_key,
        event_map=event_map,
        success_event=success_event,
        failure_event=failure_event,
        thread_id=thread_id if isinstance(thread_id, str) else None,
        phase=phase if isinstance(phase, str) else "graph",
        payload_keys=payload_keys if isinstance(payload_keys, list) else None,
    )
