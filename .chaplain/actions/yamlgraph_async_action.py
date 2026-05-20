import asyncio
import logging
import re
from pathlib import Path
from typing import Any

from yamlgraph.utils.fsm import YamlgraphAsyncAction as _SharedYamlgraphAsyncAction
from yamlgraph.utils.fsm.action import run_legacy_yamlgraph_async
from yamlgraph.utils.fsm.event_sender import send_event

_PLACEHOLDER_PATTERN = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")
_EXACT_PLACEHOLDER_PATTERN = re.compile(r"^\{[A-Za-z_][A-Za-z0-9_]*\}$")
_NORMALIZE_EMPTY_ON_UNRESOLVED = {
    "precommit_output",
    "validate_gate_output",
    "fr_path",
}
_JUDGE_WRITEBACK_MTIME_KEY = "_judge_writeback_mtime_before"
logger = logging.getLogger(__name__)


def _is_unresolved_placeholder(value: str) -> bool:
    return bool(_EXACT_PLACEHOLDER_PATTERN.fullmatch(value))


def _interpolate_legacy(value: Any, context: dict[str, Any]) -> Any:
    if not isinstance(value, str):
        return value

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key in context:
            return str(context[key])
        return match.group(0)

    return _PLACEHOLDER_PATTERN.sub(_replace, value)


def _resolve_fr_path(context: dict[str, Any] | None) -> Path | None:
    if not isinstance(context, dict):
        return None

    fr_path = context.get("fr_path")
    if not isinstance(fr_path, str) or not fr_path:
        return None

    fr = Path(fr_path)
    if fr.is_absolute():
        return fr

    wt_dir = context.get("wt_dir")
    main_dir = context.get("main_dir")

    if isinstance(wt_dir, str) and wt_dir:
        wt = Path(wt_dir)
        if wt.is_absolute():
            return wt / fr
        if isinstance(main_dir, str) and main_dir:
            return Path(main_dir) / wt / fr

    if isinstance(main_dir, str) and main_dir:
        return Path(main_dir) / fr

    return fr


class YamlgraphAsyncAction(_SharedYamlgraphAsyncAction):
    """Chaplain adapter over the shared FSM bridge."""

    GRAPH_BASE_DIR = Path(__file__).resolve().parents[2]

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(dict(config or {}))
        self._runtime_main_dir: str | None = None

    async def execute(self, context: dict[str, Any]) -> str | None:
        _ = asyncio.current_task()
        if "current_state" not in context:
            return await run_legacy_yamlgraph_async(
                config=self.config,
                context=context,
                logger_obj=logger,
            )

        main_dir = context.get("main_dir")
        self._runtime_main_dir = (
            str(main_dir) if isinstance(main_dir, str) and main_dir else None
        )
        try:
            return await super().execute(context)
        finally:
            self._runtime_main_dir = None

    def on_launch(self, _snap: Any, context: dict[str, Any]) -> None:
        if context.get("current_state") != "judge":
            return

        fr = _resolve_fr_path(context)
        if fr is None or not fr.exists():
            context[_JUDGE_WRITEBACK_MTIME_KEY] = None
            return

        context[_JUDGE_WRITEBACK_MTIME_KEY] = fr.stat().st_mtime_ns

    def pre_dispatch(
        self,
        _snap: Any,
        event: str,
        _payload: dict[str, Any] | None,
        context: dict[str, Any] | None,
    ) -> bool:
        if not isinstance(context, dict):
            return True

        if context.get("current_state") != "judge":
            return True

        if event not in {"revise", "reject"}:
            return True

        machine_name = self.get_machine_name(context)
        fr = _resolve_fr_path(context)
        mtime_before = context.get(_JUDGE_WRITEBACK_MTIME_KEY)

        if fr is None or not fr.exists() or mtime_before is None:
            logger.error(
                "[%s] judge writeback guard: missing fr_path or baseline mtime",
                machine_name,
            )
            send_event(machine_name, "error")
            return False

        if fr.stat().st_mtime_ns == mtime_before:
            logger.error(
                "[%s] judge writeback guard: FR file unchanged after %s verdict: %s",
                machine_name,
                event,
                fr,
            )
            send_event(machine_name, "error")
            return False

        return True

    def _resolve_graph_path(self, graph_path: str) -> str:
        raw = Path(graph_path)
        if raw.is_absolute():
            return str(raw)
        if self._runtime_main_dir:
            return str(Path(self._runtime_main_dir) / raw)
        return super()._resolve_graph_path(graph_path)

    def pre_snapshot(self, params: dict[str, Any], context: dict[str, Any]) -> None:
        graph = params.get("graph")
        main_dir = context.get("main_dir")
        if (
            isinstance(graph, str)
            and isinstance(main_dir, str)
            and graph
            and not Path(graph).is_absolute()
        ):
            params["graph"] = str(Path(main_dir) / Path(graph))

        variables = params.get("variables")
        if not isinstance(variables, dict):
            return

        resolved_variables: dict[str, Any] = {}
        for key, value in variables.items():
            resolved = _interpolate_legacy(value, context)
            if (
                key in _NORMALIZE_EMPTY_ON_UNRESOLVED
                and isinstance(resolved, str)
                and _is_unresolved_placeholder(resolved)
            ):
                resolved = ""
            resolved_variables[key] = resolved

        params["variables"] = resolved_variables


__all__ = ["YamlgraphAsyncAction"]
