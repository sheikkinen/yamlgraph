"""Prototype tests for DM v2 book-scope chapters (FR-488).

A *visibility* harness, not a governance gate (FR-474 J3/J4): no
``@pytest.mark.req``. These pin the book-scope planning layer added after the
synopsis — the chapter outline (synopsis split into one-paragraph chapter
summaries) and the per-chapter expansion that carries an explicit ``world_state``
forward from the previous chapter.

The load-bearing test is the **forward-carry seam** (J7), preserved through play
(FR-491): closing played ``chapter:2`` must thread ``chapter:1``'s ``world_state``
into the chapter-close graph variables, and a chapter's play (``running_scene``)
must see the previous chapter's world_state — never its turns. That is a
deterministic-plumbing assertion — the mock supplies the world-state content; the
test proves the wiring delivers it.

Run directly:
    pytest examples/dungeon_master/tests/test_chapters.py --no-cov
"""

from __future__ import annotations

import asyncio
import copy
from unittest.mock import patch

import pytest

from examples.dungeon_master.api import chapter_ops, outline_ops
from examples.dungeon_master.api.gap_detectors import (
    reversal_pack_gap,
    unplayable_beat_gap,
)

SYNOPSIS_TEXT = "Kara leads the band against a rival raider as the floodwaters rise."

# A structured two-chapter outline (J1): {chapters: [{title, summary, beats}]} —
# the shape split_roster cannot carry, so the outline is parsed as JSON, not
# lines. FR-504: every chapter carries a non-empty ``beats`` list (the boundary
# contract enforced by ``_require_beats``).
OUTLINE = {
    "chapters": [
        {
            "title": "Chapter 1 — The Water Rises",
            "summary": "Kara musters the band.",
            "beats": ["Kara musters the band", "the floodwaters rise"],
        },
        {
            "title": "Chapter 2 — The Last Ledge",
            "summary": "Kara corners the raider.",
            "beats": ["Kara reaches the ledge", "Kara corners the raider"],
        },
    ]
}


def _capturing_mock(captured: list[dict]):
    """A mock execute_prompt that records the chapter-close graph's variables (J7)."""

    def _mock(prompt_name, variables=None, **kwargs):
        variables = variables or {}
        if prompt_name == "chapter_outline":
            return OUTLINE
        if prompt_name == "chapter_close":
            captured.append(dict(variables))
            return {
                "world_state": {
                    "characters": [],
                    "objects": [],
                    "facts": [
                        f"WS@{variables.get('index', '?')} "
                        f"(prev={variables.get('previous_world_state') or 'none'})"
                    ],
                },
                "seam_packet": {
                    "resolved_events": ["The ledge is secured."],
                    "open_threads": ["Hilde distrusts Gunnar"],
                    "must_carry_facts": ["Arnulf is believed dead."],
                    "opening_constraints": ["FORBID: Arnulf returns alive"],
                },
            }
        if prompt_name == "final_cut":
            # The per-chapter finish (FR-492): compose the chapter's final text
            # from its played arc. The mock echoes the assembled arc so a test can
            # see the recaps flowed into the composed prose.
            return f"FINAL CUT: {variables.get('arc', '')}"
        raise AssertionError(f"unexpected prompt {prompt_name!r}")

    return _mock


def _patched(mock):
    return patch.multiple(
        "yamlgraph.node_factory.llm_nodes",
        execute_prompt=mock,
    ), patch.multiple(
        "yamlgraph.executor",
        execute_prompt=mock,
    )


def _run(coro):
    return asyncio.run(coro)


def _doc_with_chapters() -> dict:
    """A doc whose synopsis is reviewed and whose chapter outline is already derived."""
    return {
        "synopsis": {"text": SYNOPSIS_TEXT, "reviewed": True},
        "chapters": {
            "reviewed": False,
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "title": "Chapter 1 — The Water Rises",
                    "summary": "Kara musters the band.",
                    "beats": ["Kara musters the band", "the floodwaters rise"],
                    "text": "Chapter 1 full text.",
                    "world_state": {
                        "characters": [],
                        "objects": [],
                        "facts": ["WS1-CARRIED-FORWARD: the band reached the ledge."],
                    },
                    "reviewed": True,
                },
                "2": {
                    "title": "Chapter 2 — The Last Ledge",
                    "summary": "Kara corners the raider.",
                    "beats": ["Kara reaches the ledge", "Kara corners the raider"],
                    "text": "",
                    "world_state": "",
                    "reviewed": False,
                },
            },
        },
    }


# ── J7: the forward-carry seam ───────────────────────────────────────────────


