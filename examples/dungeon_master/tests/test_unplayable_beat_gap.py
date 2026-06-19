"""Condemn the unplayable final-beat epilogue at OUTLINE time (FR-528 re-scope).

THE DEFECT (forensic, from outputs/dungeon-master/10025-BC story.json CH8):
    The whole-book partitioner (``outline_chapters`` + ``chapter_outline.yaml``)
    authored Chapter 8's FINAL beat as a time-skip epilogue --
    "By autumn, Hilde and Gunnar force a settlement that ends the blood-feud and
    joins the clans into one camp". A chapter resolves only when its director
    computes ``scene_complete = (k == n)`` over ``n = len(beats)`` (``turn_ops.
    _apply_beat_ledger``); a beat that happens *after a season passes* can never be
    enacted inside the FR-501 16-turn cap, so ``k`` is pinned at ``n-1`` forever,
    ``scene_complete`` never fires, and the chapter rides the cap replaying its
    already-resolved confrontation (the 208-turn no-progress tail FR-527 measured).

    FR-527 tried to cut this tail at the PLAY boundary with a beat-stall guard and
    was falsified: a count plateau is indistinguishable from a routine mid-scene
    pause (up to 9 turns in the corpus). The plateau is an OUTLINE defect -- a beat
    the bounded scene cannot physically reach -- so the cure normalizes at the
    partitioner boundary (``the_one_law``), not downstream.

    ``unplayable_beat_gap`` is that outline-time witness. It reads only the AUTHORED
    beats (no committed ledger, which does not exist before play) and fires when the
    FINAL beat LEADS with a future-time-skip marker ("By autumn,", "Years later,").
    The leading-anchor is the precise discriminator: an epilogue *opens* with the
    time jump, whereas a present-tense in-scene resolution does not -- so a beat that
    merely NAMES a settlement or the feud's end (a thing the scene CAN play) is not
    flagged. These tests pin (a) the real 10025-BC epilogue fires, (b) present-tense
    in-scene resolutions are clean, (c) a "settlement"/"feud" beat WITHOUT a leading
    time-skip is clean (the plausible-wrong-answer guard), and (d) a time-skip in a
    NON-final beat is not flagged (only the terminal epilogue pins the chapter open).

Example tests are requirement-exempt (FR-474 J3): no ``@pytest.mark.req``.
"""

from __future__ import annotations

from examples.dungeon_master.api import gap_detectors

# The exact 10025-BC CH8 shape: a final beat that LEADS with a time-skip ("By
# autumn,") describing a settlement reached after a season -- unplayable in 16 turns.
_EPILOGUE_CARD = {
    "title": "The Settlement",
    "beats": [
        "The clans reel as the living Arnulf shatters the flood's divine verdict",
        "Hilde and Gunnar stand against the renewed feud on the high ground",
        "By autumn, Hilde and Gunnar force a settlement that ends the blood-feud "
        "and joins the clans into one camp",
    ],
}

# A present-tense in-scene resolution (10020-BC CH8 / 10022-BC CH8 shape): the
# chapter's own scene CAN play this, so it is clean -- the GREEN target.
_IN_SCENE_RESOLUTION_CARD = {
    "title": "Dry Ground",
    "beats": [
        "The survivors crest the ridge into the high valley",
        "the survivors begin a new life on dry ground",
    ],
}

# The plausible-wrong-answer guard (10023-BC CH7 shape): the FINAL beat NAMES a
# settlement and the feud's end but in PRESENT tense, with NO leading time-skip --
# the scene plays it, so it must NOT be flagged. A co-occurrence detector keyed on
# "settlement"/"feud" would over-fire here; the leading-anchor does not.
_PRESENT_TENSE_SETTLEMENT_CARD = {
    "title": "The Truce Holds",
    "beats": [
        "Arnulf backs the break with the old feud",
        "Hilde ends the blood feud and Gunnar accepts the new settlement",
    ],
}

# A time-skip that appears in a NON-final beat is not the chapter-pinning epilogue:
# the chapter's LAST beat is still in-scene and reachable, so the chapter resolves.
_MIDDLE_TIME_SKIP_CARD = {
    "title": "The Long Climb",
    "beats": [
        "By autumn the passes will close, so they must move now",
        "Hilde and Gunnar reach the high ledge together",
    ],
}


def test_final_time_skip_epilogue_beat_is_flagged():
    """The real 10025-BC CH8 epilogue ("By autumn,...") fires once -- the bug."""
    result = gap_detectors.unplayable_beat_gap(_EPILOGUE_CARD)
    assert result["gap_count"] == 1
    gap = result["gaps"][0]
    assert gap["beat_index"] == 2
    assert gap["marker"] == "by autumn"
    assert gap["reason"] == "final_beat_time_skip_epilogue"
    assert gap["beat"].lower().startswith("by autumn")


def test_in_scene_resolution_final_beat_is_clean():
    """A present-tense in-scene resolution is playable within the cap -> no gap."""
    result = gap_detectors.unplayable_beat_gap(_IN_SCENE_RESOLUTION_CARD)
    assert result["gap_count"] == 0
    assert result["gaps"] == []


def test_present_tense_settlement_is_clean_plausible_wrong_answer_guard():
    """A final beat that NAMES a settlement/feud-end but does NOT lead with a
    time-skip is in-scene -> not flagged. Proves the witness keys on the leading
    time jump, not the mere presence of "settlement"/"feud" (the over-fire trap)."""
    result = gap_detectors.unplayable_beat_gap(_PRESENT_TENSE_SETTLEMENT_CARD)
    assert result["gap_count"] == 0
    assert result["gaps"] == []


def test_time_skip_in_non_final_beat_is_clean():
    """Only the FINAL beat pins the chapter open; a time-skip earlier in the list
    with an in-scene closing beat is clean (non-vacuous negative control)."""
    result = gap_detectors.unplayable_beat_gap(_MIDDLE_TIME_SKIP_CARD)
    assert result["gap_count"] == 0
    assert result["gaps"] == []


def test_empty_card_does_not_crash():
    """A card with no beats normalizes to no gap (boundary safety)."""
    result = gap_detectors.unplayable_beat_gap({})
    assert result["gap_count"] == 0
    assert result["gaps"] == []
