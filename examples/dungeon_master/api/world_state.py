"""Structured world_state ledger for DM v2 (FR-499 Phase A).

The forward-carry ledger that threads across chapters was a free-prose ``str`` —
which let the model silently contradict an earlier chapter's facts (a clan-flip,
a phantom hand-axe, a seized staff wielded again). This module replaces it with a
**typed** ledger validated at the boundary and a deterministic formatter that
renders it back into the play/close prompts.

The shape (the canonical state the next chapter inherits):

    {
      "characters": [{name, faction, status, location, inventory: [str]}],
      "objects":    [{name, holder, location}],
      "facts":      [str],
    }

The model emits this as JSON (``parse_json`` in ``chapter_close.yaml``);
:func:`parse_world_state` validates + normalizes it at the close boundary, and the
stored value is a plain ``dict`` (JSON-serializable for ``story.json``).
:func:`format_world_state` renders it back to terse prompt text — never a raw dict
repr, never into the rendered manuscript.

Pure: no LLM, no I/O.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Character(BaseModel):
    """One principal's standing in the ledger."""

    name: str = ""
    faction: str = ""
    status: str = ""
    location: str = ""
    inventory: list[str] = Field(default_factory=list)


class WorldObject(BaseModel):
    """A story object whose holder/location later chapters must not contradict."""

    name: str = ""
    holder: str = ""
    location: str = ""


class WorldState(BaseModel):
    """The end-of-chapter ledger the next chapter inherits (FR-499A)."""

    characters: list[Character] = Field(default_factory=list)
    objects: list[WorldObject] = Field(default_factory=list)
    facts: list[str] = Field(default_factory=list)


_EMPTY: dict = {"characters": [], "objects": [], "facts": []}


def parse_world_state(raw: object) -> dict:
    """Validate a raw ledger into the typed shape, tolerant at the boundary.

    A well-formed dict is validated (missing keys default to empty); anything
    else — the legacy prose string, ``None``, junk — yields an empty typed ledger
    rather than raising mid-pipeline (normalize at the boundary; never substitute
    a plausible-but-wrong value, return the empty truth).
    """
    if not isinstance(raw, dict):
        return dict(_EMPTY)
    try:
        return WorldState.model_validate(raw).model_dump()
    except Exception:
        return dict(_EMPTY)


def _is_empty(ws: dict) -> bool:
    return not (ws.get("characters") or ws.get("objects") or ws.get("facts"))


def format_world_state(ws: object) -> str:
    """Render a structured ledger to terse prompt text; ``""`` when empty.

    Deterministic (input order preserved) so the play/close prompts read a stable
    ledger and tests can pin the text. An empty or missing ledger renders to ``""``
    so callers keep their "no prior world state" opening fallback.
    """
    ledger = parse_world_state(ws)
    if _is_empty(ledger):
        return ""
    lines: list[str] = []
    if ledger["characters"]:
        lines.append("Characters:")
        for c in ledger["characters"]:
            faction = c["faction"] or "unaligned"
            status = c["status"] or "alive"
            location = c["location"] or "whereabouts unknown"
            line = f"- {c['name']} ({faction}) — {status}, at {location}"
            if c["inventory"]:
                line += f"; holds: {', '.join(c['inventory'])}"
            lines.append(line)
    if ledger["objects"]:
        lines.append("Objects:")
        for o in ledger["objects"]:
            holder = o["holder"] or "no one"
            location = o["location"] or "location unknown"
            lines.append(f"- {o['name']} — held by {holder}, at {location}")
    if ledger["facts"]:
        lines.append("Facts:")
        for fact in ledger["facts"]:
            lines.append(f"- {fact}")
    return "\n".join(lines)
