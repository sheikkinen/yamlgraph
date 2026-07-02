"""Genesis tools — load premise file and parse roster text (FR-655)."""

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


def parse_roster(state: dict[str, Any]) -> dict[str, Any]:
    """Parse roster text (one name per line) into a list of names."""
    roster_text = state.get("roster_text", "")
    names = [n.strip() for n in roster_text.strip().splitlines() if n.strip()]
    return {"character_names": names}
