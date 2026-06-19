"""FR-523: state-aware chapter re-outline — GREEN acceptance (J1–J10).

The chapter outliner is state-blind: it writes each chapter's beats from the
synopsis alone, so a lethal beat ("Arnulf is swept away by the flood") can land on
an actor the prior chapter left safe on the higher bank, with no beat bridging the
two — the seam-teleport condemned in ``test_seam_precondition_gap.py``. This
re-authors the NEXT chapter's beats from the prior chapter's committed
``world_state``/``seam_packet`` so the planner can write the bridging reposition
beat the death requires.

AC-1 is the deterministic gate (stubbed graph + fixture + a non-vacuity negative
control); the live regen is corroboration, not a gate. Example tests are
REQ-exempt (FR-474 J3).
"""

from __future__ import annotations

import copy

import pytest

from examples.dungeon_master.api import (
    chapter_ops,
    doc_ops,
    gap_detectors,
)


class _StubApp:
    """A stub compiled graph whose ``ainvoke`` returns a fixed re-outline payload."""

    def __init__(self, beats: list[str]):
        self._beats = beats

    async def ainvoke(self, payload: dict) -> dict:
        return {"reoutline": {"beats": list(self._beats)}}


def _seam_doc() -> dict:
    """Two-chapter doc: ch1 closed leaving Arnulf safe + high, ch2 unplayed with a
    bare lethal beat — the exact 10023-BC pathology."""
    return {
        "synopsis": {"text": "the flood takes the valley; Arnulf is lost and returns"},
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
                                "location": (
                                    "on the higher bank with the retreating line"
                                ),
                            }
                        ],
                        "objects": [],
                        "facts": ["the clan is forced back onto the higher bank"],
                    },
                    "seam_packet": {
                        "must_carry_facts": ["the clan holds the higher bank"],
                        "character_lifecycle": [],
                    },
                    "turns": [{"n": 1, "recap": {"text": "r", "reviewed": True}}],
                },
                "2": {
                    "title": "The River Breaks",
                    "summary": "the flood takes the low ground and Arnulf is lost",
                    "reviewed": False,
                    "beats": [
                        "Arnulf is swept away by the flood",
                        "the others mourn Arnulf as drowned",
                    ],
                    "turns": [],
                },
            },
        },
    }


_BRIDGE_BEATS = [
    "Arnulf goes back down the bank for a stranded clansman",
    "Arnulf is swept away by the flood",
    "the others mourn Arnulf as drowned",
]
_NO_BRIDGE_BEATS = [
    "Arnulf is swept away by the flood",
    "the others mourn Arnulf as drowned",
]


# ── AC-1: deterministic gate — adapter writes bridge beats, gap clears ────────


@pytest.mark.asyncio
async def test_reoutline_writes_bridge_beats_and_clears_gap(tmp_path, monkeypatch):
    doc = _seam_doc()
    # Precondition: the unbridged seam IS present before re-outline (the bug).
    assert gap_detectors.seam_precondition_gap(doc, "2")["gap_count"] == 1

    monkeypatch.setattr(chapter_ops, "get_app", lambda graph: _StubApp(_BRIDGE_BEATS))

    await doc_ops.reoutline_next_chapter(doc, tmp_path, "1")

    assert doc["chapters"]["cards"]["2"]["beats"] == _BRIDGE_BEATS
    assert gap_detectors.seam_precondition_gap(doc, "2")["gap_count"] == 0


@pytest.mark.asyncio
async def test_negative_control_no_bridge_leaves_gap(tmp_path, monkeypatch):
    """A re-outline returning beats WITHOUT a bridge leaves the gap — proving the
    assertion measures the bridge, not the plumbing (J5 non-vacuity)."""
    doc = _seam_doc()
    monkeypatch.setattr(
        chapter_ops, "get_app", lambda graph: _StubApp(_NO_BRIDGE_BEATS)
    )

    await doc_ops.reoutline_next_chapter(doc, tmp_path, "1")

    assert doc["chapters"]["cards"]["2"]["beats"] == _NO_BRIDGE_BEATS
    assert gap_detectors.seam_precondition_gap(doc, "2")["gap_count"] == 1


# ── AC-2: purity — the pure fn never mutates doc; raises on empty ─────────────


@pytest.mark.asyncio
async def test_reoutline_chapter_beats_is_pure(monkeypatch):
    doc = _seam_doc()
    original = copy.deepcopy(doc)
    monkeypatch.setattr(chapter_ops, "get_app", lambda graph: _StubApp(_BRIDGE_BEATS))

    beats = await chapter_ops.reoutline_chapter_beats(doc, "2")

    assert beats == _BRIDGE_BEATS
    assert doc == original  # pure read, no mutation


@pytest.mark.asyncio
async def test_reoutline_chapter_beats_raises_on_empty(monkeypatch):
    doc = _seam_doc()
    monkeypatch.setattr(chapter_ops, "get_app", lambda graph: _StubApp([]))
    with pytest.raises(ValueError):
        await chapter_ops.reoutline_chapter_beats(doc, "2")


# ── AC-3: frozen title/summary — only beats change ───────────────────────────


@pytest.mark.asyncio
async def test_reoutline_freezes_title_and_summary(tmp_path, monkeypatch):
    doc = _seam_doc()
    title_before = doc["chapters"]["cards"]["2"]["title"]
    summary_before = doc["chapters"]["cards"]["2"]["summary"]
    monkeypatch.setattr(chapter_ops, "get_app", lambda graph: _StubApp(_BRIDGE_BEATS))

    await doc_ops.reoutline_next_chapter(doc, tmp_path, "1")

    assert doc["chapters"]["cards"]["2"]["title"] == title_before
    assert doc["chapters"]["cards"]["2"]["summary"] == summary_before


# ── AC-4: guards — no next chapter / reviewed / played turns => no-op ─────────


@pytest.mark.asyncio
async def test_reoutline_noop_when_no_next_chapter(tmp_path, monkeypatch):
    doc = _seam_doc()
    monkeypatch.setattr(chapter_ops, "get_app", lambda graph: _StubApp(_BRIDGE_BEATS))
    original = copy.deepcopy(doc)
    await doc_ops.reoutline_next_chapter(doc, tmp_path, "2")  # "2" is the last chapter
    assert doc == original


@pytest.mark.asyncio
async def test_reoutline_noop_when_next_reviewed(tmp_path, monkeypatch):
    doc = _seam_doc()
    doc["chapters"]["cards"]["2"]["reviewed"] = True
    monkeypatch.setattr(chapter_ops, "get_app", lambda graph: _StubApp(_BRIDGE_BEATS))
    original = copy.deepcopy(doc)
    await doc_ops.reoutline_next_chapter(doc, tmp_path, "1")
    assert doc == original


@pytest.mark.asyncio
async def test_reoutline_noop_when_next_has_played_turns(tmp_path, monkeypatch):
    doc = _seam_doc()
    doc["chapters"]["cards"]["2"]["turns"] = [{"n": 1}]
    monkeypatch.setattr(chapter_ops, "get_app", lambda graph: _StubApp(_BRIDGE_BEATS))
    original = copy.deepcopy(doc)
    await doc_ops.reoutline_next_chapter(doc, tmp_path, "1")
    assert doc == original
