"""Reload canon pages at runtime for loop iteration freshness.

Framework workaround: data_files loads at compile time (once).
Pages generated in iteration N are invisible in iteration N+1
via data_files. This node re-reads canon/*.yaml at runtime.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def reload_canon(state: dict[str, Any]) -> dict[str, Any]:
    """Re-read all canon/*.yaml and inject current wiki into state."""
    canon_dir = Path(__file__).parent.parent / "canon"
    pages: dict[str, dict] = {}
    synopsis_text = ""
    for f in sorted(canon_dir.glob("*.yaml")):
        with open(f) as fh:
            data = yaml.safe_load(fh)
            if data and isinstance(data, dict) and "id" in data:
                pages[data["id"]] = data
                if data.get("type") == "synopsis":
                    synopsis_text = data.get("text", "")
    return {
        "canon_pages": pages,
        "canon_count": len(pages),
        "synopsis_text": synopsis_text,
    }
