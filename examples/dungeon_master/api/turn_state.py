"""Per-chapter turn-record accessors for DM v2 (FR-536).

The leaf primitives the play loop, chapter-open gate, and final cut all read:
pure, read-mostly views over a chapter's played turns
(``chapters.cards[<cid>]["turns"]``, FR-491 Amendment C) plus the chapter's
turn budget. Kept dependency-light (only :mod:`chapter_nav`) so it can sit
under every other turn module without an import cycle.
"""

from __future__ import annotations

from examples.dungeon_master.api import chapter_nav


def chapter_turns(doc: dict, cid: str) -> list[dict]:
    """Read-only view of chapter ``cid``'s played turns (FR-491 C; empty if none)."""
    return chapter_nav.chapter_turns(doc, cid)


def chapter_beat_list(doc: dict, cid: str) -> list[str]:
    """Chapter ``cid``'s enumerated key-event beats (FR-503; empty if none).

    The finite contract the director selects from and the play loop drives toward.
    Non-empty by the FR-504 boundary contract (``outline_ops._require_beats``); a
    chapter persisted before that contract — or one with no card — yields ``[]``.
    """
    return list(chapter_nav.chapter_card(doc, cid).get("beats") or [])


def reset_chapter_for_replay(doc: dict, cid: str) -> None:
    """Wipe chapter ``cid``'s played state so it can be re-played from its inherited start.

    Single named site for the doc-shape surgery a chapter replay requires (FR-522
    J1): drop this chapter's played ``turns``, clear its ``reviewed`` flag, and pop
    its own committed ``world_state``/``seam_packet`` (the close-graph emissions),
    so the next play derives them afresh. It touches ONLY ``cid``'s card — the
    inherited start (every prior chapter's committed state) is never read here and
    never mutated, which is what makes a replay a controlled experiment.
    """
    card = doc.get("chapters", {}).get("cards", {}).get(cid)
    if not isinstance(card, dict):
        return
    card["turns"] = []
    card["reviewed"] = False
    card.pop("world_state", None)
    card.pop("seam_packet", None)


def turn_record(doc: dict, cid: str, n: int) -> dict:
    """Chapter ``cid``'s ``turns[n-1]`` record ``{n, intents, recap}`` (created if absent).

    Turns are stored per chapter under ``chapters.cards[<cid>]["turns"]`` (FR-491
    Amendment C), never the flat ``doc["turns"]``: each chapter plays its own loop.
    """
    cards = doc.setdefault("chapters", {}).setdefault("cards", {})
    card = cards.setdefault(cid, {})
    turns = card.setdefault("turns", [])
    while len(turns) < n:
        m = len(turns) + 1
        turns.append({"n": m, "intents": {}, "recap": {"text": "", "reviewed": False}})
    rec = turns[n - 1]
    rec.setdefault("intents", {})
    rec.setdefault("recap", {"text": "", "reviewed": False})
    return rec


def turn_direction(doc: dict, cid: str, n: int) -> dict:
    """The director's ``direction`` side-channel for chapter ``cid``'s turn ``n``.

    A structured ``{phase, establishing, beats_satisfied, scene_complete, steer,
    continuity}`` judgement produced alongside the turn's intents (FR-479 J4);
    the recap entry shape stays ``{text, reviewed}`` (FR-477 J3). Empty if absent.
    """
    turns = chapter_turns(doc, cid)
    if n < 1 or len(turns) < n:
        return {}
    return turns[n - 1].get("direction") or {}


def turn_intents(doc: dict, chars: dict, cid: str, n: int) -> list[dict]:
    """Chapter ``cid``'s turn ``n`` intents as ordered performance cards (cast order).

    Each card is ``{name, thinking, intent, dialogue, expression}`` (FR-486): the
    private ``thinking`` and the decisive ``intent`` the arc reads, plus the
    outward performance layer — the spoken ``dialogue`` and the visible
    ``expression`` that projects the thinking. A turn played before FR-486 carries
    only the first two keys; the new keys default to ``""`` (a silent character is
    legitimate, not a defect — an additive side-channel, never a raise).
    """
    turns = chapter_turns(doc, cid)
    if n < 1 or len(turns) < n:
        return []
    intents = turns[n - 1].get("intents", {})
    out: list[dict] = []
    for char_id in chars["roster"]:
        if char_id in intents:
            perf = intents[char_id]
            out.append(
                {
                    "name": chars["cards"].get(char_id, {}).get("name") or char_id,
                    "thinking": perf.get("thinking", ""),
                    "intent": perf.get("intent", ""),
                    "dialogue": perf.get("dialogue", ""),
                    "expression": perf.get("expression", ""),
                }
            )
    return out


def prior_intents(doc: dict, cid: str, n: int) -> dict:
    """Each character's intent from chapter ``cid``'s turn ``n-1`` (empty before turn 2)."""
    turns = chapter_turns(doc, cid)
    if n < 2 or len(turns) < n - 1:
        return {}
    prev = turns[n - 2].get("intents", {})
    return {char_id: v.get("intent", "") for char_id, v in prev.items()}


