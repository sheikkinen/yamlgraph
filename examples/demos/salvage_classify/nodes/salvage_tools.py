"""Deterministic helpers for the FR-868 salvage_classify demo."""

import json
import subprocess
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

VERDICTS = ("duplicate", "lift", "obsolete")
TEXT_LIMIT = 12000
MAX_CANDIDATES = 10


class AssetClassification(BaseModel):
    path: str
    category: str
    verdict: Literal["duplicate", "lift", "obsolete"]
    rationale: str = Field(min_length=1)
    yamlgraph_equivalent: str | None = None
    target_path: str | None = None


class SalvageDisposition(BaseModel):
    source_repo: str
    source_sha: str = Field(min_length=7)
    manifest_count: int
    items: list[AssetClassification]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _git_ls_files(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def _source_root(source_repo: str | Path) -> Path:
    root = Path(source_repo).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"source_repo is not a directory: {root}")
    return root


def collect_manifest(source_repo: str) -> list[str]:
    """Return tracked source repo files as POSIX paths, or graph state updates."""
    if isinstance(source_repo, dict):
        state = source_repo
        root = _source_root(str(state.get("source_repo") or ""))
        manifest = _git_ls_files(root)
        return {
            "manifest": manifest,
            "manifest_count": len(manifest),
            "assets": [_asset_payload(root, path) for path in manifest],
            "has_manifest": bool(manifest),
        }

    return _git_ls_files(_source_root(source_repo))


def _asset_payload(source_root: Path, rel_path: str) -> dict:
    return {
        "path": rel_path,
        "category_hint": _category_for(rel_path),
        "content": _read_excerpt(source_root / rel_path),
        "candidate_equivalents": _candidate_equivalents(rel_path),
    }


def _read_excerpt(path: Path) -> str:
    with path.open("rb") as handle:
        data = handle.read(TEXT_LIMIT + 1)
    text = data[:TEXT_LIMIT].decode("utf-8", errors="replace")
    if len(data) <= TEXT_LIMIT:
        return text
    return text + "\n...[truncated]"


def _category_for(rel_path: str) -> str:
    path = Path(rel_path)
    parts = path.parts
    suffix = path.suffix.lower()
    if any(part == "workflows" for part in parts):
        return "workflow"
    if ".github" in parts or "hooks" in parts:
        return "hook"
    if suffix in {".md", ".rst", ".txt"}:
        return "docs"
    if suffix in {".sh", ".bash", ".zsh"}:
        return "script"
    if suffix in {".yaml", ".yml", ".toml", ".json", ".ini", ".cfg"}:
        return "config"
    if "test" in path.name or "tests" in parts:
        return "test"
    if suffix in {".py", ".js", ".ts", ".go", ".rs", ".java", ".rb"}:
        return "source"
    return "asset"


def _candidate_equivalents(source_rel: str) -> list[dict[str, str]]:
    repo = _repo_root()
    tracked = _git_ls_files(repo)
    source_path = Path(source_rel)
    candidates: list[dict[str, str]] = []
    seen: set[str] = set()

    def add(path: str, reason: str) -> None:
        if path not in seen:
            candidates.append({"path": path, "reason": reason})
            seen.add(path)

    if source_rel in tracked:
        add(source_rel, "same repo-relative path")

    for path in tracked:
        if len(candidates) >= MAX_CANDIDATES:
            break
        current = Path(path)
        if current.name == source_path.name:
            add(path, "same filename")

    source_tokens = {
        token
        for token in source_path.stem.replace("-", "_").split("_")
        if len(token) >= 4
    }
    for path in tracked:
        if len(candidates) >= MAX_CANDIDATES:
            break
        lowered = path.lower()
        if source_tokens and any(token.lower() in lowered for token in source_tokens):
            add(path, "source-name token match")

    return candidates


def _as_dict(item: dict | BaseModel) -> dict:
    return item.model_dump() if isinstance(item, BaseModel) else dict(item)


