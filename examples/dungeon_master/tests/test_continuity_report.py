"""FR-531: the unified continuity report (deterministic shelf + per-premise trend).

The continuity program grew six hand-run witnesses and never showed a trend
(``continuity-issues.md`` 5.5). ``continuity_report`` collapses the deterministic
ones into one per-book table whose rows are grouped by PREMISE (the exact
``tagline``) so a delta column compares like-with-like -- the corpus mixes three
premises (em-dash floodmark, hyphen floodmark, "Romance, Adventure, Erotica"
floodmark), and a raw slot-ordered delta across them would manufacture a false
trend (FR-531 J2).

Two seams are pinned here: (a) ``book_metrics`` reuses the importable witness
functions (no duplicated measurement, FR-531 J1/J3) and (b) ``render_markdown``
groups by premise and computes the per-metric delta only against the PRIOR book of
the SAME premise.

Example tests are requirement-exempt (FR-474 J3): no ``@pytest.mark.req``.
"""

from __future__ import annotations

from examples.dungeon_master.api import witness_metrics
from examples.dungeon_master.scripts import continuity_report


# A capped chapter that stalls (rode the 16-turn cap, beats_satisfied frozen from
# t6) and a clean chapter that resolved via scene_complete -- the turn-waste shape
# scan_turn_waste measures, now reused from witness_metrics.book_turn_waste.
def _doc_with_turn_waste() -> dict:
    capped_turns = [
        {"direction": {"beats_satisfied": ["a", "b"], "scene_complete": False}}
        for _ in range(16)
    ]
    # Progress froze at t2 (count 2 from the start); 16 - 2 = 14 stalled turns.
    capped_turns[0]["direction"]["beats_satisfied"] = ["a"]
    resolved_turns = [
        {"direction": {"beats_satisfied": ["a"], "scene_complete": False}},
        {"direction": {"beats_satisfied": ["a", "b"], "scene_complete": True}},
    ]
    return {
        "tagline": "Premise One",
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "beats": ["a", "b"],
                    "turns": capped_turns,
                    "text": "Chapter 1 closed prose.",
                    "reviewed": True,
                },
                "2": {
                    "beats": ["a", "b"],
                    "turns": resolved_turns,
                    "text": "Chapter 2 closed prose.",
                    "reviewed": True,
                },
            },
        },
    }


def test_book_turn_waste_counts_only_capped_stall():
    """A capped, stalled chapter contributes its no-progress tail; a resolved one
    contributes zero (reused by both scan_turn_waste and the report)."""
    result = witness_metrics.book_turn_waste(_doc_with_turn_waste())
    assert result["wasted_turns"] == 14
    assert result["capped_chapters"] == 1
    assert result["chapters"] == 2


def test_book_turn_waste_clean_doc_is_zero():
    doc = {
        "chapters": {
            "order": ["1"],
            "cards": {
                "1": {
                    "beats": ["a"],
                    "turns": [
                        {
                            "direction": {
                                "beats_satisfied": ["a"],
                                "scene_complete": True,
                            }
                        }
                    ],
                }
            },
        }
    }
    result = witness_metrics.book_turn_waste(doc)
    assert result["wasted_turns"] == 0
    assert result["capped_chapters"] == 0


def test_book_metrics_reuses_witness_functions():
    """book_metrics aggregates the importable deterministic witnesses into one row
    -- no re-implemented measurement (FR-531 J1)."""
    doc = _doc_with_turn_waste()
    row = continuity_report.book_metrics(doc)
    # Every advertised metric is present and integer-typed.
    for key in (
        "seam_gaps",
        "beat_gaps",
        "reversal_packs",
        "unplayable_beats",
        "wasted_turns",
        "completed_chapters",
    ):
        assert key in row, key
        assert isinstance(row[key], int)
    assert row["wasted_turns"] == 14
    assert row["completed_chapters"] == 2


def test_book_metrics_flags_unplayable_epilogue_beat():
    """The FR-528 witness is part of the shelf: a final time-skip beat is counted."""
    doc = {
        "tagline": "Premise One",
        "chapters": {
            "order": ["1"],
            "cards": {
                "1": {
                    "beats": [
                        "Hilde reaches the ridge",
                        "By autumn, the clans share the high valley",
                    ],
                    "turns": [],
                }
            },
        },
    }
    assert continuity_report.book_metrics(doc)["unplayable_beats"] == 1


def test_premise_of_uses_exact_tagline():
    assert continuity_report.premise_of({"tagline": "  Premise A  "}) == "Premise A"
    assert continuity_report.premise_of({}) == "(unknown premise)"


def test_render_markdown_groups_by_premise_and_deltas_within_group():
    """The trend delta compares only books of the SAME premise (FR-531 J2): a
    cross-premise delta would compare unlike books and manufacture a false trend."""
    rows = [
        {
            "slot": "10001-BC",
            "premise": "Premise A",
            "metrics": {
                "seam_gaps": 5,
                "beat_gaps": 0,
                "reversal_packs": 0,
                "unplayable_beats": 0,
                "wasted_turns": 10,
                "completed_chapters": 8,
            },
        },
        {
            "slot": "10002-BC",
            "premise": "Premise A",
            "metrics": {
                "seam_gaps": 2,
                "beat_gaps": 0,
                "reversal_packs": 0,
                "unplayable_beats": 0,
                "wasted_turns": 4,
                "completed_chapters": 8,
            },
        },
        {
            "slot": "10003-BC",
            "premise": "Premise B",
            "metrics": {
                "seam_gaps": 9,
                "beat_gaps": 1,
                "reversal_packs": 0,
                "unplayable_beats": 1,
                "wasted_turns": 20,
                "completed_chapters": 8,
            },
        },
    ]
    md = continuity_report.render_markdown(rows)
    # Both premise groups are labelled as section headers.
    assert "Premise A" in md
    assert "Premise B" in md
    # The first book of each premise has no in-group predecessor -> no delta arrow.
    # The second Premise-A book shows the improvement vs the FIRST Premise-A book
    # (5 -> 2 seam gaps = -3), NOT vs the cross-premise Premise-B row.
    assert "-3" in md
    # The lone Premise-B book is first in its group: no spurious delta against the
    # Premise-A book that precedes it in slot order.
    assert "+4" not in md  # 5->9 would be the false cross-premise delta


def test_render_markdown_handles_single_book_premise():
    rows = [
        {
            "slot": "10003-BC",
            "premise": "Solo",
            "metrics": {
                "seam_gaps": 1,
                "beat_gaps": 0,
                "reversal_packs": 0,
                "unplayable_beats": 0,
                "wasted_turns": 0,
                "completed_chapters": 5,
            },
        }
    ]
    md = continuity_report.render_markdown(rows)
    assert "Solo" in md
    assert "10003-BC" in md