def test_close_chapter_threads_previous_chapter_world_state():
    doc = _doc_with_chapters()
    # Chapter 2 has been played: closing it derives its end-of-chapter world_state
    # from the inherited ledger + the played recaps (FR-491 B).
    doc["chapters"]["cards"]["2"]["turns"] = [
        {"n": 1, "recap": {"text": "Kara corners the raider on the ledge."}}
    ]
    captured: list[dict] = []
    mock = _capturing_mock(captured)
    m1, m2 = _patched(mock)
    with m1, m2:
        result = _run(chapter_ops.close_chapter(doc, "2"))
    assert len(captured) == 1
    # The plumbing delivered chapter 1's world_state to chapter 2's close.
    assert "WS1-CARRIED-FORWARD" in captured[0]["previous_world_state"]
    # And chapter 2 read its own summary, not chapter 1's.
    assert "corners the raider" in captured[0]["summary"]
    # The played recaps are delivered to the close graph for the world_state.
    assert "on the ledge" in captured[0]["recaps"]
    # The chapter's final text is the per-chapter Final Cut composed over its arc
    # (FR-492), so the played recap flows through into the prose.
    assert "on the ledge" in result["text"]
    # The close returns the new world-state ledger the next chapter inherits.
    assert result["world_state"]
    assert result["seam_packet"]["must_carry_facts"] == ["Arnulf is believed dead."]


def test_close_chapter_one_has_no_previous_world_state():
    doc = _doc_with_chapters()
    doc["chapters"]["cards"]["1"]["turns"] = [
        {"n": 1, "recap": {"text": "Kara musters the band at dawn."}}
    ]
    captured: list[dict] = []
    mock = _capturing_mock(captured)
    m1, m2 = _patched(mock)
    with m1, m2:
        _run(chapter_ops.close_chapter(doc, "1"))
    # Chapter 1 is the first: there is no prior world state to carry.
    assert captured[0]["previous_world_state"] == ""


def test_close_chapter_clamps_lifecycle_reappearance_to_planned_return_chapter():
    doc = {
        "synopsis": {"text": SYNOPSIS_TEXT, "reviewed": True},
        "chapters": {
            "order": ["1", "2", "3", "4", "5"],
            "cards": {
                "1": {"summary": "setup", "beats": ["a"]},
                "2": {
                    "summary": "Arnulf presumed dead",
                    "beats": ["a"],
                    "turns": [{"n": 1, "recap": {"text": "The flood takes Arnulf."}}],
                },
                "3": {"summary": "travel", "beats": ["a"]},
                "4": {"summary": "feud", "beats": ["a"]},
                "5": {
                    "title": "Chapter 5 - Arnulf Returns",
                    "summary": "Arnulf returns alive and is verified",
                    "beats": ["Arnulf reappears alive"],
                },
            },
        },
    }

    def _mock(prompt_name, variables=None, **kwargs):
        if prompt_name == "chapter_close":
            return {
                "world_state": {"characters": [], "objects": [], "facts": []},
                "seam_packet": {
                    "character_lifecycle": [
                        {
                            "name": "Arnulf",
                            "existence_state": "missing_presumed_dead",
                            "visibility_mode": "absent",
                            "allowed_reappearance_from_chapter": 3,
                            "source_chapter": 2,
                        }
                    ]
                },
            }
        if prompt_name == "final_cut":
            return "final"
        raise AssertionError(f"unexpected prompt {prompt_name!r}")

    m1, m2 = _patched(_mock)
    with m1, m2:
        result = _run(chapter_ops.close_chapter(doc, "2"))

    lifecycle = result["seam_packet"]["character_lifecycle"]
    assert lifecycle[0]["name"] == "Arnulf"
    assert lifecycle[0]["allowed_reappearance_from_chapter"] == 5


