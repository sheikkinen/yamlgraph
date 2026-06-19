"""FR-539 S1: the entrance manifest + prior-prose tail reach the Final Cut context.

The deterministic half of the seam-aware Final Cut. ``final_cut_context`` is the
pure assembler that hands the narrator its prompt variables; these tests pin that
the FR-539 manifest (``cast_entrances``) and the prior chapter's closing prose
(``prior_tail``) are present in that context — the narrator INPUT proven to reach
the prompt, independent of the generative compose (which the integration suite
exercises). The manifest is input, never a gate over FR-538's prose-outcome gap
(paired B1).

Example tests are requirement-exempt (FR-474 J3): no ``@pytest.mark.req``.
"""

from __future__ import annotations

from examples.dungeon_master.api.final_cut import final_cut_context


def _doc() -> dict:
    """Two chapters: Ch2 scopes in Arnulf, who is absent from Ch1's closing prose."""
    return {
        "synopsis": {"text": "synopsis"},
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "summary": "c1",
                    "beats": ["Hilde holds the ridge"],
                    "cast": ["Hilde"],
                    "text": "Hilde held the ridge as the clan fell back to the ford.",
                    "world_state": {
                        "characters": [
                            {
                                "name": "Arnulf",
                                "status": "wounded",
                                "location": "the ford",
                            }
                        ]
                    },
                },
                "2": {
                    "summary": "c2",
                    "beats": ["Hilde and Arnulf press the assault"],
                    "cast": ["Hilde", "Arnulf"],
                    "turns": [
                        {
                            "n": 1,
                            "direction": {"beats_satisfied": ["beat"]},
                            "recap": {"text": "recap"},
                        }
                    ],
                },
            },
        },
        "characters": {
            "roster": ["hilde", "arnulf"],
            "cards": {
                "hilde": {"name": "Hilde", "reviewed": True},
                "arnulf": {"name": "Arnulf", "reviewed": True},
            },
        },
    }


def test_context_includes_entrance_manifest():
    """The scoped entrant absent from Ch1 surfaces in the prompt's cast_entrances."""
    ctx = final_cut_context(_doc(), "2")
    assert "Arnulf (new)" in ctx["cast_entrances"]


def test_context_surfaces_inherited_row_for_returning_entrant():
    """A continuing entrant's OWN inherited ledger row reaches the narrator (R2).

    Arnulf is on-page Ch1, scoped out Ch2, back in Ch3's cast. His Ch2 ledger row
    (wounded at the ford) is the char-bounded material the narrator writes the
    arrival from; Hilde's row must not leak into Arnulf's line.
    """
    doc = {
        "synopsis": {"text": "synopsis"},
        "chapters": {
            "order": ["1", "2", "3"],
            "cards": {
                "1": {
                    "summary": "c1",
                    "beats": ["Hilde and Arnulf hold the pass"],
                    "cast": ["Hilde", "Arnulf"],
                    "text": "Hilde and Arnulf held the pass through the night.",
                },
                "2": {
                    "summary": "c2",
                    "beats": ["Hilde presses on"],
                    "cast": ["Hilde"],
                    "text": "Hilde pressed on alone toward the valley.",
                    "world_state": {
                        "characters": [
                            {
                                "name": "Hilde",
                                "status": "marching",
                                "location": "the valley",
                            },
                            {
                                "name": "Arnulf",
                                "status": "wounded",
                                "location": "the ford",
                            },
                        ]
                    },
                },
                "3": {
                    "summary": "c3",
                    "beats": ["Hilde and Arnulf reunite"],
                    "cast": ["Hilde", "Arnulf"],
                    "turns": [
                        {
                            "n": 1,
                            "direction": {"beats_satisfied": ["beat"]},
                            "recap": {"text": "recap"},
                        }
                    ],
                },
            },
        },
        "characters": {
            "roster": ["hilde", "arnulf"],
            "cards": {
                "hilde": {"name": "Hilde", "reviewed": True},
                "arnulf": {"name": "Arnulf", "reviewed": True},
            },
        },
    }
    manifest = final_cut_context(doc, "3")["cast_entrances"]
    assert "Arnulf (continuing)" in manifest
    assert "the ford" in manifest
    assert "the valley" not in manifest  # Hilde's row must not leak (char-bounded)


def test_context_includes_prior_chapter_tail():
    """The previous chapter's committed closing prose reaches the prompt (R3)."""
    ctx = final_cut_context(_doc(), "2")
    assert "Hilde held the ridge" in ctx["prior_tail"]


def test_first_chapter_has_no_seam_context():
    """Chapter 1 has no prior, so both seam blocks render empty (additive)."""
    ctx = final_cut_context(_doc(), "1")
    assert ctx["cast_entrances"] == ""
    assert ctx["prior_tail"] == ""
