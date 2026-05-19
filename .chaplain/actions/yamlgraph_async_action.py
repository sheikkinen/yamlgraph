import asyncio
import logging
import re
from pathlib import Path
from typing import Any

from yamlgraph.utils.fsm import YamlgraphAsyncAction as _SharedYamlgraphAsyncAction
from yamlgraph.utils.fsm.action import run_legacy_yamlgraph_async

_PLACEHOLDER_PATTERN = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")
_EXACT_PLACEHOLDER_PATTERN = re.compile(r"^\{[A-Za-z_][A-Za-z0-9_]*\}$")
_NORMALIZE_EMPTY_ON_UNRESOLVED = {"precommit_output", "validate_gate_output"}
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
