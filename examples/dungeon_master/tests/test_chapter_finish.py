"""Phase-2 witness: the finish must read the LIVE chapter-play doc (FR-492).

A *visibility* harness, not a governance gate (FR-474 J3): no
``@pytest.mark.req``. This is the test the FR-491-Slice-4 rollback's restored
suite does **not** provide. Those restored finish tests build their own *old-shape*
fixtures (flat ``doc["turns"]``, ``doc["key_scene"]``) and so report green while
proving nothing about the live chapter-play doc, where turns live under
``chapters.cards[<cid>]["turns"]`` and ``key_scene`` no longer exists.

The load-bearing assertion: ``final_cut_context`` assembles a chapter's finished
arc from that chapter's played turns and its own summary — never the absent flat
``doc["turns"]``. A finish context whose arc is empty on a played chapter is the
false-green the judgement named; this test condemns it.

Run directly:
    pytest examples/dungeon_master/tests/test_chapter_finish.py --no-cov
"""

from __future__ import annotations

from examples.dungeon_master.api import turn_ops


def _played_chapter_doc() -> dict:
    """A live chapter-play doc: a played chapter whose turns sit under its card.

    No flat ``doc["turns"]``, no ``doc["key_scene"]`` — the shape the chapter-play
    slices (FR-491) left in place. Chapter ``1`` has three played turns with
    director phases (rising → climax → falling) and ordered recaps.
    """
    return {
        "synopsis": {"text": "Kara leads the band against a raider.", "reviewed": True},
        "chapters": {
            "order": ["1"],
            "cards": {
                "1": {
                    "title": "Chapter 1 — The Last Ledge",
                    "summary": "Kara corners the raider on the ledge as the water rises.",
                    "text": "",
                    "world_state": "",
                    "turns": [
                        {
                            "n": 1,
                            "intents": {
                                "hilde": {
                                    "intent": "muster the band",
                                    "dialogue": "Up the slope. Now.",
                                    "expression": "jaw set, hand raised",
                                },
                                "gunnar": {
                                    "intent": "push the line uphill",
                                    "dialogue": "Move.",
                                    "expression": "eyes fixed on the ridge",
                                },
                            },
                            "recap": {"text": "Kara musters the band at dawn."},
                            "direction": {
                                "phase": "rising",
                                "beats_satisfied": ["the band is mustered"],
                            },
                        },
                        {
                            "n": 2,
                            "intents": {
                                "hilde": {
                                    "intent": "corner the raider",
                                    "dialogue": "No path left for you.",
                                    "expression": "teeth bared, stance lowered",
                                },
                                "gunnar": {
                                    "intent": "seal the ledge exit",
                                    "dialogue": "Hold the edge.",
                                    "expression": "shoulders square, blade up",
                                },
                            },
                            "recap": {"text": "Kara corners the raider on the ledge."},
                            "direction": {
                                "phase": "climax",
                                "beats_satisfied": [
                                    "the band is mustered",
                                    "the raider is cornered",
                                ],
                            },
                        },
                        {
                            "n": 3,
                            "intents": {
                                "hilde": {
                                    "intent": "accept surrender",
                                    "dialogue": "Drop it and live.",
                                    "expression": "chin lifted, breath hard",
                                },
                                "gunnar": {
                                    "intent": "hold the line",
                                    "dialogue": "Yield now.",
                                    "expression": "jaw tight, feet planted",
                                },
                            },
                            "recap": {"text": "The raider yields as the flood crests."},
                            "direction": {
                                "phase": "falling",
                                "scene_complete": True,
                                "beats_satisfied": [
                                    "the band is mustered",
                                    "the raider is cornered",
                                    "the raider yields",
                                ],
                            },
                        },
                    ],
                },
            },
        },
        "characters": {
            "roster": ["hilde", "gunnar"],
            "cards": {
                "hilde": {"name": "Hilde"},
                "gunnar": {"name": "Gunnar"},
            },
        },
    }


