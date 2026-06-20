"""Condemn the frozen-sheet flat arc with a derived per-chapter overlay (FR-541).

THE PROBLEM (from outputs/dungeon-master/10029-BC review): every turn a character's
intent node reads the SAME immutable origin sheet in chapter 1 and chapter 7. A
character who died and returned, or turned enemy to ally across chapters, still
acts from their origin sheet -- arcs read flat (Ch5 "Arnulf's arc compresses",
Ch6 "Arnulf is passive").

THE FIX: ``character_overlay.derive_overlay`` accrues the committed
``character_state_deltas`` of prior chapters into a CURRENT STATE the intent node
reads alongside (not instead of) the immutable ORIGIN sheet. Deterministic,
last-write-wins, additive (empty until a delta exists). It REUSES the
``lifecycle_resolver`` delta fold rather than re-implementing one (FR-541 J1).

Example tests are requirement-exempt (FR-474 J3): no ``@pytest.mark.req``.
"""

from __future__ import annotations

import asyncio

from examples.dungeon_master.api import turn_ops
from examples.dungeon_master.api.character_overlay import derive_overlay
from examples.dungeon_master.api.lifecycle_resolver import _state_map_from_memory


def _run(coro):
    return asyncio.run(coro)


def _delta(name: str, to_state: str) -> dict:
    return {"name": name, "from_state": None, "to_state": to_state, "evidence": "x"}


def _doc(order: list[str], memories: dict[str, list[dict]]) -> dict:
    """A doc whose chapter cards carry the supplied committed state deltas."""
    cards = {
        cid: {"chapter_memory": {"character_state_deltas": memories.get(cid, [])}}
        for cid in order
    }
    return {"chapters": {"order": order, "cards": cards}}


# ── derive_overlay: deterministic accrual ────────────────────────────────────


def test_no_prior_deltas_yields_empty_overlay() -> None:
    """Chapter 1 (no prior committed state) ⇒ empty overlay (additive)."""
    doc = _doc(["1", "2"], {})
    assert derive_overlay(doc, "1", "Arnulf") == {}


def test_overlay_accrues_last_write_wins_across_prior_chapters() -> None:
    """The current status is the most recent prior to_state; history is ordered."""
    doc = _doc(
        ["1", "2", "3"],
        {
            "1": [_delta("Arnulf", "swept downriver, missing")],
            "2": [_delta("Arnulf", "alive, hauled out far downstream")],
        },
    )
    overlay = derive_overlay(doc, "3", "Arnulf")
    assert overlay["status"] == "alive, hauled out far downstream"
    assert overlay["history"] == [
        "chapter 1: swept downriver, missing",
        "chapter 2: alive, hauled out far downstream",
    ]


def test_overlay_ignores_the_querying_chapter_and_its_successors() -> None:
    """Only chapters BEFORE ``cid`` contribute (the chapter opens FROM the past)."""
    doc = _doc(
        ["1", "2", "3"],
        {
            "1": [_delta("Hilde", "leading the remnant")],
            "2": [_delta("Hilde", "wounded at the ford")],
            "3": [_delta("Hilde", "this-chapter state, must not leak")],
        },
    )
    overlay = derive_overlay(doc, "3", "Hilde")
    assert overlay["status"] == "wounded at the ford"


def test_overlay_reuses_lifecycle_resolver_fold() -> None:
    """FR-541 J1: the overlay status agrees with the existing delta fold, not a copy."""
    memory = {"character_state_deltas": [_delta("Arnulf", "alive, returned")]}
    doc = _doc(["1", "2"], {"1": memory["character_state_deltas"]})
    overlay = derive_overlay(doc, "2", "Arnulf")
    folded = _state_map_from_memory(memory)
    assert overlay["status"] == folded["arnulf"]


# ── invoke_turn integration: the overlay reaches the intent bundle ───────────


class _GraphCapture:
    def __init__(self) -> None:
        self.payload: dict | None = None

    async def ainvoke(self, payload):
        self.payload = payload
        return {"intents": [], "direction": {}, "recap": "ok"}


def _chars() -> dict:
    return {
        "roster": ["arnulf"],
        "cards": {"arnulf": {"name": "Arnulf", "text": "origin", "reviewed": True}},
    }


def _turn_doc(order: list[str], memories: dict[str, list[dict]]) -> dict:
    doc = _doc(order, memories)
    # The chapter under play needs a card to host its turns; give the last one a
    # cast so the cast resolver admits Arnulf.
    doc["chapters"]["cards"][order[-1]].update({"cast": ["Arnulf"], "turns": []})
    doc["characters"] = _chars()
    return doc


def test_invoke_turn_passes_overlay_when_prior_delta_exists(monkeypatch) -> None:
    """A character with a prior committed delta carries a CURRENT STATE overlay."""
    doc = _turn_doc(
        ["1", "2"],
        {"1": [_delta("Arnulf", "alive, returned after the flood")]},
    )
    capture = _GraphCapture()
    monkeypatch.setattr(turn_ops, "get_app", lambda name: capture)

    _run(turn_ops.invoke_turn(doc, _chars(), "2", 1))

    bundle = capture.payload["cast"][0]
    assert bundle["sheet"] == "origin"
    assert bundle["overlay"]["status"] == "alive, returned after the flood"


def test_invoke_turn_chapter_one_overlay_is_empty(monkeypatch) -> None:
    """FR-541 J3: chapter 1 (no prior delta) carries an empty overlay (additive)."""
    doc = _turn_doc(["1"], {})
    capture = _GraphCapture()
    monkeypatch.setattr(turn_ops, "get_app", lambda name: capture)

    _run(turn_ops.invoke_turn(doc, _chars(), "1", 1))

    bundle = capture.payload["cast"][0]
    assert bundle["overlay"] == {}
