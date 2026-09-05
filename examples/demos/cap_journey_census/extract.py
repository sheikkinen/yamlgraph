"""CAP journey census — discover + extract (mechanical facts before the model call).

Research plan: docs/2026-09-05-research-plan-cap-journey-census.md.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
MAX_ITEMS = 250
FR_HEAD_LINES = 40
MAX_HITS = 12
_ID_RE = re.compile(r"^(CAP|FR)-\d+$")
_CODE_DIRS = ["examples", "graphs", "scripts", ".github", ".chaplain", "yamlgraph"]
_CODE_FILES = ["pyproject.toml", ".pre-commit-config.yaml"]
_CODE_EXTS = ("py", "yaml", "yml", "sh", "toml", "json")
_CONSUMER_PATHS = [f"{d}/*.{e}" for d in _CODE_DIRS for e in _CODE_EXTS] + _CODE_FILES
_CONSUMER_EXCLUDE = [
    "*.log",
    ".chaplain/done",
    ".chaplain/demos",
    ".chaplain/failed",
    "*/proofs/*",
    "*/fixtures/*",
    "examples/demos/philosopher_book",
]
_DOC_PATHS = [
    "reference",
    "README.md",
    "ARCHITECTURE.md",
    "examples/*.md",
    ".github/*.md",
]
_INCIDENT_PATHS = ["docs/diary", "feature-requests"]
_TOKEN_STOP = frozenset(
    {
        "prompts",
        "models",
        "utils",
        "tools",
        "schemas",
        "config",
        "state",
        "graph",
        "nodes",
        "executor",
        "cli",
        "main",
    }
)


def _require(state: dict[str, Any], key: str) -> str:
    value = state.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value


# ---------------------------------------------------------------- discover
def cap_discover(state: dict[str, Any]) -> list[str]:
    """source: 'capabilities' | 'capabilities:<regex on filename>' | 'capabilities:ids=CAP-1,CAP-2'."""
    source = _require(state, "source")
    folder, _, selector = source.partition(":")
    root = Path(folder)
    if not root.is_dir():
        raise NotADirectoryError(f"cap_discover: not a directory: {root}")
    files = sorted(root.glob("CAP-*.yaml"))
    if selector.startswith("ids="):
        wanted = {i.strip() for i in selector[4:].split(",") if i.strip()}
        files = [
            f
            for f in files
            if f.name.split("-", 2)[0] + "-" + f.name.split("-", 2)[1] in wanted
        ]
        missing = wanted - {
            f.name.split("-", 2)[0] + "-" + f.name.split("-", 2)[1] for f in files
        }
        if missing:
            raise ValueError(f"cap_discover: ids not found: {sorted(missing)}")
    elif selector:
        files = [f for f in files if re.search(selector, f.name)]
    if not files:
        raise ValueError(f"cap_discover: no CAP files match '{source}'")
    if len(files) > MAX_ITEMS:
        raise ValueError(f"cap_discover: {len(files)} exceeds {MAX_ITEMS}")
    return [str(f.relative_to(REPO_ROOT)) if f.is_absolute() else str(f) for f in files]


# ----------------------------------------------------------------- extract
def _git_grep(pattern: str, pathspecs: list[str], exclude: list[str]) -> list[str]:
    cmd = ["git", "grep", "-l", "-I", "-F", "-e", pattern, "--", *pathspecs]
    cmd += [f":(exclude){e}" for e in exclude]
    proc = subprocess.run(
        cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )
    if proc.returncode not in (0, 1):
        raise RuntimeError(f"git grep failed: {proc.stderr.strip()}")
    return sorted(p for p in proc.stdout.splitlines() if p)


def _fr_ids(cap: dict[str, Any]) -> list[str]:
    raw = cap.get("fr") or cap.get("feature_request") or ""
    values = raw if isinstance(raw, list) else [raw]
    return [str(v).strip() for v in values if _ID_RE.match(str(v).strip() or "")]


def _fr_head(fr_id: str) -> str:
    hits = [
        p
        for p in (REPO_ROOT / "feature-requests").glob(f"{fr_id}-*.md")
        if ".judgement" not in p.name and ".research" not in p.name
    ]
    if not hits:
        return ""
    lines = (
        hits[0]
        .read_text(encoding="utf-8", errors="replace")
        .splitlines()[:FR_HEAD_LINES]
    )
    return "\n".join(lines)


def _module_needles(cap: dict[str, Any]) -> list[str]:
    """Import-precise needles: dotted path for yamlgraph modules, bare token for legacy names."""
    mods: list[str] = list(cap.get("modules") or [])
    for req in cap.get("requirements") or []:
        mods.extend(req.get("modules") or [])
    needles: list[str] = []
    for m in mods:
        m = str(m).strip().rstrip("/")
        if not m or m.startswith(("tests/", "examples/", "docs/")):
            continue
        if m.startswith("yamlgraph/"):
            needle = m.removesuffix(".py").removesuffix("/__init__").replace("/", ".")
        else:
            needle = m.removesuffix(".py").split("/")[-1].split(".")[0]
            if len(needle) < 6 or needle in _TOKEN_STOP:
                continue
        if needle not in needles:
            needles.append(needle)
    return needles[:8]


def _mechanical(cap: dict[str, Any], cap_path: str) -> dict[str, Any]:
    cap_id = str(cap.get("id", ""))
    fr_ids = _fr_ids(cap)
    own_fr_files = [f"feature-requests/{f}-*" for f in fr_ids]
    exclude = [cap_path, HERE.relative_to(REPO_ROOT).as_posix(), *_CONSUMER_EXCLUDE]
    consumers: set[str] = set()
    for needle in [cap_id, *fr_ids]:
        consumers.update(_git_grep(needle, _CONSUMER_PATHS, exclude))
    module_consumers: set[str] = set()
    own_modules = {str(m).rstrip("/") for m in cap.get("modules") or []}
    for needle in _module_needles(cap):
        module_consumers.update(
            p
            for p in _git_grep(needle, _CONSUMER_PATHS, exclude)
            if p not in own_modules
        )
    docs: set[str] = set()
    for needle in [cap_id, *fr_ids]:
        docs.update(_git_grep(needle, _DOC_PATHS, [cap_path]))
    incidents: set[str] = set()
    for needle in [cap_id, *fr_ids]:
        incidents.update(_git_grep(needle, _INCIDENT_PATHS, [cap_path, *own_fr_files]))
    req_ids = [str(r.get("id")) for r in cap.get("requirements") or [] if r.get("id")]
    tests = 0
    for rid in req_ids:
        tests += len(_git_grep(f'"{rid}"', ["tests"], []))
    return {
        "consumers_by_id": sorted(consumers)[:MAX_HITS],
        "consumers_by_module": sorted(module_consumers)[:MAX_HITS],
        "consumer_count": len(consumers | module_consumers),
        "doc_mentions": len(docs),
        "incident_files": len(incidents),
        "diary_mentions": sum(1 for p in incidents if p.startswith("docs/diary/")),
        "test_files_tagged": tests,
        "req_ids": req_ids,
    }


def cap_extract(state: dict[str, Any]) -> str:
    """One CAP's evidence bundle as a JSON string."""
    item = _require(state, "item")
    path = REPO_ROOT / item
    if not path.is_file():
        raise FileNotFoundError(f"cap_extract: not a file: {path}")
    cap_text = path.read_text(encoding="utf-8", errors="replace")
    cap = yaml.safe_load(cap_text) or {}
    fr_ids = _fr_ids(cap)
    bundle = {
        "item_ref": item,
        "id": cap.get("id"),
        "name": cap.get("name"),
        "status": cap.get("status") or "active",
        "fr": fr_ids or [str(cap.get("fr") or cap.get("feature_request") or "")],
        "cap_yaml": cap_text[:5000],
        "fr_head": _fr_head(fr_ids[0]) if fr_ids else "",
        "mechanical": _mechanical(cap, item),
    }
    return json.dumps(bundle, ensure_ascii=False)