def _validate_path_under(root: Path, rel_path: str) -> bool:
    if not rel_path:
        return False
    candidate = (root / rel_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return candidate.exists()


def validate_disposition(
    disposition: dict, manifest: list[str], repo_root
) -> list[str]:
    """Return disposition validation errors without writing files."""
    errors: list[str] = []
    try:
        validated = SalvageDisposition.model_validate(disposition)
    except ValidationError as exc:
        errors.append(str(exc))
        raw_items = disposition.get("items") or []
    else:
        raw_items = [item.model_dump() for item in validated.items]

    normalized: list[dict] = []
    for raw in raw_items:
        item = _as_dict(raw)
        try:
            normalized.append(AssetClassification.model_validate(item).model_dump())
        except ValidationError as exc:
            errors.append(f"{item.get('path', '(unknown path)')}: {exc}")
            normalized.append(item)

    classified_paths = [str(item.get("path") or "") for item in normalized]
    classified_set = set(classified_paths)
    missing = [path for path in manifest if path not in classified_set]
    extras = [path for path in classified_paths if path and path not in set(manifest)]
    if len(normalized) != len(manifest) or missing:
        detail = ", ".join(missing) if missing else "(no missing paths identified)"
        errors.append(
            f"count mismatch: {len(manifest)} manifest paths, "
            f"{len(normalized)} classifications; missing: {detail}"
        )
    if extras:
        errors.append("classification paths not in manifest: " + ", ".join(extras))

    root = Path(repo_root).expanduser().resolve()
    for item in normalized:
        verdict = item.get("verdict")
        path = item.get("path") or "(unknown path)"
        equivalent = item.get("yamlgraph_equivalent")
        target = item.get("target_path")
        if verdict == "duplicate" and not _validate_path_under(
            root, str(equivalent or "")
        ):
            errors.append(
                f"duplicate {path!r} must name an existing yamlgraph_equivalent: "
                f"{equivalent!r}"
            )
        if verdict == "lift" and not str(target or "").startswith("ramp/salvage/"):
            errors.append(
                f"lift {path!r} target_path must start with ramp/salvage/: "
                f"{target!r}"
            )
    return errors


def _normalize_map_results(map_results: list[dict], manifest: list[str]) -> list[dict]:
    """Normalize map output, repairing each item's path from branch identity.

    The model's echoed ``path`` is a claim; the branch's ``_map_index`` into
    the manifest is the source of truth (twin filenames like ``hooks/x.sh``
    vs ``_templates/hooks/x.sh`` provoke wrong echoes — repair, don't trust).
    """
    items: list[dict] = []
    for result in sorted(map_results or [], key=lambda item: item.get("_map_index", 0)):
        item = dict(result)
        index = item.pop("_map_index", None)
        true_path = (
            manifest[index]
            if isinstance(index, int) and 0 <= index < len(manifest)
            else ""
        )
        if "_error" in item:
            items.append(
                {
                    "path": true_path,
                    "category": "asset",
                    "verdict": "obsolete",
                    "rationale": item["_error"],
                }
            )
            continue
        payload = item.get("classification") or item
        if hasattr(payload, "model_dump"):
            payload = payload.model_dump()
        if isinstance(payload, dict):
            payload = dict(payload)
            payload.pop("_map_index", None)
            if true_path:
                payload["path"] = true_path
            items.append(payload)
    return items


def merge_disposition(state: dict) -> dict:
    """Graph-facing merge: validate map output and write review drafts."""
    manifest = state.get("manifest") or []
    items = _normalize_map_results(state.get("classifications") or [], manifest)
    disposition = {
        "source_repo": state.get("source_repo") or "",
        "source_sha": state.get("source_sha") or "",
        "manifest_count": state.get("manifest_count", len(state.get("manifest") or [])),
        "items": items,
    }
    errors = validate_disposition(disposition, manifest, _repo_root())
    if errors:
        raise ValueError("; ".join(errors))
    paths = write_drafts(disposition)
    return {"disposition": disposition, "validation_errors": [], "draft_paths": paths}


def _items_by_verdict(items: list[dict]) -> dict[str, list[dict]]:
    return {
        verdict: [item for item in items if item.get("verdict") == verdict]
        for verdict in VERDICTS
    }


def _render_markdown(disposition: dict) -> str:
    items = [_as_dict(item) for item in disposition.get("items") or []]
    grouped = _items_by_verdict(items)
    lines = [
        "# Salvage disposition draft",
        "",
        f"- Source repo: `{disposition.get('source_repo', '')}`",
        f"- Source SHA: `{disposition.get('source_sha', '')}`",
        "",
    ]

    for verdict in VERDICTS:
        lines += ["", f"## {verdict}", ""]
        if not grouped[verdict]:
            lines.append("- None.")
            continue
        for item in grouped[verdict]:
            lines.append(f"### `{item.get('path', '')}`")
            lines.append("")
            lines.append(f"- Category: {item.get('category', '')}")
            lines.append(f"- Rationale: {item.get('rationale', '')}")
            if item.get("yamlgraph_equivalent"):
                lines.append(
                    f"- YAMLGraph equivalent: `{item['yamlgraph_equivalent']}`"
                )
            if item.get("target_path"):
                lines.append(f"- Target path: `{item['target_path']}`")
            lines.append("")

    lines += [
        "## Reconciliation",
        "",
        f"- Manifest count: {disposition.get('manifest_count', 0)}",
        f"- Classified count: {len(items)}",
    ]
    return "\n".join(lines).rstrip() + "\n"


def write_drafts(disposition: dict, base_dir=".") -> dict:
    """Write exactly tmp/ramp/salvage-disposition.md and .json under base_dir."""
    validated = SalvageDisposition.model_validate(disposition)
    payload = validated.model_dump()
    out_dir = Path(base_dir) / "tmp" / "ramp"
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / "salvage-disposition.md"
    json_path = out_dir / "salvage-disposition.json"
    md_path.write_text(_render_markdown(payload), encoding="utf-8")
    json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {"markdown": str(md_path), "json": str(json_path)}
