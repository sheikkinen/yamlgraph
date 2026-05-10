#!/usr/bin/env python3
"""Extract normalized process-mining events from Copilot instrumentation artifacts.

FR-362: Copilot instrumentation process-mining POC.

Input contract:
    outputs/copilot-instrumentation/<run-id>/<phase>/

Primary sources:
    - OTel JSONL spans (otel.jsonl)
    - Git diff snapshots (git-diff.patch)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field


class CopilotProcessEvent(BaseModel):
    """Normalized process-mining event boundary model."""

    case_id: str = Field(description="Instrumentation run identifier")
    phase: str = Field(description="Execution phase (for example: plan, implement)")
    event_type: str = Field(description="Event kind (otel_span, git_diff)")
    timestamp: str = Field(description="ISO-8601 timestamp")
    summary: str = Field(description="Human-readable event summary")


def _iso_from_start_time(value: list | str | int | None, fallback: datetime) -> str:
    """Convert OTel startTime to ISO-8601.

    Copilot file exporter emits startTime as [seconds, nanos] array.
    OTLP JSON format uses startTimeUnixNano as a nanosecond integer or string.
    """
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


def _iter_phase_dirs(run_dir: Path) -> list[Path]:
    return sorted([path for path in run_dir.iterdir() if path.is_dir()])


def _extract_otel_events(
    case_id: str, phase: str, otel_path: Path
) -> list[CopilotProcessEvent]:
    events: list[CopilotProcessEvent] = []
    mtime = datetime.fromtimestamp(otel_path.stat().st_mtime, tz=UTC)

    for line in otel_path.read_text().splitlines():
        if not line.strip():
            continue

        payload = json.loads(line)

        # Copilot file exporter: flat {"type":"span",...} records
        if payload.get("type") == "span":
            span_name = payload.get("name", "unnamed-span")
            timestamp = _iso_from_start_time(payload.get("startTime"), mtime)
            events.append(
                CopilotProcessEvent(
                    case_id=case_id,
                    phase=phase,
                    event_type="otel_span",
                    timestamp=timestamp,
                    summary=f"OTel span '{span_name}'",
                )
            )
            continue

        # OTLP JSON format: {"resourceSpans":[...]}
        for resource_span in payload.get("resourceSpans", []):
            for scope_span in resource_span.get("scopeSpans", []):
                for span in scope_span.get("spans", []):
                    span_name = span.get("name", "unnamed-span")
                    timestamp = _iso_from_start_time(
                        span.get("startTimeUnixNano"), mtime
                    )
                    events.append(
                        CopilotProcessEvent(
                            case_id=case_id,
                            phase=phase,
                            event_type="otel_span",
                            timestamp=timestamp,
                            summary=f"OTel span '{span_name}'",
                        )
                    )
    return events


def _summarize_diff(diff_text: str) -> tuple[int, int]:
    added = 0
    removed = 0
    for line in diff_text.splitlines():
        if line.startswith("+++ ") or line.startswith("--- "):
            continue
        if line.startswith("+"):
            added += 1
        elif line.startswith("-"):
            removed += 1
    return added, removed


def _extract_git_diff_event(
    case_id: str, phase: str, diff_path: Path
) -> list[CopilotProcessEvent]:
    diff_text = diff_path.read_text()
    added, removed = _summarize_diff(diff_text)
    timestamp = datetime.fromtimestamp(diff_path.stat().st_mtime, tz=UTC).isoformat()

    event = CopilotProcessEvent(
        case_id=case_id,
        phase=phase,
        event_type="git_diff",
        timestamp=timestamp,
        summary=f"Git diff snapshot (+{added} / -{removed})",
    )
    return [event]


def extract_events(run_dir: Path) -> list[CopilotProcessEvent]:
    """Extract all normalized events from one instrumentation run directory."""
    if not run_dir.exists() or not run_dir.is_dir():
        raise FileNotFoundError(f"Run directory does not exist: {run_dir}")

    case_id = run_dir.name
    events: list[CopilotProcessEvent] = []

    for phase_dir in _iter_phase_dirs(run_dir):
        phase = phase_dir.name
        otel_path = phase_dir / "otel.jsonl"
        if otel_path.exists():
            events.extend(
                _extract_otel_events(case_id=case_id, phase=phase, otel_path=otel_path)
            )

        diff_path = phase_dir / "git-diff.patch"
        if diff_path.exists():
            events.extend(
                _extract_git_diff_event(
                    case_id=case_id,
                    phase=phase,
                    diff_path=diff_path,
                )
            )

    return sorted(events, key=lambda event: event.timestamp)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract normalized process-mining events from Copilot instrumentation artifacts"
    )
    parser.add_argument(
        "run_dir", help="Path to outputs/copilot-instrumentation/<run-id>"
    )
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    try:
        events = extract_events(run_dir)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
        print(f"extract_copilot_events.py: {error}", file=sys.stderr)
        return 1

    for event in events:
        print(json.dumps(event.model_dump()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
