"""Pure `/hello` adapter slice — no discord.py, no network (FR-812, REQ-YG-600).

Maps interaction options to hello-graph state and graph results to embed
fields. Errors surface visibly with a correlation ID; never a fallback
greeting.
"""

from __future__ import annotations

from typing import Any

STYLE_CHOICES: tuple[str, ...] = ("formal", "casual", "playful")

_NAME_MAX = 80


def options_to_state(name: str, style: str) -> dict[str, str]:
    """Validate slash-command options into hello-graph initial state."""
    cleaned = name.strip()
    if not cleaned or len(cleaned) > _NAME_MAX:
        raise ValueError(f"name must be 1-{_NAME_MAX} characters after trimming")
    if style not in STYLE_CHOICES:
        raise ValueError(f"style must be one of {STYLE_CHOICES}, got {style!r}")
    return {"name": cleaned, "style": style}


def greeting_to_embed(greeting: dict[str, Any]) -> dict[str, str]:
    """Render the hello graph's structured greeting as embed fields."""
    fields = {}
    for key in ("greeting", "emoji", "formality_level"):
        value = greeting.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"greeting result missing or empty field: {key}")
        fields[key] = value.strip()
    return {
        "title": f"{fields['emoji']} {fields['greeting']}",
        "footer": fields["formality_level"],
    }


def error_message(correlation_id: str) -> str:
    """Operator-visible failure text; details stay in server logs."""
    return f"⚠️ /hello failed — correlation id `{correlation_id}` (see server logs)"