def test_close_chapter_softens_confirmed_dead_with_planned_return(monkeypatch):
    # FR-526 (J6 integration): a close seam that commits an actor confirmed_dead
    # while the plan grants a reappearance is reconciled AT THE CLOSE SEAM to
    # missing_presumed_dead (the coherent record the 10024-BC Ch3 row lacked), and
    # the reconciled state does NOT introduce a spurious memory-precedence conflict.
    from examples.dungeon_master.api import turn_ops

    doc = {
        "synopsis": {"text": SYNOPSIS_TEXT, "reviewed": True},
        # The live synopsis tracks Arnulf as presumed dead (the plan brings him
        # back). Before the coherence fix the seam committed confirmed_dead, which
        # would mismatch this and trip the memory-precedence gate; after the fix the
        # seam reads missing_presumed_dead and aligns -- so the gate stays silent.
        "live_synopsis": {"character_states": {"Arnulf": "missing_presumed_dead"}},
        "chapters": {
            "order": ["1", "2", "3", "4", "5"],
            "cards": {
                "1": {"summary": "setup", "beats": ["a"]},
                "2": {
                    "summary": "Arnulf presumed dead",
                    "beats": ["a"],
                    "turns": [{"n": 1, "recap": {"text": "The flood takes Arnulf."}}],
                },
                "3": {"summary": "travel", "beats": ["a"]},
                "4": {"summary": "feud", "beats": ["a"]},
                "5": {
                    "title": "Chapter 5 - Arnulf Returns",
                    "summary": "Arnulf returns alive and is verified",
                    "beats": ["Arnulf reappears alive"],
                },
            },
        },
    }

    def _mock(prompt_name, variables=None, **kwargs):
        if prompt_name == "chapter_close":
            return {
                "world_state": {"characters": [], "objects": [], "facts": []},
                "seam_packet": {
                    # The close LLM derives confirmed_dead from the loss -- the
                    # incoherent half. The plan (Ch5) grants the return.
                    "character_lifecycle": [
                        {
                            "name": "Arnulf",
                            "existence_state": "confirmed_dead",
                            "visibility_mode": "absent",
                            "allowed_reappearance_from_chapter": 5,
                            "source_chapter": 2,
                        }
                    ]
                },
            }
        if prompt_name == "final_cut":
            return "final"
        raise AssertionError(f"unexpected prompt {prompt_name!r}")

    m1, m2 = _patched(_mock)
    with m1, m2:
        result = _run(chapter_ops.close_chapter(doc, "2"))

    row = result["seam_packet"]["character_lifecycle"][0]
    assert row["name"] == "Arnulf"
    # The incoherent confirmed_dead is softened; the return intent is preserved.
    assert row["existence_state"] == "missing_presumed_dead"
    assert row["allowed_reappearance_from_chapter"] == 5

    # J6: the reconciled seam state, fed to the next chapter's open, raises no
    # spurious memory-precedence conflict (the gate compares seam vs synopsis vs
    # chapter_memory state for equality and raises on mismatch).
    doc["chapters"]["cards"]["2"]["seam_packet"] = result["seam_packet"]
    doc["chapters"]["cards"]["2"]["world_state"] = result["world_state"]
    turn_ops._enforce_memory_precedence_gate(doc, "3", 1)

    doc = _doc_with_chapters()
    doc["chapters"]["cards"]["2"]["turns"] = [
        {"n": 1, "recap": {"text": "Kara corners the raider on the ledge."}}
    ]

    def _mock(prompt_name, variables=None, **kwargs):
        if prompt_name == "chapter_close":
            return {
                "world_state": {"characters": [], "objects": [], "facts": []},
                "seam_packet": {
                    "resolved_events": ["The ledge is secured."],
                    "open_threads": ["Can the truce hold?"],
                    "must_carry_facts": ["Arnulf is believed dead."],
                    "opening_constraints": ["FORBID: Arnulf returns alive"],
                    "character_lifecycle": [
                        {
                            "name": "Arnulf",
                            "existence_state": "missing_presumed_dead",
                            "visibility_mode": "absent",
                            "allowed_reappearance_from_chapter": 5,
                            "source_chapter": 2,
                        }
                    ],
                },
            }
        if prompt_name == "final_cut":
            return "final"
        raise AssertionError(f"unexpected prompt {prompt_name!r}")

    m1, m2 = _patched(_mock)
    with m1, m2:
        result = _run(chapter_ops.close_chapter(doc, "2"))

    memory = result["chapter_memory"]
    assert memory["resolved_events"] == ["The ledge is secured."]
    assert memory["irreversible_facts"] == ["Arnulf is believed dead."]
    assert memory["forbidden_regressions"] == ["FORBID: Arnulf returns alive"]
    assert memory["character_state_deltas"][0]["name"] == "Arnulf"
    assert memory["character_state_deltas"][0]["to_state"] == "missing_presumed_dead"


def test_apply_chapter_close_updates_live_synopsis_and_chapter_memory(tmp_path):
    from examples.dungeon_master.api import doc_ops

    doc = _doc_with_chapters()
    doc["chapters"]["cards"]["2"]["turns"] = [
        {"n": 1, "recap": {"text": "Kara corners the raider on the ledge."}}
    ]

    def _mock(prompt_name, variables=None, **kwargs):
        if prompt_name == "chapter_close":
            return {
                "world_state": {"characters": [], "objects": [], "facts": []},
                "seam_packet": {
                    "resolved_events": ["The ledge is secured."],
                    "open_threads": ["Can the truce hold?"],
                    "must_carry_facts": ["Arnulf is believed dead."],
                    "opening_constraints": ["FORBID: Arnulf returns alive"],
                },
            }
        if prompt_name == "final_cut":
            return "final"
        raise AssertionError(f"unexpected prompt {prompt_name!r}")

    story_dir = tmp_path / "story"
    story_dir.mkdir(parents=True, exist_ok=True)

    m1, m2 = _patched(_mock)
    with m1, m2:
        _run(doc_ops.apply_chapter_close(doc, story_dir, "2"))

    card = doc["chapters"]["cards"]["2"]
    assert card["chapter_memory"]["irreversible_facts"] == ["Arnulf is believed dead."]
    assert doc["live_synopsis"]["last_chapter_id"] == "2"
    assert "After chapter 2:" in doc["live_synopsis"]["summary"]
    assert "Arnulf is believed dead." in doc["live_synopsis"]["immutable_ledger"]


