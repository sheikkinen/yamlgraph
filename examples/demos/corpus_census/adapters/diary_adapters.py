"""Diary corpus adapters for the FR-893 trap census.

Slot contract per FR-892 convention: state-dict in; discover returns a
list of item refs, extract returns one entry's text.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

MAX_ITEMS = 200  # graph max_map_items; corpus runs are month-batched
MAX_CHARS = 6000


def _require(state: dict[str, Any], key: str) -> str:
    value = state.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value


def diary_discover(state: dict[str, Any]) -> list[str]:
    """Enumerate diary entries. source: '<dir>' or '<dir>:<substr>'.

    The optional substring filter (e.g. '2026-08') selects a month batch —
    the full 1271-entry corpus exceeds the graph's map cap by design.
    """
    source = _require(state, "source")
    folder, _, needle = source.partition(":")
    root = Path(folder)
    if not root.is_dir():
        raise NotADirectoryError(f"diary_discover: not a directory: {root}")
    items = [str(p) for p in sorted(root.glob("*.md")) if needle in p.name]
    if not items:
        raise ValueError(f"diary_discover: no entries match '{needle}' in {root}")
    if len(items) > MAX_ITEMS:
        raise ValueError(
            f"diary_discover: batch of {len(items)} exceeds {MAX_ITEMS}; "
            f"narrow the source filter (got '{source}')"
        )
    return items


def diary_extract(state: dict[str, Any]) -> str:
    """One diary entry's text, size-capped."""
    item = _require(state, "item")
    path = Path(item)
    if not path.is_file():
        raise FileNotFoundError(f"diary_extract: not a file: {path}")
    return path.read_text(encoding="utf-8", errors="replace")[:MAX_CHARS]
