"""FR-511 tests: one-pass final-cut revise cycle behavior."""

from __future__ import annotations

import asyncio

import pytest

from examples.dungeon_master.api import chapter_ops, turn_ops


class _MockCloseApp:
    async def ainvoke(self, variables):
        return {
            "chapter_close": {
                "world_state": {"characters": [], "objects": [], "facts": []},
                "seam_packet": {"character_lifecycle": []},
            }
        }


def _run(coro):
    return asyncio.run(coro)


def _doc() -> dict:
    return {
        "synopsis": {"text": "synopsis"},
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "summary": "c1",
                    "beats": ["beat one"],
                    "seam_packet": {
                        "character_lifecycle": [
                            {
                                "name": "Alwina",
                                "existence_state": "confirmed_dead",
                                "visibility_mode": "absent",
                                "allowed_reappearance_from_chapter": None,
                                "source_chapter": 1,
                            }
                        ]
                    },
                },
                "2": {
                    "summary": "c2",
                    "beats": ["beat one"],
                    "turns": [
                        {
                            "n": 1,
                            "direction": {"beats_satisfied": ["beat one"]},
                            "recap": {"text": "recap"},
                        }
                    ],
                },
            },
        },
        "characters": {
            "roster": ["hilde", "alwina"],
            "cards": {
                "hilde": {"name": "Hilde", "reviewed": True},
                "alwina": {"name": "Alwina", "reviewed": True},
            },
        },
    }


def test_close_chapter_raises_after_one_revise_attempt_when_still_violating(
    monkeypatch,
):
    calls = []

    async def _fake_final_cut(doc, cid, instruction="", draft=""):
        calls.append((instruction, draft))
        if len(calls) == 1:
            return "Hilde kept watch.\nAlwina came forward with her staff."
        return "Hilde kept watch.\nAlwina demanded judgment."

    monkeypatch.setattr(chapter_ops, "get_app", lambda _name: _MockCloseApp())
    monkeypatch.setattr(turn_ops, "invoke_final_cut", _fake_final_cut)

    with pytest.raises(chapter_ops.FinalCutReviseError):
        _run(chapter_ops.close_chapter(_doc(), "2"))

    assert len(calls) == 2


def test_close_chapter_raises_when_revise_breaks_invariants(monkeypatch):
    calls = []

    async def _fake_final_cut(doc, cid, instruction="", draft=""):
        calls.append((instruction, draft))
        if len(calls) == 1:
            return "Hilde kept watch over the ledge.\nAlwina came forward."
        return "ok"

    monkeypatch.setattr(chapter_ops, "get_app", lambda _name: _MockCloseApp())
    monkeypatch.setattr(turn_ops, "invoke_final_cut", _fake_final_cut)

    with pytest.raises(chapter_ops.FinalCutReviseError):
        _run(chapter_ops.close_chapter(_doc(), "2"))

    assert len(calls) == 2


def test_close_chapter_accepts_revised_text_when_clean_and_invariants_hold(monkeypatch):
    calls = []

    async def _fake_final_cut(doc, cid, instruction="", draft=""):
        calls.append((instruction, draft))
        if len(calls) == 1:
            return "Hilde kept watch over the ledge.\nAlwina came forward."
        return "Hilde kept watch over the ledge.\nThe fallen staff lay still."

    monkeypatch.setattr(chapter_ops, "get_app", lambda _name: _MockCloseApp())
    monkeypatch.setattr(turn_ops, "invoke_final_cut", _fake_final_cut)

    result = _run(chapter_ops.close_chapter(_doc(), "2"))
    assert "Alwina came forward" not in result["text"]
    assert "Hilde kept watch over the ledge." in result["text"]
    assert len(calls) == 2