def test_running_scene_turn_one_includes_opening_onepager_contract():
    from examples.dungeon_master.api import turn_ops

    doc = {
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "title": "Chapter 1",
                    "summary": "chapter one",
                    "world_state": {"characters": [], "objects": [], "facts": []},
                    "seam_packet": {
                        "must_carry_facts": ["Arnulf is believed dead."],
                        "opening_constraints": ["FORBID: Arnulf returns alive"],
                        "character_lifecycle": [
                            {
                                "name": "Arnulf",
                                "existence_state": "missing_presumed_dead",
                                "visibility_mode": "absent",
                                "allowed_reappearance_from_chapter": 7,
                                "source_chapter": 1,
                            }
                        ],
                    },
                    "chapter_memory": {
                        "resolved_events": ["The flood took Arnulf."],
                        "irreversible_facts": ["Arnulf is believed dead."],
                        "character_state_deltas": [
                            {
                                "name": "Arnulf",
                                "from_state": "alive",
                                "to_state": "missing_presumed_dead",
                                "evidence": "seam_lifecycle(source_chapter=1)",
                            }
                        ],
                        "open_threads": [],
                        "forbidden_regressions": ["FORBID: Arnulf returns alive"],
                    },
                },
                "2": {
                    "title": "Chapter 2",
                    "summary": "chapter two",
                    "beats": ["b"],
                    "turns": [],
                },
            },
        },
        "live_synopsis": {
            "summary": "After chapter 1: The flood took Arnulf.",
            "immutable_ledger": ["Arnulf is believed dead."],
            "character_states": {"Arnulf": "missing_presumed_dead"},
            "last_chapter_id": "1",
        },
    }

    scene = turn_ops.running_scene(doc, "2", 1)
    assert "OPENING ONEPAGER CONTRACT" in scene
    assert "Must Include:" in scene
    assert "Arnulf is believed dead." in scene
    assert "Must Exclude:" in scene
    assert "FORBID: Arnulf returns alive" in scene


def test_running_scene_turn_one_does_not_reintroduce_synopsis_framing():
    from examples.dungeon_master.api import turn_ops

    doc = {
        "synopsis": {"text": "A broad book outline.", "reviewed": True},
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "title": "Chapter 1",
                    "summary": "chapter one",
                    "world_state": {"characters": [], "objects": [], "facts": []},
                    "seam_packet": {
                        "must_carry_facts": ["Keep the ledge intact."],
                        "opening_constraints": ["FORBID: the river is calm"],
                        "character_lifecycle": [],
                    },
                },
                "2": {
                    "title": "Chapter 2",
                    "summary": "chapter two",
                    "beats": ["b"],
                    "turns": [],
                },
            },
        },
    }

    scene = turn_ops.running_scene(doc, "2", 1)
    lowered = scene.lower()
    assert "synopsis" not in lowered
    assert "live_synopsis" not in lowered
    assert "chapter two" in scene
    assert "Keep the ledge intact." in scene
    assert "FORBID: the river is calm" in scene


def test_invoke_turn_raises_continuity_memory_conflict_on_state_precedence_mismatch():
    from examples.dungeon_master.api import turn_ops

    doc = {
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "title": "Chapter 1",
                    "summary": "chapter one",
                    "seam_packet": {
                        "character_lifecycle": [
                            {
                                "name": "Arnulf",
                                "existence_state": "confirmed_dead",
                                "visibility_mode": "absent",
                                "allowed_reappearance_from_chapter": 7,
                                "source_chapter": 1,
                            }
                        ]
                    },
                    "chapter_memory": {
                        "resolved_events": [],
                        "irreversible_facts": ["Arnulf is alive."],
                        "character_state_deltas": [
                            {
                                "name": "Arnulf",
                                "from_state": "missing_presumed_dead",
                                "to_state": "alive",
                                "evidence": "witness",
                            }
                        ],
                        "open_threads": [],
                        "forbidden_regressions": [],
                    },
                    "world_state": {"characters": [], "objects": [], "facts": []},
                },
                "2": {"title": "Chapter 2", "summary": "chapter two", "beats": ["b"]},
            },
        },
        "live_synopsis": {
            "summary": "After chapter 1.",
            "immutable_ledger": ["Arnulf is alive."],
            "character_states": {"Arnulf": "alive"},
            "last_chapter_id": "1",
        },
    }

    chars = {"roster": [], "cards": {}}
    try:
        _run(turn_ops.invoke_turn(doc, chars, "2", 1, instruction=""))
    except turn_ops.ContinuityMemoryConflictError as exc:
        assert exc.payload["code"] == "CONTINUITY_MEMORY_CONFLICT"
        assert exc.payload["chapter_id"] == "2"
        assert exc.payload["source_pointer"]["chapter_id"] == "1"
        assert exc.payload["source_pointer"]["seam_hash"]
    else:
        raise AssertionError("expected ContinuityMemoryConflictError")


def test_chapter_two_play_sees_chapter_one_world_state_not_its_turns():
    """A chapter's play reads the PREVIOUS chapter's world_state, never its turns.

    The slice-3 load-bearing seam (FR-491): each chapter is played from where the
    last left off. ``running_scene`` for chapter 2 must inherit chapter 1's
    end-of-chapter ``world_state`` (the established START) and read chapter 2's own
    summary — but it must NOT see chapter 1's played turns, which are private to
    chapter 1's loop.
    """
    from examples.dungeon_master.api import turn_ops

    doc = {
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "title": "Chapter 1 — The Water Rises",
                    "summary": "Kara musters the band.",
                    "world_state": {
                        "characters": [],
                        "objects": [],
                        "facts": ["WS1-AFTER-CHAPTER-ONE: the band holds the ledge."],
                    },
                    "turns": [
                        {"n": 1, "recap": {"text": "CH1-TURN-RECAP private to ch 1."}}
                    ],
                },
                "2": {
                    "title": "Chapter 2 — The Last Ledge",
                    "summary": "Kara corners the raider.",
                    "world_state": "",
                    "turns": [],
                },
            },
        },
    }
    scene = turn_ops.running_scene(doc, "2", 1)
    # Chapter 2's play inherits chapter 1's end-of-chapter world_state (the carry)…
    assert "WS1-AFTER-CHAPTER-ONE" in scene
    # …and reads its own summary…
    assert "Kara corners the raider" in scene
    # …but NOT chapter 1's played turns (private to chapter 1's loop).
    assert "CH1-TURN-RECAP" not in scene


