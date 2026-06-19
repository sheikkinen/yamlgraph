"""Final Cut assembly for DM v2 chapters (FR-536).

The deterministic seam that turns a chapter's played arc into final prose: beat
grouping, per-turn performance cards, the dead-character and possession
constraints (FR-519), the Final Cut context assembly (FR-492), and the single
Final Cut graph invocation. Split from the turn play loop (:mod:`turn_ops`) so
the finish — read-only over the recorded arc — sits apart from the loop that
records it. Reads turn primitives from :mod:`turn_state` and the cast admission
from :mod:`chapter_open`.
"""

from __future__ import annotations

from examples.dungeon_master.api import chapter_nav
from examples.dungeon_master.api.chapter_open import build_allowed_scene_cast
from examples.dungeon_master.api.graph_app import clean_text, get_app
from examples.dungeon_master.api.lifecycle_resolver import (
    _norm_name,
    protected_cast_names,
)
from examples.dungeon_master.api.seam_packet import parse_seam_packet
from examples.dungeon_master.api.tree import FINAL_CUT_GRAPH
from examples.dungeon_master.api.turn_state import (
    chapter_beat_list,
    chapter_beats,
    chapter_turns,
    climax_turn,
)
from examples.dungeon_master.api.world_state import parse_world_state

_MAX_CUE_FIELD_CHARS = 240


def _trim_value(value: object, *, max_chars: int = _MAX_CUE_FIELD_CHARS) -> str:
    """Stringify and bound payload fields without dropping schema keys."""
    text = str(value or "")
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def _cast_order(doc: dict) -> list[tuple[str, str]]:
    """Return cast order as ``[(char_id, display_name), ...]``."""
    chars = doc.get("characters", {})
    roster = list(chars.get("roster") or [])
    cards = chars.get("cards") or {}
    return [
        (char_id, (cards.get(char_id, {}).get("name") or char_id)) for char_id in roster
    ]


def _turn_performance_cards(doc: dict, turn: dict) -> list[dict]:
    """Stable-schema performance cards for one turn in cast order (FR-505 C1)."""
    intents = (turn.get("intents") or {}) if isinstance(turn, dict) else {}
    cards: list[dict] = []
    for char_id, name in _cast_order(doc):
        perf = intents.get(char_id) or {}
        cards.append(
            {
                "name": name,
                "intent": _trim_value(perf.get("intent", "")),
                "dialogue": _trim_value(perf.get("dialogue", "")),
                "expression": _trim_value(perf.get("expression", "")),
            }
        )
    return cards


def beat_turn_groups(doc: dict, cid: str) -> list[dict]:
    """Group chapter turns by first-advanced beat with connective carryover.

    Each turn is assigned to exactly one beat group. A turn that advances no new
    beats attaches to the most-recently-advanced beat (or the first beat when no
    beat has advanced yet), so no recap/performance card is orphaned.
    """
    turns = chapter_turns(doc, cid)
    beats = chapter_beat_list(doc, cid) or chapter_beats(doc, cid)
    if not beats:
        return []

    # Preserve beat order while admitting any unexpected director beat text.
    ordered = list(
        dict.fromkeys(beats + [b for b in chapter_beats(doc, cid) if b not in beats])
    )
    groups = {beat: {"beat": beat, "turns": [], "is_climax": False} for beat in ordered}

    seen: set[str] = set()
    owner = ordered[0]
    climax_n = climax_turn(doc, cid)

    for t in turns:
        n = int(t.get("n", len(groups) + 1))
        rec = (t.get("direction") or {}).get("beats_satisfied") or []
        current = [b for b in rec if isinstance(b, str) and b in groups]
        advanced = [b for b in current if b not in seen]
        seen.update(current)
        if advanced:
            owner = advanced[-1]

        groups[owner]["turns"].append(
            {
                "n": n,
                "recap": _trim_value(
                    (t.get("recap") or {}).get("text", ""), max_chars=600
                ),
                "intents": _turn_performance_cards(doc, t),
                "advanced_beats": advanced,
            }
        )

        if n == climax_n:
            groups[owner]["is_climax"] = True

    return [groups[b] for b in ordered]


