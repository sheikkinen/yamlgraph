"""Tests for FR-510: confirmed-dead character prose exclusion.

Tests for the active-role detection validator, the dead_characters context
field, and witness metric extraction.
"""

from __future__ import annotations

from examples.dungeon_master.api.prose_continuity import (
    detect_dead_character_prose_violations,
    detect_object_use_after_loss,
)
from examples.dungeon_master.api.turn_ops import (
    build_allowed_scene_cast,
    dead_character_names,
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


def test_final_cut_context_includes_dead_before_open_from_seam():
    doc = _doc_with_confirmed_dead_seam()
    ctx = final_cut_context(doc, "2")
    assert "dead_before_open" in ctx
    assert "Alwina" in ctx["dead_before_open"]
    # FR-510 regression: prior-seam dead does NOT leak into the within block.
    assert ctx["dead_within_chapter"] == ""


def test_final_cut_context_no_prior_seam_yields_empty_dead_before_open():
    # Chapter 1 has no prior chapter — empty seam, empty dead_before_open.
    doc = _doc_with_confirmed_dead_seam()
    ctx = final_cut_context(doc, "1")
    assert "dead_before_open" in ctx
    assert ctx["dead_before_open"] == ""
    assert ctx["dead_within_chapter"] == ""
    assert ctx["possession_facts"] == ""


# ── FR-519: intra-chapter prose-vs-state enforcement ─────────────────────────


def _closed_with_within_chapter_death() -> dict:
    """The close-graph output for a chapter where Hagan dies DURING the chapter."""
    return {
        "world_state": {
            "characters": [
                {"name": "Hilde", "status": "alive", "inventory": ["weapon"]},
                {"name": "Hagan", "status": "dead"},
            ],
            "objects": [{"name": "ritual staff", "holder": "Hagan"}],
        },
        "seam_packet": {
            "character_lifecycle": [
                {
                    "name": "Hagan",
                    "existence_state": "confirmed_dead",
                    "source_chapter": 6,
                }
            ]
        },
    }


def test_within_chapter_death_routes_to_dead_within_not_before_open():
    doc = _doc_with_confirmed_dead_seam()
    closed = _closed_with_within_chapter_death()
    before, within = dead_character_names(doc, "2", closed)
    assert "Hagan" in within
    assert "Hagan" not in before
    # Prior-seam death stays in before_open, never duplicated into within.
    assert "Alwina" in before
    assert "Alwina" not in within


def test_final_cut_context_threads_within_chapter_death_from_closed():
    doc = _doc_with_confirmed_dead_seam()
    closed = _closed_with_within_chapter_death()
    ctx = final_cut_context(doc, "2", closed)
    assert "Hagan" in ctx["dead_within_chapter"]
    assert "Alwina" in ctx["dead_before_open"]


def test_dead_within_empty_without_closed():
    # No closed payload at context time → no within-chapter death signal.
    doc = _doc_with_confirmed_dead_seam()
    before, within = dead_character_names(doc, "2", None)
    assert within == []
    assert "Alwina" in before


def _doc_with_inherited_possession() -> dict:
    return {
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "summary": "ch1",
                    "beats": ["a"],
                    "turns": [],
                    "world_state": {
                        "characters": [
                            {"name": "Hilde", "inventory": ["weapon"]},
                        ],
                        "objects": [{"name": "ritual staff", "holder": "Hagan"}],
                    },
                },
                "2": {"summary": "ch2", "beats": ["b"], "turns": []},
            },
        }
    }


def test_possession_facts_from_inherited_ledger():
    doc = _doc_with_inherited_possession()
    ctx = final_cut_context(doc, "2")
    pf = ctx["possession_facts"]
    assert "Hilde holds: weapon" in pf
    assert "ritual staff is held by Hagan" in pf


def test_possession_facts_empty_for_first_chapter():
    doc = _doc_with_inherited_possession()
    ctx = final_cut_context(doc, "1")
    assert ctx["possession_facts"] == ""


def test_detect_object_use_after_loss_flags_use_after_drop():
    text = (
        "Hilde drove her weapon into the mud, freeing both hands. "
        "Later she raised the weapon high and struck."
    )
    hits = detect_object_use_after_loss("weapon", "Hilde", text)
    assert hits
    assert hits[0]["object"] == "weapon"


def test_detect_object_use_after_loss_no_loss_no_hit():
    text = "Hilde raised the weapon high and struck the rival down."
    hits = detect_object_use_after_loss("weapon", "Hilde", text)
    assert hits == []


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


# ── FR-521 J2: missing_presumed_dead is a chapter-scoped death-point ──────────
#
# The synopsis "presumed dead → returns" arc rides exactly the lifecycle state the
# confirmed-only death-token filter excluded. Within a chapter, a presumed-dead
# character must be treated as a death-point; across chapters, the before-open bar
# stays confirmed-dead only, so a legitimate return is not barred.


def _closed_with_presumed_dead(name: str = "Arnulf") -> dict:
    """Close-graph output for a chapter where a character is swept to presumed dead."""
    return {
        "world_state": {
            "characters": [
                {"name": "Hilde", "status": "alive", "inventory": ["weapon"]},
                {"name": name, "status": "missing_presumed_dead"},
            ],
            "objects": [],
        },
        "seam_packet": {"character_lifecycle": []},
    }


def test_missing_presumed_dead_routes_to_dead_within_chapter():
    doc = _doc_with_confirmed_dead_seam()
    closed = _closed_with_presumed_dead("Arnulf")
    _before, within = dead_character_names(doc, "2", closed)
    assert "Arnulf" in within


def test_presumed_dead_inherited_seam_does_not_bar_before_open():
    # A character missing_presumed_dead at chapter open (NOT confirmed_dead) must
    # not be barred — the synopsis can return them (Arnulf ch6).
    doc = {
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "summary": "ch1",
                    "beats": ["a"],
                    "turns": [],
                    "seam_packet": {
                        "character_lifecycle": [
                            {
                                "name": "Arnulf",
                                "existence_state": "missing_presumed_dead",
                                "visibility_mode": "absent",
                                "allowed_reappearance_from_chapter": 6,
                                "source_chapter": 1,
                            }
                        ]
                    },
                },
                "2": {"summary": "ch2", "beats": ["b"], "turns": []},
            },
        }
    }
    before, _within = dead_character_names(doc, "2", None)
    assert "Arnulf" not in before
