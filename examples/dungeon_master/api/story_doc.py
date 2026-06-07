"""Per-session story document store for the DM v2 synopsis prototype (FR-474).

A tiny JSON file per session is the single source of truth for the synopsis
loop. The v2 overlay is intentionally small: ``tagline``, ``synopsis``,
``reviewed``. No graph or LLM touches this file — reads and writes are plain
document operations.
"""

from __future__ import annotations

import json
from pathlib import Path


def doc_path(story_dir: Path | str) -> Path:
    """Path to the per-session ``story.json``."""
    return Path(story_dir) / "story.json"


def read(story_dir: Path | str) -> dict:
    """Read the story document. Raises if it does not exist (boundary)."""
    return json.loads(doc_path(story_dir).read_text())


def write(story_dir: Path | str, doc: dict) -> None:
    """Persist the story document for a single-writer UI."""
    Path(story_dir).mkdir(parents=True, exist_ok=True)
    doc_path(story_dir).write_text(json.dumps(doc, indent=2, ensure_ascii=False))
