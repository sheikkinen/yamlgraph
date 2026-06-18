"""Typed chapter seam packet for DM v2 continuity handoff (FR-506).

The chapter close already carries ``world_state`` across chapter boundaries, but
continuity defects persist because turn-1 of the next chapter lacks explicit seam
obligations. This module defines a normalized, deterministic seam contract stored
on each chapter card and rendered into prompt context for chapter-open turns.

Canonical shape:

    {
      "resolved_events": [str],
      "open_threads": [str],
      "must_carry_facts": [str],
      "opening_constraints": [str],
    }

Boundary rules (load-bearing):
- All keys always present on stored packets.
- Non-list / invalid provider values normalize to ``[]``.
- ``None`` / blank / non-string list entries are dropped.
- Stable order preserved, duplicates removed by first appearance.
- Each field bounded (max items and max chars per item), truncating rather than
  dropping keys.

Pure utilities:
- ``parse_seam_packet``: tolerant boundary parse to canonical dict shape.
- ``format_seam_packet``: deterministic prompt text rendering.
- ``validate_opening_context``: deterministic seam guard over turn-1 context.
- ``validate_character_lifecycle``: deterministic chapter-open lifecycle gate.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

_MAX_ITEMS = 12
_MAX_CHARS = 240
_KEYS = (
    "resolved_events",
    "open_threads",
    "must_carry_facts",
    "opening_constraints",
)


class CharacterLifecycle(BaseModel):
    """Typed lifecycle constraint for a character at chapter seam."""

    name: str = ""
    existence_state: Literal["alive", "missing_presumed_dead", "confirmed_dead"] = (
        "alive"
    )
    visibility_mode: Literal["present", "absent", "rumor_only"] = "present"
    allowed_reappearance_from_chapter: int | None = None
    source_chapter: int = 0


class SeamPacket(BaseModel):
    """Canonical seam packet shape persisted on chapter cards."""

    resolved_events: list[str] = Field(default_factory=list)
    open_threads: list[str] = Field(default_factory=list)
    must_carry_facts: list[str] = Field(default_factory=list)
    opening_constraints: list[str] = Field(default_factory=list)
    character_lifecycle: list[CharacterLifecycle] = Field(default_factory=list)


_EMPTY: dict = {
    "resolved_events": [],
    "open_threads": [],
    "must_carry_facts": [],
    "opening_constraints": [],
    "character_lifecycle": [],
}


def _trim(text: str) -> str:
    if len(text) <= _MAX_CHARS:
        return text
    return text[: _MAX_CHARS - 1].rstrip() + "..."


def _normalize_list(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, str):
            continue
        text = item.strip()
        if not text:
            continue
        text = _trim(text)
        if text in seen:
            continue
        seen.add(text)
        out.append(text)
        if len(out) >= _MAX_ITEMS:
            break
    return out


def _normalize_int(raw: object) -> int | None:
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str) and raw.strip().isdigit():
        return int(raw.strip())
    return None


def _normalize_lifecycle(raw: object) -> list[dict]:
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        dedupe_key = " ".join(name.lower().split())
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        state = str(item.get("existence_state") or "alive").strip()
        if state not in {"alive", "missing_presumed_dead", "confirmed_dead"}:
            state = "alive"

        visibility = str(item.get("visibility_mode") or "present").strip()
        if visibility not in {"present", "absent", "rumor_only"}:
            visibility = "present"

        allowed = _normalize_int(item.get("allowed_reappearance_from_chapter"))
        if allowed is not None and allowed < 1:
            allowed = None

        source = _normalize_int(item.get("source_chapter"))
        source = source if (source is not None and source >= 0) else 0

        out.append(
            {
                "name": name,
                "existence_state": state,
                "visibility_mode": visibility,
                "allowed_reappearance_from_chapter": allowed,
                "source_chapter": source,
            }
        )
        if len(out) >= _MAX_ITEMS:
            break
    return out


def parse_seam_packet(raw: object) -> dict:
    """Normalize a provider/raw seam packet to canonical typed dict shape."""
    if not isinstance(raw, dict):
        return dict(_EMPTY)

    normalized = {k: _normalize_list(raw.get(k)) for k in _KEYS}
    normalized["character_lifecycle"] = _normalize_lifecycle(
        raw.get("character_lifecycle")
    )
    try:
        return SeamPacket.model_validate(normalized).model_dump()
    except Exception:
        return dict(_EMPTY)


def format_seam_packet(packet: object) -> str:
    """Render seam packet to deterministic prompt text; empty string when empty."""
    data = parse_seam_packet(packet)
    if not any(data[k] for k in _KEYS):
        return ""

    lines: list[str] = []
    labels = (
        ("resolved_events", "Resolved Events"),
        ("open_threads", "Open Threads"),
        ("must_carry_facts", "Must-Carry Facts"),
        ("opening_constraints", "Opening Constraints"),
    )
    for key, label in labels:
        vals = data[key]
        if not vals:
            continue
        lines.append(f"{label}:")
        lines.extend(f"- {v}" for v in vals)
    lifecycle = data["character_lifecycle"]
    if lifecycle:
        lines.append("Character Lifecycle:")
        for item in lifecycle:
            allowed = item.get("allowed_reappearance_from_chapter")
            allowed_text = (
                f", allowed_reappearance_from_chapter={allowed}"
                if allowed is not None
                else ""
            )
            lines.append(
                "- "
                f"{item.get('name')}: existence_state={item.get('existence_state')}, "
                f"visibility_mode={item.get('visibility_mode')}{allowed_text}"
            )
    return "\n".join(lines)


def _norm(s: str) -> str:
    return " ".join((s or "").lower().split())


def validate_opening_context(
    packet: object, opening_context: str
) -> list[dict[str, str]]:
    """Deterministic seam guard for chapter-open context.

    Violations:
    - ``missing_must_carry_fact``: a required fact absent from opening context.
    - ``forbidden_opening_assertion``: a forbidden assertion appears in opening
      context; constraints are encoded as ``FORBID: <phrase>`` entries.
    """
    data = parse_seam_packet(packet)
    text = _norm(opening_context)
    out: list[dict[str, str]] = []

    for fact in data["must_carry_facts"]:
        if _norm(fact) and _norm(fact) not in text:
            out.append({"type": "missing_must_carry_fact", "value": fact})

    for rule in data["opening_constraints"]:
        lower = rule.lower()
        if lower.startswith("forbid:"):
            phrase = rule.split(":", 1)[1].strip()
            if _norm(phrase) and _norm(phrase) in text:
                out.append({"type": "forbidden_opening_assertion", "value": phrase})

    return out


def validate_character_lifecycle(
    packet: object, chapter_id: int, active_cast_names: list[str]
) -> list[dict[str, str]]:
    """Deterministic lifecycle gate for chapter-open active cast.

    Violations:
    - ``early_return_violation``: active before allowed reappearance chapter.
    - ``state_contradiction_violation``: active while confirmed dead.
    - ``visibility_contradiction_violation``: active while mode is absent/rumor_only.
    """
    data = parse_seam_packet(packet)
    active = {" ".join((n or "").lower().split()) for n in active_cast_names}
    out: list[dict[str, str]] = []
    chapter = chapter_id if chapter_id >= 1 else 1

    for item in data.get("character_lifecycle", []):
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        key = " ".join(name.lower().split())
        if key not in active:
            continue

        allowed = item.get("allowed_reappearance_from_chapter")
        if isinstance(allowed, int) and chapter < allowed:
            out.append(
                {
                    "type": "early_return_violation",
                    "name": name,
                    "detail": f"present before chapter {allowed}",
                }
            )

        state = item.get("existence_state")
        if state == "confirmed_dead":
            out.append(
                {
                    "type": "state_contradiction_violation",
                    "name": name,
                    "detail": "confirmed_dead character cannot be active",
                }
            )
        if state == "missing_presumed_dead" and allowed is None:
            out.append(
                {
                    "type": "state_contradiction_violation",
                    "name": name,
                    "detail": "missing_presumed_dead character cannot be active",
                }
            )

        visibility = item.get("visibility_mode")
        if visibility in {"absent", "rumor_only"}:
            out.append(
                {
                    "type": "visibility_contradiction_violation",
                    "name": name,
                    "detail": (
                        f"visibility_mode={visibility} conflicts with active cast"
                    ),
                }
            )

    return out
