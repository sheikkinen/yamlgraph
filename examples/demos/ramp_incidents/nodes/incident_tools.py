"""FR-866 RAMP incident tools: source corpus -> incident draft."""

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ValidationError, model_validator


class IncidentClassification(BaseModel):
    verdict: Literal["incident", "not_an_incident"]
    path: str = ""
    date: str = ""
    defect: str = ""
    root_cause: str = ""
    cure: str = ""
    witness: str = ""
    source_ref: str = ""

    @model_validator(mode="after")
    def require_incident_fields(self) -> "IncidentClassification":
        if self.verdict != "incident":
            return self
        missing = [
            name
            for name in (
                "date",
                "defect",
                "root_cause",
                "cure",
                "witness",
                "source_ref",
            )
            if not getattr(self, name).strip()
        ]
        if missing:
            raise ValueError(
                "incident verdict requires non-empty fields: " + ", ".join(missing)
            )
        return self


EXAMPLE_DRAFT: dict = {
    "target": "deviant-daily",
    "incidents": [
        {
            "verdict": "incident",
            "path": "feature-requests/FR-863-deviant-daily-publish-policy-boundary-mirroring.md",
            "date": "2026-08-23",
            "defect": "vision payload exceeded provider ceiling",
            "root_cause": "external provider payload and target API limits were not mirrored at the boundary",
            "cure": "downscale vision payloads, mirror title caps, and stabilize corpus identity",
            "witness": "run 32623570851 failed at describe; run 32624747449 recovered publication",
            "source_ref": "feature-requests/FR-863-deviant-daily-publish-policy-boundary-mirroring.md",
        }
    ],
    "not_an_incident": [
        {
            "verdict": "not_an_incident",
            "path": "feature-requests/authoring-briefs/fr-866-ramp-incidents-brief.md",
        }
    ],
    "validation_errors": [],
    "corpus": [
        "feature-requests/FR-863-deviant-daily-publish-policy-boundary-mirroring.md",
        "feature-requests/authoring-briefs/fr-866-ramp-incidents-brief.md",
    ],
}


def _root(path: str | Path) -> Path:
    root = Path(path).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"source repo not found: {root}")
    return root


def _candidate_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for rel_dir in ("feature-requests", "docs/diary"):
        base = root / rel_dir
        if not base.is_dir():
            continue
        files.extend(path for path in base.rglob("*.md") if path.is_file())
    return sorted(files)


def _rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _collect_paths(source_repo: str | Path, target_name: str) -> list[str]:
    if not target_name:
        raise ValueError("target_name is required")
    root = _root(source_repo)
    paths: list[str] = []
    for path in _candidate_files(root):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if target_name in text:
            paths.append(_rel(root, path))
    return paths


def _documents(root: Path, corpus: list[str]) -> list[dict]:
    return [
        {
            "path": rel,
            "text": (root / rel).read_text(encoding="utf-8", errors="ignore"),
        }
        for rel in corpus
    ]


def collect_corpus(
    source_repo: str | dict,
    target_name: str | None = None,
) -> list[str] | dict:
    """Collect repo-relative FR/diary paths containing the target token."""
    if isinstance(source_repo, dict):
        state = source_repo
        source = state.get("source_repo") or state.get("source") or "."
        target = state.get("target_name") or target_name
        corpus = _collect_paths(source, str(target or ""))
        root = _root(source)
        return {
            "corpus": corpus,
            "documents": _documents(root, corpus),
            "has_corpus": bool(corpus),
        }

    return _collect_paths(source_repo, str(target_name or ""))


def _as_dict(item: dict | BaseModel) -> dict:
    return item.model_dump() if isinstance(item, BaseModel) else dict(item)


def _source_ref_exists(source_repo: str | Path, source_ref: str) -> bool:
    root = _root(source_repo)
    candidate = (root / source_ref).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return candidate.is_file()


