"""Fixture commit adapters for the pattern/model census demo."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_records(source: str) -> list[dict[str, Any]]:
    path = Path(source)
    if not path.is_file():
        raise FileNotFoundError(f"source is not a fixture JSON file: {path}")
    records = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(records, list) or not records:
        raise ValueError("fixture source must contain a non-empty JSON array")
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"fixture record {index} must be an object")
    return records


def discover(state: dict[str, Any]) -> list[str]:
    """Return fixture SHAs in file order."""
    source = state.get("source")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("source is required")
    return [str(record["sha"]) for record in _load_records(source)]


def extract(state: dict[str, Any]) -> dict[str, str]:
    """Return one fixture commit metadata record."""
    source = state.get("source")
    item = state.get("item")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("source is required")
    if not isinstance(item, str) or not item.strip():
        raise ValueError("item is required")
    for record in _load_records(source):
        if record.get("sha") == item:
            return {
                "repo": str(record["repo"]),
                "sha": str(record["sha"]),
                "date": str(record["date"]),
                "subject": str(record["subject"]),
                "shortstat": str(record["shortstat"]),
            }
    raise KeyError(f"fixture commit not found: {item}")
