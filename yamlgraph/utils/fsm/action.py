"""Shared fire-and-forget FSM action for YAMLGraph execution."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from yamlgraph.utils.fsm.graph_runner import run_and_dispatch
from yamlgraph.utils.fsm.snapshot import SnapshotParams, snapshot_params

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

    def pre_snapshot(self, _params: dict[str, Any], _context: dict[str, Any]) -> None:
        """Lifecycle hook called before snapshot materialization."""

    def on_success(
        self,
        _snap: SnapshotParams | None,
        _event: str,
        _elapsed_ms: int,
        _context: dict[str, Any] | None,
    ) -> None:
        """Lifecycle hook called after successful graph execution."""

    def on_error(
        self,
        _snap: SnapshotParams | None,
        _exc: Exception,
        _elapsed_ms: int,
        _context: dict[str, Any] | None,
    ) -> None:
        """Lifecycle hook called when graph execution fails."""

    def pre_dispatch(
        self,
        _snap: SnapshotParams | None,
        _event: str,
        _payload: dict[str, Any] | None,
        _context: dict[str, Any] | None,
    ) -> bool:
        """Lifecycle hook called before FSM event dispatch."""
        return True

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

        self.pre_snapshot(params, context)
        try:
            snapshot = snapshot_params(
                params, context, project_root=self.GRAPH_BASE_DIR
            )
        except ValueError:
            logger.error("yamlgraph_async: no graph specified in params")
            return params.get("failure", "failed")

        machine_name = context.get("machine_name", "unknown")
        snapshot.graph_path = self._resolve_graph_path(snapshot.graph_path)
        logger.info(
            "🚀 yamlgraph_async: launching %s in state %s",
            snapshot.graph_path,
            current_state,
        )

        asyncio.create_task(
            run_and_dispatch(
                graph_path=snapshot.graph_path,
                initial_state=snapshot.initial_state,
                input_key=snapshot.input_key,
                output_key=snapshot.output_key,
                event_key=snapshot.event_key,
                event_map=snapshot.event_map,
                success_event=snapshot.success_event,
                failure_event=snapshot.failure_event,
                machine_name=machine_name,
                thread_id=snapshot.thread_id,
                context=context,
                guard_key=guard_key,
                snapshot=snapshot,
                pre_dispatch_fn=self.pre_dispatch,
                on_success_fn=self.on_success,
                on_error_fn=self.on_error,
            )
        )

        context[guard_key] = True
        return None