def chapter_recaps_text(doc: dict, cid: str) -> str:
    """Chapter ``cid``'s played recaps, in order, as one labelled block (FR-491 B)."""
    lines = []
    for t in chapter_turns(doc, cid):
        txt = (t.get("recap") or {}).get("text", "")
        if txt.strip():
            lines.append(f"Turn {t.get('n')}: {txt}")
    return "\n\n".join(lines)


def chapter_scene_complete(doc: dict, cid: str) -> bool:
    """Whether any of chapter ``cid``'s played turns reported the scene complete."""
    return any(
        (t.get("direction") or {}).get("scene_complete")
        for t in chapter_turns(doc, cid)
    )


# A chapter's only natural exit is its director emitting ``scene_complete``. A
# director that never resolves (observed live: a diffusion provider stuck in the
# "rising" phase for 91 turns) would consume the entire book turn_cap on a single
# chapter. This per-chapter turn budget is the deterministic backstop that bounds
# any provider: a chapter force-closes once it has played this many turns without
# resolving. Generous above the natural chapter length (~6 turns observed) so it
# rarely triggers on a well-behaved director, yet caps a runaway (FR-501).
CHAPTER_TURN_CAP = 16


def chapter_should_close(doc: dict, cid: str, n: int) -> bool:
    """Whether chapter ``cid`` should close after its turn ``n`` (FR-501).

    True when the director reported ``scene_complete`` for the turn, OR the chapter
    has played its full per-chapter turn budget (``CHAPTER_TURN_CAP``) without ever
    resolving — the safety valve that stops a director which never declares the
    scene complete from running the chapter away with the whole book budget.
    """
    if turn_direction(doc, cid, n).get("scene_complete"):
        return True
    return n >= CHAPTER_TURN_CAP


def climax_turn(doc: dict, cid: str) -> int:
    """The 1-based turn index chapter ``cid`` turns on, derived from the phases (FR-492).

    The director's ``phase`` is monotonic (FR-481), so the first turn to reach
    ``"climax"`` is the pivotal beat. When no turn ever recorded a climax phase,
    fall back to the turn that reported ``scene_complete``; failing even that, the
    last turn. Pure code over **this chapter's** played turns
    (``chapters.cards[cid].turns``) — the Final Cut is handed this marker rather
    than asked to recompute what the recorded arc already knows (FR-482 law).
    """
    turns = chapter_turns(doc, cid)
    for t in turns:
        if (t.get("direction") or {}).get("phase") == "climax":
            return int(t.get("n", turns.index(t) + 1))
    for t in turns:
        if (t.get("direction") or {}).get("scene_complete"):
            return int(t.get("n", turns.index(t) + 1))
    return int(turns[-1].get("n", len(turns))) if turns else 0


def chapter_beats(doc: dict, cid: str) -> list[str]:
    """The beats chapter ``cid`` satisfied, accumulated across its turns (FR-492).

    The fidelity signal the Final Cut must preserve. The director records
    ``beats_satisfied`` cumulatively per turn as canonical beat TEXT resolved from
    the finite enumerated list (``_apply_beat_ledger``, FR-503/FR-504). This unions
    the chapter's turns' beats, de-duplicated and order-preserving, so the finish
    is handed the canonical beats the play loop confirmed rather than re-deriving
    them.
    """
    beats: list[str] = []
    for t in chapter_turns(doc, cid):
        for b in (t.get("direction") or {}).get("beats_satisfied") or []:
            if b not in beats:
                beats.append(b)
    return beats


def _chapter_cast_exits(doc: dict, cid: str, n: int) -> list[str]:
    """Names the director benched in chapter ``cid``'s turns *before* ``n`` (FR-521 S2).

    The director's structured ``cast_exits`` field names roster members who have
    left the scene this chapter — died, been swept away — and must not act again.
    Accumulated (union) across every prior turn so a single later clean turn cannot
    resurrect a benched actor, and chapter-scoped (read only from this chapter's
    own turns) so a legitimate cross-chapter return is never barred here. De-duped,
    first-seen order.
    """
    exits: list[str] = []
    for k in range(1, n):
        d = turn_direction(doc, cid, k)
        exits.extend(str(x) for x in (d.get("cast_exits") or []) if str(x).strip())
    return list(dict.fromkeys(exits))


def chapter_cast_exits(doc: dict, cid: str) -> list[str]:
    """All roster members the director benched across chapter ``cid`` (FR-542 A).

    The chapter-wide union of :func:`_chapter_cast_exits` over *every* played turn
    (not just those before a given turn ``n``), so :func:`chapter_ops.close_chapter`
    can reconcile the emitted end-of-chapter ledger against the exits the director
    actually reported. De-duped, first-seen order; empty when no turn is played.
    """
    return _chapter_cast_exits(doc, cid, len(chapter_turns(doc, cid)) + 1)
