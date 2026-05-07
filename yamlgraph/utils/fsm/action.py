"""Shared fire-and-forget FSM action for YAMLGraph execution."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from yamlgraph.utils.fsm.graph_runner import run_and_dispatch
from yamlgraph.utils.fsm.helpers import resolve_context_ref

logger = logging.getLogger(__name__)

_GUARD_PREFIX = "_graph_running_"
_MISSING_FSM_EXTRA = (
    "statemachine-engine not installed. Install with: pip install yamlgraph[fsm]"
)

try:
    from statemachine_engine.actions.base import BaseAction
except ImportError as exc:  # pragma: no cover - exercised in environments without fsm
    _FSM_IMPORT_ERROR = exc

    class BaseAction:  # type: ignore[no-redef]
        """Fallback base class that raises a clear optional-extra error."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise ImportError(_MISSING_FSM_EXTRA) from _FSM_IMPORT_ERROR


class YamlgraphAsyncAction(BaseAction):
    """Fire-and-forget YAMLGraph pipeline via ``asyncio.create_task``."""

    GRAPH_BASE_DIR: Path | None = None

    def _resolve_graph_path(self, graph_path: str) -> str:
        raw = Path(graph_path)
        if raw.is_absolute() or raw.exists():
            return str(raw)

        candidate_roots = [Path.cwd()]
        if self.GRAPH_BASE_DIR is not None:
            candidate_roots.insert(0, self.GRAPH_BASE_DIR)

        for root in candidate_roots:
            candidate = root / graph_path
            if candidate.exists():
                return str(candidate)

        return str(raw)

    async def execute(self, context: dict[str, Any]) -> str | None:
        """Launch graph in the background and return immediately."""
        params = self.config.get("params", {})
        current_state = context.get("current_state", "unknown")
        guard_key = f"{_GUARD_PREFIX}{current_state}"

        stale_guards = [
            key
            for key in list(context)
            if key.startswith(_GUARD_PREFIX) and key != guard_key
        ]
        for key in stale_guards:
            del context[key]

        if context.get(guard_key):
            return None

        graph_path = params.get("graph")
        if not graph_path:
            logger.error("yamlgraph_async: no graph specified in params")
            return params.get("failure", "failed")

        input_key = params.get("input_key", "input")
        input_value = resolve_context_ref(
            params.get("input_value") or context.get(input_key, ""),
            context,
            missing="",
        )
        output_key = params.get("output_key", "yamlgraph_result")
        event_key = params.get("event_key") or output_key
        event_map = params.get("event_map", {})
        success_event = params.get("success", "completed")
        failure_event = params.get("failure", "failed")
        thread_id = resolve_context_ref(params.get("thread_id"), context)

        initial_state: dict[str, Any] = {input_key: input_value}
        for key, value in params.get("variables", {}).items():
            initial_state[key] = resolve_context_ref(value, context)

        machine_name = context.get("machine_name", "unknown")
        resolved_graph = self._resolve_graph_path(str(graph_path))
        logger.info(
            "🚀 yamlgraph_async: launching %s in state %s",
            resolved_graph,
            current_state,
        )

        asyncio.create_task(
            run_and_dispatch(
                graph_path=resolved_graph,
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