# ── J1: the outline is a structured parse, not a split_roster mirror ─────────


def test_outline_chapters_parses_structured_title_summary():
    doc = {"synopsis": {"text": SYNOPSIS_TEXT, "reviewed": True}}
    mock = _capturing_mock([])
    m1, m2 = _patched(mock)
    with m1, m2:
        chapters = _run(outline_ops.outline_chapters(doc))
    assert [c["title"] for c in chapters] == [
        "Chapter 1 — The Water Rises",
        "Chapter 2 — The Last Ledge",
    ]
    assert all(c["summary"] for c in chapters)


# ── FR-525: the outliner split-gate (no chapter packs a removal AND return) ───

# A single chapter that both removes Arnulf (swept away, presumed drowned) AND
# returns him alive — the un-playable reversal the 16-turn cap (FR-501) would
# force-close mid-arc. ``reversal_pack_gap`` fires on this card.
_OVERPACKED_OUTLINE = {
    "chapters": [
        {
            "title": "Chapter 1 — The Flood Takes Arnulf",
            "summary": (
                "Arnulf is swept away by the floodwaters and presumed drowned, "
                "then Arnulf reappears alive on the far bank."
            ),
            "beats": ["Arnulf is swept away", "Arnulf reappears alive"],
        }
    ]
}

# The same reversal split across two chapters — each chapter clean on its own.
_SPLIT_OUTLINE = {
    "chapters": [
        {
            "title": "Chapter 1 — The Flood Takes Arnulf",
            "summary": "Arnulf is swept away by the floodwaters and presumed drowned.",
            "beats": ["Arnulf is swept away", "the band mourns him"],
        },
        {
            "title": "Chapter 2 — The Return",
            "summary": "Arnulf reappears alive on the far bank and rejoins the band.",
            "beats": ["Arnulf reappears alive", "Arnulf rejoins the band"],
        },
    ]
}

# A loss with no return — clean on the first roll (negative control).
_REMOVAL_ONLY_OUTLINE = {
    "chapters": [
        {
            "title": "Chapter 1 — The Flood Takes Arnulf",
            "summary": "Arnulf is swept away by the floodwaters and presumed drowned.",
            "beats": ["Arnulf is swept away", "the band mourns him"],
        }
    ]
}


def _sequence_outline_mock(outlines: list[dict], calls: list[int]):
    """A mock ``execute_prompt`` that yields each outline in turn (FR-525 retry)."""

    seq = iter(outlines)

    def _mock(prompt_name, variables=None, **kwargs):
        if prompt_name == "chapter_outline":
            calls.append(1)
            try:
                return next(seq)
            except StopIteration as exc:  # pragma: no cover - guards over-invocation
                raise AssertionError(
                    "outline graph invoked more than expected"
                ) from exc
        raise AssertionError(f"unexpected prompt {prompt_name!r}")

    return _mock


def test_outline_chapters_retries_until_reversal_pack_clears():
    # A packed first roll is re-rolled; the corrected split is accepted (FR-525).
    doc = {"synopsis": {"text": SYNOPSIS_TEXT, "reviewed": True}}
    calls: list[int] = []
    mock = _sequence_outline_mock([_OVERPACKED_OUTLINE, _SPLIT_OUTLINE], calls)
    m1, m2 = _patched(mock)
    with m1, m2:
        chapters = _run(outline_ops.outline_chapters(doc))
    assert len(calls) == 2  # first packed → re-rolled once
    assert all(reversal_pack_gap(c)["gap_count"] == 0 for c in chapters)
    assert [c["title"] for c in chapters] == [
        "Chapter 1 — The Flood Takes Arnulf",
        "Chapter 2 — The Return",
    ]


def test_outline_chapters_clean_outline_is_not_re_rolled():
    # Non-vacuous negative control: a removal-only outline passes untouched, with
    # no spurious re-invoke (the gate fires only on an actual pack).
    doc = {"synopsis": {"text": SYNOPSIS_TEXT, "reviewed": True}}
    calls: list[int] = []
    mock = _sequence_outline_mock([_REMOVAL_ONLY_OUTLINE], calls)
    m1, m2 = _patched(mock)
    with m1, m2:
        chapters = _run(outline_ops.outline_chapters(doc))
    assert len(calls) == 1  # clean → no retry
    assert all(reversal_pack_gap(c)["gap_count"] == 0 for c in chapters)


