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

from examples.dungeon_master.api import turn_ops
from examples.dungeon_master.api.tree import (
    CHAR_PREFIX,
    FINAL_CUT,
    FINAL_CUT_TURNS,
    STAGE_BY_NAME,
    TURN_PREFIX,
    WALKTHROUGH,
    Stage,
    cut_present,
    preplan_complete,
    scene_is_complete,
)


def _cards(doc: dict) -> dict:
    """Read-only view of the character cards (never mutates, unlike ``_characters``)."""
    return doc.get("characters", {}).get("cards", {})


def _roster(doc: dict) -> list:
    """Read-only view of the rostered character ids."""
    return doc.get("characters", {}).get("roster", [])


def can_visit(doc: dict, target: str) -> bool:
    """Whether ``target`` is currently reachable (parent-reviewed / roster gates)."""
    if target == "synopsis":
        return True
    if target.startswith(CHAR_PREFIX):
        cid = target[len(CHAR_PREFIX) :]
        return bool(doc.get("synopsis", {}).get("reviewed")) and (cid in _cards(doc))
    if target.startswith(TURN_PREFIX):
        # Play turns unlock only once the whole preplan is reviewed; a player
        # may revisit any existing turn or open the next one.
        if not preplan_complete(doc):
            return False
        suffix = target[len(TURN_PREFIX) :]
        if not suffix.isdigit():
            return False
        return 1 <= int(suffix) <= len(doc.get("turns", [])) + 1
    if target in (FINAL_CUT, FINAL_CUT_TURNS):
        # The terminal Final Cut leaves (continuous FR-484 + turn-structured
        # FR-485) both unlock only once the scene is complete.
        return scene_is_complete(doc)
    if target == WALKTHROUGH:
        # The full-text walkthrough renders the FR-485 cut as its spine, so it
        # unlocks only once the scene is complete AND that cut is present
        # (FR-487 OQ1) — otherwise it would have to invent the structure.
        return scene_is_complete(doc) and cut_present(doc)
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
        return "key_scene"
    if stage.name == "key_scene":
        # Accepting the key scene may be the act that completes the preplan.
        if preplan_complete(doc):
            return f"{TURN_PREFIX}1"
        return next_unreviewed_char(doc)
    if stage.name.startswith(CHAR_PREFIX):
        nxt = next_unreviewed_char(doc, after=stage.name[len(CHAR_PREFIX) :])
        if nxt is not None:
            return nxt
        # Last character reviewed: open Play if the rest of the preplan is too.
        return f"{TURN_PREFIX}1" if preplan_complete(doc) else None
    if stage.name.startswith(TURN_PREFIX):
        n = int(stage.name[len(TURN_PREFIX) :])
        # Once the director reports the scene's END reached, stop offering a
        # plain next-turn advance — the scene is done, not replayed (FR-479 J5).
        # Land on the terminal Final Cut leaf to compose the whole arc (FR-484).
        if turn_ops.turn_direction(doc, n).get("scene_complete"):
            return FINAL_CUT
        return f"{TURN_PREFIX}{n + 1}"
    # The three finishes chain so accepting one leads to the next, walking the
    # DM through every closing artifact (FR-487): the continuous Final Cut
    # (FR-484) → the turn-structured Final Cut (FR-485, which also drafts the
    # cut spine the walkthrough needs) → the full-text Walkthrough (FR-487),
    # which is the true terminal leaf.
    if stage.name == FINAL_CUT:
        return FINAL_CUT_TURNS
    if stage.name == FINAL_CUT_TURNS:
        return WALKTHROUGH
    return None
