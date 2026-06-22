"""FR-564 M4b realize: beat-driven turn instruction (beat_instruction + belief_at + wiring).

Example tests are requirement-exempt (FR-474 J3): NO ``@pytest.mark.req``, NO capability YAML.

The realize milestone closes the v3 loop: the validated ``PlotPlan`` steers the prose via
``beat_instruction(plan, chapter) -> str`` producing a turn instruction from authored beats,
focalized on belief (not world-truth). Tests are deterministic (no LLM); the end-to-end render
is witnessed by the demo path (AC5b).

AC1: beat renders to instruction (ch1 villainy, ch6 reveal + reconciliation).
AC2: un-planned chapter returns ''.
AC3: wiring is additive + gated (plan attached vs absent).
AC4: belief focalization, not world revival.
"""

from __future__ import annotations

from examples.dungeon_master.api.plot import floodmark as fm
from examples.dungeon_master.api.plot.project import belief_at
from examples.dungeon_master.api.plot.realize import beat_instruction

# --- AC1: Beat renders to instruction ---------------------------------------------------


def test_beat_instruction_ch1_villainy():
    """F1 villainy at ch1: directive names the villainy intent (loss / presumed-dead belief flip)."""
    result = beat_instruction(fm.floodmark, 1)
    assert result, "ch1 carries F1 villainy -- must produce a non-empty directive"
    assert "villainy" in result.lower() or "F1" in result


def test_beat_instruction_ch6_reveal_and_reconciliation():
    """Ch6 carries BOTH Fr (reveal) and Ff (reconciliation) in ordered_functions order."""
    result = beat_instruction(fm.floodmark, 6)
    assert result, "ch6 carries two beats -- must produce a non-empty directive"
    # Both beats named
    assert "Fr" in result or "reveal" in result.lower()
    assert "Ff" in result or "reconciliation" in result.lower()
    # The reveal appears before the reconciliation (ordered_functions order)
    reveal_pos = result.lower().find("reveal")
    recon_pos = result.lower().find("reconciliation")
    if reveal_pos >= 0 and recon_pos >= 0:
        assert (
            reveal_pos < recon_pos
        ), "reveal must precede reconciliation (ordered_functions)"


# --- AC2: Un-planned chapter is empty ---------------------------------------------------


def test_beat_instruction_empty_chapter():
    """Chapter 3 carries no beat -- returns '' (byte-for-byte unchanged instruction)."""
    assert beat_instruction(fm.floodmark, 3) == ""


def test_beat_instruction_far_future_chapter():
    """Chapter 99 carries no beat -- returns '' (no beats anywhere near)."""
    assert beat_instruction(fm.floodmark, 99) == ""


# --- AC3: Wiring is additive + gated (invoke_turn boundary) ----------------------------


def test_wiring_additive_with_plan():
    """With a plan attached, instruction contains both stage instruction and beat directive."""
    from examples.dungeon_master.api.plot.realize import merge_beat_instruction

    stage_instruction = "The storm intensifies."
    beat = beat_instruction(fm.floodmark, 1)
    merged = merge_beat_instruction(stage_instruction, beat)
    assert "The storm intensifies." in merged
    assert beat in merged
    assert merged != stage_instruction, "merge must augment, not passthrough"


def test_wiring_passthrough_without_beat():
    """No beat at this chapter -> instruction is byte-for-byte the stage value."""
    from examples.dungeon_master.api.plot.realize import merge_beat_instruction

    stage_instruction = "The storm intensifies."
    beat = beat_instruction(fm.floodmark, 3)  # empty
    merged = merge_beat_instruction(stage_instruction, beat)
    assert merged == stage_instruction, "empty beat must not alter instruction"


def test_wiring_passthrough_without_plan():
    """No plan attached -> merge with empty beat is identity."""
    from examples.dungeon_master.api.plot.realize import merge_beat_instruction

    stage_instruction = "The storm intensifies."
    merged = merge_beat_instruction(stage_instruction, "")
    assert merged == stage_instruction


# --- AC4: Belief focalization, not world revival -----------------------------------------


def test_belief_at_ch1_through_ch5_believes_dead():
    """During the belief window (F1@ch1 flips belief), (Clan, Arnulf) -> False for ch1-5."""
    for ch in range(1, 6):
        beliefs = belief_at(fm.floodmark, ch)
        assert ("Clan", "Arnulf") in beliefs, f"ch{ch}: missing belief entry"
        assert (
            beliefs[("Clan", "Arnulf")] is False
        ), f"ch{ch}: clan must believe Arnulf dead"


def test_belief_at_ch6_believes_alive():
    """At ch6 the reveal Fr restores (Clan, Arnulf) -> True."""
    beliefs = belief_at(fm.floodmark, 6)
    assert ("Clan", "Arnulf") in beliefs
    assert beliefs[("Clan", "Arnulf")] is True


def test_belief_at_initial_believes_alive():
    """Before any beat (ch0), initial_belief: (Clan, Arnulf) -> True."""
    beliefs = belief_at(fm.floodmark, 0)
    assert ("Clan", "Arnulf") in beliefs
    assert beliefs[("Clan", "Arnulf")] is True


def test_beat_instruction_ch1_focalized_on_belief():
    """The ch1 villainy instruction asserts belief (believes-dead), not world-truth death."""
    result = beat_instruction(fm.floodmark, 1)
    lower = result.lower()
    # Must reference belief, not world-truth death
    assert "believ" in lower or "belief" in lower or "presumed" in lower
    # Must NOT assert world-truth death
    for forbidden in [
        "world-truth",
        "actually dies",
        "truly dead",
        "killed in reality",
    ]:
        assert (
            forbidden not in lower
        ), f"instruction must not assert world-truth: {forbidden}"


def test_beat_instruction_ch6_focalized_on_belief_restoration():
    """The ch6 reveal instruction asserts belief restoration, not world-truth revival."""
    result = beat_instruction(fm.floodmark, 6)
    lower = result.lower()
    # Must reference the belief flipping back to alive
    assert "believ" in lower or "belief" in lower or "reveal" in lower