def test_outline_chapters_raises_when_pack_persists():
    # Commandment 6: a pack that survives every bounded re-roll RAISES — the
    # outliner never emits a packed outline downstream via silent fallback.
    doc = {"synopsis": {"text": SYNOPSIS_TEXT, "reviewed": True}}
    calls: list[int] = []
    mock = _sequence_outline_mock([_OVERPACKED_OUTLINE] * 3, calls)
    m1, m2 = _patched(mock)
    with m1, m2, pytest.raises(ValueError, match="packs a removal-and-return"):
        _run(outline_ops.outline_chapters(doc))
    assert len(calls) == 3  # bounded: first roll + two corrected re-rolls


# ── FR-528: the outliner unplayable-epilogue gate (no final time-skip beat) ───

# A chapter whose FINAL beat LEADS with a future-time-skip ("By autumn, …") — the
# 10025-BC CH8 shape. The bounded 16-turn scene (FR-501) can never enact a beat that
# resolves only after a season passes, so ``scene_complete = (k == n)`` never fires
# and the chapter rides the cap (the no-progress tail FR-527 mis-treated downstream).
# ``unplayable_beat_gap`` fires on this card.
_EPILOGUE_OUTLINE = {
    "chapters": [
        {
            "title": "Chapter 1 — The Settlement",
            "summary": "The clans reach the high valley and end the feud.",
            "beats": [
                "The clans reel as the living Arnulf shatters the divine verdict",
                "By autumn, Hilde and Gunnar force a settlement that ends the "
                "blood-feud and joins the clans into one camp",
            ],
        }
    ]
}

# The corrected outline: the resolution is re-authored as a present-tense, in-scene
# final beat the chapter can actually play (the epilogue folded into ``summary``).
_IN_SCENE_FIXED_OUTLINE = {
    "chapters": [
        {
            "title": "Chapter 1 — The Settlement",
            "summary": (
                "The clans reach the high valley and end the feud; by autumn the "
                "shared camp holds."
            ),
            "beats": [
                "The clans reel as the living Arnulf shatters the divine verdict",
                "Hilde and Gunnar force the settlement that ends the blood-feud here",
            ],
        }
    ]
}


def test_outline_chapters_retries_until_unplayable_beat_clears():
    # A first roll whose final beat is an unplayable time-skip epilogue is re-rolled;
    # the corrected in-scene resolution is accepted (FR-528).
    doc = {"synopsis": {"text": SYNOPSIS_TEXT, "reviewed": True}}
    calls: list[int] = []
    mock = _sequence_outline_mock([_EPILOGUE_OUTLINE, _IN_SCENE_FIXED_OUTLINE], calls)
    m1, m2 = _patched(mock)
    with m1, m2:
        chapters = _run(outline_ops.outline_chapters(doc))
    assert len(calls) == 2  # first epilogue → re-rolled once
    assert all(unplayable_beat_gap(c)["gap_count"] == 0 for c in chapters)
    assert chapters[0]["beats"][-1].lower().startswith("hilde and gunnar force")


def test_outline_chapters_raises_when_unplayable_beat_persists():
    # Commandment 6: an unplayable final beat that survives every bounded re-roll
    # RAISES — the outliner never emits a cap-riding chapter via silent fallback.
    doc = {"synopsis": {"text": SYNOPSIS_TEXT, "reviewed": True}}
    calls: list[int] = []
    mock = _sequence_outline_mock([_EPILOGUE_OUTLINE] * 3, calls)
    m1, m2 = _patched(mock)
    with m1, m2, pytest.raises(ValueError, match="unplayable time-skip epilogue"):
        _run(outline_ops.outline_chapters(doc))
    assert len(calls) == 3  # bounded: first roll + two corrected re-rolls


# ── purity: chapter_ops must not mutate the doc it reads ──────────────────────


def test_close_chapter_does_not_mutate_doc():
    doc = _doc_with_chapters()
    doc["chapters"]["cards"]["2"]["turns"] = [
        {"n": 1, "recap": {"text": "Kara corners the raider on the ledge."}}
    ]
    before = copy.deepcopy(doc)
    mock = _capturing_mock([])
    m1, m2 = _patched(mock)
    with m1, m2:
        _run(chapter_ops.close_chapter(doc, "2"))
    assert doc == before


# ── J3: chapters are independent of the preplan/play gate ────────────────────


def test_chapters_do_not_affect_preplan_complete():
    from examples.dungeon_master.api import tree

    # A doc with a fully derived chapter set but NO cast: the cast gate must stay
    # closed — chapters are a separate branch (J3).
    doc = {
        "synopsis": {"text": SYNOPSIS_TEXT, "reviewed": True},
        "chapters": {
            "reviewed": True,
            "order": ["1", "2"],
            "cards": {
                "1": {"reviewed": True},
                "2": {"reviewed": True},
            },
        },
    }
    assert tree.cast_complete(doc) is False
    # And a complete cast stays complete regardless of chapter state.
    doc["characters"] = {
        "roster": ["kara"],
        "cards": {"kara": {"reviewed": True}},
    }
    assert tree.cast_complete(doc) is True


