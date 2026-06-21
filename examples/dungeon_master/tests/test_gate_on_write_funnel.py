"""Condemn the bypassable card-write boundary that FR-558 (Contract C) funnels.

THE DEFECT (composition, not detector): the per-card playability detectors
(``reversal_pack_gap``, ``unplayable_beat_gap``) are correct in isolation, but they
are wired into the outline path by convention -- any code that authors a chapter
card and writes it through a different door commits an un-playable card ungated.
FR-525/FR-528/FR-555 each re-bound the SAME battery at a NEW write site after a
bug slipped through the previous one. Contract C ends the whack-a-mole: bind the
per-card battery to the ONE typed write seam (``chapter_nav.write_chapter_card``,
FR-556) so every authoring path inherits it, and expose ``gate_chapter_card`` as
the single per-card wiring both outline paths call.

These tests prove the BINDING, not the detectors (which keep their own tests):
(a) writing a card that packs a removal-and-return reversal through the setter
RAISES ``ChapterGateError`` -- and the test never calls a detector to decide it,
proving the gate rides the write; (b) the same for a time-skip-epilogue final
beat; (c) a clean card commits unchanged (the passing path is byte-identical to
the FR-556 setter); (d) ``reoutline_chapter_beats`` now rejects an unplayable
final beat too (the battery generalized to the second authoring path); and (e)
``gate_chapter_card`` returns both detectors' gaps, tagged by kind.

Example tests are requirement-exempt (FR-474 J3): no ``@pytest.mark.req``.
"""

from __future__ import annotations

import pytest

from examples.dungeon_master.api import chapter_nav, gap_detectors, outline_ops

# A card whose authored summary+beats pack Arnulf's removal AND return into one
# chapter -- the un-playable reversal the 16-turn cap (FR-501) force-closes.
_PACKED_CARD = {
    "title": "Arnulf Lost and Returned",
    "summary": (
        "Arnulf is swept away by the flood and presumed drowned, then reappears "
        "alive among downstream refugees as the blood-feud reopens"
    ),
    "beats": [
        "Arnulf is swept from the ledge and lost to the flood",
        "Arnulf reappears alive among the downstream refugees",
    ],
    "cast": ["Arnulf"],
    "entry_state": "",
    "exit_state": "",
}

# A card whose FINAL beat is an unplayable time-skip epilogue (FR-528): a bounded
# scene can never enact a resolution that arrives only after a season passes.
_EPILOGUE_CARD = {
    "title": "The Long Winter",
    "summary": "The clan holds the ridge as the cold closes in.",
    "beats": [
        "The clan rations the last of the grain",
        "By spring, the survivors rebuild the steading on the high ground",
    ],
    "cast": ["Hilde"],
    "entry_state": "",
    "exit_state": "",
}

# A clean card: no same-chapter reversal, no time-skip final beat.
_CLEAN_CARD = {
    "title": "The Ridge Holds",
    "summary": "The clan fortifies the ridge against the next surge.",
    "beats": [
        "Scouts report the water still rising",
        "The clan raises an earthwork along the ridge",
    ],
    "cast": ["Hilde"],
    "entry_state": "",
    "exit_state": "",
}


def test_setter_funnels_reversal_pack_to_gate_error():
    """Writing a removal-and-return card through the ONE setter RAISES -- the gate
    rides the write, not the writer. The test never calls a detector to decide."""
    doc: dict = {"chapters": {"order": [], "cards": {}}}
    with pytest.raises(gap_detectors.ChapterGateError):
        chapter_nav.write_chapter_card(doc, "1", _PACKED_CARD)
    assert chapter_nav.chapter_card(doc, "1") == {}  # never committed


def test_setter_funnels_unplayable_epilogue_to_gate_error():
    """The same seam catches a time-skip-epilogue final beat (FR-528)."""
    doc: dict = {"chapters": {"order": [], "cards": {}}}
    with pytest.raises(gap_detectors.ChapterGateError):
        chapter_nav.write_chapter_card(doc, "1", _EPILOGUE_CARD)
    assert chapter_nav.chapter_card(doc, "1") == {}


def test_setter_commits_clean_card_unchanged():
    """The passing path is byte-identical to the FR-556 setter: a clean card commits."""
    doc: dict = {"chapters": {"order": [], "cards": {}}}
    chapter_nav.write_chapter_card(doc, "1", _CLEAN_CARD)
    assert chapter_nav.chapter_card(doc, "1") == _CLEAN_CARD


def test_gate_chapter_card_tags_both_detectors():
    """``gate_chapter_card`` is the single per-card wiring: it returns both detectors'
    gaps, each tagged by ``kind`` (reversal | unplayable). Empty for a clean card."""
    assert gate_chapter_card_kinds(_CLEAN_CARD) == set()
    assert gate_chapter_card_kinds(_PACKED_CARD) == {"reversal"}
    assert gate_chapter_card_kinds(_EPILOGUE_CARD) == {"unplayable"}


def gate_chapter_card_kinds(card: dict) -> set:
    return {g["kind"] for g in gap_detectors.gate_chapter_card(card)}


class _SeqStubApp:
    """A stub compiled graph whose ``ainvoke`` returns the next queued beat list."""

    def __init__(self, beat_lists: list[list[str]]):
        self._queue = list(beat_lists)

    async def ainvoke(self, payload: dict) -> dict:
        beats = self._queue.pop(0) if len(self._queue) > 1 else self._queue[0]
        return {"reoutline": {"beats": list(beats)}}


def _epilogue_reoutline_doc() -> dict:
    """A two-chapter doc whose ch2 is unplayed; the re-outline will return a beat
    list ending in a time-skip epilogue -- the unplayable beat the generalized
    battery must now catch at the SECOND authoring boundary too."""
    return {
        "synopsis": {"text": "the clan endures the long winter on the ridge"},
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "title": "The River Breaks",
                    "summary": "The clan retreats to the ridge",
                    "reviewed": True,
                    "world_state": {"characters": [], "objects": [], "facts": []},
                    "seam_packet": {"must_carry_facts": [], "character_lifecycle": []},
                    "turns": [{"n": 1, "recap": {"text": "r", "reviewed": True}}],
                },
                "2": {
                    "title": "The Long Winter",
                    "summary": "The clan holds the ridge as the cold closes in",
                    "reviewed": False,
                    "beats": ["the clan rations the grain"],
                    "turns": [],
                },
            },
        },
    }


_EPILOGUE_BEATS = [
    "The clan rations the last of the grain",
    "By spring, the survivors rebuild the steading on the high ground",
]


@pytest.mark.asyncio
async def test_reoutline_rejects_unplayable_final_beat(monkeypatch):
    """The battery generalized: ``reoutline_chapter_beats`` -- the FR-555 second
    authoring boundary -- now also rejects a time-skip-epilogue final beat, not just
    a packed reversal. A stub that only ever returns the epilogue exhausts retries
    and RAISES rather than committing the unplayable beat list."""
    doc = _epilogue_reoutline_doc()
    monkeypatch.setattr(
        outline_ops, "get_app", lambda graph: _SeqStubApp([_EPILOGUE_BEATS])
    )
    with pytest.raises(ValueError):
        await outline_ops.reoutline_chapter_beats(doc, "2")
