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
                            "recap": {"text": "Kara musters the band at dawn."},
                            "direction": {"phase": "rising"},
                        },
                        {
                            "n": 2,
                            "recap": {"text": "Kara corners the raider on the ledge."},
                            "direction": {"phase": "climax"},
                        },
                        {
                            "n": 3,
                            "recap": {"text": "The raider yields as the flood crests."},
                            "direction": {"phase": "falling", "scene_complete": True},
                        },
                    ],
                },
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
    assert "THE CLIMAX" in ctx["arc"]
