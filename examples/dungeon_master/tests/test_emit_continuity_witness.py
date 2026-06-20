"""FR-530 Stage 1 -- tests for the post-generation continuity witness.

Example-scoped (FR-474 J3): NO ``@pytest.mark.req``.
"""

from __future__ import annotations

import json
from pathlib import Path

from examples.dungeon_master.scripts import emit_continuity_witness as ew

_REVIEW_MD = """# Book Review

**Overall:** 4/5

## Continuity

Score: 2/5
- Arnulf declared dead then reappears alive.
- A resolved conflict restarts in the next chapter.

## Synopsis delivery

Score: 5/5
"""


def test_build_witness_projects_score_and_break_count() -> None:
    w = ew.build_witness("10099-BC", _REVIEW_MD)
    assert w["book"] == "10099-BC"
    assert w["continuity_score"] == 2
    assert w["break_count"] == 2
    # FR-522 posture is stamped into the record so consumers cannot mistake it for a gate.
    assert w["posture"] == "visibility-not-gate"


def test_write_witness_emits_machine_readable_json(tmp_path: Path) -> None:
    out = tmp_path / "10099-BC"
    out.mkdir()
    (out / "review.md").write_text(_REVIEW_MD, encoding="utf-8")

    witness = ew.write_witness(out)
    assert witness is not None

    written = out / ew.WITNESS_FILENAME
    assert written.exists()
    loaded = json.loads(written.read_text(encoding="utf-8"))
    # FR-531 can later join this record -- it is structured, not prose.
    assert loaded == {
        "book": "10099-BC",
        "continuity_score": 2,
        "break_count": 2,
        "posture": "visibility-not-gate",
    }


def test_write_witness_is_non_blocking_when_review_absent(tmp_path: Path) -> None:
    out = tmp_path / "no-review"
    out.mkdir()
    # No review.md: the witness must skip, not raise (FR-522 non-blocking posture).
    assert ew.write_witness(out) is None
    assert not (out / ew.WITNESS_FILENAME).exists()


# ── FR-538: additive seam-entrance block (roster lens, non-gating) ────────────


def _entrance_story_doc() -> dict:
    """A two-chapter doc whose Ch2 has a roster entrant acting with no arrival.

    Hilde is on-page in both; Arnulf acts in Ch2, was absent from Ch1 prose, and no
    arrival is staged — exactly one roster seam-entrance gap.
    """
    return {
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "text": "Hilde held the line on the ridge while the clan retreated.",
                    "turns": [{"n": 1, "intents": {"hilde": {"intent": "holds"}}}],
                },
                "2": {
                    "text": (
                        "Arnulf cut down the raider at the gate. "
                        "Hilde rallied the survivors behind him."
                    ),
                    "turns": [
                        {
                            "n": 1,
                            "intents": {
                                "arnulf": {"intent": "fights"},
                                "hilde": {"intent": "rallies"},
                            },
                        }
                    ],
                },
            },
        },
        "characters": {
            "roster": ["hilde", "arnulf"],
            "cards": {"hilde": {"name": "Hilde"}, "arnulf": {"name": "Arnulf"}},
        },
    }


def test_seam_entrance_summary_aggregates_roster_gaps() -> None:
    summary = ew.seam_entrance_summary(_entrance_story_doc())
    assert summary["gap_count"] == 1
    assert summary["by_kind"] == {"new": 1}
    assert summary["by_chapter"] == [
        {"chapter": "2", "gap_count": 1, "gaps": [{"name": "Arnulf", "kind": "new"}]}
    ]


def test_write_witness_includes_seam_entrance_block_when_story_present(
    tmp_path: Path,
) -> None:
    out = tmp_path / "10100-BC"
    (out / "story").mkdir(parents=True)
    (out / "review.md").write_text(_REVIEW_MD, encoding="utf-8")
    (out / "story" / "story.json").write_text(
        json.dumps(_entrance_story_doc()), encoding="utf-8"
    )

    witness = ew.write_witness(out)
    assert witness is not None
    assert witness["seam_entrance"]["gap_count"] == 1
    assert witness["seam_entrance"]["by_kind"] == {"new": 1}
    # The base record is unchanged; the block is purely additive (FR-538).
    assert witness["continuity_score"] == 2
    assert witness["posture"] == "visibility-not-gate"


