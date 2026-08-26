"""Deterministic tools for the FR-890 research-route demo."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator

REQUIRED_SECTIONS = (
    "Problem statement",
    "Classification",
    "Constraints",
    "Witnessed incidents",
)

PERSONA_KEYS = (
    "os_infra_finding",
    "data_process_finding",
    "yamlgraph_native_finding",
    "subtractionist_finding",
    "librarian_finding",
)

TABLE_COLUMNS = (
    "candidate",
    "persona",
    "class",
    "verdict",
    "precedent",
    "is_this_a_graph",
    "effort-risk",
)

URL_RE = re.compile(r"https?://\S+")
LIBRARIAN_ERROR_STRINGS = ("Error:", "No results")


class PersonaFinding(BaseModel):
    """One closed-input planning alternative from one persona."""

    persona: str = Field(min_length=1)
    candidate: str = Field(min_length=1)
    solution_class: str = Field(min_length=1)
    verdict: str = Field(min_length=1)
    precedent: str = Field(min_length=1)
    is_this_a_graph: str = Field(min_length=1)
    effort_risk: str = Field(min_length=1)

    @field_validator("*", mode="before")
    @classmethod
    def _reject_blank(cls, value: Any) -> Any:
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                raise ValueError("empty required cell")
            return stripped
        return value


def _state_value(value: Any, key: str) -> Any:
    if isinstance(value, dict):
        return value[key]
    return value


def _section(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"^#{{1,6}}\s*{re.escape(heading)}\s*$(.*?)(?=^#{{1,6}}\s|\Z)",
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def load_brief(brief_path: str) -> dict:
    """Parse the four allowed problem-brief sections into graph state."""
    path = Path(_state_value(brief_path, "brief_path"))
    text = path.read_text(encoding="utf-8")

    parsed = {
        "problem_statement": _section(text, "Problem statement"),
        "classification": _section(text, "Classification"),
        "constraints": _section(text, "Constraints"),
        "witnessed_incidents": _section(text, "Witnessed incidents"),
    }
    missing = [name for name, value in parsed.items() if not value]
    if missing:
        raise ValueError(f"brief missing required sections: {', '.join(missing)}")
    return parsed


def collect_graph_shapes(demos_dir: str = "examples/demos") -> str:
    """Return one line per demo graph with name and description."""
    raw_dir = (
        demos_dir.get("demos_dir", "examples/demos")
        if isinstance(demos_dir, dict)
        else demos_dir
    )
    root = Path(raw_dir)
    if not root.is_absolute():
        root = Path.cwd() / root
    if not root.is_dir():
        raise ValueError(f"demos directory not found: {root}")

    lines: list[str] = []
    for graph_path in sorted(root.glob("*/graph.yaml")):
        with graph_path.open(encoding="utf-8") as handle:
            config = yaml.safe_load(handle) or {}
        name = str(config.get("name") or graph_path.parent.name).strip()
        description = " ".join(str(config.get("description") or "").split())
        lines.append(f"{name}: {description}")

    if not any(
        line.startswith("map-demo:") or line.startswith("map:") for line in lines
    ):
        raise ValueError("graph shapes inventory did not include the map demo")
    return "\n".join(lines)


def _normalize_finding(value: Any, key: str) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    if not isinstance(value, dict):
        raise ValueError(f"persona output {key!r} is not a dict")
    return value


def gather_findings(state: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Gather the five persona findings without deduplication."""
    missing = [key for key in PERSONA_KEYS if key not in state]
    if missing:
        raise ValueError(f"missing persona findings: {', '.join(missing)}")
    return {"findings": [_normalize_finding(state[key], key) for key in PERSONA_KEYS]}


def _validate_findings(findings: list[dict]) -> list[PersonaFinding]:
    validated: list[PersonaFinding] = []
    for index, finding in enumerate(findings, start=1):
        try:
            row = PersonaFinding.model_validate(finding)
        except ValidationError as exc:
            raise ValueError(
                f"empty or invalid required cell in finding {index}: {exc}"
            ) from exc
        validated.append(row)

    for row in validated:
        if row.persona.lower() == "librarian":
            if any(marker in row.precedent for marker in LIBRARIAN_ERROR_STRINGS):
                raise ValueError("librarian precedent is an error string")
            if not URL_RE.search(row.precedent):
                raise ValueError("librarian precedent must contain a URL")

    class_count = len({row.solution_class for row in validated})
    if not 4 <= class_count <= 6:
        raise ValueError(f"solution class count must be 4-6, got {class_count}")

    return validated


def _cell(value: str) -> str:
    return " ".join(value.split()).replace("|", "/")


def reduce_findings(
    findings: list[dict],
    brief_path: str,
    base_dir: str = ".",
) -> dict:
    """Validate persona findings and write tmp/draft-alternatives.md."""
    rows = _validate_findings(findings)
    artifact = Path(base_dir) / "tmp" / "draft-alternatives.md"
    artifact.parent.mkdir(parents=True, exist_ok=True)

    personas = ", ".join(row.persona for row in rows)
    run_date = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "# Draft alternatives",
        "",
        f"- brief: {Path(brief_path).name}",
        f"- run date: {run_date}",
        f"- personas executed: {personas}",
        "",
        "| candidate | persona | class | verdict | precedent | is_this_a_graph | effort-risk |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                (
                    _cell(row.candidate),
                    _cell(row.persona),
                    _cell(row.solution_class),
                    _cell(row.verdict),
                    _cell(row.precedent),
                    _cell(row.is_this_a_graph),
                    _cell(row.effort_risk),
                )
            )
            + " |"
        )
    lines.append("")
    artifact.write_text("\n".join(lines), encoding="utf-8")
    return {
        "artifact": str(artifact),
        "rows": len(rows),
        "classes": len({r.solution_class for r in rows}),
    }


def write_alternatives(state: dict[str, Any]) -> dict[str, dict]:
    """Graph node wrapper for reduce_findings."""
    return {
        "result": reduce_findings(
            state["findings"],
            state["brief_path"],
            base_dir=state.get("base_dir", "."),
        )
    }
