#!/usr/bin/env python3
"""Extract normalized process-mining events from Copilot instrumentation artifacts."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class CopilotProcessEvent(BaseModel):
    """Normalized process-mining event model."""

    case_id: str = Field(description="Instrumentation run identifier")
    phase: str = Field(description="Execution phase (plan, implement)")
    event_type: str = Field(description="Event kind")
    timestamp: str = Field(description="ISO-8601 timestamp")
    summary: str = Field(description="Human-readable event summary")
    source: str = Field(description="Artifact origin (otel, git)")
    success: bool = Field(description="Whether operation succeeded")
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured event payload",
    )


def _iso_from_start_time(value: list | str | int | None, fallback: datetime) -> str:
    if value is None:
        return fallback.astimezone(UTC).isoformat()
    if isinstance(value, list) and len(value) == 2:
        seconds, nanos = int(value[0]), int(value[1])
        dt = datetime.fromtimestamp(seconds, tz=UTC).replace(microsecond=nanos // 1000)
        return dt.isoformat()
    nanos = int(value)
    seconds, rem_nanos = divmod(nanos, 1_000_000_000)
    dt = datetime.fromtimestamp(seconds, tz=UTC).replace(microsecond=rem_nanos // 1000)
    return dt.isoformat()


def _event(
    case_id: str,
    phase: str,
    event_type: str,
    timestamp: str,
    summary: str,
    source: str,
    success: bool,
    details: dict[str, Any] | None = None,
) -> CopilotProcessEvent:
    return CopilotProcessEvent(
        case_id=case_id,
        phase=phase,
        event_type=event_type,
        timestamp=timestamp,
        summary=summary,
        source=source,
        success=success,
        details=details or {},
    )


def _derive_success(result: Any) -> bool:
    if not isinstance(result, dict):
        return True
    if isinstance(result.get("success"), bool):
        return result["success"]
    exit_code = result.get("exit_code")
    return (exit_code == 0) if isinstance(exit_code, int) else True


def _read_str(arguments: Any, key: str) -> str | None:
    if not isinstance(arguments, dict):
        return None
    value = arguments.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _tool_target(tool_name: str, arguments: Any) -> str | None:
    if not tool_name:
        return None
    if tool_name == "bash":
        command = _read_str(arguments, "command")
        return f"bash:{command}" if command else "bash"
    if tool_name in {"create", "edit"}:
        path = _read_str(arguments, "path")
        return f"{tool_name}:{path}" if path else tool_name
    return tool_name


def _extract_flat_span_events(
    case_id: str,
    phase: str,
    payload: dict[str, Any],
    fallback_time: datetime,
    failed_targets: set[str],
) -> list[CopilotProcessEvent]:
    span_name = str(payload.get("name", "unnamed-span"))
    timestamp = _iso_from_start_time(payload.get("startTime"), fallback_time)
    attributes = payload.get("attributes")
    attr_dict = attributes if isinstance(attributes, dict) else {}
    tool_name = str(attr_dict.get("tool_name", "")).strip()
    arguments = attr_dict.get("arguments")
    result = attr_dict.get("result")
    success = _derive_success(result)
    target = _tool_target(tool_name, arguments)

    details: dict[str, Any] = {"span_name": span_name}
    if tool_name:
        details["tool_name"] = tool_name
    if isinstance(arguments, dict):
        details["arguments"] = arguments
    if isinstance(result, dict):
        details["result"] = result

    events = [
        _event(
            case_id,
            phase,
            "otel_span",
            timestamp,
            f"OTel span '{span_name}'",
            "otel",
            success,
            details,
        )
    ]

    if target and success and target in failed_targets:
        events.append(
            _event(
                case_id,
                phase,
                "retry",
                timestamp,
                f"Retry succeeded for {target}",
                "otel",
                True,
                {"target": target, "tool_name": tool_name},
            )
        )
        failed_targets.remove(target)

    if tool_name == "report_intent":
        intent = _read_str(arguments, "intent")
        if intent:
            events.append(
                _event(
                    case_id,
                    phase,
                    "phase_marker",
                    timestamp,
                    f"Phase marker: {intent}",
                    "otel",
                    True,
                    {"intent": intent},
                )
            )

    if tool_name == "bash":
        command = _read_str(arguments, "command")
        if command:
            lower = command.lower()
            if "pytest" in lower:
                events.append(
                    _event(
                        case_id,
                        phase,
                        "test_run",
                        timestamp,
                        f"Test command: {command}",
                        "otel",
                        success,
                        {"command": command},
                    )
                )
            if "ruff" in lower or "yamlgraph graph lint" in lower:
                events.append(
                    _event(
                        case_id,
                        phase,
                        "lint_run",
                        timestamp,
                        f"Lint command: {command}",
                        "otel",
                        success,
                        {"command": command},
                    )
                )

    if tool_name == "create":
        path = _read_str(arguments, "path")
        if path:
            events.append(
                _event(
                    case_id,
                    phase,
                    "file_create",
                    timestamp,
                    f"Created file: {path}",
                    "otel",
                    success,
                    {"path": path},
                )
            )
    if tool_name == "edit":
        path = _read_str(arguments, "path")
        if path:
            events.append(
                _event(
                    case_id,
                    phase,
                    "file_edit",
                    timestamp,
                    f"Edited file: {path}",
                    "otel",
                    success,
                    {"path": path},
                )
            )

    if not success:
        failure_details: dict[str, Any] = {"tool_name": tool_name or span_name}
        if target:
            failed_targets.add(target)
            failure_details["target"] = target
        if isinstance(result, dict):
            failure_details["result"] = result
        events.append(
            _event(
                case_id,
                phase,
                "failure",
                timestamp,
                f"Failure in {tool_name or span_name}",
                "otel",
                False,
                failure_details,
            )
        )
    return events


def _extract_otel_events(
    case_id: str, phase: str, otel_path: Path
) -> list[CopilotProcessEvent]:
    events: list[CopilotProcessEvent] = []
    failed_targets: set[str] = set()
    mtime = datetime.fromtimestamp(otel_path.stat().st_mtime, tz=UTC)

    for line in otel_path.read_text().splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            continue

        if payload.get("type") == "span":
            events.extend(
                _extract_flat_span_events(
                    case_id=case_id,
                    phase=phase,
                    payload=payload,
                    fallback_time=mtime,
                    failed_targets=failed_targets,
                )
            )
            continue

        if "event_type" in payload and "summary" in payload:
            events.append(
                _event(
                    case_id,
                    phase,
                    str(payload["event_type"]),
                    str(payload.get("timestamp") or mtime.astimezone(UTC).isoformat()),
                    str(payload["summary"]),
                    str(payload.get("source", "otel")),
                    bool(payload.get("success", True)),
                    payload["details"]
                    if isinstance(payload.get("details"), dict)
                    else {},
                )
            )
            continue

        for resource_span in payload.get("resourceSpans", []):
            if not isinstance(resource_span, dict):
                continue
            for scope_span in resource_span.get("scopeSpans", []):
                if not isinstance(scope_span, dict):
                    continue
                for span in scope_span.get("spans", []):
                    if not isinstance(span, dict):
                        continue
                    span_name = str(span.get("name", "unnamed-span"))
                    timestamp = _iso_from_start_time(
                        span.get("startTimeUnixNano"), mtime
                    )
                    events.append(
                        _event(
                            case_id,
                            phase,
                            "otel_span",
                            timestamp,
                            f"OTel span '{span_name}'",
                            "otel",
                            True,
                            {"span_name": span_name},
                        )
                    )
    return events


def _summarize_diff(diff_text: str) -> tuple[int, int]:
    added = removed = 0
    for line in diff_text.splitlines():
        if line.startswith(("+++ ", "--- ")):
            continue
        if line.startswith("+"):
            added += 1
        elif line.startswith("-"):
            removed += 1
    return added, removed


def _extract_git_diff_event(
    case_id: str, phase: str, diff_path: Path
) -> list[CopilotProcessEvent]:
    added, removed = _summarize_diff(diff_path.read_text())
    timestamp = datetime.fromtimestamp(diff_path.stat().st_mtime, tz=UTC).isoformat()
    return [
        _event(
            case_id,
            phase,
            "git_diff",
            timestamp,
            f"Git diff snapshot (+{added} / -{removed})",
            "git",
            True,
            {
                "artifact": diff_path.name,
                "added_lines": added,
                "removed_lines": removed,
            },
        )
    ]


def extract_events(run_dir: Path) -> list[CopilotProcessEvent]:
    """Extract all normalized events from one instrumentation run directory."""
    if not run_dir.exists() or not run_dir.is_dir():
        raise FileNotFoundError(f"Run directory does not exist: {run_dir}")

    events: list[CopilotProcessEvent] = []
    case_id = run_dir.name
    diff_names = ("git-diff-before.patch", "git-diff-after.patch", "git-diff.patch")

    for phase_dir in sorted(path for path in run_dir.iterdir() if path.is_dir()):
        phase = phase_dir.name
        otel_path = phase_dir / "otel.jsonl"
        if otel_path.exists():
            events.extend(_extract_otel_events(case_id, phase, otel_path))
        for diff_name in diff_names:
            diff_path = phase_dir / diff_name
            if diff_path.exists():
                events.extend(_extract_git_diff_event(case_id, phase, diff_path))

    return sorted(events, key=lambda e: (e.timestamp, e.phase, e.event_type, e.summary))


def render_conformance_table(events: list[CopilotProcessEvent]) -> str:
    """Build deterministic per-phase conformance table."""
    by_phase: dict[str, list[CopilotProcessEvent]] = defaultdict(list)
    for event in events:
        by_phase[event.phase].append(event)

    lines = ["| Phase | Conformance | Events | Event Types |", "|---|---|---:|---|"]
    if not by_phase:
        lines.append("| — | no-events | 0 | — |")
        return "\n".join(lines)

    semantic_types = {
        "phase_marker",
        "test_run",
        "lint_run",
        "file_create",
        "file_edit",
        "failure",
        "retry",
    }
    for phase in sorted(by_phase):
        phase_events = by_phase[phase]
        event_types = sorted({event.event_type for event in phase_events})
        observed_semantic = semantic_types.intersection(event_types)
        conformance = f"{len(observed_semantic)}/7 semantic"
        type_cell = ", ".join(event_types) if event_types else "—"
        lines.append(f"| {phase} | {conformance} | {len(phase_events)} | {type_cell} |")
    return "\n".join(lines)
