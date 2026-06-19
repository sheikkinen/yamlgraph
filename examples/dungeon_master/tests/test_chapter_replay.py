"""FR-522: single-chapter replay witness — driver isolation + actor metrics.

The replay harness re-plays ONE chapter from its inherited start so a continuity
change can be measured as a controlled experiment (one changed variable, same
inherited state). The pure measurement lives in ``witness_metrics`` (deterministic,
no LLM); the impure driver lives in ``chapter_replay`` and is exercised here with a
stubbed ``invoke_turn`` so isolation is proven without a live model (J1/J2/J3/J4).
"""

from __future__ import annotations

import copy
import json

import pytest

from examples.dungeon_master.api import (
    chapter_replay,
    turn_ops,
    turn_state,
    witness_metrics,
)


def _two_chapter_doc() -> dict:
    """A doc with a finished chapter 1 and a chapter 2 to replay."""
    return {
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "title": "Chapter 1",
                    "summary": "the band musters",
                    "reviewed": True,
                    "world_state": {
                        "characters": [{"name": "Hilde", "status": "alive"}],
                        "objects": [],
                        "facts": ["WS1: the band holds the ledge."],
                    },
                    "beats": ["muster"],
                    "turns": [
                        {"n": 1, "recap": {"text": "CH1 turn recap.", "reviewed": True}}
                    ],
                },
                "2": {
                    "title": "Chapter 2",
                    "summary": "the river breaks",
                    "reviewed": True,
                    "world_state": {
                        "characters": [],
                        "objects": [],
                        "facts": ["stale"],
                    },
                    "seam_packet": {"character_lifecycle": []},
                    "beats": ["flee"],
                    "turns": [
                        {
                            "n": 1,
                            "recap": {
                                "text": "old replayed-over recap",
                                "reviewed": True,
                            },
                            "intents": {"arnulf": {"intent": "old", "dialogue": ""}},
                            "direction": {
                                "continuity": ["old flag"],
                                "scene_complete": True,
                            },
                        }
                    ],
                },
            },
        },
        "characters": {
            "reviewed": True,
            "roster": ["hilde", "arnulf"],
            "cards": {
                "hilde": {"name": "Hilde", "reviewed": True, "text": "war-leader"},
                "arnulf": {"name": "Arnulf", "reviewed": True, "text": "brother"},
            },
        },
    }


# ── reset_chapter_for_replay (J1) ────────────────────────────────────────────


def test_reset_chapter_for_replay_wipes_only_target_chapter():
    doc = _two_chapter_doc()
    turn_state.reset_chapter_for_replay(doc, "2")
    card2 = doc["chapters"]["cards"]["2"]
    assert card2["turns"] == []
    assert card2["reviewed"] is False
    assert "world_state" not in card2
    assert "seam_packet" not in card2
    # Chapter 1 (the inherited start) is untouched.
    card1 = doc["chapters"]["cards"]["1"]
    assert card1["turns"] == [
        {"n": 1, "recap": {"text": "CH1 turn recap.", "reviewed": True}}
    ]
    assert card1["world_state"]["facts"] == ["WS1: the band holds the ledge."]


# ── chapter_actor_flag_metrics (J3 pure metric, J4 acting definition) ─────────


def _metric_doc() -> dict:
    return {
        "chapters": {
            "cards": {
                "3": {
                    "turns": [
                        {  # acting, not flagged
                            "n": 1,
                            "intents": {
                                "arnulf": {"intent": "I reach the bank", "dialogue": ""}
                            },
                            "direction": {"continuity": []},
                        },
                        {  # acting AND flagged
                            "n": 2,
                            "intents": {
                                "arnulf": {"intent": "I climb out", "dialogue": ""}
                            },
                            "direction": {
                                "continuity": ["Arnulf acts after being swept away."]
                            },
                        },
                        {  # flagged, but the actor is not acting this turn
                            "n": 3,
                            "intents": {
                                "hilde": {"intent": "I haul the rope", "dialogue": ""}
                            },
                            "direction": {
                                "continuity": [
                                    "Arnulf is re-presented after disappearing."
                                ]
                            },
                        },
                        {  # neither
                            "n": 4,
                            "intents": {"hilde": {"intent": "I rest", "dialogue": ""}},
                            "direction": {"continuity": []},
                        },
                    ]
                }
            }
        }
    }