def validate_disposition(
    classifications: list[dict],
    corpus: list[str],
    source_repo: str,
) -> list[str]:
    """Return validation errors for coverage and source citation defects."""
    errors: list[str] = []
    normalized: list[dict] = []
    for raw in classifications:
        item = _as_dict(raw)
        try:
            normalized.append(IncidentClassification.model_validate(item).model_dump())
        except ValidationError as exc:
            errors.append(f"{item.get('path', '(unknown path)')}: {exc}")
            normalized.append(item)

    classified_paths = {item.get("path", "") for item in normalized}
    missing = [path for path in corpus if path not in classified_paths]
    if len(classifications) != len(corpus) or missing:
        detail = ", ".join(missing) if missing else "(no missing paths identified)"
        errors.append(
            f"count mismatch: {len(corpus)} corpus paths, "
            f"{len(classifications)} classifications; missing: {detail}"
        )

    for item in normalized:
        if item.get("verdict") != "incident":
            continue
        source_ref = str(item.get("source_ref") or "")
        if not _source_ref_exists(source_repo, source_ref):
            errors.append(
                f"incident source_ref does not resolve under source_repo: {source_ref!r}"
            )
    return errors


def _normalize_map_results(map_results: list[dict]) -> list[dict]:
    classifications: list[dict] = []
    for result in sorted(map_results or [], key=lambda item: item.get("_map_index", 0)):
        item = dict(result)
        item.pop("_map_index", None)
        if "_error" in item:
            classifications.append(
                {
                    "verdict": "not_an_incident",
                    "path": "",
                    "source_ref": "",
                    "_error": item["_error"],
                }
            )
            continue
        payload = item.get("incident_classification") or item
        if hasattr(payload, "model_dump"):
            payload = payload.model_dump()
        if isinstance(payload, dict):
            classifications.append(payload)
    return classifications


def _line_items(items: list[str]) -> list[str]:
    return [f"- `{item}`" for item in items] if items else ["- None."]


def _render_markdown(draft: dict) -> str:
    target = draft.get("target") or "(unknown target)"
    incidents = sorted(
        draft.get("incidents") or [], key=lambda item: item.get("date", "")
    )
    not_incidents = sorted(
        item.get("path", "") for item in draft.get("not_an_incident") or []
    )
    errors = draft.get("validation_errors") or []

    lines = [
        "# Incident repatriation draft",
        "",
        f"> Draft target: `{target}`. Human review is required before doctrine use.",
        "",
        "## Incidents",
        "",
    ]
    if incidents:
        for item in incidents:
            lines += [
                f"### {item.get('date', '')} — {item.get('defect', '').strip()}",
                "",
                f"- Source: `{item.get('source_ref', '')}`",
                f"- Document: `{item.get('path', '')}`",
                f"- Root cause: {item.get('root_cause', '').strip()}",
                f"- Cure: {item.get('cure', '').strip()}",
                f"- Witness: {item.get('witness', '').strip()}",
                "",
            ]
    else:
        lines.append("No incidents were classified.")

    lines += [
        "",
        "## Reconciliation",
        "",
        "### not_an_incident paths",
        "",
        *_line_items(not_incidents),
        "",
        "### Validation errors",
        "",
        *_line_items(errors),
    ]
    return "\n".join(lines).rstrip() + "\n"


def write_drafts(draft: dict, base_dir: str | Path) -> tuple[str, str]:
    """Write exactly tmp/ramp/incidents-draft.md and .json under base_dir."""
    out_dir = Path(base_dir) / "tmp" / "ramp"
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / "incidents-draft.md"
    json_path = out_dir / "incidents-draft.json"
    md_path.write_text(_render_markdown(draft), encoding="utf-8")
    json_path.write_text(
        json.dumps(draft, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return str(md_path), str(json_path)


def merge_incidents(state: dict) -> dict:
    """Graph-facing merge node: validate classifications and write drafts."""
    classifications = _normalize_map_results(state.get("map_results") or [])
    corpus = state.get("corpus") or []
    source = state.get("source") or "."
    errors = validate_disposition(classifications, corpus, source_repo=source)
    if errors:
        raise ValueError("; ".join(errors))

    incidents = [item for item in classifications if item.get("verdict") == "incident"]
    not_incidents = [
        item for item in classifications if item.get("verdict") == "not_an_incident"
    ]
    draft = {
        "target": state.get("target_name") or "",
        "source": source,
        "corpus": corpus,
        "incidents": incidents,
        "not_an_incident": not_incidents,
        "validation_errors": [],
    }
    md_path, json_path = write_drafts(draft, base_dir=source)
    return {
        "incidents": incidents,
        "not_an_incident": not_incidents,
        "validation_errors": [],
        "draft": draft,
        "draft_paths": {"markdown": md_path, "json": json_path},
    }
