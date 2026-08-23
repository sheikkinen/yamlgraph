"""Deterministic helpers for the FR-866 ramp_doctrine demo."""

import json
import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel

FAMILY_KEYS = {"traps": "trap", "cures": "cure", "questions": "question"}
EFFECT_MARKERS = ("urllib", "requests", "httpx", "socket", "subprocess")
SKIP_DIRS = {".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", "__pycache__"}
LANGUAGE_BY_SUFFIX = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".rb": "Ruby",
    ".php": "PHP",
    ".sh": "Shell",
    ".yaml": "YAML",
    ".yml": "YAML",
}


class DoctrineVerdict(BaseModel):
    family: Literal["trap", "cure", "question"]
    id: str
    verdict: Literal["applies", "not", "tailor"]
    reason: str
    target_evidence: str


EXAMPLE_DRAFT: dict = {
    "target": "fixture-target",
    "items": [
        {
            "family": "trap",
            "id": "continuation_bias",
            "text": "Default mode is text generation; ask before generating.",
            "verdict": "tailor",
            "reason": "The target publishes generated cards automatically.",
            "target_evidence": "src/publisher/api.py; .github/workflows/publish.yml",
        },
        {
            "family": "question",
            "id": "who_reads_this_when",
            "text": "Name the reader and moment for every artifact.",
            "verdict": "applies",
            "reason": "The scheduled publisher has a clear publication moment.",
            "target_evidence": ".github/workflows/publish.yml: schedule",
        },
    ],
    "inventory": {
        "languages": ["Python", "YAML"],
        "entry_points": ["pyproject.toml"],
        "effect_sites": ["src/publisher/api.py"],
        "gates": [],
        "workflow_triggers": [".github/workflows/publish.yml: schedule"],
    },
}


def _repo_path(root: str | Path, relative: str) -> Path:
    return Path(root).expanduser().resolve() / relative


def _read_scripture_yaml(source_repo: str | Path) -> dict:
    instructions = _repo_path(source_repo, ".github/copilot-instructions.md")
    text = instructions.read_text(encoding="utf-8")
    for match in re.finditer(r"```yaml\s*\n(.*?)\n```", text, re.S):
        payload = yaml.safe_load(match.group(1)) or {}
        if all(key in payload for key in FAMILY_KEYS):
            return payload
    raise ValueError(
        "No Scripture YAML block with traps, cures, and questions found in "
        f"{instructions}"
    )


def collect_doctrine(source_repo: str) -> list[dict]:
    """Collect trap/cure/question entries from source Scripture."""
    payload = _read_scripture_yaml(source_repo)
    items: list[dict] = []
    for yaml_key, family in FAMILY_KEYS.items():
        entries = payload.get(yaml_key) or {}
        if not isinstance(entries, dict):
            raise ValueError(f"Scripture family {yaml_key!r} is not a mapping")
        for entry_id, text in entries.items():
            items.append({"family": family, "id": str(entry_id), "text": str(text)})
    return items


def _iter_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        files.append(path)
    return files


def _rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _collect_languages(root: Path, files: list[Path]) -> list[str]:
    languages = {
        LANGUAGE_BY_SUFFIX[path.suffix]
        for path in files
        if path.suffix in LANGUAGE_BY_SUFFIX
    }
    return sorted(languages)


def _collect_entry_points(root: Path, files: list[Path]) -> list[str]:
    conventional = {
        "pyproject.toml",
        "package.json",
        "Cargo.toml",
        "go.mod",
        "Makefile",
        "README.md",
    }
    entry_points: set[str] = set()
    for path in files:
        rel = _rel(root, path)
        if rel in conventional or path.name in {"main.py", "app.py", "cli.py"}:
            entry_points.add(rel)
        if path.name == "__main__.py":
            entry_points.add(rel)
    return sorted(entry_points)


def _collect_effect_sites(root: Path, files: list[Path]) -> list[str]:
    effect_sites: list[str] = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if any(marker in text for marker in EFFECT_MARKERS):
            effect_sites.append(_rel(root, path))
    return effect_sites


