"""Direct unit tests for the pure navigation module (FR-489 Phase 2, J5).

These exercise reachability and landing as pure functions of the story document.
The whole point of the extraction is that they need **no ``DMSession``**, no
``TestClient``, no filesystem — a plain dict in, a stage name out. They also pin
the purity refinement (J3): navigation must not mutate ``doc`` (the old
session-bound version did, via the ``setdefault`` characters accessor).
"""

from __future__ import annotations

import copy

from examples.dungeon_master.api import navigation
from examples.dungeon_master.api.tree import STAGE_BY_NAME


def _preplan_doc() -> dict:
    """A document with a reviewed preplan (synopsis + key scene + one card)."""
    return {
        "synopsis": {"text": "s", "reviewed": True},
        "key_scene": {"text": "k", "reviewed": True},
        "characters": {
            "reviewed": True,
            "roster": ["kara"],
            "cards": {"kara": {"name": "Kara", "text": "c", "reviewed": True}},
        },
    }


# ── can_visit ────────────────────────────────────────────────────────────────


def test_synopsis_always_reachable():
    assert navigation.can_visit({}, "synopsis") is True


def test_char_card_needs_synopsis_reviewed_and_roster_membership():
    doc = {
        "synopsis": {"reviewed": True},
        "characters": {"roster": ["kara"], "cards": {"kara": {}}},
    }
    assert navigation.can_visit(doc, "char:kara") is True
    assert navigation.can_visit(doc, "char:ghost") is False  # not in cast
    doc["synopsis"]["reviewed"] = False
    assert navigation.can_visit(doc, "char:kara") is False  # synopsis not done


def test_characters_group_is_not_visitable():
    doc = {"synopsis": {"reviewed": True}}
    assert navigation.can_visit(doc, "characters") is False


def test_unknown_stage_is_not_visitable():
    assert navigation.can_visit({}, "no_such_stage") is False


def test_turns_unlock_only_when_preplan_complete():
    incomplete = {"synopsis": {"reviewed": True}, "key_scene": {"reviewed": False}}
    assert navigation.can_visit(incomplete, "turn:1") is False
    doc = _preplan_doc()
    assert navigation.can_visit(doc, "turn:1") is True  # next turn opens
    assert navigation.can_visit(doc, "turn:2") is False  # one past the next


# ── chapters (FR-488, J3/J5) ─────────────────────────────────────────────────


def _chapters_doc() -> dict:
    """A document whose synopsis is reviewed and chapter set derived (no preplan)."""
    return {
        "synopsis": {"text": "s", "reviewed": True},
        "chapters": {
            "reviewed": False,
            "order": ["1", "2"],
            "cards": {
                "1": {"title": "One", "summary": "a", "reviewed": False},
                "2": {"title": "Two", "summary": "b", "reviewed": False},
            },
        },
    }


def test_chapter_card_needs_synopsis_reviewed_and_membership():
    doc = _chapters_doc()
    assert navigation.can_visit(doc, "chapter:1") is True
    assert navigation.can_visit(doc, "chapter:9") is False  # not in the derived set
    doc["synopsis"]["reviewed"] = False
    assert navigation.can_visit(doc, "chapter:1") is False  # synopsis not done


def test_chapter_unlocks_without_preplan_or_play():
    # J3: chapters are an INDEPENDENT branch off the synopsis — reachable with no
    # key scene, no cast, no completed preplan. A reviewed synopsis is enough.
    doc = {
        "synopsis": {"reviewed": True},
        "chapters": {"order": ["1"], "cards": {"1": {}}},
    }
    assert navigation.can_visit(doc, "chapter:1") is True


def test_accept_chapter_lands_on_next_chapter_then_dead_ends():
    doc = _chapters_doc()
    from examples.dungeon_master.api.tree import resolve_stage

    assert navigation.accept_target(doc, resolve_stage(doc, "chapter:1")) == "chapter:2"
    # The last chapter dead-ends (J5): the chapter branch is a planning artifact,
    # not a chain into play or a finish.
    assert navigation.accept_target(doc, resolve_stage(doc, "chapter:2")) is None


# ── next_unreviewed_char ─────────────────────────────────────────────────────


def test_next_unreviewed_char_finds_first_pending():
    doc = {
        "characters": {
            "roster": ["a", "b", "c"],
            "cards": {
                "a": {"reviewed": True},
                "b": {"reviewed": False},
                "c": {"reviewed": False},
            },
        }
    }
    assert navigation.next_unreviewed_char(doc) == "char:b"
    assert navigation.next_unreviewed_char(doc, after="b") == "char:c"


def test_next_unreviewed_char_none_when_cast_complete():
    doc = _preplan_doc()
    assert navigation.next_unreviewed_char(doc) is None


# ── accept_target (pure landing) ─────────────────────────────────────────────


def test_synopsis_lands_on_key_scene():
    assert navigation.accept_target({}, STAGE_BY_NAME["synopsis"]) == "key_scene"


def test_key_scene_lands_on_play_when_preplan_complete():
    assert (
        navigation.accept_target(_preplan_doc(), STAGE_BY_NAME["key_scene"]) == "turn:1"
    )


def test_finishes_chain_walks_to_walkthrough():
    assert navigation.accept_target({}, STAGE_BY_NAME["final_cut"]) == "final_cut_turns"
    assert (
        navigation.accept_target({}, STAGE_BY_NAME["final_cut_turns"]) == "walkthrough"
    )
    assert navigation.accept_target({}, STAGE_BY_NAME["walkthrough"]) is None


# ── purity (FR-489 J3) ───────────────────────────────────────────────────────


def test_navigation_never_mutates_doc():
    # The old session-bound _can_visit reached the cards through a setdefault
    # accessor, which seeded an empty "characters" sub-doc as a side effect.
    # The pure module must leave the document byte-for-byte unchanged.
    doc = {"synopsis": {"reviewed": True}}
    before = copy.deepcopy(doc)
    navigation.can_visit(doc, "char:kara")
    navigation.next_unreviewed_char(doc)
    navigation.accept_target(doc, STAGE_BY_NAME["synopsis"])
    assert doc == before
    assert "characters" not in doc  # no phantom sub-doc seeded
