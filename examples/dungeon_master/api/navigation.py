"""Pure tree-navigation functions for the DM v2 session (FR-489 Phase 2).

Reachability (``can_visit``) and landing (``accept_target``,
``next_unreviewed_char``) are properties of the stage tree and the story
document, not of the session adapter. They are **pure functions of ``doc``**:
they read it through a read-only characters view, return a target stage name (or
``None``), and never mutate the document or invoke a graph.

The one side-effect that used to live in the synopsis-landing branch — deriving
the character roster — stays in the adapter's ``accept()`` (FR-489 J1). Navigation
only decides *where to land*, given the document exactly as it is; the adapter is
responsible for any expansion that must happen before it asks.
"""

from __future__ import annotations

from examples.dungeon_master.api import turn_state
from examples.dungeon_master.api.tree import (
    CHAPTER_PREFIX,
    CHAR_PREFIX,
    STAGE_BY_NAME,
    TURN_PREFIX,
    Stage,
    all_chapters_played,
    cast_complete,
    parse_turn,
)


def _cards(doc: dict) -> dict:
    """Read-only view of the character cards (never mutates, unlike ``_characters``)."""
    return doc.get("characters", {}).get("cards", {})


def _roster(doc: dict) -> list:
    """Read-only view of the rostered character ids."""
    return doc.get("characters", {}).get("roster", [])


def _chapter_cards(doc: dict) -> dict:
    """Read-only view of the book-chapter cards (FR-488)."""
    return doc.get("chapters", {}).get("cards", {})


def _chapter_order(doc: dict) -> list:
    """Read-only view of the ordered chapter ids (FR-488)."""
    return doc.get("chapters", {}).get("order", [])


def can_visit(doc: dict, target: str) -> bool:
    """Whether ``target`` is currently reachable (parent-reviewed / roster gates)."""
    if target == "synopsis":
        return True
    if target.startswith(CHAR_PREFIX):
        cid = target[len(CHAR_PREFIX) :]
        return bool(doc.get("synopsis", {}).get("reviewed")) and (cid in _cards(doc))
    if target.startswith(CHAPTER_PREFIX):
        # A book chapter (FR-488): an independent branch off the synopsis. It
        # unlocks once the synopsis is reviewed (the act that derives the chapter
        # set) and the id is in the derived set — never gated on the preplan or
        # play (J3).
        cid = target[len(CHAPTER_PREFIX) :]
        return bool(doc.get("synopsis", {}).get("reviewed")) and (
            cid in _chapter_cards(doc)
        )
    if target.startswith(TURN_PREFIX):
        # Play turns unlock once the cast is complete; a turn is scoped to a
        # chapter (FR-491 C, ``turn:<cid>:<n>``), so the chapter id must be in the
        # derived order and the index a revisit or the chapter's next turn.
        if not cast_complete(doc):
            return False
        cid, n = parse_turn(target)
        if not cid or cid not in _chapter_order(doc):
            return False
        return 1 <= n <= len(turn_state.chapter_turns(doc, cid)) + 1
    if target == "book":
        # The terminal Book leaf (FR-492 Phase 3): unlocks only once every chapter
        # is played, not by the ordinary parent-reviewed rule.
        return all_chapters_played(doc)
    stage = STAGE_BY_NAME.get(target)
    if stage is None or stage.kind == "roster":
        # Unknown stage, or the non-visitable Characters group.
        return False
    if stage.parent:
        return bool(doc.get(stage.parent, {}).get("reviewed"))
    return True


def next_unreviewed_char(doc: dict, after: str | None = None) -> str | None:
    """The next unreviewed character id (searching after ``after``, wrapping)."""
    roster = _roster(doc)
    cards = _cards(doc)
    order = roster
    if after and after in roster:
        i = roster.index(after)
        order = roster[i + 1 :] + roster[: i + 1]
    for cid in order:
        if not cards.get(cid, {}).get("reviewed"):
            return CHAR_PREFIX + cid
    return None


def accept_target(doc: dict, stage: Stage) -> str | None:
    """The node to land on after accepting ``stage`` (FR-475 / FR-477).

    Pure: the synopsis-landing roster expansion is the adapter's responsibility
    (FR-489 J1) and is assumed already done by the time this is asked.
    """
    if stage.name == "synopsis":
        # FR-491 J1: the cast is derived before chapters, so accepting the synopsis
        # lands on the first character. The adapter has already expanded the roster
        # (FR-489 J1) by the time this is asked.
        return next_unreviewed_char(doc)
    if stage.name.startswith(CHAR_PREFIX):
        nxt = next_unreviewed_char(doc, after=stage.name[len(CHAR_PREFIX) :])
        if nxt is not None:
            return nxt
        # Last character reviewed: the cast is complete, so the chapter outline has
        # been derived — land on the Chapters overview (FR-491 J1).
        return "chapters" if cast_complete(doc) else None
    if stage.name.startswith(CHAPTER_PREFIX):
        # A chapter is PLAYED (FR-491): visiting it lands on its first turn so the
        # play loop begins. Chapter completion happens via its last turn's
        # scene_complete, not by accepting the chapter itself.
        cid = stage.name[len(CHAPTER_PREFIX) :]
        return f"{TURN_PREFIX}{cid}:1"
    if stage.name.startswith(TURN_PREFIX):
        cid, n = parse_turn(stage.name)
        # Once the director reports the chapter's scene complete — or the chapter
        # exhausts its per-chapter turn budget (FR-501) — stop advancing turns
        # (FR-479 J5): the adapter closes the chapter (deriving its end-of-chapter
        # world_state and its beat-faithful final text via the per-chapter Final
        # Cut, FR-492) and play moves to the NEXT chapter's first turn, carrying
        # that ledger forward (FR-491). The last chapter dead-ends — the
        # deterministic Book compose is the whole-book finish (FR-492 Phase 3), not
        # a navigable leaf.
        if turn_state.chapter_should_close(doc, cid, n):
            order = _chapter_order(doc)
            if cid in order:
                i = order.index(cid)
                if i + 1 < len(order):
                    return f"{TURN_PREFIX}{order[i + 1]}:1"
            return None
        return f"{TURN_PREFIX}{cid}:{n + 1}"
    return None