def _collect_gates(root: Path) -> list[str]:
    gates: list[str] = []
    for name in (".pre-commit-config.yaml", ".pre-commit-config.yml"):
        if (root / name).is_file():
            gates.append(name)
    workflows = root / ".github" / "workflows"
    if workflows.is_dir():
        for path in sorted([*workflows.glob("*.yml"), *workflows.glob("*.yaml")]):
            text = path.read_text(encoding="utf-8", errors="ignore")
            if re.search(r"\b(pytest|tox|ruff|mypy|npm\s+test|go\s+test)\b", text):
                gates.append(f"{_rel(root, path)}: test")
    return sorted(gates)


def _collect_workflow_triggers(root: Path) -> list[str]:
    triggers: list[str] = []
    workflows = root / ".github" / "workflows"
    if not workflows.is_dir():
        return triggers
    for path in sorted([*workflows.glob("*.yml"), *workflows.glob("*.yaml")]):
        in_on = False
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip()
            if stripped == "on:":
                in_on = True
                continue
            if in_on and line and not line.startswith((" ", "\t")):
                in_on = False
            if not in_on or not line.startswith("  ") or not stripped.endswith(":"):
                continue
            trigger = stripped[:-1]
            if trigger and not trigger.startswith("#"):
                triggers.append(f"{_rel(root, path)}: {trigger}")
    return triggers


def collect_inventory(target_repo: str) -> dict:
    """Collect deterministic target facts shown to the map-stage LLM."""
    root = Path(target_repo).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(
            f"Target repo does not exist or is not a directory: {root}"
        )
    files = _iter_files(root)
    return {
        "languages": _collect_languages(root, files),
        "entry_points": _collect_entry_points(root, files),
        "effect_sites": _collect_effect_sites(root, files),
        "gates": _collect_gates(root),
        "workflow_triggers": _collect_workflow_triggers(root),
    }


def collect_inputs(state: dict) -> dict:
    """Graph-facing collection node."""
    source = state.get("source") or "."
    target = state["target"]
    return {
        "source_items": collect_doctrine(source),
        "target_inventory": collect_inventory(target),
    }


def _as_dict(item: dict | BaseModel) -> dict:
    return item.model_dump() if isinstance(item, BaseModel) else dict(item)


def validate_draft(verdicts: list[dict], source_items: list[dict]) -> list[str]:
    """Validate map output against collected source doctrine."""
    source_ids = {(item["family"], item["id"]) for item in source_items}
    errors: list[str] = []
    for raw in verdicts:
        item = _as_dict(raw)
        family = item.get("family", "")
        entry_id = item.get("id", "")
        decision = item.get("verdict", "")
        if (family, entry_id) not in source_ids:
            errors.append(f"invented id {entry_id!r} for family {family!r}")
        if (
            decision in {"applies", "tailor"}
            and not item.get("target_evidence", "").strip()
        ):
            errors.append(f"{family}:{entry_id} requires target_evidence")
        if decision == "not" and not item.get("reason", "").strip():
            errors.append(f"{family}:{entry_id} requires reason")
    return errors


def _normalize_map_results(state: dict) -> list[dict]:
    decisions: list[dict] = []
    for result in sorted(
        state.get("map_results") or [], key=lambda r: r.get("_map_index", 0)
    ):
        item = dict(result)
        map_index = item.pop("_map_index", None)
        if "_error" in item:
            decisions.append(
                {
                    "_error": item["_error"],
                    "_map_index": map_index,
                    "family": "",
                    "id": "",
                    "verdict": "",
                    "reason": "",
                    "target_evidence": "",
                }
            )
            continue
        decisions.append(item)
    return decisions


