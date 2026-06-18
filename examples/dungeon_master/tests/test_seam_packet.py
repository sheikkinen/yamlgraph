"""Prototype tests for DM v2 chapter seam continuity packet (FR-506).

A visibility harness, not a governance gate (FR-474 J3). These tests pin the
pure seam boundary utilities:
- tolerant parse/normalization from provider output,
- deterministic prompt formatting,
- deterministic opening-context validator.
"""

from __future__ import annotations

from examples.dungeon_master.api import seam_packet


def test_parse_seam_packet_tolerates_non_dict() -> None:
    assert seam_packet.parse_seam_packet(None) == {
        "resolved_events": [],
        "open_threads": [],
        "must_carry_facts": [],
        "opening_constraints": [],
        "character_lifecycle": [],
    }
    assert seam_packet.parse_seam_packet("junk") == {
        "resolved_events": [],
        "open_threads": [],
        "must_carry_facts": [],
        "opening_constraints": [],
        "character_lifecycle": [],
    }


def test_parse_seam_packet_normalizes_lists_and_dedupes() -> None:
    raw = {
        "resolved_events": [
            " The dam burst at dusk. ",
            "The dam burst at dusk.",
            None,
            3,
            "",
        ],
        "open_threads": ["Hilde distrusts Gunnar", "Hilde distrusts Gunnar"],
        "must_carry_facts": ["Arnulf is believed dead."],
        "opening_constraints": ["FORBID: Arnulf returns on page one"],
    }
    parsed = seam_packet.parse_seam_packet(raw)

    assert parsed["resolved_events"] == ["The dam burst at dusk."]
    assert parsed["open_threads"] == ["Hilde distrusts Gunnar"]
    assert parsed["must_carry_facts"] == ["Arnulf is believed dead."]
    assert parsed["opening_constraints"] == ["FORBID: Arnulf returns on page one"]


def test_format_seam_packet_renders_stable_sections() -> None:
    text = seam_packet.format_seam_packet(
        {
            "resolved_events": ["The dam burst at dusk."],
            "open_threads": ["Hilde distrusts Gunnar"],
            "must_carry_facts": ["Arnulf is believed dead."],
            "opening_constraints": ["FORBID: Arnulf returns on page one"],
        }
    )
    assert "Resolved Events:" in text
    assert "Open Threads:" in text
    assert "Must-Carry Facts:" in text
    assert "Opening Constraints:" in text


def test_validate_opening_context_reports_missing_and_forbidden() -> None:
    packet = {
        "must_carry_facts": ["Arnulf is believed dead."],
        "opening_constraints": ["FORBID: Arnulf returns alive"],
    }
    opening = "The camp argues at dawn; Gunnar says Arnulf returns alive before noon."
    violations = seam_packet.validate_opening_context(packet, opening)

    assert {
        "type": "missing_must_carry_fact",
        "value": "Arnulf is believed dead.",
    } in violations
    assert {
        "type": "forbidden_opening_assertion",
        "value": "Arnulf returns alive",
    } in violations


def test_validate_opening_context_clean_when_constraints_met() -> None:
    packet = {
        "must_carry_facts": ["Arnulf is believed dead."],
        "opening_constraints": ["FORBID: Arnulf returns alive"],
    }
    opening = "The band climbs in silence; Arnulf is believed dead."
    assert seam_packet.validate_opening_context(packet, opening) == []


def test_parse_seam_packet_normalizes_character_lifecycle_shape() -> None:
    parsed = seam_packet.parse_seam_packet(
        {
            "character_lifecycle": [
                {
                    "name": " Arnulf ",
                    "existence_state": "missing_presumed_dead",
                    "visibility_mode": "absent",
                    "allowed_reappearance_from_chapter": 5,
                    "source_chapter": 2,
                },
                {
                    "name": "arnulf",
                    "existence_state": "alive",
                    "visibility_mode": "present",
                    "allowed_reappearance_from_chapter": None,
                    "source_chapter": 3,
                },
            ]
        }
    )
    assert parsed["character_lifecycle"] == [
        {
            "name": "Arnulf",
            "existence_state": "missing_presumed_dead",
            "visibility_mode": "absent",
            "allowed_reappearance_from_chapter": 5,
            "source_chapter": 2,
        }
    ]


def test_validate_character_lifecycle_reports_early_return_and_visibility() -> None:
    packet = {
        "character_lifecycle": [
            {
                "name": "Arnulf",
                "existence_state": "missing_presumed_dead",
                "visibility_mode": "absent",
                "allowed_reappearance_from_chapter": 5,
                "source_chapter": 2,
            }
        ]
    }
    violations = seam_packet.validate_character_lifecycle(
        packet, chapter_id=3, active_cast_names=["Arnulf"]
    )
    assert {
        "type": "early_return_violation",
        "name": "Arnulf",
        "detail": "present before chapter 5",
    } in violations
    assert {
        "type": "visibility_contradiction_violation",
        "name": "Arnulf",
        "detail": "visibility_mode=absent conflicts with active cast",
    } in violations


def test_validate_character_lifecycle_reports_state_contradiction_for_confirmed_dead() -> (
    None
):
    packet = {
        "character_lifecycle": [
            {
                "name": "Arnulf",
                "existence_state": "confirmed_dead",
                "visibility_mode": "absent",
                "allowed_reappearance_from_chapter": None,
                "source_chapter": 4,
            }
        ]
    }
    violations = seam_packet.validate_character_lifecycle(
        packet, chapter_id=5, active_cast_names=["Arnulf"]
    )
    assert {
        "type": "state_contradiction_violation",
        "name": "Arnulf",
        "detail": "confirmed_dead character cannot be active",
    } in violations
