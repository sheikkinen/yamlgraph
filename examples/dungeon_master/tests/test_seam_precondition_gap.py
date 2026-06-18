"""Condemn the state-blind-outliner seam-teleport bug with a deterministic fixture.

THE HYPOTHESIS (forensic, from outputs/dungeon-master/10023-BC story.json):
    The chapter outliner writes each chapter's beats from the synopsis ALONE,
    blind to the physical end-state the prior chapter carried forward. In 10023-BC
    Chapter 2 closed with Arnulf ``status=alive, location="on the higher bank"``,
    yet Chapter 3 beat[0] was "Arnulf is swept away by the flood" — a death that
    requires him AT THE WATER. No bridging beat moved him there, so the generator
    silently teleported him from the safe high bank back into the flood. The
    director was later BLAMED for a continuity break the *planner* authored.

This fixture reproduces that exact seam with controlled vocabulary so the defect
is provable without a live model. ``seam_precondition_gap`` is the pure witness;
these tests prove (a) the unbridged lethal seam IS flagged — the bug — and
(b) a single bridging reposition beat CLEARS it — the fix's success criterion.

Example tests are requirement-exempt (FR-474 J3): no ``@pytest.mark.req``.
"""

from __future__ import annotations

from examples.dungeon_master.api import witness_metrics


def _floodmark_seam_doc(ch2_beats: list[str]) -> dict:
    """Two-chapter doc mirroring the 10023-BC Arnulf seam.

    Chapter 1 closes carrying Arnulf forward as alive on the higher bank (the
    inherited hard position). Chapter 2's beats are supplied by the caller so the
    presence/absence of a bridging reposition beat is the single changed variable.
    """
    return {
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "title": "The Line Holds",
                    "summary": "the clan is forced back up the slope",
                    "reviewed": True,
                    "world_state": {
                        "characters": [
                            {
                                "name": "Arnulf",
                                "status": "alive",
                                "location": "on the higher bank with the retreating line",
                            },
                            {
                                "name": "Hilde",
                                "status": "alive",
                                "location": "on the higher bank beside Gunnar",
                            },
                        ],
                        "objects": [],
                        "facts": ["the clan is forced back onto the higher bank"],
                    },
                    "seam_packet": {"character_lifecycle": []},
                    "beats": ["the line is forced back up the slope"],
                    "turns": [],
                },
                "2": {
                    "title": "The River Breaks",
                    "summary": "the flood takes the low ground",
                    "reviewed": False,
                    "beats": ch2_beats,
                    "turns": [],
                },
            },
        },
        "characters": {
            "reviewed": True,
            "roster": ["arnulf", "hilde"],
            "cards": {
                "arnulf": {"name": "Arnulf", "reviewed": True, "text": "brother"},
                "hilde": {"name": "Hilde", "reviewed": True, "text": "war-leader"},
            },
        },
    }


# ── the bug: a bare lethal beat over a carried-safe actor, no bridge ──────────


def test_unbridged_lethal_seam_is_flagged():
    """Arnulf carried safe on the higher bank, then 'swept away' with no bridge.

    This is the 10023-BC defect: the carried position and the death are physically
    incompatible and nothing moves him between them. The witness MUST flag it.
    """
    doc = _floodmark_seam_doc(
        [
            "Arnulf is swept away by the flood",
            "the others assume Arnulf has drowned",
        ]
    )
    result = witness_metrics.seam_precondition_gap(doc, "2")

    assert result["gap_count"] == 1, result
    gap = result["gaps"][0]
    assert gap["actor"] == "Arnulf"
    assert gap["carried_location"] == "on the higher bank with the retreating line"
    assert gap["exit_beat"] == "Arnulf is swept away by the flood"
    assert gap["exit_beat_index"] == 0
    assert gap["bridged"] is False


# ── the fix's success criterion: one bridging beat clears the gap ────────────


def test_bridge_beat_before_death_clears_the_gap():
    """A reposition beat that first moves Arnulf to the water removes the gap.

    This is exactly what a state-aware outliner (Fix A) would author: a bridge beat
    that makes the death physically continuous with the carried position.
    """
    doc = _floodmark_seam_doc(
        [
            "Arnulf goes back down the bank for a stranded clansman",
            "Arnulf is swept away by the flood",
            "the others assume Arnulf has drowned",
        ]
    )
    result = witness_metrics.seam_precondition_gap(doc, "2")
    assert result["gap_count"] == 0, result


def test_self_bridging_lethal_beat_clears_the_gap():
    """A single beat that both repositions and kills is self-bridged (no gap)."""
    doc = _floodmark_seam_doc(
        [
            "Arnulf loses his footing at the edge and is swept away by the flood",
        ]
    )
    result = witness_metrics.seam_precondition_gap(doc, "2")
    assert result["gap_count"] == 0, result


# ── boundary conditions: do not over-fire ────────────────────────────────────


def test_no_lethal_beat_means_no_gap():
    """An actor carried forward with no death beat is not a seam gap."""
    doc = _floodmark_seam_doc(
        [
            "Hilde rallies the survivors on the ridge",
            "Arnulf scouts the treeline",
        ]
    )
    result = witness_metrics.seam_precondition_gap(doc, "2")
    assert result["gap_count"] == 0, result


def test_first_chapter_has_no_carried_state_so_no_gap():
    """Chapter 1 inherits nothing, so it cannot have a carried-position gap."""
    doc = _floodmark_seam_doc(["Arnulf is swept away by the flood"])
    result = witness_metrics.seam_precondition_gap(doc, "1")
    assert result["carried_count"] == 0
    assert result["gap_count"] == 0