def merge_doctrine(state: dict) -> dict:
    """Graph-facing merge node: validate, render, and write draft files."""
    source_items = state.get("source_items") or []
    decisions = _normalize_map_results(state)
    errors: list[str] = []
    if len(decisions) != len(source_items):
        errors.append(
            f"count mismatch: {len(source_items)} source items, {len(decisions)} outputs"
        )
    for decision in decisions:
        if "_error" in decision:
            errors.append(
                f"map item {decision.get('_map_index')} failed: {decision['_error']}"
            )
    errors.extend(validate_draft(decisions, source_items))
    if errors:
        raise ValueError("; ".join(errors))

    source_by_key = {(item["family"], item["id"]): item for item in source_items}
    kept: list[dict] = []
    for decision in decisions:
        if decision["verdict"] not in {"applies", "tailor"}:
            continue
        source = source_by_key[(decision["family"], decision["id"])]
        kept.append({**decision, "text": source["text"]})

    draft = {
        "target": state["target"],
        "source": state.get("source") or ".",
        "items": kept,
        "all_dispositions": decisions,
        "inventory": state.get("target_inventory") or {},
    }
    md_path, json_path = write_drafts(draft, base_dir=".")
    return {
        "draft": draft,
        "draft_errors": [],
        "draft_paths": {"markdown": md_path, "json": json_path},
    }


def _family_title(family: str) -> str:
    return {"trap": "Traps", "cure": "Cures", "question": "Questions"}[family]


_CITATION_PAREN = re.compile(r"\s*\([^()]*\b(?:FR|NC)-\d+[^()]*\)")
_CITATION_TOKEN = re.compile(r"\b(?:FR|NC)-\d+\b")


def _scrub_citations(text: str) -> str:
    """Empty source-repo witness citations; the target has its own incidents."""
    text = _CITATION_PAREN.sub("", text)
    return _CITATION_TOKEN.sub("a source-repo incident", text)


def _scrubbed_items(draft: dict) -> list[dict]:
    items = []
    for item in draft.get("items") or []:
        item = dict(item)
        for key in ("text", "reason", "target_evidence"):
            if isinstance(item.get(key), str):
                item[key] = _scrub_citations(item[key])
        items.append(item)
    return items


def _render_markdown(draft: dict) -> str:
    target = draft.get("target", "(unknown target)")
    lines = [
        "# AGENTS.md doctrine draft",
        "",
        f"> Draft target: `{target}`. Human review is required before landing.",
        "",
        "## Target inventory",
    ]
    inventory = draft.get("inventory") or {}
    for key in (
        "languages",
        "entry_points",
        "effect_sites",
        "gates",
        "workflow_triggers",
    ):
        values = inventory.get(key) or []
        rendered = ", ".join(f"`{value}`" for value in values) if values else "(none)"
        lines.append(f"- **{key}**: {rendered}")

    items = _scrubbed_items(draft)
    for family in ("trap", "cure", "question"):
        lines += ["", f"## {_family_title(family)}"]
        family_items = [item for item in items if item.get("family") == family]
        if not family_items:
            lines.append("")
            lines.append("- (none carried from source doctrine)")
            continue
        for item in family_items:
            lines += [
                "",
                f"### `{item['id']}`",
                "",
                item["text"],
                "",
                f"- Applicability: {item['verdict']}",
                f"- Rationale: {item['reason']}",
                f"- Target evidence: {item['target_evidence']}",
                "- Witness citations:",
            ]

    lines += [
        "",
        "## Local incidents",
        "",
        "_Intentionally blank for ramp_incidents to fill._",
        "",
    ]
    return "\n".join(lines)


def write_drafts(draft: dict, base_dir: str | Path) -> tuple[str, str]:
    """Write exactly the markdown and JSON doctrine drafts under tmp/ramp."""
    out_dir = Path(base_dir) / "tmp" / "ramp"
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / "doctrine-draft.md"
    json_path = out_dir / "doctrine-draft.json"
    payload = dict(draft)
    payload["items"] = _scrubbed_items(draft)
    payload["all_dispositions"] = _scrubbed_items(
        {"items": draft.get("all_dispositions") or []}
    )
    md_path.write_text(_render_markdown(payload), encoding="utf-8")
    json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return str(md_path), str(json_path)
