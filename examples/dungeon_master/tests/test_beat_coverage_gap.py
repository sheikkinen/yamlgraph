"""Condemn the phantom-promise beat bug with a deterministic fixture (FR-524 Judgement).

THE HYPOTHESIS (forensic, from outputs/dungeon-master/10024-BC story.json — a book
generated WITH FR-523's state-aware beat re-outline already active):
    The chapter outliner packed a *reversal* into one chapter — Chapter 3's beats
    promise Arnulf is swept away (beat 1), grieved (beat 3), then "reappears alive"
    (beat 4) and "demands blood" (beat 5). But the play loop closes a chapter at
    CHAPTER_TURN_CAP = 16 turns (FR-501) whether or not every beat is reached.
    Chapter 3 played 16 turns of a single ledge scene, realized only beat 1, and was
    force-closed. ``close_chapter`` then FAITHFULLY committed Arnulf
    ``status="dead", location="downstream, carried off by the flood"``. Beats 4-5
    became phantom promises rendered into story.md that Chapter 4 correctly ignored
    — read by ``book_reviewer`` as a continuity break (Continuity 1/5).

    This is NOT cross-chapter "future-summary drift" (the FR-524 draft's claim): the
    committed ledger and Chapter 4 are mutually consistent. The contradiction is
    INSIDE Chapter 3 — between its enumerated beats and its own committed end-state.

This fixture reproduces that exact contradiction with controlled vocabulary so the
defect is provable without a live model. ``beat_coverage_gap`` is the pure witness;
these tests prove (a) a beat the chapter's OWN committed terminal ledger contradicts
IS flagged — the bug — and (b) a chapter whose ledger agrees with its beats is clean
— the negative control that proves the witness measures the contradiction, not the
mere presence of a return beat.

Example tests are requirement-exempt (FR-474 J3): no ``@pytest.mark.req``.
"""

from __future__ import annotations

from examples.dungeon_master.api import witness_metrics


def _reversal_chapter_doc(ch_beats: list[str], arnulf_status: str) -> dict:
    """One closed chapter whose committed ledger marks Arnulf ``arnulf_status``.

    The chapter's beats are supplied by the caller so the only changed variable is
    whether a beat promises a return the committed terminal status contradicts.
    """
    return {
        "chapters": {
            "order": ["3"],
            "cards": {
                "3": {
                    "title": "Arnulf Lost and Returned",
                    "summary": (
                        "Arnulf is swept away and presumed dead, then returns alive "
                        "and the feud reopens"
                    ),
                    "reviewed": True,
                    "beats": ch_beats,
                    "world_state": {
                        "characters": [
                            {
                                "name": "Arnulf",
                                "status": arnulf_status,
                                "location": "downstream, carried off by the flood",
                            },
                            {
                                "name": "Hilde",
                                "status": "alive",
                                "location": "on the narrow ledge",
                            },
                        ],
                        "objects": [],
                        "facts": ["the flood still blocks the route to higher ground"],
                    },
                    "seam_packet": {"character_lifecycle": []},
                    "turns": [{"n": i} for i in range(1, 17)],
                }
            },
        }
    }


_REVERSAL_BEATS = [
    "Floodwater tears Arnulf from the ledge and sweeps him downstream",
    "Hilde and Gunnar remain stranded as the Aschenwulf assume Arnulf has drowned",
    "Hilde grieves Arnulf while holding her war band together",
    "Arnulf reappears alive with a downstream group of refugees",
    "Arnulf blames Gunnar for the disaster and demands blood",
]

# The removal-only beats: no return promised, so the terminal ledger contradicts
# nothing — the negative control.
_REMOVAL_ONLY_BEATS = [
    "Floodwater tears Arnulf from the ledge and sweeps him downstream",
    "Hilde and Gunnar remain stranded as the Aschenwulf assume Arnulf has drowned",
    "Hilde grieves Arnulf while holding her war band together",
]


def test_phantom_return_beat_is_flagged():
    """A 'reappears alive' beat in a chapter whose ledger commits Arnulf dead fires."""
    doc = _reversal_chapter_doc(_REVERSAL_BEATS, arnulf_status="dead")
    result = witness_metrics.beat_coverage_gap(doc, "3")
    assert result["terminal_count"] == 1
    assert result["gap_count"] == 1
    gap = result["gaps"][0]
    assert gap["actor"] == "Arnulf"
    assert gap["ledger_status"] == "dead"
    assert gap["beat_index"] == 3
    assert gap["reason"] == "ledger_contradicts_beat"


def test_removal_only_chapter_is_clean_negative_control():
    """No return beat → the terminal ledger contradicts nothing → no gap.

    Proves the witness measures the beat-vs-ledger contradiction, not the mere
    presence of a dead character or a removal beat.
    """
    doc = _reversal_chapter_doc(_REMOVAL_ONLY_BEATS, arnulf_status="dead")
    result = witness_metrics.beat_coverage_gap(doc, "3")
    assert result["terminal_count"] == 1
    assert result["gap_count"] == 0


def test_living_ledger_with_return_beat_is_clean():
    """If the chapter committed Arnulf alive, a 'reappears alive' beat is consistent."""
    doc = _reversal_chapter_doc(_REVERSAL_BEATS, arnulf_status="alive")
    result = witness_metrics.beat_coverage_gap(doc, "3")
    assert result["terminal_count"] == 0
    assert result["gap_count"] == 0


def test_unclosed_chapter_with_prose_world_state_does_not_crash():
    """A not-yet-closed chapter (legacy prose world_state) normalizes to no terminal."""
    doc = _reversal_chapter_doc(_REVERSAL_BEATS, arnulf_status="dead")
    doc["chapters"]["cards"]["3"]["world_state"] = "Arnulf was swept away by the flood."
    result = witness_metrics.beat_coverage_gap(doc, "3")
    assert result["terminal_count"] == 0
    assert result["gap_count"] == 0
