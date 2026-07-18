"""FR-748 collector — deterministic corpus scan (REQ-YG-566).

Population id = filename stem, NEVER a prefix regex (judgement F2: the
unprefixed elder files are exactly the graveyard exemplars a naive
``FR-\\d+`` parser would drop). Companions (TEMPLATE.md,
``*.judgement.md``) are excluded and counted (F4). Headerless files are
reported by id, never dropped. Dates come from one ``git log`` pass,
never from header text (F3).
"""

from __future__ import annotations

import re
import subprocess
from collections import defaultdict
from pathlib import Path

import yaml

_STATUS_RE = re.compile(r"^\*\*Status:\*\*\s*(.+)$", re.M)
_SECTION_RE = re.compile(r"^##\s+(Problem|Summary|Purpose|Motivation)\b", re.M)
_PATH_RE = re.compile(
    r"\b(?:yamlgraph|examples|scripts|services|graphs|prompts|tests)/[\w./-]+\.\w{2,4}\b"
)

# F3: first-word normalization with a visible `other` bucket — a real
# status taxonomy is its own FR with its own consumer (purge list).
_KNOWN_BUCKETS = {
    "proposed",
    "draft",
    "judged",
    "approved",
    "implemented",
    "enforced",
    "completed",
    "complete",
    "rejected",
    "condemned",
}
EXCERPT_LINES = 10
CHUNK_SIZE = 50


def _bucket(status_line: str | None) -> str:
    if not status_line:
        return "other"
    head = status_line.split()[0].split("(")[0].strip(" —-:").lower()
    if "reject" in status_line.lower():
        return "rejected"
    return head if head in _KNOWN_BUCKETS else "other"


def _excerpt(text: str) -> str:
    match = _SECTION_RE.search(text)
    if not match:
        return "\n".join(text.splitlines()[:EXCERPT_LINES])
    lines = text[match.end() :].lstrip("\n").splitlines()
    body = [ln for ln in lines[: EXCERPT_LINES + 2] if not ln.startswith("## ")]
    return "\n".join(body[:EXCERPT_LINES]).strip()


def _last_activity(fr_dir: Path) -> dict[str, str]:
    """One git log --name-only pass: file → last commit date (F3)."""
    try:
        out = subprocess.run(
            [
                "git",
                "-C",
                str(fr_dir.parent),
                "log",
                "--name-only",
                "--pretty=format:@%as",
                "--",
                fr_dir.name,
            ],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {}
    dates: dict[str, str] = {}
    current = ""
    for line in out.splitlines():
        if line.startswith("@"):
            current = line[1:]
        elif line.strip() and line not in dates:
            dates[Path(line).stem] = current
    return dates


def _module_index(project_dir: Path) -> dict[str, list[str]]:
    """CAP registry REQ→modules join when the convention exists."""
    caps = project_dir / "capabilities"
    index: dict[str, list[str]] = {}
    if not caps.is_dir():
        return index
    for cap_file in sorted(caps.glob("*.yaml")):
        try:
            payload = yaml.safe_load(cap_file.read_text()) or {}
        except yaml.YAMLError:
            continue
        fr = str(payload.get("fr") or "")
        modules = payload.get("modules") or []
        if fr and modules:
            index.setdefault(fr, []).extend(modules)
    return index


def collect_frs(state: dict) -> dict:
    """Scan {project_dir}/feature-requests/ → digests + notes (merged)."""
    project_dir = Path(state["project_dir"]).expanduser()
    fr_dir = project_dir / "feature-requests"
    if not fr_dir.is_dir():
        raise FileNotFoundError(
            f"No feature-requests/ directory under {project_dir} — "
            "point project_dir at a repo root that has one"
        )
    dates = _last_activity(fr_dir)
    digests: list[dict] = []
    excluded = 0
    headerless: list[str] = []
    for path in sorted(fr_dir.glob("*.md")):
        if path.name == "TEMPLATE.md" or path.name.endswith(".judgement.md"):
            excluded += 1
            continue
        fr_id = path.stem  # F2: never a prefix regex
        text = path.read_text(errors="ignore")
        match = _STATUS_RE.search(text)
        status = match.group(1).strip() if match else None
        if status is None:
            headerless.append(fr_id)
        title_line = next(
            (ln.lstrip("# ").strip() for ln in text.splitlines() if ln.startswith("#")),
            fr_id,
        )
        digests.append(
            {
                "id": fr_id,
                "title": title_line,
                "status": status or "(no status header)",
                "status_bucket": _bucket(status),
                "excerpt": _excerpt(text),
                "paths": sorted(set(_PATH_RE.findall(text)))[:12],
                "last_activity": dates.get(fr_id, ""),
            }
        )
    return {
        "fr_digests": digests,
        "fr_population": [d["id"] for d in digests],
        "fr_chunks": chunk_digests(digests),
        "module_index": _module_index(project_dir),
        "parse_notes": {"excluded": excluded, "headerless": headerless},
    }


def chunk_digests(digests: list[dict], size: int = CHUNK_SIZE) -> list[dict]:
    """Every population id in exactly one chunk; block pre-rendered by
    code (formatting is mechanizable, not the model's job)."""
    chunks: list[dict] = []
    for i in range(0, len(digests), size):
        part = digests[i : i + size]
        block = "\n\n".join(
            f"[{d['id']}] {d['title']} — {d['status']}\n{d['excerpt']}" for d in part
        )
        chunks.append(
            {
                "chunk_id": f"c{len(chunks) + 1}",
                "ids": [d["id"] for d in part],
                "digest_block": block,
            }
        )
    return chunks


def status_histogram(digests: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for d in digests:
        counts[d["status_bucket"]] += 1
    return dict(sorted(counts.items(), key=lambda kv: -kv[1]))