def test_chapter_actor_flag_metrics_reports_k_over_n_and_both_counts():
    m = witness_metrics.chapter_actor_flag_metrics(_metric_doc(), "3", "Arnulf")
    assert m["total"] == 4
    assert m["flag_turns"] == 2  # turns 2, 3
    assert m["acting_turns"] == 2  # turns 1, 2 (intent non-empty under arnulf key)
    # Per-turn detail carries both signals so the confound can be read off.
    per = {t["n"]: t for t in m["per_turn"]}
    assert per[1]["acting"] is True and per[1]["flagged"] is False
    assert per[2]["acting"] is True and per[2]["flagged"] is True
    assert per[3]["acting"] is False and per[3]["flagged"] is True
    assert per[4]["acting"] is False and per[4]["flagged"] is False


def test_chapter_actor_flag_metrics_actor_match_is_case_insensitive_substring():
    m = witness_metrics.chapter_actor_flag_metrics(_metric_doc(), "3", "arnulf")
    assert m["flag_turns"] == 2


def test_chapter_actor_flag_metrics_absent_actor_is_zero_not_crash():
    m = witness_metrics.chapter_actor_flag_metrics(_metric_doc(), "3", "Gunnar")
    assert m["flag_turns"] == 0
    assert m["acting_turns"] == 0
    assert m["total"] == 4


def test_chapter_actor_flag_metrics_acting_counts_dialogue_only():
    doc = {
        "chapters": {
            "cards": {
                "1": {
                    "turns": [
                        {
                            "n": 1,
                            "intents": {
                                "arnulf": {"intent": "", "dialogue": "I live!"}
                            },
                            "direction": {"continuity": []},
                        }
                    ]
                }
            }
        }
    }
    m = witness_metrics.chapter_actor_flag_metrics(doc, "1", "Arnulf")
    assert m["acting_turns"] == 1


# ── replay_chapter driver (J2 mockable isolation) ────────────────────────────


@pytest.mark.asyncio
async def test_replay_chapter_isolates_prior_chapters(monkeypatch):
    doc = _two_chapter_doc()
    original = copy.deepcopy(doc)

    async def _stub_invoke_turn(d, chars, cid, n, instruction=""):
        rec = turn_state.turn_record(d, cid, n)
        rec["intents"] = {"arnulf": {"intent": f"replayed intent {n}", "dialogue": ""}}
        rec["direction"] = {
            "continuity": ["Arnulf acts after being swept away."],
            "scene_complete": n >= 2,
        }
        return f"replayed recap {n}"

    monkeypatch.setattr(turn_ops, "invoke_turn", _stub_invoke_turn)

    replayed = await chapter_replay.replay_chapter(doc, "2")

    # The driver returns a NEW doc; the caller's doc is never mutated.
    assert doc == original
    # Chapter 1 (the inherited start) is byte-identical in the replayed doc.
    assert replayed["chapters"]["cards"]["1"] == original["chapters"]["cards"]["1"]
    # Chapter 2 was re-played fresh: new recaps, terminated at scene_complete.
    turns2 = replayed["chapters"]["cards"]["2"]["turns"]
    assert [t["n"] for t in turns2] == [1, 2]
    assert turns2[0]["recap"]["text"] == "replayed recap 1"


@pytest.mark.asyncio
async def test_replay_chapter_honors_turn_cap(monkeypatch):
    doc = _two_chapter_doc()

    async def _never_complete(d, chars, cid, n, instruction=""):
        rec = turn_state.turn_record(d, cid, n)
        rec["intents"] = {}
        rec["direction"] = {"continuity": [], "scene_complete": False}
        return f"recap {n}"

    monkeypatch.setattr(turn_ops, "invoke_turn", _never_complete)
    replayed = await chapter_replay.replay_chapter(doc, "2", turn_cap=3)
    assert len(replayed["chapters"]["cards"]["2"]["turns"]) == 3


# ── report + output plumbing (J6 witness-only, AC-5/6) ────────────────────────


def test_render_report_shows_baseline_and_replay_counts():
    base = witness_metrics.chapter_actor_flag_metrics(_metric_doc(), "3", "Arnulf")
    rep = witness_metrics.chapter_actor_flag_metrics(_metric_doc(), "3", "Arnulf")
    text = chapter_replay.render_report("3", "Arnulf", base, rep)
    assert "BASELINE" in text
    assert "Arnulf" in text
    assert "2/4" in text  # flag_turns / total


def test_maybe_write_doc_writes_only_when_path_given(tmp_path):
    doc = {"hello": "world"}
    out = tmp_path / "replay.json"
    assert chapter_replay.maybe_write_doc(doc, str(out)) is True
    assert json.loads(out.read_text(encoding="utf-8")) == doc
    # No path → nothing written, no crash.
    assert chapter_replay.maybe_write_doc(doc, None) is False
    assert chapter_replay.maybe_write_doc(doc, "") is False