def test_chapters_appear_as_breadcrumb_peer_of_characters():
    from examples.dungeon_master.api import tree

    doc = {
        "synopsis": {"text": SYNOPSIS_TEXT, "reviewed": True},
        "chapters": {"order": ["1"], "cards": {"1": {"title": "One"}}},
        "characters": {"roster": ["kara"], "cards": {"kara": {"name": "Kara"}}},
        "stage": "chapters",
    }
    labels = [c["label"] for c in tree.breadcrumb(doc)]
    assert "Chapters" in labels
    # Chapters sits after Synopsis and before Characters (independent branch).
    assert labels.index("Synopsis") < labels.index("Chapters")
    assert labels.index("Chapters") < labels.index("Characters")


# ── J6: the chapter set is FIXED at derivation (idempotent expansion) ─────────


def test_expand_chapters_is_idempotent(tmp_path, monkeypatch):
    from examples.dungeon_master.api import doc_ops
    from examples.dungeon_master.api import session as session_mod

    monkeypatch.setattr(session_mod, "STORY_ROOT", tmp_path)
    session_mod._reset_caches()

    calls = {"outline": 0}

    def _counting_mock(prompt_name, variables=None, **kwargs):
        variables = variables or {}
        if prompt_name == "chapter_outline":
            calls["outline"] += 1
            return OUTLINE
        raise AssertionError(f"unexpected prompt {prompt_name!r}")

    m1, m2 = _patched(_counting_mock)
    doc = {"synopsis": {"text": SYNOPSIS_TEXT, "reviewed": True}}
    story_dir = tmp_path / "ch-idem"
    story_dir.mkdir(parents=True, exist_ok=True)
    with m1, m2:
        _run(doc_ops.expand_chapters(doc, story_dir))
        order_first = list(doc["chapters"]["order"])
        # A second derivation must be a no-op: numeric ids cannot append like
        # slugs, so the set is fixed (J6) and the outline graph is not re-run.
        _run(doc_ops.expand_chapters(doc, story_dir))
    assert calls["outline"] == 1
    assert doc["chapters"]["order"] == order_first == ["1", "2"]


# ── FR-490: the chapter outline needs a face (overview card + navigation) ─────
#
# The outline is the load-bearing view of book scope, yet FR-488 gave it no
# surface (J1). These pin the presentation/navigation seam: the repurposed
# (formerly dead) ``chapters`` stage is a read-only overview the group crumb
# lands on; ``StageView`` carries the outline projection and per-chapter
# ``summary``/``world_state``; member peers are discoverable from the overview.


def _view_doc_with_chapters() -> dict:
    """A reviewed-synopsis doc with a derived two-chapter set (chapter 1 expanded)."""
    return {
        "synopsis": {"text": SYNOPSIS_TEXT, "reviewed": True},
        "chapters": {
            "reviewed": False,
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "title": "Chapter 1 — The Water Rises",
                    "summary": "Kara musters the band.",
                    "text": "Chapter 1 full text.",
                    "world_state": {
                        "characters": [],
                        "objects": [],
                        "facts": ["WS1-CARRIED-FORWARD: the band reached the ledge."],
                    },
                    "reviewed": True,
                },
                "2": {
                    "title": "Chapter 2 — The Last Ledge",
                    "summary": "Kara corners the raider.",
                    "text": "",
                    "world_state": "",
                    "reviewed": False,
                },
            },
        },
    }


# ── J5: StageView carries the outline + per-chapter context ───────────────────


def test_view_populates_summary_and_world_state_for_chapter_card():
    from examples.dungeon_master.api import session as session_mod

    sess = session_mod.DMSession("v490")
    doc = _view_doc_with_chapters()
    doc["stage"] = "chapter:1"
    view = sess._view(doc)
    assert view.kind == "chapter"
    # The card's summary (what this chapter is) and inherited world_state (the
    # J7 forward-carry) are surfaced on the view, above the prose.
    assert view.summary == "Kara musters the band."
    assert "WS1-CARRIED-FORWARD" in view.world_state


def test_view_populates_chapters_list_for_overview():
    from examples.dungeon_master.api import session as session_mod

    sess = session_mod.DMSession("v490")
    doc = _view_doc_with_chapters()
    doc["stage"] = "chapters"
    view = sess._view(doc)
    assert view.kind == "chapters"
    # The overview projects the ordered set as {id, title, summary, reviewed}.
    assert [c["id"] for c in view.chapters] == ["1", "2"]
    assert [c["title"] for c in view.chapters] == [
        "Chapter 1 — The Water Rises",
        "Chapter 2 — The Last Ledge",
    ]
    assert [c["summary"] for c in view.chapters] == [
        "Kara musters the band.",
        "Kara corners the raider.",
    ]
    assert [c["reviewed"] for c in view.chapters] == [True, False]


def test_view_leaves_chapter_fields_empty_for_non_chapter_stage():
    from examples.dungeon_master.api import session as session_mod

    sess = session_mod.DMSession("v490")
    doc = _view_doc_with_chapters()
    doc["stage"] = "synopsis"
    view = sess._view(doc)
    # Additive: every non-chapter stage leaves the new fields at their defaults.
    assert view.summary == ""
    assert view.world_state == ""
    assert view.chapters == []


# ── J4: the overview reads the chapter group dict without mutating it ─────────


