"""Direct unit tests for the pure navigation module (FR-489 Phase 2, J5).

These exercise reachability and landing as pure functions of the story document.
The whole point of the extraction is that they need **no ``DMSession``**, no
``TestClient``, no filesystem — a plain dict in, a stage name out. They also pin
the purity refinement (J3): navigation must not mutate ``doc`` (the old
session-bound version did, via the ``setdefault`` characters accessor).
"""

from __future__ import annotations

import copy

from examples.dungeon_master.api import navigation, turn_ops
from examples.dungeon_master.api.tree import STAGE_BY_NAME, resolve_stage


def _cast_doc() -> dict:
    """A document with a complete cast (synopsis + one reviewed character; FR-491).

    The cast gate (``cast_complete``) is synopsis ✓ + all characters ✓ — the key
    scene is retired, so it is no longer part of the gate. A derived chapter set is
    included because play turns are chapter-scoped (FR-491 C): a turn unlocks only
    when its chapter id is in the order.
    """
    return {
        "synopsis": {"text": "s", "reviewed": True},
        "characters": {
            "reviewed": True,
            "roster": ["kara"],
            "cards": {"kara": {"name": "Kara", "text": "c", "reviewed": True}},
        },
        "chapters": {
            "reviewed": False,
            "order": ["1"],
            "cards": {"1": {"title": "One", "summary": "a", "reviewed": False}},
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


def test_turns_unlock_only_when_cast_complete():
    incomplete = {"synopsis": {"reviewed": True}}  # no cast yet
    assert navigation.can_visit(incomplete, "turn:1:1") is False
    doc = _cast_doc()
    # A turn is chapter-scoped (FR-491 C): ``turn:<cid>:<n>``.
    assert navigation.can_visit(doc, "turn:1:1") is True  # next turn opens
    assert navigation.can_visit(doc, "turn:1:2") is False  # one past the next


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


def test_accept_chapter_lands_on_first_turn():
    doc = _chapters_doc()
    from examples.dungeon_master.api.tree import resolve_stage

    # FR-491: a chapter is PLAYED — accepting it (visiting) lands on its first
    # turn so the play loop begins. Chapter completion happens via the last turn's
    # scene_complete, not by accepting the chapter itself.
    assert navigation.accept_target(doc, resolve_stage(doc, "chapter:1")) == "turn:1:1"
    assert navigation.accept_target(doc, resolve_stage(doc, "chapter:2")) == "turn:2:1"


# ── FR-490: the chapters overview is visitable (the repurposed dead stage) ────


def test_chapters_overview_visitable_once_synopsis_reviewed():
    # J6: the overview is a read-only directory gated identically to its cards —
    # reachable via the generic parent gate, no special-case branch in can_visit.
    doc = _chapters_doc()
    assert navigation.can_visit(doc, "chapters") is True
    doc["synopsis"]["reviewed"] = False
    assert navigation.can_visit(doc, "chapters") is False


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
    doc = _cast_doc()
    assert navigation.next_unreviewed_char(doc) is None


# ── accept_target (pure landing) ─────────────────────────────────────────────


def test_synopsis_lands_on_first_character():
    # FR-491 J1: the cast is derived before chapters, so accepting the synopsis
    # lands on the first character — the key scene is retired from the flow.
    doc = {"characters": {"roster": ["elara", "coil"], "cards": {"elara": {}}}}
    assert navigation.accept_target(doc, STAGE_BY_NAME["synopsis"]) == "char:elara"


def test_last_character_lands_on_chapters_overview():
    # FR-491 J1: accepting the last character completes the cast, which derives the
    # chapter outline; navigation lands on the Chapters overview.
    from examples.dungeon_master.api.tree import resolve_stage

    doc = _cast_doc()
    assert navigation.accept_target(doc, resolve_stage(doc, "char:kara")) == "chapters"


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


# ── FR-501: per-chapter turn budget (the runaway-chapter safety valve) ────────
#
# The play loop's only exit for a chapter is the director emitting
# ``scene_complete``. A director that never resolves (observed live: a diffusion
# provider stuck in "rising" for 91 turns) would otherwise consume the whole book
# turn_cap on one chapter. ``chapter_should_close`` adds a deterministic backstop
# so every chapter — under any provider — closes within its own budget.


def _played_turns(n: int, *, scene_complete_at: int | None = None) -> list[dict]:
    """``n`` played turn records; ``scene_complete`` set only at ``scene_complete_at``."""
    return [
        {
            "n": i,
            "recap": {"text": f"Turn {i}", "reviewed": True},
            "direction": {"scene_complete": i == scene_complete_at},
        }
        for i in range(1, n + 1)
    ]


def _playing_doc(turns: list[dict]) -> dict:
    """A two-chapter doc whose chapter 1 has the given played turns."""
    return {
        "synopsis": {"text": "s", "reviewed": True},
        "chapters": {
            "reviewed": False,
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "title": "One",
                    "summary": "a",
                    "reviewed": False,
                    "turns": turns,
                },
                "2": {"title": "Two", "summary": "b", "reviewed": False},
            },
        },
    }


def test_chapter_should_close_on_scene_complete():
    doc = _playing_doc(_played_turns(3, scene_complete_at=3))
    assert turn_ops.chapter_should_close(doc, "1", 3) is True


def test_chapter_should_close_at_turn_budget_without_scene_complete():
    # The runaway case: no turn ever reported scene_complete, but the chapter has
    # spent its full per-chapter budget — the backstop forces closure.
    cap = turn_ops.CHAPTER_TURN_CAP
    doc = _playing_doc(_played_turns(cap))
    assert turn_ops.chapter_should_close(doc, "1", cap) is True


