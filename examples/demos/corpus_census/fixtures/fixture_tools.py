"""Fixture corpus adapters for the corpus-census demo."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def discover(state: dict[str, Any]) -> list[str]:
    """Return sorted text-file paths under the provided fixture source."""
    source = state.get("source")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("source is required")
    root = Path(source)
    if not root.is_dir():
        raise NotADirectoryError(f"source is not a directory: {root}")
    items = [str(path) for path in sorted(root.glob("*.txt"))]
    if not items:
        raise ValueError(f"source contains no .txt files: {root}")
    return items


def extract(state: dict[str, Any]) -> str:
    """Return one corpus item's text content."""
    item = state.get("item")
    if not isinstance(item, str) or not item.strip():
        raise ValueError("item is required")
    path = Path(item)
    if not path.is_file():
        raise FileNotFoundError(f"item is not a file: {path}")
    return path.read_text(encoding="utf-8")
