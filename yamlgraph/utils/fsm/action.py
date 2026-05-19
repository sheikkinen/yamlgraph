"""Shared fire-and-forget FSM action for YAMLGraph execution."""

from __future__ import annotations

import asyncio
import logging
import re
from pathlib import Path
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from yamlgraph.utils.fsm.graph_runner import run_and_dispatch
from yamlgraph.utils.fsm.snapshot import SnapshotParams, snapshot_params

logger = logging.getLogger(__name__)

_GUARD_PREFIX = "_graph_running_"
_EXACT_PLACEHOLDER_PATTERN = re.compile(r"^\{[A-Za-z_][A-Za-z0-9_]*\}$")
_MISSING_FSM_EXTRA = (
    "statemachine-engine not installed. Install with: pip install yamlgraph[fsm]"
)
_NORMALIZE_EMPTY_ON_UNRESOLVED = {"precommit_output", "validate_gate_output"}

# Keys stripped before ActionConfig validation.
# Two categories:
#   engine-injected: "type", "params" — added by statemachine_engine, not authored
#   author-annotation: "description" — human label, no runtime meaning
_STRIP_BEFORE_VALIDATE: frozenset[str] = frozenset({"type", "params", "description"})


class ActionConfig(BaseModel):
    """Validated contract for a yamlgraph_async FSM action payload.

    Accepts both flat YAML syntax (vars, error) and canonical names (variables,
    failure) via AliasChoices. Unknown keys are rejected at parse time.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    # Required
    graph: str

    # Input/output wiring
    input_key: str = "input"
    input_value: str | None = None
    output_key: str = "yamlgraph_result"
    event_key: str | None = None
    payload_keys: list[str] | None = None

    # Routing
    event_map: dict[str, str] = Field(default_factory=dict)
    success: str = "completed"
    failure: str = Field(
        "failed",
        validation_alias=AliasChoices("failure", "error"),
    )

    # Graph execution context
    variables: dict[str, str] = Field(
        default_factory=dict,
        validation_alias=AliasChoices("variables", "vars"),
    )
    thread_id: str | None = None
    phase: str = "graph"
    timeout: int = 300

    @field_validator("event_map", mode="before")
    @classmethod
    def _normalize_event_map(cls, v: Any) -> dict[str, str]:
        """Lowercase and strip all event_map keys for case-insensitive matching."""
        if not isinstance(v, dict):
            return {}
        return {
            str(k).strip().lower(): str(val) for k, val in v.items() if str(k).strip()
        }


try:
    from statemachine_engine.actions.base import BaseAction
except ImportError as exc:  # pragma: no cover - exercised in environments without fsm
    _FSM_IMPORT_ERROR = exc

    class BaseAction:  # type: ignore[no-redef]
        """Placeholder raised when fsm extra is missing at import time."""

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

    def on_launch(self, _snap: SnapshotParams, _context: dict[str, Any]) -> None:
        """Lifecycle hook called after snapshot resolution and before task launch."""

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
        # Strip engine envelope keys; prefer params sub-dict if graph not at top level
        raw_payload: dict[str, Any] = {
            k: v for k, v in self.config.items() if k not in _STRIP_BEFORE_VALIDATE
        }
        if not raw_payload.get("graph") and isinstance(self.config.get("params"), dict):
            raw_payload = dict(self.config["params"])

        from pydantic import ValidationError

        try:
            action_config = ActionConfig.model_validate(raw_payload)
        except ValidationError as exc:
            logger.error("yamlgraph_async: invalid action config: %s", exc)
            return raw_payload.get("failure") or raw_payload.get("error", "error")

        params: dict[str, Any] = action_config.model_dump(by_alias=False)
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
        self.on_launch(snapshot, context)

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


def _is_legacy_placeholder(value: str) -> bool:
    return bool(_EXACT_PLACEHOLDER_PATTERN.fullmatch(value))


async def run_legacy_yamlgraph_async(
    *,
    config: dict[str, Any],
    context: dict[str, Any],
    logger_obj: logging.Logger | None = None,
) -> str:
    """Execute legacy argv contract and route stdout with legacy event_map rules."""
    log = logger_obj or logger

    graph = config.get("graph", "")
    var_dict = config.get("vars", {})
    success_event = config.get("success", "done")
    error_event = config.get("error", "error")
    event_map = config.get("event_map", {})
    timeout = config.get("timeout", 300)
    machine_name = context.get("machine_name", "watcher-pipeline-v2")

    main_dir = context.get("main_dir", ".")
    graph_path = f"{main_dir}/{graph}" if not str(graph).startswith("/") else str(graph)

    cmd_parts = ["yamlgraph", "graph", "run", graph_path, "--full"]
    if isinstance(var_dict, dict):
        for key, value in var_dict.items():
            resolved = str(value)
            for ctx_key, ctx_val in context.items():
                resolved = resolved.replace(f"{{{ctx_key}}}", str(ctx_val))
            if key in _NORMALIZE_EMPTY_ON_UNRESOLVED and _is_legacy_placeholder(
                resolved
            ):
                resolved = ""
            cmd_parts.extend(["--var", f"{key}={resolved}"])
    log.info("[%s] yamlgraph argv=%s", machine_name, cmd_parts[:20])

    wt_dir = context.get("wt_dir")
    cwd = f"{main_dir}/{wt_dir}" if wt_dir else main_dir
    log.debug("[%s] cwd=%s", machine_name, cwd)

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd_parts,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except TimeoutError:
        log.error("[%s] yamlgraph timed out after %ss", machine_name, timeout)
        return error_event
    except Exception as exc:
        log.error("[%s] yamlgraph failed: %s", machine_name, exc)
        return error_event

    stdout_text = stdout.decode().strip()
    stderr_text = stderr.decode().strip()

    log.info(
        "[%s] yamlgraph exit=%s, stdout=%s chars, stderr=%s chars",
        machine_name,
        process.returncode,
        len(stdout_text),
        len(stderr_text),
    )

    if stderr_text:
        log.warning("[%s] yamlgraph stderr: %s", machine_name, stderr_text[:2000])

    if process.returncode != 0:
        log.error(
            "[%s] yamlgraph exit %s: %s",
            machine_name,
            process.returncode,
            stderr_text[:300],
        )
        return error_event

    if isinstance(event_map, dict) and event_map:
        for pattern, event in event_map.items():
            if pattern in stdout_text:
                log.info(
                    "[%s] event_map matched '%s' → %s", machine_name, pattern, event
                )
                log.debug("[%s] yamlgraph stdout: %s", machine_name, stdout_text[:2000])
                return event
        log.warning(
            "[%s] No event_map match in output: %s", machine_name, stdout_text[:2000]
        )

    log.debug("[%s] yamlgraph stdout: %s", machine_name, stdout_text[:2000])
    return success_event
