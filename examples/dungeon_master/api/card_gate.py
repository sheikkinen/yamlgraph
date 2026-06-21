"""The per-card playability gate for DM v2 chapter authoring (FR-558 Contract C).

The ONE binding point for the per-card playability detectors. The pure witnesses
live in :mod:`gap_detectors`; this module COMPOSES the two card-level ones
(:func:`gap_detectors.reversal_pack_gap`, :func:`gap_detectors.unplayable_beat_gap`)
into a single battery and the :class:`ChapterGateError` raised when a card fails it.

The whole point of Contract C is that no authoring path can bypass the gates: the
typed setter (:func:`chapter_nav.write_chapter_card`) calls :func:`gate_chapter_card`
on every full card write (binding the gate to the WRITE, not the writer), and both
outline paths (``outline_ops.outline_chapters`` and ``reoutline_chapter_beats``)
route their per-card detection through this one function rather than wiring the
detectors themselves. The SEQUENCE-level gate (``composition_gap``) is deliberately
NOT here -- it is an adjacent-pair check, a different arity, and stays outline-level
(FR-558 J1).

A leaf over :mod:`gap_detectors`; never an LLM, never ``turn_ops``.
"""

from __future__ import annotations

from examples.dungeon_master.api.gap_detectors import (
    reversal_pack_gap,
    unplayable_beat_gap,
)


class ChapterGateError(ValueError):
    """A chapter card failed the per-card playability gate at the write boundary.

    Carries the chapter id (:attr:`cid`) and the tagged :attr:`gaps` the battery
    flagged, so a caller (or a forensic log) can see WHICH gate fired without
    re-running a detector. Distinct from :class:`story_doc.InvalidChapterCard`
    (structure, FR-556): this is playability -- a structurally-valid card the bounded
    16-turn scene (FR-501) could never actually play.
    """

    def __init__(self, cid: str, gaps: list[dict]):
        self.cid = cid
        self.gaps = gaps
        kinds = sorted({str(g.get("kind") or "?") for g in gaps})
        actors = sorted(
            {g["actor"] for g in gaps if g.get("kind") == "reversal" and "actor" in g}
        )
        detail = f"kinds={kinds}"
        if actors:
            detail += f" actors={actors}"
        super().__init__(
            f"chapter {cid} fails the per-card playability gate ({detail}): {gaps}"
        )


def gate_chapter_card(card: dict) -> list[dict]:
    """Run the per-card playability battery, returning tagged gaps (empty if clean).

    The single per-card detector wiring: :func:`gap_detectors.reversal_pack_gap`
    (removal AND return packed into one chapter) then
    :func:`gap_detectors.unplayable_beat_gap` (a time-skip-epilogue final beat the
    bounded scene cannot enact). Each returned gap is the detector's own gap dict
    tagged with ``kind`` (``"reversal"`` | ``"unplayable"``) so a caller can split
    them for per-kind correction feedback. Pure: reads only ``card``.
    """
    gaps: list[dict] = []
    for gap in reversal_pack_gap(card)["gaps"]:
        gaps.append({"kind": "reversal", **gap})
    for gap in unplayable_beat_gap(card)["gaps"]:
        gaps.append({"kind": "unplayable", **gap})
    return gaps
