"""Prototype tests for FR-507 lifecycle turn-1 gate.

These pin deterministic chapter-open lifecycle enforcement before any LLM turn
fanout runs.
"""

from __future__ import annotations

import asyncio

import pytest

from examples.dungeon_master.api import chapter_open, turn_engine, turn_ops


class _UnexpectedGraphCall:
    async def ainvoke(self, payload):  # pragma: no cover - should never be called
        raise AssertionError("turn graph should not run when lifecycle gate fails")


class _GraphCapture:
    def __init__(self) -> None:
        self.payload: dict | None = None

    async def ainvoke(self, payload):
        self.payload = payload
        return {"intents": [], "direction": {}, "recap": "ok"}


def _chars_with_arnulf() -> dict:
    return {
        "roster": ["arnulf"],
        "cards": {
            "arnulf": {
                "name": "Arnulf",
                "text": "sheet",
                "reviewed": True,
            }
        },
    }


def _doc_with_lifecycle_gate() -> dict:
    return {
        "chapters": {
            "order": ["1", "2", "3", "4", "5"],
            "cards": {
                "2": {
                    "seam_packet": {
                        "character_lifecycle": [
                            {
                                "name": "Arnulf",
                                "existence_state": "missing_presumed_dead",
                                "visibility_mode": "absent",
                                "allowed_reappearance_from_chapter": 5,
                                "source_chapter": 2,
                            }
                        ]
                    }
                },
                "3": {
                    "summary": "chapter 3",
                    "beats": ["a", "b"],
                    "turns": [],
                },
            },
        }
    }


def _chars_with_hilde_and_arnulf() -> dict:
    return {
        "roster": ["hilde", "arnulf"],
        "cards": {
            "hilde": {
                "name": "Hilde",
                "text": "h sheet",
                "reviewed": True,
            },
            "arnulf": {
                "name": "Arnulf",
                "text": "a sheet",
                "reviewed": True,
            },
        },
    }


def _doc_with_mixed_cast_lifecycle_gate() -> dict:
    doc = _doc_with_lifecycle_gate()
    doc["chapters"]["cards"]["2"]["seam_packet"]["character_lifecycle"].append(
        {
            "name": "Hilde",
            "existence_state": "alive",
            "visibility_mode": "present",
            "allowed_reappearance_from_chapter": None,
            "source_chapter": 2,
        }
    )
    return doc


def test_invoke_turn_raises_lifecycle_gate_error_before_graph(monkeypatch):
    doc = _doc_with_lifecycle_gate()
    chars = _chars_with_arnulf()
    monkeypatch.setattr(turn_engine, "get_app", lambda name: _UnexpectedGraphCall())

    with pytest.raises(chapter_open.LifecycleGateError) as err:
        asyncio.run(turn_ops.invoke_turn(doc, chars, "3", 1))

    payload = err.value.payload
    assert payload["code"] == "LIFECYCLE_GATE_VIOLATION"
    assert payload["chapter_id"] == "3"
    assert payload["turn_n"] == 1
    assert any(v["type"] == "early_return_violation" for v in payload["violations"])


def test_invoke_turn_filters_invalid_character_from_cast_at_chapter_open(monkeypatch):
    doc = _doc_with_mixed_cast_lifecycle_gate()
    chars = _chars_with_hilde_and_arnulf()
    capture = _GraphCapture()
    monkeypatch.setattr(turn_engine, "get_app", lambda name: capture)

    text = asyncio.run(turn_ops.invoke_turn(doc, chars, "3", 1))

    assert text == "ok"
    assert capture.payload is not None
    cast_names = [c.get("name") for c in (capture.payload.get("cast") or [])]
    assert cast_names == ["Hilde"]


def test_cast_filter_identity_matching_is_case_insensitive() -> None:
    doc = _doc_with_lifecycle_gate()
    chars = {
        "roster": ["arnulf"],
        "cards": {
            "arnulf": {
                "name": "  ARnUlf  ",
                "text": "sheet",
                "reviewed": True,
            }
        },
    }

    with pytest.raises(chapter_open.LifecycleGateError) as err:
        chapter_open.filter_roster_for_lifecycle(doc, chars, "3", 1, ["arnulf"])

    payload = err.value.payload
    assert payload["code"] == "LIFECYCLE_GATE_VIOLATION"
    assert any(v["type"] == "early_return_violation" for v in payload["violations"])
