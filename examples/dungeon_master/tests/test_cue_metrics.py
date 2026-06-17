"""Deterministic cue-uptake metric tests for FR-505 (J3 example scope)."""

from __future__ import annotations

from examples.dungeon_master.api.cue_metrics import (
    cue_uptake,
    round_robin_paragraph_fraction,
)


def test_cue_uptake_matches_dialogue_and_expression_positive_case():
    prose = (
        "Hilde snapped, up the slope now, while Gunnar locked his feet at the ridge. "
        "Her jaw set and his eyes fixed on the ridge as the line held."
    )
    metrics = cue_uptake(
        prose,
        dialogue_snippets=["Up the slope now", "Hold the edge"],
        expression_cues=["jaw set, hand raised", "eyes fixed on the ridge"],
    )
    assert metrics["dialogue_total"] == 2
    assert metrics["dialogue_matched"] == 1
    assert metrics["expression_total"] == 2
    assert metrics["expression_matched"] >= 1
    assert metrics["cue_uptake"] > 0.0


def test_cue_uptake_negative_fixture_stays_zero():
    prose = "Rain hit the stone and the valley went quiet before dawn."
    metrics = cue_uptake(
        prose,
        dialogue_snippets=["Up the slope now", "Hold the edge"],
        expression_cues=["jaw set, hand raised", "eyes fixed on the ridge"],
    )
    assert metrics["dialogue_matched"] == 0
    assert metrics["expression_matched"] == 0
    assert metrics["cue_uptake"] == 0.0


def test_round_robin_paragraph_fraction_high_for_fixed_cycle():
    prose = (
        "Hilde drives the line uphill.\n\n"
        "Gunnar seals the flank with a short shout.\n\n"
        "Reinmar drags the gear clear of the water.\n\n"
        "Oda raises the staff and calls the pace.\n\n"
        "Hilde checks the ridge and keeps moving.\n\n"
        "Gunnar points the rear guard forward."
    )
    score = round_robin_paragraph_fraction(prose, ["Hilde", "Gunnar", "Reinmar", "Oda"])
    assert score == 1.0


def test_round_robin_paragraph_fraction_zero_for_varied_subjects():
    prose = (
        "The ridge path narrowed as floodwater hit the stones.\n\n"
        "Hilde barked one order and let silence carry the rest.\n\n"
        "A fallen pine split the trail and forced the column to bunch.\n\n"
        "Reinmar slipped, recovered, and threw the pack higher.\n\n"
        "Spray and grit blinded everyone for a breath."
    )
    score = round_robin_paragraph_fraction(prose, ["Hilde", "Gunnar", "Reinmar", "Oda"])
    assert score == 0.0
