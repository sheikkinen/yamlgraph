"""Direct unit tests for the pure navigation module (FR-489 Phase 2, J5).

These exercise reachability and landing as pure functions of the story document.
The whole point of the extraction is that they need **no ``DMSession``**, no
``TestClient``, no filesystem — a plain dict in, a stage name out. They also pin
the purity refinement (J3): navigation must not mutate ``doc`` (the old
session-bound version did, via the ``setdefault`` characters accessor).
"""

from __future__ import annotations

import copy

from examples.dungeon_master.api import navigation, turn_state
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
    assert turn_state.chapter_should_close(doc, "1", 3) is True


def test_chapter_should_close_at_turn_budget_without_scene_complete():
    # The runaway case: no turn ever reported scene_complete, but the chapter has
    # spent its full per-chapter budget — the backstop forces closure.
    cap = turn_state.CHAPTER_TURN_CAP
    doc = _playing_doc(_played_turns(cap))
    assert turn_state.chapter_should_close(doc, "1", cap) is True


def test_chapter_should_not_close_below_budget_without_scene_complete():
    cap = turn_state.CHAPTER_TURN_CAP
    doc = _playing_doc(_played_turns(cap - 1))
    assert turn_state.chapter_should_close(doc, "1", cap - 1) is False


def test_accept_target_force_closes_chapter_at_budget():
    # At the per-chapter cap with no scene_complete, landing advances to the NEXT
    # chapter's first turn (force-close), not turn cap+1 in the same chapter.
    cap = turn_state.CHAPTER_TURN_CAP
    doc = _playing_doc(_played_turns(cap))
    stage = resolve_stage(doc, f"turn:1:{cap}")
    assert navigation.accept_target(doc, stage) == "turn:2:1"


def test_accept_target_keeps_advancing_below_budget():
    cap = turn_state.CHAPTER_TURN_CAP
    doc = _playing_doc(_played_turns(cap - 1))
    stage = resolve_stage(doc, f"turn:1:{cap - 1}")
    assert navigation.accept_target(doc, stage) == f"turn:1:{cap}"


# ── FR-527: beat-progress early close -- FALSIFIED at enforce ─────────────────
#
# Premise: a chapter whose director satisfies the beats it CAN satisfy but never
# reaches ``scene_complete`` (k == n) plateaus at k < n and rides the FR-501 cap,
# replaying the resolved scene (the no-progress tail, ~208 turns over 127 chapters).
# Proposed cure (Fix A): close such a chapter once its ``beats_satisfied`` count has
# not grown for ``BEAT_STALL_LIMIT`` turns.
#
# The judgement's own load-bearing J6 corpus safety check FALSIFIED Fix A during
# enforce: natural directors routinely PAUSE beat-marking mid-scene and RESUME.
# The longest such pause in a naturally-closing chapter is 9 turns (10013-BC CH1:
# count freezes at 2 for t2..t10, then resumes and closes at t13). Any stall limit
# small enough to cut a waste tail also preempts these natural pauses, and any limit
# large enough to spare them (> 9) shrinks to the cap (the CH8 waste tail of 11
# turns fires at t16 == the cap, saving zero turns). The count-plateau signal cannot
# separate a *finished* director from a *pausing* one. Fix A is abandoned; the real
# cure is the outliner refusing to author a final beat the capped scene can never
# reach (FR-528). This test pins the non-separability so the dead end is not retried.


def test_beat_plateau_signal_is_non_separable():
    # Over every recorded book, the longest count-plateau (>=1) that PRECEDES a
    # natural scene_complete must be >= the shorter waste-case tails -- proving no
    # single stall window both spares natural pauses and cuts the waste tail.
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    stories = sorted((root / "outputs" / "dungeon-master").glob("100*-BC/story.json"))
    if not stories:
        return  # corpus absent in this checkout -- nothing to assert

    max_natural_plateau = 0
    waste_tails: list[int] = []
    for story in stories:
        doc = json.loads(story.read_text())
        chapters = doc.get("chapters") or {}
        for cid in chapters.get("order") or []:
            card = (chapters.get("cards") or {}).get(cid) or {}
            turns = card.get("turns") or []
            counts = [
                len((t.get("direction") or {}).get("beats_satisfied") or [])
                for t in turns
            ]
            complete_turn = next(
                (
                    i
                    for i, t in enumerate(turns, 1)
                    if (t.get("direction") or {}).get("scene_complete")
                ),
                None,
            )
            if complete_turn is not None:
                run = 1
                for i in range(1, complete_turn):
                    if counts[i - 1] >= 1 and counts[i - 1] == counts[i]:
                        run += 1
                        max_natural_plateau = max(max_natural_plateau, run)
                    else:
                        run = 1
            elif counts:
                last, tail = counts[-1], 0
                for c in reversed(counts):
                    if c == last and c >= 1:
                        tail += 1
                    else:
                        break
                waste_tails.append(tail)

    # Natural directors pause beat-marking for many turns then resume: the signal is
    # noisy. A safe limit must exceed the longest natural plateau, yet most waste
    # tails are shorter than it -- so a count-plateau guard cannot both spare natural
    # closes and meaningfully cut the waste. This is why Fix A was abandoned.
    assert (
        max_natural_plateau >= 9
    ), f"expected a long natural plateau in the corpus, got {max_natural_plateau}"
    spared_waste = sum(1 for t in waste_tails if t <= max_natural_plateau)
    assert spared_waste > 0, (
        "expected waste tails shorter than the longest natural plateau -- the "
        "overlap that makes the count-plateau signal non-separable"
    )