def _format_beat_groups(groups: list[dict]) -> str:
    """Render beat groups for prompt consumption."""
    blocks: list[str] = []
    for i, group in enumerate(groups, start=1):
        beat = group.get("beat", "")
        climax = "  <-- CLIMAX BEAT" if group.get("is_climax") else ""
        lines = [f"Beat {i}: {beat}{climax}"]
        for turn in group.get("turns") or []:
            lines.append(f"  Turn {turn.get('n')}: {turn.get('recap', '')}")
            for perf in turn.get("intents") or []:
                name = perf.get("name", "")
                intent = perf.get("intent", "")
                dialogue = perf.get("dialogue", "")
                expression = perf.get("expression", "")
                lines.append(f"    - {name} intent: {intent}")
                if dialogue:
                    lines.append(f"      dialogue: {dialogue}")
                if expression:
                    lines.append(f"      expression: {expression}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


# FR-519: status tokens that mean a character has died (within-chapter death
# signal from the close-graph world_state lane).
_DEAD_STATUS_TOKENS = {"dead", "slain", "killed", "deceased", "fallen"}

# FR-521 J2: within a chapter, "presumed dead / swept away" is a death-point too —
# the character must not keep acting after it. The widening is chapter-scoped: it
# feeds ONLY the within-chapter lane (read from this chapter's ``closed``). The
# before-open bar stays confirmed_dead only, so a legitimate synopsis return
# (presumed-dead → reappears) is never barred at the next chapter's open.
_PRESUMED_DEAD_TOKENS = {"missing_presumed_dead", "presumed_dead"}
_WITHIN_DEATH_STATUS_TOKENS = _DEAD_STATUS_TOKENS | _PRESUMED_DEAD_TOKENS
_WITHIN_DEATH_EXISTENCE_STATES = {"confirmed_dead"} | _PRESUMED_DEAD_TOKENS


def dead_character_names(
    doc: dict, cid: str, closed: dict | None = None
) -> tuple[list[str], list[str]]:
    """``(dead_before_open, dead_within_chapter)`` display names for chapter ``cid``.

    Two distinct lifecycle classes the final cut must treat differently (FR-519):

    - ``dead_before_open``: confirmed-dead at chapter open, read from the
      **inherited** seam (the prior chapter's close) — the FR-510 cross-chapter
      case; these characters must not appear at all.
    - ``dead_within_chapter``: died **during** this chapter, read from the
      close-graph output ``closed`` (its ``world_state`` dead-status characters and
      its closing seam ``character_lifecycle`` rows). They act legitimately up to
      their death and must not act after it.

    ``closed`` must be threaded in, not read back from the doc: at final-cut time
    the chapter's own ``world_state`` is not yet committed (it is derived *after*
    ``invoke_final_cut`` returns), so reading the doc card would see the stale
    prior state (FR-519 B1). A character dead at open is never re-listed as within.
    """
    prior_seam = parse_seam_packet(chapter_nav.inherited_seam_packet(doc, cid))
    before: dict[str, str] = {}
    for item in prior_seam.get("character_lifecycle") or []:
        if str(item.get("existence_state") or "").strip() != "confirmed_dead":
            continue
        name = str(item.get("name") or "").strip()
        if name:
            before.setdefault(_norm_name(name), name)

    within: dict[str, str] = {}
    if isinstance(closed, dict):
        ws = parse_world_state(closed.get("world_state"))
        for c in ws.get("characters", []):
            if (
                str(c.get("status") or "").strip().lower()
                in _WITHIN_DEATH_STATUS_TOKENS
            ):
                name = str(c.get("name") or "").strip()
                if name:
                    within.setdefault(_norm_name(name), name)
        close_seam = parse_seam_packet(closed.get("seam_packet"))
        for item in close_seam.get("character_lifecycle") or []:
            if (
                str(item.get("existence_state") or "").strip()
                not in _WITHIN_DEATH_EXISTENCE_STATES
            ):
                continue
            name = str(item.get("name") or "").strip()
            if name:
                within.setdefault(_norm_name(name), name)

    for key in list(within):
        if key in before:
            within.pop(key, None)

    return list(before.values()), list(within.values())


def _possession_facts(doc: dict, cid: str, closed: dict | None = None) -> str:
    """Lines of who-holds-what the chapter's prose must not contradict (FR-519).

    Sourced from the **inherited** ledger (the prior chapter's committed
    ``world_state`` — the persistent, correct possession truth at chapter open),
    overlaid with the close-graph ``closed`` emission when present so an object
    picked up within the chapter is also covered. Deterministic order: inherited
    first, then close-emission overrides in place. ``""`` when nothing is tracked.
    """
    char_inv: dict[str, tuple[str, list[str]]] = {}
    obj_holder: dict[str, tuple[str, str]] = {}

    def _absorb(ws: dict) -> None:
        for c in ws.get("characters", []):
            name = str(c.get("name") or "").strip()
            items = [
                str(i).strip() for i in (c.get("inventory") or []) if str(i).strip()
            ]
            if name and items:
                char_inv[_norm_name(name)] = (name, items)
        for o in ws.get("objects", []):
            name = str(o.get("name") or "").strip()
            holder = str(o.get("holder") or "").strip()
            if name and holder:
                obj_holder[_norm_name(name)] = (name, holder)

    _absorb(parse_world_state(chapter_nav.inherited_world_state(doc, cid)))
    if isinstance(closed, dict):
        _absorb(parse_world_state(closed.get("world_state")))

    lines = [f"{disp} holds: {', '.join(items)}" for disp, items in char_inv.values()]
    lines += [f"the {disp} is held by {holder}" for disp, holder in obj_holder.values()]
    return "\n".join(lines)


def final_cut_context(doc: dict, cid: str, closed: dict | None = None) -> dict:
    """Assemble chapter ``cid``'s finished arc as Final Cut graph variables (FR-492).

    A pure function over the story ``doc``: the chapter ``summary`` as the scene
    plan (standing in for the retired ``key_scene``), **every** played turn recap
    in order (``chapters.cards[cid].turns``, not the flat ``doc["turns"]`` the
    pre-chapter shape used), each turn's director ``phase`` with the pivotal turn
    marked, the beats the director confirmed (:func:`chapter_beats`), and a derived
    ``climax`` marker. This is the deterministic seam — the model is handed the
    assembled context and asked only for prose, never to recompute the arc's
    structure.

    FR-519 threads the chapter's committed physical state into the prompt as a hard
    constraint: ``dead_before_open`` / ``dead_within_chapter`` (lifecycle split, the
    within class sourced from the close-graph ``closed`` since the chapter's own
    ``world_state`` is not yet committed) and ``possession_facts`` (who-holds-what
    from the inherited ledger). Each is an empty string when nothing applies, so a
    chapter with no deaths or tracked objects renders an unchanged prompt.
    """
    card = chapter_nav.chapter_card(doc, cid)
    summary = card.get("summary", "")
    turns = chapter_turns(doc, cid)
    climax_n = climax_turn(doc, cid)
    groups = beat_turn_groups(doc, cid)
    beats = chapter_beats(doc, cid)
    before_open, within_chapter = dead_character_names(doc, cid, closed)
    allowed_cast = build_allowed_scene_cast(doc, cid)
    return {
        "key_scene": summary,
        "arc": _format_beat_groups(groups),
        "beats": "\n".join(f"- {b}" for b in beats),
        "climax": f"Turn {climax_n}" if turns else "",
        "beat_groups": _format_beat_groups(groups),
        "dead_before_open": ", ".join(before_open),
        "dead_within_chapter": ", ".join(within_chapter),
        "possession_facts": _possession_facts(doc, cid, closed),
        "allowed_cast": ", ".join(allowed_cast),
        "protected_cast": ", ".join(protected_cast_names(doc, cid)),
    }


async def invoke_final_cut(
    doc: dict,
    cid: str,
    instruction: str = "",
    draft: str = "",
    closed: dict | None = None,
) -> str:
    """Compose chapter ``cid``'s continuous final text from its whole arc (FR-492).

    Runs ``final_cut.yaml`` once over :func:`final_cut_context` plus the current
    draft and a writer's instruction, and returns the cleaned narration — the
    chapter's beat-faithful final text. Reads the chapter's played turns; writes
    none of them. ``closed`` (the close-graph output) is threaded through so the
    within-chapter death constraint is available before the chapter's own
    ``world_state`` is committed (FR-519).
    """
    result = await get_app(FINAL_CUT_GRAPH).ainvoke(
        {
            **final_cut_context(doc, cid, closed),
            "draft": draft,
            "instruction": instruction,
            "final_cut": "",
        }
    )
    return clean_text(result.get("final_cut"))
