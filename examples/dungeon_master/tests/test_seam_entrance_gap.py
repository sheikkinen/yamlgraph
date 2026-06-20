"""Condemn the unrendered-entrance seam defect with a deterministic fixture (FR-538).

THE DEFECT (forensic, from outputs/dungeon-master/10028-BC review.md):
    FR-537 scoped *who acts* per chapter, producing clean two-handers. But a
    character correctly absent from chapter N's scoped cast now enters N+1 with no
    narrated arrival: 10028-BC Chapter 3 opened with Arnulf acting, though he was
    "never mentioned, named, or present in Chapter 2." We model exits
    (``seam_precondition_gap``) but not entrances — the mirror edge.

``seam_entrance_gap`` is the pure witness for that edge. It flags any character who
ACTS in a chapter's final-cut prose but crossed the seam with no on-page arrival —
present in chapter N, neither on-page in N−1 nor staged arriving in N. The
gating signal is PROSE establishment (an arrival/reposition token-run near the
entrant), never a manifest lookup (FR-538 Judgement B1): a name FR-539 lists but
does not narrate still counts as a gap.

These tests prove (a) the unrendered entrance IS flagged; (b) a single arrival line
CLEARS it (the fix's success criterion); (c) an entrant already on-page in N−1 is
not a gap; (d) a merely-mentioned (grieved, not acting) name is not a gap; plus the
first-chapter exclusion and the new/returning/continuing taxonomy.

Example tests are requirement-exempt (FR-474 J3): no ``@pytest.mark.req``.
"""

from __future__ import annotations

from examples.dungeon_master.api import seam_entrance as gap_detectors


def _doc(chapters: list[dict]) -> dict:
    """Build a DM v2 doc from per-chapter specs (the single changed variable).

    Each ``chapters`` entry is ``{text, acting_ids, [seam_lifecycle]}``:
    - ``text``: the chapter's final-cut prose (what the reviewer reads).
    - ``acting_ids``: roster char-ids that recorded a turn intent that chapter
      (the "acted" half of acted-vs-mentioned — FR-538 R1).
    - ``seam_lifecycle`` (optional): the chapter's ``character_lifecycle`` rows,
      inherited by the NEXT chapter (drives the ``returning`` taxonomy).
    """
    order = [str(i + 1) for i in range(len(chapters))]
    cards: dict = {}
    for i, ch in enumerate(chapters):
        cid = str(i + 1)
        intents = {
            char_id: {
                "intent": "acts",
                "thinking": "",
                "dialogue": "",
                "expression": "",
            }
            for char_id in ch.get("acting_ids", [])
        }
        card = {
            "title": f"Chapter {cid}",
            "reviewed": True,
            "text": ch["text"],
            "turns": [
                {"n": 1, "intents": intents, "recap": {"text": "", "reviewed": True}}
            ],
        }
        if "seam_lifecycle" in ch:
            card["seam_packet"] = {"character_lifecycle": ch["seam_lifecycle"]}
        cards[cid] = card
    return {
        "chapters": {"order": order, "cards": cards},
        "characters": {
            "reviewed": True,
            "roster": ["hilde", "arnulf"],
            "cards": {
                "hilde": {"name": "Hilde", "reviewed": True},
                "arnulf": {"name": "Arnulf", "reviewed": True},
            },
        },
    }


# ── the defect: an entrant who acts with no on-page arrival ───────────────────


def test_unrendered_entrance_is_flagged():
    """Arnulf acts in Ch2, was not on-page in Ch1, and no arrival is staged.

    This is the 10028-BC seam-entrance defect: a major named character appears with
    no prior establishment. The witness MUST flag it. Hilde acts in both chapters
    (on-page in Ch1) and is the negative control — she is not an entrance.
    """
    doc = _doc(
        [
            {
                "text": "Hilde held the line on the ridge while the clan retreated.",
                "acting_ids": ["hilde"],
            },
            {
                "text": (
                    "Arnulf cut down the raider at the gate and seized the standard. "
                    "Hilde rallied the survivors behind him."
                ),
                "acting_ids": ["arnulf", "hilde"],
            },
        ]
    )
    result = gap_detectors.seam_entrance_gap(doc, "2")

    assert result["chapter"] == "2"
    assert result["acting_count"] == 2
    assert result["gap_count"] == 1, result
    gap = result["gaps"][0]
    assert gap["name"] == "Arnulf"
    assert gap["kind"] == "new"  # never on-page in any prior chapter
    assert gap["last_on_page_chapter"] is None
    assert gap["established"] is False


# ── the fix's success criterion: a staged arrival clears the gap ──────────────


def test_staged_arrival_clears_the_gap():
    """One arrival line for Arnulf in Ch2 prose removes the gap.

    This is exactly what FR-539's seam-aware Final Cut must author: prose that
    stages the entrance. Establishment is measured in the PROSE, not a manifest
    (FR-538 B1).
    """
    doc = _doc(
        [
            {
                "text": "Hilde held the line on the ridge while the clan retreated.",
                "acting_ids": ["hilde"],
            },
            {
                "text": (
                    "Arnulf arrived at the gate at dawn, having marched through the "
                    "night, then cut down the raider and seized the standard."
                ),
                "acting_ids": ["arnulf", "hilde"],
            },
        ]
    )
    result = gap_detectors.seam_entrance_gap(doc, "2")
    assert result["gap_count"] == 0, result


# ── boundary conditions: do not over-fire ─────────────────────────────────────


