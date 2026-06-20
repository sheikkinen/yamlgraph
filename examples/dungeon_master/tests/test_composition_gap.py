"""Condemn cross-chapter non-composition at outline time (FR-540).

THE PROBLEM (outputs/dungeon-master/10029-BC review, Ch2->Ch3): chapter 2 closes in
isolated grief (two people alone on a ledge); chapter 3 opens mid-crowd (an
assembled band) with no transition. Each chapter is locally coherent; together
they do not COMPOSE. The partitioner authors summary/beats/cast but never states
what is true at a chapter's open/close, so it cannot author chapter N+1 to open
FROM chapter N's close, and nothing validates the seam.

THE FIX: two authored chapter fields -- ``entry_state`` (true at open) and
``exit_state`` (true at close) -- plus a deterministic, roster-bounded
``composition_gap`` that flags an adjacent pair whose entry/exit configurations
contradict by a FROZEN antonym set {present<->absent, together<->scattered}. A
re-rollable outline gate in the family of FR-525/FR-528.

Scope carve (judged Condition 1): ``composition_gap`` is the SOCIAL-configuration
seam; the PHYSICAL lethal-seam belongs to ``seam_precondition_gap``. A pure
lethal-seam case must NOT be flagged here (test below).

Example tests are requirement-exempt (FR-474 J3): no ``@pytest.mark.req``.
"""

from __future__ import annotations

from examples.dungeon_master.api import turn_ops
from examples.dungeon_master.api.composition_gap import composition_gap
from examples.dungeon_master.api.gap_detectors import seam_precondition_gap
from examples.dungeon_master.api.outline_ops import _state_field


def _ch(
    *,
    title: str = "C",
    summary: str = "s",
    beats: tuple[str, ...] = ("b1", "b2"),
    cast: tuple[str, ...] = (),
    entry: str = "",
    exit_: str = "",
) -> dict:
    return {
        "title": title,
        "summary": summary,
        "beats": list(beats),
        "cast": list(cast),
        "entry_state": entry,
        "exit_state": exit_,
    }


# ── composition_gap: deterministic, roster-bounded antonym contradiction ─────


def test_composing_pair_passes() -> None:
    """An entry that composes with the prior exit raises no gap."""
    chapters = [
        _ch(exit_="The band stands together at the hall."),
        _ch(entry="The band is together at the hall, ready to set out."),
    ]
    assert composition_gap(chapters)["gap_count"] == 0


def test_together_scattered_contradiction_flagged() -> None:
    """The measured 10029-BC class: isolated close -> assembled open."""
    chapters = [
        _ch(exit_="Hilde and Arnulf are left alone, scattered on the ledge."),
        _ch(entry="The whole band is assembled together in the hall."),
    ]
    gap = composition_gap(chapters)
    assert gap["gap_count"] == 1
    assert gap["gaps"][0]["concept"] == "together-scattered"


def test_present_absent_shared_subject_flagged() -> None:
    """A roster name placed absent at close but present at next open is a gap."""
    chapters = [
        _ch(cast=("Arnulf",), exit_="Arnulf is swept away, gone downriver."),
        _ch(cast=("Arnulf",), entry="Arnulf is present at the gathering."),
    ]
    gap = composition_gap(chapters)
    assert gap["gap_count"] == 1
    assert gap["gaps"][0]["concept"] == "present-absent"


def test_present_absent_different_subjects_not_flagged() -> None:
    """Roster-bounded: absent X then present Y (a different actor) is not a gap."""
    chapters = [
        _ch(cast=("Arnulf", "Hilde"), exit_="Arnulf is gone downriver."),
        _ch(cast=("Arnulf", "Hilde"), entry="Hilde is present at the hall."),
    ]
    assert composition_gap(chapters)["gap_count"] == 0


def test_missing_contract_degrades_additively() -> None:
    """Condition 3: a pre-FR-540 chapter (no entry/exit_state) raises no gap."""
    chapters = [_ch(), _ch()]
    assert composition_gap(chapters)["gap_count"] == 0


# ── Condition 1 carve: the lethal-seam belongs to its sibling ────────────────


def test_pure_lethal_seam_not_flagged_by_composition_gap() -> None:
    """A physical lethal-seam fires seam_precondition_gap, NOT composition_gap."""
    doc = {
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "world_state": {
                        "characters": [
                            {
                                "name": "Arnulf",
                                "status": "alive",
                                "location": "the upper ford",
                            }
                        ],
                        "objects": [],
                        "facts": [],
                        "relationships": [],
                    },
                },
                "2": {
                    "beats": ["Arnulf is swept away by the flood and drowns"],
                    "entry_state": "The band gathers at the ford together.",
                    "exit_state": "The band remains together at the ford.",
                },
            },
        }
    }
    assert seam_precondition_gap(doc, "2")["gap_count"] >= 1
    chapters = [
        doc["chapters"]["cards"]["1"],
        doc["chapters"]["cards"]["2"],
    ]
    assert composition_gap(chapters)["gap_count"] == 0


# ── _state_field parser (outline boundary) ───────────────────────────────────


def test_state_field_parses_and_trims() -> None:
    assert _state_field({"entry_state": "  open here  "}, "entry_state") == "open here"


def test_state_field_missing_yields_empty() -> None:
    assert _state_field({"beats": []}, "entry_state") == ""
    assert _state_field({"exit_state": 42}, "exit_state") == ""


# ── running_scene surfaces entry_state on turn 1 only ────────────────────────


def test_running_scene_surfaces_entry_state_turn_one_only() -> None:
    doc = {
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {},
                "2": {
                    "title": "The Gathering",
                    "summary": "They assemble.",
                    "entry_state": "The whole band is assembled in the longhouse.",
                    "turns": [{"n": 1, "recap": {"text": "They gather."}}],
                },
            },
        }
    }
    scene_one = turn_ops.running_scene(doc, "2", 1)
    scene_two = turn_ops.running_scene(doc, "2", 2)
    assert "assembled in the longhouse" in scene_one
    assert "assembled in the longhouse" not in scene_two
