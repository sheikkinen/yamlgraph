"""Regulated route-evidence policy and sink preflight (FR-808)."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from yamlgraph.models import ErrorType, PipelineError

ENV_VAR = "YAMLGRAPH_ROUTE_LOG"
OVERRIDE_ENV_VAR = "YAMLGRAPH_ROUTE_LOG_OVERRIDE"
_OFF_VALUES = {"", "0", "false", "no"}
_ON_VALUES = {"1", "true", "yes"}


@dataclass(frozen=True)
class RegulatedPolicy:
    enabled: bool
    sink_dir: Path
    strict: bool


class EvidenceLossError(RuntimeError):
    """Strict regulated run lost evidence at the route-log boundary."""

    def __init__(self, dropped_events: int, sink: Path):
        self.pipeline_error = PipelineError(
            type=ErrorType.UNKNOWN_ERROR,
            message=f"route evidence loss: dropped_events={dropped_events}, sink={sink}",
            node="route_log",
            details={"dropped_events": dropped_events, "sink": str(sink)},
        )
        super().__init__(self.pipeline_error.message)


def resolve_regulated_policy(
    observability: dict[str, object], graph: str, logger: logging.Logger
) -> RegulatedPolicy:
    """Resolve regulated emission and env override precedence."""
    sink_dir = Path(str(observability["route_log_sink"]))
    strict = bool(observability.get("strict_evidence", False))
    raw_route_log = os.environ.get(ENV_VAR)
    disable = raw_route_log is not None and raw_route_log.strip().lower() in _OFF_VALUES
    override = os.environ.get(OVERRIDE_ENV_VAR, "").strip().lower()
    override_requested = override in _ON_VALUES
    if disable and strict:
        raise ValueError("strict_evidence forbids YAMLGRAPH_ROUTE_LOG disable requests")
    if disable and override_requested:
        logger.warning(
            "regulated route evidence disable recorded_exception "
            "profile=regulated graph=%s sink=%s env_source=%s "
            "override=true recorded_exception=true",
            graph,
            sink_dir,
            ENV_VAR,
        )
        return RegulatedPolicy(enabled=False, sink_dir=sink_dir, strict=False)
    if disable:
        logger.warning(
            "regulated route evidence disable ignored "
            "profile=regulated graph=%s sink=%s env_source=%s override=false",
            graph,
            sink_dir,
            ENV_VAR,
        )
    return RegulatedPolicy(enabled=True, sink_dir=sink_dir, strict=strict)


def preflight_regulated_sink(policy: RegulatedPolicy, run_id: str) -> Path:
    """Create and verify the regulated per-run sink before execution."""
    directory = policy.sink_dir.resolve()
    if directory.exists() and not directory.is_dir():
        raise ValueError(f"route_log_sink must be a directory: {directory}")
    try:
        directory.mkdir(parents=True, exist_ok=True)
        probe = directory / ".yamlgraph-write-probe"
        probe.write_text("", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        raise ValueError(f"route_log_sink is not writable: {directory}") from exc
    return directory / f"{run_id}.route.jsonl"


__all__ = [
    "EvidenceLossError",
    "RegulatedPolicy",
    "preflight_regulated_sink",
    "resolve_regulated_policy",
]
