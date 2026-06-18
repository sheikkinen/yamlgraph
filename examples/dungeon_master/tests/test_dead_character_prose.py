"""Tests for FR-510: confirmed-dead character prose exclusion.

Tests for the active-role detection validator, the dead_characters context
field, and witness metric extraction.
"""

from __future__ import annotations

from examples.dungeon_master.api.chapter_ops import (
    detect_dead_character_prose_violations,
)
from examples.dungeon_master.api.turn_ops import (
    build_allowed_scene_cast,
    final_cut_context,
)

# ── Active-role validator tests ──────────────────────────────────────────────


def test_active_verb_within_8_words_is_violation():
    text = "Alwina came forward with her ritual staff upright."
    violations = detect_dead_character_prose_violations("Alwina", text)
    assert len(violations) == 1
    assert violations[0]["type"] == "active_presence"
    assert "Alwina" in violations[0]["name"]


def test_active_verb_direct_after_name_is_violation():
    text = "Alwina drove her staff down beside the camp line."
    violations = detect_dead_character_prose_violations("Alwina", text)
    assert len(violations) == 1


def test_dialogue_attribution_is_violation():
    text = "Alwina demanded that he name his place with the camp or against it."
    violations = detect_dead_character_prose_violations("Alwina", text)
    assert len(violations) == 1


def test_possessive_staff_is_not_a_violation():
    text = "Gunnar shoved Alwina's ritual staff fully aside with the butt of his spear."
    violations = detect_dead_character_prose_violations("Alwina", text)
    assert violations == []


def test_possessive_body_is_not_a_violation():
    text = "They stood over Alwina's body while the survivors kept climbing."
    violations = detect_dead_character_prose_violations("Alwina", text)
    assert violations == []


def test_locative_past_is_not_a_violation():
    text = "The survivors went around where Alwina had stood and kept climbing."
    violations = detect_dead_character_prose_violations("Alwina", text)
    assert violations == []


def test_empty_dead_characters_empty_seam_returns_no_violations():
    # B4 edge case: chapter 1 has no prior seam.
    violations = detect_dead_character_prose_violations("", "any text here")
    assert violations == []


def test_name_not_in_text_returns_no_violations():
    text = "Hilde stepped forward and planted the staff."
    violations = detect_dead_character_prose_violations("Alwina", text)
    assert violations == []


# ── final_cut_context dead_characters field test ──────────────────────────────


def _doc_with_confirmed_dead_seam() -> dict:
    return {
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "seam_packet": {
                        "character_lifecycle": [
                            {
                                "name": "Alwina",
                                "existence_state": "confirmed_dead",
                                "visibility_mode": "absent",
                                "allowed_reappearance_from_chapter": None,
                                "source_chapter": 1,
                            }
                        ]
                    },
                    "turns": [],
                    "summary": "ch1",
                    "beats": ["a"],
                },
                "2": {
                    "turns": [],
                    "summary": "ch2",
                    "beats": ["b"],
                },
            },
        }
    }


def test_final_cut_context_includes_dead_characters_from_seam():
    doc = _doc_with_confirmed_dead_seam()
    ctx = final_cut_context(doc, "2")
    assert "dead_characters" in ctx
    assert "Alwina" in ctx["dead_characters"]


def test_final_cut_context_no_prior_seam_yields_empty_dead_characters():
    # Chapter 1 has no prior chapter — empty seam, empty dead_characters.
    doc = _doc_with_confirmed_dead_seam()
    ctx = final_cut_context(doc, "1")
    assert "dead_characters" in ctx
    assert ctx["dead_characters"] == ""


def test_build_allowed_scene_cast_filters_reviewed_and_lifecycle_forbidden():
    doc = {
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "seam_packet": {
                        "character_lifecycle": [
                            {
                                "name": "Alwina",
                                "existence_state": "confirmed_dead",
                                "visibility_mode": "absent",
                                "allowed_reappearance_from_chapter": None,
                                "source_chapter": 1,
                            }
                        ]
                    }
                },
                "2": {},
            },
        },
        "characters": {
            "roster": ["hilde", "alwina", "gunnar", "extra"],
            "cards": {
                "hilde": {"name": "Hilde", "reviewed": True},
                "alwina": {"name": "Alwina", "reviewed": True},
                "gunnar": {"name": "Gunnar", "reviewed": True},
                "extra": {"name": "Extra", "reviewed": False},
            },
        },
    }
    allowed = build_allowed_scene_cast(doc, "2")
    assert allowed == ["Hilde", "Gunnar"]


def test_final_cut_context_includes_allowed_cast_field():
    doc = {
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "summary": "s1",
                    "beats": ["b1"],
                    "seam_packet": {
                        "character_lifecycle": [
                            {
                                "name": "Alwina",
                                "existence_state": "confirmed_dead",
                                "visibility_mode": "absent",
                                "allowed_reappearance_from_chapter": None,
                                "source_chapter": 1,
                            }
                        ]
                    },
                },
                "2": {
                    "summary": "s2",
                    "beats": ["b2"],
                    "turns": [],
                },
            },
        },
        "characters": {
            "roster": ["hilde", "alwina"],
            "cards": {
                "hilde": {"name": "Hilde", "reviewed": True},
                "alwina": {"name": "Alwina", "reviewed": True},
            },
        },
    }
    ctx = final_cut_context(doc, "2")
    assert "allowed_cast" in ctx
    assert ctx["allowed_cast"] == "Hilde"