def test_on_page_in_previous_chapter_is_not_an_entrance():
    """Arnulf already on-page in Ch1 prose is a continuation, not an entrance."""
    doc = _doc(
        [
            {
                "text": "Hilde and Arnulf held the line on the ridge together.",
                "acting_ids": ["hilde", "arnulf"],
            },
            {
                "text": "Arnulf cut down the raider at the gate.",
                "acting_ids": ["arnulf"],
            },
        ]
    )
    result = gap_detectors.seam_entrance_gap(doc, "2")
    assert result["gap_count"] == 0, result


def test_merely_mentioned_name_is_not_an_entrance():
    """A name in prose without a recorded intent is mentioned, not acting (R1).

    Hilde grieves FOR Arnulf in Ch2; he is named but records no intent. A grieved
    name is not an entrance — only acting names can cross a seam.
    """
    doc = _doc(
        [
            {
                "text": "Hilde held the line on the ridge while the clan retreated.",
                "acting_ids": ["hilde"],
            },
            {
                "text": (
                    "Hilde grieved for Arnulf, who had not been seen since the "
                    "bridge fell, and rallied the survivors alone."
                ),
                "acting_ids": ["hilde"],
            },
        ]
    )
    result = gap_detectors.seam_entrance_gap(doc, "2")
    assert result["gap_count"] == 0, result


def test_first_chapter_has_no_previous_so_no_entrance_gap():
    """Chapter 1 has no prior chapter, so it cannot have a seam-entrance gap."""
    doc = _doc(
        [
            {
                "text": "Arnulf cut down the raider at the gate.",
                "acting_ids": ["arnulf"],
            },
        ]
    )
    result = gap_detectors.seam_entrance_gap(doc, "1")
    assert result["gap_count"] == 0
    assert result["gaps"] == []


# ── taxonomy: new / returning / continuing (derived, never authored) ──────────


def test_returning_entrant_via_inherited_lifecycle():
    """Arnulf on-page in Ch1, absent Ch2 (lifecycle record), back acting in Ch3.

    The inherited ``character_lifecycle`` absence record classifies him as
    ``returning``; ``last_on_page_chapter`` points at his last on-page chapter.
    """
    doc = _doc(
        [
            {
                "text": "Hilde and Arnulf held the line on the ridge together.",
                "acting_ids": ["hilde", "arnulf"],
                "seam_lifecycle": [],
            },
            {
                "text": "Hilde mourned the missing and held the gate alone.",
                "acting_ids": ["hilde"],
                "seam_lifecycle": [
                    {
                        "name": "Arnulf",
                        "existence_state": "missing_presumed_dead",
                        "visibility_mode": "absent",
                    }
                ],
            },
            {
                "text": "Arnulf cut down the raider at the gate and seized the standard.",
                "acting_ids": ["arnulf"],
            },
        ]
    )
    result = gap_detectors.seam_entrance_gap(doc, "3")
    assert result["gap_count"] == 1, result
    gap = result["gaps"][0]
    assert gap["name"] == "Arnulf"
    assert gap["kind"] == "returning"
    assert gap["last_on_page_chapter"] == "1"


def test_continuing_entrant_scoped_out_then_back():
    """Arnulf on-page Ch1, scoped out of Ch2 (no lifecycle record), back in Ch3.

    No absence record exists, so he is ``continuing`` — on-page earlier, off in the
    immediate prior chapter, back now — distinct from a genuine newcomer.
    """
    doc = _doc(
        [
            {
                "text": "Hilde and Arnulf held the line on the ridge together.",
                "acting_ids": ["hilde", "arnulf"],
            },
            {
                "text": "Hilde held the gate while the others rested below.",
                "acting_ids": ["hilde"],
            },
            {
                "text": "Arnulf cut down the raider at the gate and seized the standard.",
                "acting_ids": ["arnulf"],
            },
        ]
    )
    result = gap_detectors.seam_entrance_gap(doc, "3")
    assert result["gap_count"] == 1, result
    gap = result["gaps"][0]
    assert gap["name"] == "Arnulf"
    assert gap["kind"] == "continuing"
    assert gap["last_on_page_chapter"] == "1"


# ── FR-543: a later death-fall sentence must not clear an unbridged entrance ───


def test_exit_fall_sentence_does_not_clear_unbridged_entrance():
    """10030-BC Ch3: Arnulf enters unbridged, then later FALLS -- still a gap.

    Forensic (outputs/dungeon-master/10030-BC, review break #2): Arnulf is absent
    from the prose of Ch1 and Ch2, then first appears in Ch3 as "was already with
    them" -- the literal opposite of a narrated arrival. A LATER sentence narrates
    his death-fall "into the water" (an EXIT). The FR-538 witness borrowed the
    exit-edge lexicon, so the fall token wrongly cleared the entrance and reported
    ``gap_count == 0``.

    The establish lexicon must contain ONLY arrival verbs: a fall/exit sentence is
    not an arrival, so the unbridged entrance MUST still be flagged.
    """
    doc = _doc(
        [
            {
                "text": "Hilde held the line on the ridge while the clan retreated.",
                "acting_ids": ["hilde"],
            },
            {
                "text": "Hilde mustered the survivors and waited for the flood to crest.",
                "acting_ids": ["hilde"],
            },
            {
                "text": (
                    "Arnulf was already with them on the higher stone, shoulders "
                    "squared against the wind, when Hilde turned. Later, as the water "
                    "rose, Arnulf slid off the ledge and dropped into the water below."
                ),
                "acting_ids": ["arnulf", "hilde"],
            },
        ]
    )
    result = gap_detectors.seam_entrance_gap(doc, "3")
    assert result["gap_count"] == 1, result
    gap = result["gaps"][0]
    assert gap["name"] == "Arnulf"
    assert gap["kind"] == "new"
    assert gap["established"] is False
