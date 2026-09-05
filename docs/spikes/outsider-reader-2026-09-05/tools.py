"""Outsider spike tools — read one PR description, write one report. No repo access."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def read_input(state: dict[str, Any]) -> str:
    path = Path(state["input_path"])
    if not path.is_file():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8")


def write_report(state: dict[str, Any]) -> dict[str, Any]:
    result = state.get("outsider_result")
    output = (
        result.get("output")
        if isinstance(result, dict)
        else getattr(result, "output", None)
    )
    if not isinstance(output, str) or not output.strip():
        raise ValueError(f"outsider produced no output: {result!r}")
    out = Path(state["report_path"])
    out.parent.mkdir(parents=True, exist_ok=True)
    header = (
        f"<!-- outsider spike | input: {state['input_path']} | model: {state.get('model')} "
        f"| {datetime.now(UTC).isoformat()} -->\n\n"
    )
    out.write_text(header + output.strip() + "\n", encoding="utf-8")
    return {"path": str(out), "chars": len(output)}
