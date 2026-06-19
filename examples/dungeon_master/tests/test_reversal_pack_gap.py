"""Condemn the same-chapter reversal over-pack at OUTLINE time (FR-525 Judgement).

THE DEFECT (forensic, from outputs/dungeon-master/10024-BC story.json):
    The whole-book partitioner (``outline_chapters`` + ``chapter_outline.yaml``)
    authored Chapter 3's SUMMARY to contain BOTH halves of a reversal — Arnulf is
    swept away/drowned AND reappears alive — and FR-523's beat re-outline, bound to
    "cover exactly the events the summary describes", faithfully emitted both. But the
    play loop closes a chapter at CHAPTER_TURN_CAP = 16 turns (FR-501); a single
    capped chapter cannot play a removal AND a return, so ``close_chapter`` commits
    Arnulf terminal and the return beat becomes the phantom ``beat_coverage_gap``
    flags AFTER the chapter is closed.

    ``reversal_pack_gap`` is the OUTLINE-TIME dual: it reads only the AUTHORED
    summary+beats (no committed ledger, which does not exist before play) so the pack
    can be caught and split at the partitioner — the boundary where it enters
    (``the_one_law``) — instead of patched downstream. These tests prove (a) a chapter
    whose authored text removes AND returns the same actor IS flagged — the bug — and
    (b) a removal-only chapter, a return-only chapter, and a reversal SPLIT across two
    chapters are each clean — the non-vacuous negative controls proving the witness
    measures the same-chapter pack, not the mere presence of a death or a return.

Example tests are requirement-exempt (FR-474 J3): no ``@pytest.mark.req``.
"""

from __future__ import annotations

from examples.dungeon_master.api import gap_detectors

# One chapter that packs BOTH halves of Arnulf's reversal — the summary alone
# carries removal (swept/presumed/drowned) and return (reappears/alive), and the
# beats restate both. This is the un-playable pack the 16-turn cap force-closes.
_OVERPACK_CARD = {
    "title": "Arnulf Lost and Returned",
    "summary": (
        "Arnulf is swept away by the flood and presumed drowned, then reappears "
        "alive among downstream refugees as the blood-feud reopens"
    ),
    "beats": [
        "Arnulf is swept from the ledge and lost to the flood",
        "The band mourns Arnulf as drowned and holds the high ground",
        "Arnulf reappears alive among the downstream refugees",
        "Arnulf demands blood from Gunnar for the disaster",
    ],
}

# Removal only: the same loss, no return promised anywhere — the chapter the play
# loop CAN finish inside its budget.
_REMOVAL_ONLY_CARD = {
    "title": "Arnulf Lost to the Flood",
    "summary": (
        "Arnulf is torn from the ledge and swept downstream; the band mourns him "
        "as drowned and fights to hold the high ground"
    ),
    "beats": [
        "Arnulf is swept from the ledge and lost to the flood",
        "The band mourns Arnulf as drowned and holds the high ground",
    ],
}

# Return only: the second half of the reversal, authored as its OWN later chapter
# (the FR-525 cure) — no removal token, so nothing to pack.
_RETURN_ONLY_CARD = {
    "title": "Arnulf Returns",
    "summary": (
        "Arnulf reappears alive among the downstream refugees and rejoins the band "
        "as it reaches the high valley, and the blood-feud reopens"
    ),
    "beats": [
        "Arnulf reappears alive among the downstream refugees",
        "Arnulf rejoins the band and demands blood from Gunnar",
    ],
}


def test_overpacked_reversal_chapter_is_flagged():
    """A chapter whose authored text removes AND returns Arnulf fires once for him."""
    result = gap_detectors.reversal_pack_gap(_OVERPACK_CARD)
    assert result["gap_count"] == 1
    assert result["packed_actors"] == ["Arnulf"]
    gap = result["gaps"][0]
    assert gap["actor"] == "Arnulf"
    assert gap["reason"] == "removal_and_return_same_chapter"
    assert gap_detectors._text_has_token(
        gap["removal_unit"], gap_detectors._TERMINAL_STATUS_TOKENS
    )
    assert gap_detectors._text_has_token(
        gap["return_unit"], gap_detectors._RETURN_PRESENCE_TOKENS
    )


def test_removal_only_chapter_is_clean_negative_control():
    """A loss with no promised return is playable within the cap → no pack.

    Proves the witness measures the removal+return pack, not the mere presence of a
    death or a removed character.
    """
    result = gap_detectors.reversal_pack_gap(_REMOVAL_ONLY_CARD)
    assert result["gap_count"] == 0
    assert result["packed_actors"] == []


def test_return_only_chapter_is_clean_negative_control():
    """A return authored as its own chapter (the cure) carries no removal → no pack."""
    result = gap_detectors.reversal_pack_gap(_RETURN_ONLY_CARD)
    assert result["gap_count"] == 0
    assert result["packed_actors"] == []


def test_reversal_split_across_two_chapters_is_clean():
    """The FR-525 cure: removal in chapter N, return in chapter N+1 — each clean.

    The deterministic shape the outliner must produce. Neither card, read on its own,
    packs both halves, so ``reversal_pack_gap`` is clean for both — the GREEN target.
    """
    assert gap_detectors.reversal_pack_gap(_REMOVAL_ONLY_CARD)["gap_count"] == 0
    assert gap_detectors.reversal_pack_gap(_RETURN_ONLY_CARD)["gap_count"] == 0


def test_empty_card_does_not_crash():
    """A card with no summary/beats normalizes to no pack (boundary safety)."""
    result = gap_detectors.reversal_pack_gap({})
    assert result["gap_count"] == 0
    assert result["packed_actors"] == []
