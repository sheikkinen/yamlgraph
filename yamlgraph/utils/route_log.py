"""Route decision log — one JSON line per routing decision (FR-723).

The ``yamlgraph.route`` logger namespace is **public API**: downstream
projects attach handlers/filters there to consume route facts.

Opt-in surfaces (zero overhead when off — the guard runs before any
serialization):

- env ``YAMLGRAPH_ROUTE_LOG=1`` — emit on the logger only
- env ``YAMLGRAPH_ROUTE_LOG=<path>`` — emit on the logger AND append raw
    JSON lines to ``<path>`` (a route.jsonl for ``graph export --overlay``)
    where relative paths resolve against the process working directory
- env ``YAMLGRAPH_ROUTE_LOG=<dir>/`` (or existing dir path) — append raw
    JSON lines to ``<dir>/route.jsonl``
- graph YAML ``observability.route_log: true`` — enabled at compile time
  (process-wide)

Line grammar (frozen — ninchat_voice's parser migrates onto it, NC-374)::

    {"event":"route","node":<source>,"value":<matched condition|route|
     loop_exit|no_match|default>,"target":<target>,"thread_id":<or null>}

Map fan-out decisions add ``"fan_out":<count>`` and carry the map-node
name as target — never ``repr(Send)``, whose payloads carry state content
(R-2: privacy by construction).

``thread_id``: routing seams receive state only; the invoking thread id is
carried by a contextvar set by the run entrypoints around graph invocation
(R-1). Absent an entrypoint, the field is null — never fabricated.

Emission never raises: a forensic channel must not break the run.
"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

import yaml

from yamlgraph.observability.otel import generate_run_id
from yamlgraph.utils.artifact_hash import compute_artifact_hash
from yamlgraph.utils.regulated_evidence import (
    EvidenceLossError,
    preflight_regulated_sink,
)
from yamlgraph.utils.regulated_evidence import (
    resolve_regulated_policy as _resolve_regulated_policy,
)

ROUTE_LOGGER_NAME = "yamlgraph.route"
ENV_VAR = "YAMLGRAPH_ROUTE_LOG"

route_logger = logging.getLogger(ROUTE_LOGGER_NAME)
# INFO records must reach attached handlers even when the root logger
# stays at WARNING; with no handlers attached, lines go nowhere (opt-in).
route_logger.setLevel(logging.INFO)

_thread_id_var: ContextVar[str | None] = ContextVar(
    "yamlgraph_route_thread_id", default=None
)
_run_var: ContextVar[RouteRun | None] = ContextVar("yamlgraph_route_run", default=None)
_sink_var: ContextVar[Path | None] = ContextVar("yamlgraph_route_sink", default=None)
_enabled_var: ContextVar[bool | None] = ContextVar(
    "yamlgraph_route_enabled_override", default=None
)
_flag_enabled = False
_warned_bad_targets: set[str] = set()

_OFF_VALUES = {"", "0", "false", "no"}
_ON_VALUES = {"1", "true", "yes"}
_DEFAULT_ROUTE_FILENAME = "route.jsonl"
_last_dropped_events = 0


@dataclass
class RouteRun:
    """Mutable route-evidence state scoped to one graph invocation."""

    run_id: str
    dropped_events: int = 0


def enable_route_log(enabled: bool = True) -> None:
    """Enable/disable emission process-wide (observability.route_log flag)."""
    global _flag_enabled
    _flag_enabled = enabled


def route_log_enabled() -> bool:
    """True when the graph flag or the YAMLGRAPH_ROUTE_LOG env opts in."""
    override = _enabled_var.get()
    if override is not None:
        return override
    if _flag_enabled:
        return True
    return os.environ.get(ENV_VAR, "").strip().lower() not in _OFF_VALUES


def reset_route_log() -> None:
    """Reset the flag and detach file sinks (test isolation)."""
    global _last_dropped_events
    enable_route_log(False)
    _last_dropped_events = 0
    _warned_bad_targets.clear()


def current_route_thread_id() -> str | None:
    """The invoking thread id visible at the routing seam, or None."""
    return _thread_id_var.get()


@contextmanager
def route_thread_id(thread_id: str | None) -> Iterator[None]:
    """Carry the invoking thread id across routing seams (R-1 contextvar)."""
    token = _thread_id_var.set(thread_id)
    try:
        yield
    finally:
        _thread_id_var.reset(token)


def route_thread_id_from_config(config: dict | None):
    """route_thread_id() reading LangGraph config['configurable']['thread_id'].

    Run entrypoints wrap graph invocation with this; a missing thread id
    yields null route lines — never fabricated.
    """
    configurable = (config or {}).get("configurable") or {}
    return route_thread_id(configurable.get("thread_id"))


def route_log_dropped_count() -> int:
    """Return the active run's loss count or the last completed run's count."""
    run = _run_var.get()
    return run.dropped_events if run is not None else _last_dropped_events


@contextmanager
def route_run_context(
    graph_path: str | Path,
    *,
    thread_id: str | None = None,
    run_id: str | None = None,
) -> Iterator[RouteRun]:
    """Emit one bound run header and run-end record around graph execution."""
    global _last_dropped_events
    run = RouteRun(run_id=run_id or generate_run_id())
    graph_path = Path(graph_path).resolve()
    config = yaml.safe_load(graph_path.read_text(encoding="utf-8")) or {}
    observability = config.get("observability") or {}
    policy = (
        resolve_regulated_policy(observability, graph_path.as_posix())
        if observability.get("profile") == "regulated"
        else None
    )
    sink = (
        preflight_regulated_sink(policy, run.run_id)
        if policy and policy.enabled
        else None
    )
    header: dict[str, object] = {
        "event": "run",
        "run_id": run.run_id,
        "artifact_hash": compute_artifact_hash(graph_path),
        "graph": graph_path.as_posix(),
        "yamlgraph_version": version("yamlgraph"),
        "thread_id": thread_id,
        "started_at": _timestamp(),
    }
    if observability.get("judgement_ref"):
        header["judgement"] = observability["judgement_ref"]
    run_token = _run_var.set(run)
    thread_token = _thread_id_var.set(thread_id)
    sink_token = _sink_var.set(sink)
    enabled_token = _enabled_var.set(policy.enabled if policy else None)
    try:
        if route_log_enabled():
            _emit_record(header)
        yield run
    finally:
        if route_log_enabled():
            _emit_record(
                {
                    "event": "run_end",
                    "run_id": run.run_id,
                    "ended_at": _timestamp(),
                    "dropped_events": run.dropped_events,
                }
            )
        _last_dropped_events = run.dropped_events
        _enabled_var.reset(enabled_token)
        _sink_var.reset(sink_token)
        _thread_id_var.reset(thread_token)
        _run_var.reset(run_token)
        if policy and policy.strict and run.dropped_events:
            raise EvidenceLossError(run.dropped_events, policy.sink_dir)


def resolve_regulated_policy(observability: dict[str, object], graph: str):
    """Public policy seam with the route logger bound for diagnostics."""
    return _resolve_regulated_policy(observability, graph, route_logger)


def emit_route(
    node: str, value: str, target: object, fan_out: int | None = None
) -> None:
    """Emit one route decision line. No cost when disabled; never raises."""
    if not route_log_enabled():
        return
    line: dict[str, object] = {
        "event": "route",
        "node": node,
        "value": value,
        "target": _target_name(target),
        "thread_id": _thread_id_var.get(),
        "ts": _timestamp(),
    }
    if fan_out is not None:
        line["fan_out"] = fan_out
    _emit_record(line)


def _timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _emit_record(record: dict[str, object]) -> None:
    """Deliver one record without raising; account one loss on failure."""
    try:
        _deliver_record(record)
    except Exception:
        run = _run_var.get()
        if run is not None:
            run.dropped_events += 1
        else:
            global _last_dropped_events
            _last_dropped_events += 1


def _deliver_record(record: dict[str, object]) -> None:
    line = json.dumps(record, ensure_ascii=False)
    route_logger.info(line)
    sink = _sink_var.get() or _configured_sink_path()
    if sink is not None:
        with sink.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")


def _target_name(target: object) -> str:
    """Normalize the LangGraph END sentinel to the authored name."""
    name = str(target)
    return "END" if name == "__end__" else name


def _configured_sink_path() -> Path | None:
    value = os.environ.get(ENV_VAR, "").strip()
    if not value or value.lower() in _ON_VALUES | _OFF_VALUES:
        return None
    return _resolve_sink_path(value)


def _resolve_sink_path(value: str) -> Path | None:
    """Resolve env target to a concrete file path or return None on failure."""
    raw = Path(value)
    resolved = raw if raw.is_absolute() else Path.cwd() / raw

    if _directory_mode(value, resolved):
        directory = resolved
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            _warn_invalid_target_once(
                value, f"cannot create directory '{directory}'", exc
            )
            return None
        return directory / _DEFAULT_ROUTE_FILENAME

    if resolved.exists() and not resolved.is_file():
        _warn_invalid_target_once(
            value,
            "target exists but is not a regular file",
        )
        return None

    try:
        resolved.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        _warn_invalid_target_once(
            value,
            f"cannot create parent directory '{resolved.parent}'",
            exc,
        )
        return None
    return resolved


def _directory_mode(raw_value: str, resolved: Path) -> bool:
    """Directory mode: existing directory OR trailing path separator intent."""
    if resolved.exists() and resolved.is_dir():
        return True
    if raw_value.endswith(os.sep):
        return True
    altsep = os.altsep
    return bool(altsep and raw_value.endswith(altsep))


def _warn_invalid_target_once(
    value: str, message: str, exc: OSError | None = None
) -> None:
    """Warn once per raw env value; keep route emission resilient."""
    if value in _warned_bad_targets:
        return
    _warned_bad_targets.add(value)
    if exc is None:
        route_logger.warning("YAMLGRAPH_ROUTE_LOG='%s' ignored: %s", value, message)
        return
    route_logger.warning(
        "YAMLGRAPH_ROUTE_LOG='%s' ignored: %s (%s)",
        value,
        message,
        exc,
    )


__all__ = [
    "ROUTE_LOGGER_NAME",
    "ENV_VAR",
    "route_logger",
    "enable_route_log",
    "route_log_enabled",
    "reset_route_log",
    "current_route_thread_id",
    "route_thread_id",
    "route_thread_id_from_config",
    "route_run_context",
    "route_log_dropped_count",
    "resolve_regulated_policy",
    "EvidenceLossError",
    "compute_artifact_hash",
    "emit_route",
]