# ── FR-544: additive overlay-trail block (derived projection, non-gating) ─────


def _overlay_trail_story_doc() -> dict:
    """A three-chapter doc where one roster character accrues state deltas.

    Arnulf has a committed ``character_state_delta`` in Ch1 and Ch2; Hilde never
    does. So ``derive_overlay`` returns a growing trail for Arnulf from Ch2 onward
    and ``{}`` for Hilde everywhere -- the sparse-is-truth case the FR conditions on.
    """
    return {
        "chapters": {
            "order": ["1", "2", "3"],
            "cards": {
                "1": {
                    "chapter_memory": {
                        "character_state_deltas": [
                            {
                                "name": "Arnulf",
                                "from_state": "alive",
                                "to_state": "swept downstream",
                                "evidence": "the flood took him under",
                            }
                        ]
                    },
                },
                "2": {
                    "chapter_memory": {
                        "character_state_deltas": [
                            {
                                "name": "Arnulf",
                                "from_state": "swept downstream",
                                "to_state": "alive, hauled out far downstream",
                                "evidence": "fishers dragged him from the reeds",
                            }
                        ]
                    },
                },
                "3": {"chapter_memory": {"character_state_deltas": []}},
            },
        },
        "characters": {
            "roster": ["arnulf", "hilde"],
            "cards": {"arnulf": {"name": "Arnulf"}, "hilde": {"name": "Hilde"}},
        },
    }


def test_overlay_trail_summary_emits_per_chapter_derived_state() -> None:
    summary = ew.overlay_trail_summary(_overlay_trail_story_doc())
    # One row per (chapter, character) with a non-empty overlay: Arnulf in Ch2 and Ch3.
    assert summary["transition_count"] == 2
    assert summary["posture"] == "visibility-not-gate"
    assert summary["by_chapter"] == [
        {
            "chapter": "2",
            "characters": [
                {
                    "name": "Arnulf",
                    "status": "swept downstream",
                    "history": ["chapter 1: swept downstream"],
                }
            ],
        },
        {
            "chapter": "3",
            "characters": [
                {
                    "name": "Arnulf",
                    "status": "alive, hauled out far downstream",
                    "history": [
                        "chapter 1: swept downstream",
                        "chapter 2: alive, hauled out far downstream",
                    ],
                }
            ],
        },
    ]


def test_overlay_trail_summary_omits_empty_overlay_characters() -> None:
    summary = ew.overlay_trail_summary(_overlay_trail_story_doc())
    # Hilde never accrued a delta -> empty overlay -> omitted from every chapter row.
    emitted_names = {
        c["name"] for ch in summary["by_chapter"] for c in ch["characters"]
    }
    assert "Hilde" not in emitted_names


def test_overlay_trail_summary_does_not_mutate_doc() -> None:
    doc = _overlay_trail_story_doc()
    before = json.dumps(doc, sort_keys=True)
    ew.overlay_trail_summary(doc)
    assert json.dumps(doc, sort_keys=True) == before


def test_write_witness_includes_overlay_trail_block_when_story_present(
    tmp_path: Path,
) -> None:
    out = tmp_path / "10101-BC"
    (out / "story").mkdir(parents=True)
    (out / "review.md").write_text(_REVIEW_MD, encoding="utf-8")
    (out / "story" / "story.json").write_text(
        json.dumps(_overlay_trail_story_doc()), encoding="utf-8"
    )

    witness = ew.write_witness(out)
    assert witness is not None
    assert witness["overlay_trail"]["transition_count"] == 2
    assert witness["overlay_trail"]["posture"] == "visibility-not-gate"
    # Additive: the base record and prior blocks are untouched.
    assert witness["continuity_score"] == 2
