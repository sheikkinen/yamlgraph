"""Genesis tools — load premise file (FR-655, FR-667)."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def load_premise(state: dict[str, Any]) -> dict[str, Any]:
    """Read premise text from file specified in variables."""
    premise_file = state.get("premise_file", "")
    if not premise_file:
        raise ValueError("premise_file variable not set")
    path = Path(premise_file)
    if not path.is_absolute():
        path = Path(__file__).parent.parent.parent.parent / path
    text = path.read_text(encoding="utf-8").strip()
    return {"premise_text": text}
