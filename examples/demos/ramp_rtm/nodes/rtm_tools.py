"""FR-866 RAMP RTM tools: tests -> proposed requirement draft."""

import ast
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, ValidationError


class RtmEntry(BaseModel):
    req_id: str
    statement: str
    witness_tests: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    status: Literal["proposed"]


EXAMPLE_DRAFT: dict = {
    "target": "fixture-target",
    "entries": [
        {
            "req_id": "REQ-XXX-001",
            "statement": "Titles longer than the gallery cap are rejected.",
            "witness_tests": ["test_title_cap_enforced"],
            "confidence": 0.9,
            "status": "proposed",
        }
    ],
    "gaps": ["test_edge_clamped_to_max"],
    "validation_errors": [],
    "test_count": 2,
    "candidate_count": 1,
}


def _target_from_arg(target_repo: str | dict) -> tuple[Path, bool]:
    if isinstance(target_repo, dict):
        raw = target_repo.get("target_repo") or target_repo.get("target")
        graph_call = True
    else:
        raw = target_repo
        graph_call = False
    if not raw:
        raise ValueError("target repo path is required")
    target = Path(str(raw)).expanduser().resolve()
    if not target.is_dir():
        raise FileNotFoundError(f"target repo not found: {target}")
    return target, graph_call


def _test_names(source: str, path: Path) -> list[str]:
    tree = ast.parse(source, filename=str(path))
    funcs = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and node.name.startswith("test_")
    ]
    return [node.name for node in sorted(funcs, key=lambda node: node.lineno)]


def collect_tests(target_repo: str | dict) -> list[dict] | dict:
    """Collect one inventory item per tests/**/test_*.py file."""
    target, graph_call = _target_from_arg(target_repo)
    tests_dir = target / "tests"
    if not tests_dir.is_dir():
        raise FileNotFoundError(f"no tests/ directory under target repo: {target}")

    inventory: list[dict] = []
    for path in sorted(tests_dir.glob("**/test_*.py")):
        source = path.read_text()
        inventory.append(
            {
                "path": path.relative_to(target).as_posix(),
                "tests": _test_names(source, path),
                "source": source,
            }
        )

    if graph_call:
        return {"test_inventory": inventory}
    return inventory


def _inventory_names(inventory: list[dict]) -> set[str]:
    return {name for item in inventory for name in item.get("tests", [])}


def validate_rtm(entries: list[dict], inventory: list[dict]) -> list[str]:
    """Return validation errors for invalid RTM draft entries."""
    known_tests = _inventory_names(inventory)
    errors: list[str] = []
    for raw in entries:
        try:
            entry = RtmEntry.model_validate(raw)
        except ValidationError as exc:
            errors.append(str(exc))
            witnesses = raw.get("witness_tests") if isinstance(raw, dict) else []
            for name in witnesses or []:
                if name not in known_tests:
                    errors.append(f"unknown witness test {name!r}")
            continue

        if not entry.witness_tests:
            errors.append(f"{entry.req_id}: empty witness_tests")
        for name in entry.witness_tests:
            if name not in known_tests:
                errors.append(f"{entry.req_id}: unknown witness test {name!r}")
    return errors


def gap_tests(entries: list[dict], inventory: list[dict]) -> list[str]:
    witnessed = {
        name
        for entry in entries
        for name in (entry.get("witness_tests") or [])
        if isinstance(entry, dict)
    }
    return sorted(name for name in _inventory_names(inventory) if name not in witnessed)


def _entries_from_map_results(map_results: list[dict]) -> list[dict]:
    entries: list[dict] = []
    for result in sorted(map_results or [], key=lambda item: item.get("_map_index", 0)):
        payload = result.get("file_rtm") if isinstance(result, dict) else None
        if payload is None and isinstance(result, dict):
            payload = result
        if hasattr(payload, "model_dump"):
            payload = payload.model_dump()
        if not isinstance(payload, dict):
            continue
        for entry in payload.get("entries") or []:
            if isinstance(entry, dict):
                entries.append(entry)
    return entries


def _line_items(items: list[str]) -> list[str]:
    return [f"- `{item}`" for item in items] if items else ["- None."]


def _render_markdown(draft: dict) -> str:
    entries = draft.get("entries") or []
    gaps = draft.get("gaps") or []
    errors = draft.get("validation_errors") or []
    test_count = int(draft.get("test_count") or 0)
    candidate_count = int(draft.get("candidate_count") or len(entries))

    lines = [
        "# Proposed requirement registry draft",
        "",
        "> Draft only. Requirement ids use the neutral `REQ-XXX-NNN` namespace.",
        "",
        "## Insufficiency finding",
        "",
    ]
    if candidate_count < test_count:
        lines.append(
            f"{test_count} tests support only {candidate_count} requirement "
            "candidates; unwitnessed tests remain in the gap list instead of "
            "being padded into requirements."
        )
    else:
        lines.append(
            f"{test_count} tests support {candidate_count} proposed requirement "
            "candidates."
        )

    lines += ["", "## Proposed requirements", ""]
    if entries:
        for entry in entries:
            witnesses = ", ".join(
                f"`{name}`" for name in entry.get("witness_tests", [])
            )
            lines += [
                f"### {entry.get('req_id', 'REQ-XXX-000')}",
                "",
                entry.get("statement", "").strip() or "(missing statement)",
                "",
                f"- Status: `{entry.get('status', '')}`",
                f"- Confidence: {entry.get('confidence', '')}",
                f"- Witness tests: {witnesses or '(none)'}",
                "",
            ]
    else:
        lines.append("No requirement candidates were proposed.")

    lines += [
        "",
        "## Gap tests",
        "",
        *_line_items(gaps),
        "",
        "## Validation errors",
        "",
    ]
    lines += _line_items(errors)
    return "\n".join(lines).rstrip() + "\n"


def write_drafts(draft: dict, base_dir: str | Path) -> tuple[str, str]:
    """Write exactly tmp/ramp/rtm-draft.md and tmp/ramp/rtm-draft.json."""
    out_dir = Path(base_dir) / "tmp" / "ramp"
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / "rtm-draft.md"
    json_path = out_dir / "rtm-draft.json"
    md_path.write_text(_render_markdown(draft))
    json_path.write_text(json.dumps(draft, indent=2, sort_keys=True) + "\n")
    return str(md_path), str(json_path)


def merge_rtm(state: dict) -> dict:
    inventory = state.get("test_inventory") or []
    entries = _entries_from_map_results(state.get("map_results") or [])
    errors = validate_rtm(entries, inventory)
    gaps = gap_tests(entries, inventory)
    test_count = len(_inventory_names(inventory))
    draft = {
        "target": str(state.get("target") or ""),
        "entries": entries,
        "gaps": gaps,
        "validation_errors": errors,
        "test_count": test_count,
        "candidate_count": len(entries),
    }
    md_path, json_path = write_drafts(draft, state.get("source") or ".")
    return {
        "rtm_entries": entries,
        "validation_errors": errors,
        "gaps": gaps,
        "draft": draft,
        "draft_paths": {"markdown": md_path, "json": json_path},
    }