def test_view_on_overview_does_not_mutate_chapter_group():
    from examples.dungeon_master.api import session as session_mod

    sess = session_mod.DMSession("v490")
    doc = _view_doc_with_chapters()
    doc["stage"] = "chapters"
    before = copy.deepcopy(doc["chapters"])
    sess._view(doc)
    # ``_entry("chapters")`` aliases the {reviewed, order, cards} group dict; the
    # generic setdefault must be a harmless no-op (J4) — never corrupting it.
    assert doc["chapters"] == before


# ── J6: the group crumb lands on the overview; peers visible from it ──────────


def test_chapters_group_crumb_lands_on_overview():
    from examples.dungeon_master.api import tree

    doc = _view_doc_with_chapters()
    doc["stage"] = "synopsis"
    crumbs = tree.breadcrumb(doc)
    group = next(c for c in crumbs if c["label"] == "Chapters")
    # The group crumb opens the table of contents, not blind into chapter 1.
    assert group["stage"] == "chapters"


def test_chapter_member_peers_visible_from_overview():
    from examples.dungeon_master.api import tree

    doc = _view_doc_with_chapters()
    doc["stage"] = "chapters"
    labels = [c["label"] for c in tree.breadcrumb(doc)]
    # Standing on the overview, every chapter is a discoverable member peer.
    assert "Chapter 1 — The Water Rises" in labels
    assert "Chapter 2 — The Last Ledge" in labels


# ── FR-521 S2: drop a within-chapter exited actor from the running cast ──────
#
# The director benches a roster member who has left the scene this chapter (died,
# swept away) via the structured `cast_exits` field. `_filter_roster_for_lifecycle`
# accumulates those exits across the chapter's prior turns and drops the actor from
# the cast for every later turn — turning detection into enforcement (the witnessed
# fix: advisory text was ignored; only removing the actor from the cast works).


def _chars(roster_with_names: dict[str, str]) -> dict:
    return {
        "roster": list(roster_with_names),
        "cards": {
            cid: {"name": name, "text": "sheet", "reviewed": True}
            for cid, name in roster_with_names.items()
        },
    }


def _doc_chapter_turns_with_directions(directions: list[dict]) -> dict:
    """A single-chapter doc whose chapter ``1`` turns carry the given directions."""
    turns = [
        {"n": i + 1, "recap": {"text": f"turn {i + 1}"}, "direction": d}
        for i, d in enumerate(directions)
    ]
    return {
        "chapters": {
            "order": ["1"],
            "cards": {"1": {"summary": "ch1", "beats": ["a"], "turns": turns}},
        }
    }


def test_roster_filter_drops_actor_the_director_exited_this_chapter():
    from examples.dungeon_master.api import turn_ops

    chars = _chars({"hilde": "Hilde", "arnulf": "Arnulf"})
    doc = _doc_chapter_turns_with_directions([{"cast_exits": ["Arnulf"]}])
    out = turn_ops._filter_roster_for_lifecycle(doc, chars, "1", 2, ["hilde", "arnulf"])
    assert out == ["hilde"]


def test_roster_filter_exit_persists_across_a_later_clean_turn():
    # Accumulation: exit on turn 1, no exit on turn 2 → still dropped on turn 3.
    from examples.dungeon_master.api import turn_ops

    chars = _chars({"hilde": "Hilde", "arnulf": "Arnulf"})
    doc = _doc_chapter_turns_with_directions(
        [{"cast_exits": ["Arnulf"]}, {"cast_exits": []}]
    )
    out = turn_ops._filter_roster_for_lifecycle(doc, chars, "1", 3, ["hilde", "arnulf"])
    assert out == ["hilde"]


def test_roster_filter_no_exits_leaves_roster_unchanged():
    from examples.dungeon_master.api import turn_ops

    chars = _chars({"hilde": "Hilde", "arnulf": "Arnulf"})
    doc = _doc_chapter_turns_with_directions([{"cast_exits": []}])
    out = turn_ops._filter_roster_for_lifecycle(doc, chars, "1", 2, ["hilde", "arnulf"])
    assert out == ["hilde", "arnulf"]


def test_roster_filter_never_empties_the_cast():
    # If every roster member has exited, do not hand the turn an empty cast —
    # keep the unfiltered roster (the chapter's turn cap will close it instead).
    from examples.dungeon_master.api import turn_ops

    chars = _chars({"arnulf": "Arnulf"})
    doc = _doc_chapter_turns_with_directions([{"cast_exits": ["Arnulf"]}])
    out = turn_ops._filter_roster_for_lifecycle(doc, chars, "1", 2, ["arnulf"])
    assert out == ["arnulf"]


def test_roster_filter_exit_match_is_case_insensitive():
    from examples.dungeon_master.api import turn_ops

    chars = _chars({"hilde": "Hilde", "arnulf": "  ARnUlf  "})
    doc = _doc_chapter_turns_with_directions([{"cast_exits": ["arnulf"]}])
    out = turn_ops._filter_roster_for_lifecycle(doc, chars, "1", 2, ["hilde", "arnulf"])
    assert out == ["hilde"]


def test_direction_dict_preserves_cast_exits():
    from examples.dungeon_master.api import turn_ops

    direction = turn_ops._direction_dict({"cast_exits": ["Arnulf"]})
    assert direction["cast_exits"] == ["Arnulf"]