def test_final_cut_context_reads_chapter_turns_not_flat_doc_turns():
    """The finish arc is built from ``chapters.cards[cid].turns`` (FR-492 witness).

    The target signature is ``final_cut_context(doc, cid)``. The restored helper
    reads flat ``doc["turns"]`` (absent here), so this fails RED until Phase 2
    re-scopes it to the chapter. The arc must carry every played recap in order.
    """
    doc = _played_chapter_doc()
    ctx = turn_ops.final_cut_context(doc, "1")

    arc = ctx["arc"]
    # Every played recap, in order — the proof the chapter's turns were read.
    assert "musters the band" in arc
    assert "corners the raider on the ledge" in arc
    assert "yields as the flood crests" in arc
    assert arc.index("musters") < arc.index("corners") < arc.index("yields")
    assert "dialogue:" in arc
    assert "expression:" in arc


def test_final_cut_context_uses_chapter_summary_as_the_plan():
    """The chapter summary stands in for the retired ``key_scene`` plan (FR-492)."""
    doc = _played_chapter_doc()
    ctx = turn_ops.final_cut_context(doc, "1")
    assert "corners the raider on the ledge" in ctx["key_scene"]


def test_final_cut_context_marks_the_chapter_climax():
    """The climax marker derives from THIS chapter's phase sequence (FR-492).

    Turn 2 is tagged ``climax``; the assembled arc must mark it, derived from the
    chapter's own turns rather than the absent flat ``doc["turns"]``.
    """
    doc = _played_chapter_doc()
    ctx = turn_ops.final_cut_context(doc, "1")
    assert ctx["climax"] == "Turn 2"
    assert "CLIMAX BEAT" in ctx["arc"]


def test_final_cut_context_sources_beats_from_director_not_parse_beats():
    """The fidelity beats come from the director's ``beats_satisfied`` (FR-492).

    The restored ``parse_beats`` reads a ``BEATS:`` block from a frozen key-scene
    card; a chapter has only a free-text ``summary``, so re-parsing yields an
    EMPTY beats list — restoring the prose but silently dropping the fidelity the
    finish exists to preserve. This condemns that ``plausible_wrong_answer``: the
    assembled ``beats`` must carry the beats the director accumulated across the
    chapter's turns, not be empty.
    """
    doc = _played_chapter_doc()
    ctx = turn_ops.final_cut_context(doc, "1")
    beats = ctx["beats"]
    assert beats.strip(), "beats must not be empty — the fidelity signal was dropped"
    assert "the band is mustered" in beats
    assert "the raider is cornered" in beats
    assert "the raider yields" in beats


def test_final_cut_context_emits_beat_groups_key():
    """FR-505: final_cut_context must include ``beat_groups`` for the graph state.

    The ``final_cut.yaml`` graph state schema and node variable map require a
    ``beat_groups`` key. Before FR-505, this key was absent — every chapter
    close failed with "Missing required variable(s) for prompt 'final_cut':
    beat_groups". This condemns that gap: the assembled context must contain
    ``beat_groups``, and it must be a non-empty string when turns are present.
    """
    doc = _played_chapter_doc()
    ctx = turn_ops.final_cut_context(doc, "1")
    assert (
        "beat_groups" in ctx
    ), "beat_groups key missing — final_cut graph invocation would fail"
    assert isinstance(ctx["beat_groups"], str)
    assert ctx[
        "beat_groups"
    ].strip(), "beat_groups must be non-empty for a chapter with turns"


def test_beat_turn_groups_are_total_ordered_and_cue_carrying():
    """FR-505 A1: grouped turns are total, ordered, and carry stable cue schema."""
    doc = _played_chapter_doc()
    groups = turn_ops.beat_turn_groups(doc, "1")

    assert [g["beat"] for g in groups] == [
        "the band is mustered",
        "the raider is cornered",
        "the raider yields",
    ]

    all_turn_ns = [t["n"] for g in groups for t in g["turns"]]
    assert all_turn_ns == [1, 2, 3]
    assert len(set(all_turn_ns)) == 3

    climax_groups = [g for g in groups if g["is_climax"]]
    assert len(climax_groups) == 1
    assert climax_groups[0]["beat"] == "the raider is cornered"

    for g in groups:
        for t in g["turns"]:
            for perf in t["intents"]:
                assert set(perf.keys()) == {"name", "intent", "dialogue", "expression"}