def test_chapter_should_not_close_below_budget_without_scene_complete():
    cap = turn_ops.CHAPTER_TURN_CAP
    doc = _playing_doc(_played_turns(cap - 1))
    assert turn_ops.chapter_should_close(doc, "1", cap - 1) is False


def test_accept_target_force_closes_chapter_at_budget():
    # At the per-chapter cap with no scene_complete, landing advances to the NEXT
    # chapter's first turn (force-close), not turn cap+1 in the same chapter.
    cap = turn_ops.CHAPTER_TURN_CAP
    doc = _playing_doc(_played_turns(cap))
    stage = resolve_stage(doc, f"turn:1:{cap}")
    assert navigation.accept_target(doc, stage) == "turn:2:1"


def test_accept_target_keeps_advancing_below_budget():
    cap = turn_ops.CHAPTER_TURN_CAP
    doc = _playing_doc(_played_turns(cap - 1))
    stage = resolve_stage(doc, f"turn:1:{cap - 1}")
    assert navigation.accept_target(doc, stage) == f"turn:1:{cap}"


# ── FR-527: beat-progress early close (stop the no-progress tail) ─────────────
#
# A chapter whose director satisfies the beats it CAN satisfy but never reaches
# ``scene_complete`` (k == n) plateaus at k < n and rides the FR-501 cap, replaying
# the resolved scene. The deterministic ``_beats_stalled`` guard closes such a
# chapter once its ``beats_satisfied`` count has not grown across the last
# ``BEAT_STALL_LIMIT`` turns. The hard cap stays the ultimate backstop; an opening
# that has established nothing (count == 0) is never early-closed.


def _beat_count_turns(
    counts: list[int], *, scene_complete_at: int | None = None
) -> list[dict]:
    """Played turns whose ``beats_satisfied`` has the given per-turn lengths."""
    return [
        {
            "n": i,
            "recap": {"text": f"Turn {i}", "reviewed": True},
            "direction": {
                "beats_satisfied": [f"b{j}" for j in range(c)],
                "scene_complete": i == scene_complete_at,
            },
        }
        for i, c in enumerate(counts, 1)
    ]


def test_chapter_should_close_on_beat_progress_stall():
    # The recorded 10025-BC CH8 plateau: counts climb to 4 by t6, then freeze.
    # count(9) == count(9 - 3) == 4 and count(9) >= 1 -> stalled at t9, seven turns
    # before the 16-turn cap. Pre-fix this is False (no scene_complete, n < cap).
    doc = _playing_doc(_beat_count_turns([0, 1, 2, 2, 3, 4, 4, 4, 4]))
    assert turn_ops.chapter_should_close(doc, "1", 9) is True


def test_beats_stalled_exact_semantics():
    # n > limit AND count(n) == count(n - limit) AND count(n) >= 1.
    doc = _playing_doc(_beat_count_turns([0, 1, 2, 2, 3, 4, 4, 4, 4]))
    assert turn_ops._beats_stalled(doc, "1", 9, turn_ops.BEAT_STALL_LIMIT) is True
    # First stall turn is exactly t9, not t8 (count(8)=4 vs count(5)=3 -> grew).
    assert turn_ops._beats_stalled(doc, "1", 8, turn_ops.BEAT_STALL_LIMIT) is False


def test_beats_not_stalled_when_count_still_growing():
    # count grew between t3 (3) and t6 (4) -> within the last 3 turns -> not stalled.
    doc = _playing_doc(_beat_count_turns([3, 3, 3, 4, 4, 4]))
    assert turn_ops.chapter_should_close(doc, "1", 6) is False


def test_beats_not_stalled_on_empty_opening():
    # A flat run of zero satisfied beats (count == 0) is an un-established opening,
    # not a stall: the count >= 1 clause forbids closing it early.
    doc = _playing_doc(_beat_count_turns([0, 0, 0, 0]))
    assert turn_ops.chapter_should_close(doc, "1", 4) is False


def test_beats_stalled_needs_more_turns_than_limit():
    # n <= limit can never be a stall (no full window to compare against).
    doc = _playing_doc(_beat_count_turns([4, 4, 4]))
    assert turn_ops._beats_stalled(doc, "1", 3, turn_ops.BEAT_STALL_LIMIT) is False


def test_recorded_corpus_guard_never_preempts_natural_close():
    # J6 deterministic safety check: over every recorded book, the stall guard must
    # NEVER fire strictly before a chapter's existing scene_complete turn -- proving
    # it cannot shorten a chapter that closes naturally today. Pure, no live LLM.
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    stories = sorted((root / "outputs" / "dungeon-master").glob("100*-BC/story.json"))
    if not stories:
        return  # corpus absent in this checkout -- nothing to assert
    limit = turn_ops.BEAT_STALL_LIMIT
    for story in stories:
        doc = json.loads(story.read_text())
        chapters = doc.get("chapters") or {}
        for cid in chapters.get("order") or []:
            card = (chapters.get("cards") or {}).get(cid) or {}
            turns = card.get("turns") or []
            complete_turn = next(
                (
                    i
                    for i, t in enumerate(turns, 1)
                    if (t.get("direction") or {}).get("scene_complete")
                ),
                None,
            )
            if complete_turn is None:
                continue
            for n in range(1, complete_turn):
                assert not turn_ops._beats_stalled(doc, cid, n, limit), (
                    f"{story.name} CH{cid}: stall guard preempted natural close "
                    f"at t{n} (scene_complete @t{complete_turn})"
                )
