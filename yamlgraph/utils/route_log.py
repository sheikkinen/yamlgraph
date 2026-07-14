"""Route decision log — one JSON line per routing decision (FR-723).

The ``yamlgraph.route`` logger namespace is **public API**: downstream
projects attach handlers/filters there to consume route facts.

Opt-in surfaces (zero overhead when off — the guard runs before any
serialization):

- env ``YAMLGRAPH_ROUTE_LOG=1`` — emit on the logger only
- env ``YAMLGRAPH_ROUTE_LOG=<path>`` — emit on the logger AND append raw
  JSON lines to ``<path>`` (a route.jsonl for ``graph export --overlay``)
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
from contextlib import contextmanager, suppress
from contextvars import ContextVar

ROUTE_LOGGER_NAME = "yamlgraph.route"
ENV_VAR = "YAMLGRAPH_ROUTE_LOG"

route_logger = logging.getLogger(ROUTE_LOGGER_NAME)
# INFO records must reach attached handlers even when the root logger
# stays at WARNING; with no handlers attached, lines go nowhere (opt-in).
route_logger.setLevel(logging.INFO)

_thread_id_var: ContextVar[str | None] = ContextVar(
    "yamlgraph_route_thread_id", default=None
)
_flag_enabled = False
_file_handlers: dict[str, logging.Handler] = {}

_OFF_VALUES = {"", "0", "false", "no"}
_ON_VALUES = {"1", "true", "yes"}


def enable_route_log(enabled: bool = True) -> None:
    """Enable/disable emission process-wide (observability.route_log flag)."""
    global _flag_enabled
    _flag_enabled = enabled


def route_log_enabled() -> bool:
    """True when the graph flag or the YAMLGRAPH_ROUTE_LOG env opts in."""
    if _flag_enabled:
        return True
    return os.environ.get(ENV_VAR, "").strip().lower() not in _OFF_VALUES


def reset_route_log() -> None:
    """Reset the flag and detach file sinks (test isolation)."""
    enable_route_log(False)
    for handler in _file_handlers.values():
        route_logger.removeHandler(handler)
        handler.close()
    _file_handlers.clear()


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


def emit_route(
    node: str, value: str, target: object, fan_out: int | None = None
) -> None:
    """Emit one route decision line. No cost when disabled; never raises."""
    if not route_log_enabled():
        return
    with suppress(Exception):
        _ensure_file_sink()
        line: dict[str, object] = {
            "event": "route",
            "node": node,
            "value": value,
            "target": _target_name(target),
            "thread_id": _thread_id_var.get(),
        }
        if fan_out is not None:
            line["fan_out"] = fan_out
        route_logger.info(json.dumps(line, ensure_ascii=False))


def _target_name(target: object) -> str:
    """Normalize the LangGraph END sentinel to the authored name."""
    name = str(target)
    return "END" if name == "__end__" else name


def _ensure_file_sink() -> None:
    """Attach a raw-JSON file handler when the env value is a path."""
    value = os.environ.get(ENV_VAR, "").strip()
    if not value or value.lower() in _ON_VALUES | _OFF_VALUES:
        return
    if value in _file_handlers:
        return
    handler = logging.FileHandler(value, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    handler.setLevel(logging.INFO)
    route_logger.addHandler(handler)
    _file_handlers[value] = handler


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
    "emit_route",
]
