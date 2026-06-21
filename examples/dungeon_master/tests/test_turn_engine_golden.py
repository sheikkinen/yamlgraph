"""FR-557: golden characterization of ``invoke_turn``'s doc writeback + recap.

Contract B extracts the doc-free engine core of ``invoke_turn`` (graph call + the
beat-FSM + intent/direction normalization) into ``turn_engine.play_turn``, leaving
assembly and gating in the adapter. This is the byte-identical safety net for that
move: it captures the EXACT turn record (intents keyed by char id, the computed
direction ledger) and returned recap ``invoke_turn`` produces for a fixed
cast/scene/stub. It passes against the pre-refactor ``invoke_turn`` (committed
first, J3) and must keep passing once the engine core moves out -- proving the
extraction changed nothing.

Example tests are requirement-exempt (FR-474 J3): no ``@pytest.mark.req``.
"""

from __future__ import annotations

import asyncio

from examples.dungeon_master.api import turn_ops


def _run(coro):
    return asyncio.run(coro)


class _StubGraph:
    """A stub turn graph returning one intent and a director selection.

    The director reports ``phase``/``scene_complete`` GUESSES that the beat-FSM
    must overwrite (k/N truth table, FR-503 J3), and a 1-based ``beats_satisfied``
    the FSM resolves to canonical beat TEXT -- so the golden record exercises the
    full engine core, not just the pass-through fields.
    """

    async def ainvoke(self, payload):
        return {
            "intents": [
                {
                    "thinking": "t1",
                    "intent": "i1",
                    "dialogue": "d1",
                    "expression": "e1",
                }
            ],
            "direction": {
                "phase": "resolved",  # wrong guess -- FSM recomputes to "rising"
                "establishing": "the camp at dusk",
                "beats_satisfied": [1],  # 1-based -> index 0 -> first beat text
                "scene_complete": True,  # wrong guess -- FSM recomputes to False
                "steer": "press the raid",
                "continuity": ["c1"],
                "cast_exits": [],
            },
            "recap": "  Hilde charges the camp.  ",
        }


def _chars() -> dict:
    return {
        "roster": ["hilde"],
        "cards": {
            "hilde": {"name": "Hilde", "text": "origin", "reviewed": True},
        },
    }


def _doc() -> dict:
    return {
        "chapters": {
            "order": ["1"],
            "cards": {
                "1": {
                    "title": "The Water Rises",
                    "summary": "Hilde raids; the flood strands her.",
                    "cast": ["Hilde"],
                    "beats": [
                        "Hilde raids at dawn",
                        "The river breaks its banks",
                        "Arnulf is swept downriver",
                    ],
                    "turns": [],
                }
            },
        },
        "characters": _chars(),
    }


def test_invoke_turn_golden_record_and_recap(monkeypatch):
    """The turn record (intents + computed direction) and recap are byte-stable."""
    doc = _doc()
    monkeypatch.setattr(turn_ops, "get_app", lambda name: _StubGraph())

    recap = _run(turn_ops.invoke_turn(doc, _chars(), "1", 1))

    # Recap: cleaned (stripped) graph output, returned not stored.
    assert recap == "Hilde charges the camp."

    record = doc["chapters"]["cards"]["1"]["turns"][0]
    # Intents keyed by char id, normalized to the four-field bundle.
    assert record["intents"] == {
        "hilde": {
            "thinking": "t1",
            "intent": "i1",
            "dialogue": "d1",
            "expression": "e1",
        }
    }
    # Direction: pass-through fields preserved; beats resolved to TEXT; phase and
    # scene_complete COMPUTED from k=1 / N=3 (the FSM overrides the model guess).
    assert record["direction"] == {
        "phase": "rising",
        "establishing": "the camp at dusk",
        "beats_satisfied": ["Hilde raids at dawn"],
        "scene_complete": False,
        "steer": "press the raid",
        "continuity": ["c1"],
        "cast_exits": [],
        "beats_total": 3,
    }
