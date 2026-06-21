"""FR-555: gate the state-aware re-outline output against ``reversal_pack_gap``.

The initial partition (``outline_ops.outline_chapters``) is gated: a chapter that
packs an actor's removal AND return is re-rolled with feedback, then raised
(FR-525). But the FR-523 state-aware re-outline re-authors a not-yet-played
chapter's beats from the FULL synopsis with the title/summary frozen and commits
them validating only ``_require_beats`` (non-empty) — it never re-applies
``reversal_pack_gap``. So the exact defect the partition gate exists to prevent
re-enters through a second, ungated write boundary (the 10036-BC Ch3 Arnulf
early-reveal: frozen summary "presumed dead" + a beat asserting he is "alive").

This condemns that ungated boundary: ``reoutline_chapter_beats`` must gate its own
output with the SAME detector and the SAME bounded-retry-then-raise discipline as
``outline_chapters``. Example tests are REQ-exempt (FR-474 J3).
"""

from __future__ import annotations

import pytest

from examples.dungeon_master.api import gap_detectors, outline_ops


class _SeqStubApp:
    """A stub compiled graph whose ``ainvoke`` returns the next queued beat list.

    One payload is popped per attempt, so a test can stage a packed first roll
    followed by a clean re-roll to exercise the bounded retry. When the queue is
    exhausted the last payload repeats (a stub that always packs).
    """

    def __init__(self, beat_lists: list[list[str]]):
        self._queue = list(beat_lists)

    async def ainvoke(self, payload: dict) -> dict:
        beats = self._queue.pop(0) if len(self._queue) > 1 else self._queue[0]
        return {"reoutline": {"beats": list(beats)}}


def _reveal_doc() -> dict:
    """Two-chapter doc mirroring 10036-BC: ch1 closed with Arnulf removed, ch2
    unplayed with a FROZEN summary that presumes him dead — the boundary at which a
    re-authored beat asserting he is alive packs a removal-and-return reversal."""
    return {
        "synopsis": {
            "text": "the flood takes the valley; Arnulf is presumed dead but is "
            "revealed alive far downstream and returns to the clan"
        },
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "title": "The River Breaks",
                    "summary": "Arnulf is swept away and the clan retreats",
                    "reviewed": True,
                    "world_state": {"characters": [], "objects": [], "facts": []},
                    "seam_packet": {
                        "must_carry_facts": ["Arnulf is presumed dead"],
                        "character_lifecycle": [],
                    },
                    "turns": [{"n": 1, "recap": {"text": "r", "reviewed": True}}],
                },
                "2": {
                    "title": "The Long Grief",
                    "summary": "With Arnulf presumed dead, Hilde grieves him while "
                    "holding the clan together",
                    "reviewed": False,
                    "beats": ["the clan mourns at the waterline"],
                    "turns": [],
                },
            },
        },
    }


# A re-authored beat list that re-packs the reversal: the frozen ch2 summary
# presumes Arnulf dead; this beat asserts he is alive — removal AND return, one
# chapter (the 10036-BC Ch3 early-reveal shape).
_PACKED_BEATS = [
    "Hilde learns Arnulf is revealed alive downstream and takes the news as grief",
    "the clan debates whether to search the lower fords",
]
# A clean re-roll: no actor is both removed and returned.
_CLEAN_BEATS = [
    "Hilde rations the failing grain stores",
    "the clan fortifies the ridge against the next surge",
]


@pytest.mark.asyncio
async def test_reoutline_raises_on_packed_reversal(monkeypatch):
    """RED: a re-outline that re-packs Arnulf's removal-and-return must RAISE,
    never commit the packed beats (the ungated second boundary, FR-555)."""
    doc = _reveal_doc()
    # The candidate card the gate must inspect (frozen summary + new beats) DOES pack.
    candidate = {
        "summary": doc["chapters"]["cards"]["2"]["summary"],
        "beats": _PACKED_BEATS,
    }
    assert gap_detectors.reversal_pack_gap(candidate)["gap_count"] == 1  # premise

    monkeypatch.setattr(
        outline_ops, "get_app", lambda graph: _SeqStubApp([_PACKED_BEATS])
    )

    with pytest.raises(ValueError, match="Arnulf"):
        await outline_ops.reoutline_chapter_beats(doc, "2")


@pytest.mark.asyncio
async def test_reoutline_retries_then_returns_clean_beats(monkeypatch):
    """A packed first roll is re-rolled with feedback; a clean second roll is
    accepted and returned (bounded-retry discipline mirrors outline_chapters)."""
    doc = _reveal_doc()
    monkeypatch.setattr(
        outline_ops,
        "get_app",
        lambda graph: _SeqStubApp([_PACKED_BEATS, _CLEAN_BEATS]),
    )

    beats = await outline_ops.reoutline_chapter_beats(doc, "2")

    assert beats == _CLEAN_BEATS


@pytest.mark.asyncio
async def test_reoutline_clean_passes_unchanged(monkeypatch):
    """A clean re-outline (no pack) returns its beats unchanged — no regression to
    the FR-523 seam-bridge purpose."""
    doc = _reveal_doc()
    monkeypatch.setattr(
        outline_ops, "get_app", lambda graph: _SeqStubApp([_CLEAN_BEATS])
    )

    beats = await outline_ops.reoutline_chapter_beats(doc, "2")

    assert beats == _CLEAN_BEATS


@pytest.mark.asyncio
async def test_reoutline_freezes_summary_across_retry(monkeypatch):
    """The frozen title/summary are unchanged after a packed-then-clean retry
    (J4 invariant: only beats are re-authored)."""
    doc = _reveal_doc()
    title_before = doc["chapters"]["cards"]["2"]["title"]
    summary_before = doc["chapters"]["cards"]["2"]["summary"]
    monkeypatch.setattr(
        outline_ops,
        "get_app",
        lambda graph: _SeqStubApp([_PACKED_BEATS, _CLEAN_BEATS]),
    )

    await outline_ops.reoutline_chapter_beats(doc, "2")

    assert doc["chapters"]["cards"]["2"]["title"] == title_before
    assert doc["chapters"]["cards"]["2"]["summary"] == summary_before
