"""Prototype tests for DM v2 structured world_state ledger (FR-499 Phase A).

A *visibility* harness, not a governance gate (FR-474 J3): no ``@pytest.mark.req``.
These pin the **typed ledger** that replaces the free-prose ``world_state`` string:
a validated ``{characters[], objects[], facts[]}`` structure, a deterministic
dict→text formatter that renders it back into the prompts, and the forward-carry
plumbing that hands one chapter's structured ledger to the next.

Pure — no LLM, no I/O. The behavioural proof (a regenerated book whose object
breaks are gone) is the live witness, not a unit.

Run directly:
    pytest examples/dungeon_master/tests/test_world_state.py --no-cov
"""

from __future__ import annotations

from pathlib import Path

import yaml

from examples.dungeon_master.api import render, turn_ops, world_state
from yamlgraph.executor_base import format_prompt

PROMPTS = Path(__file__).resolve().parent.parent / "prompts"


def _structured() -> dict:
    return {
        "characters": [
            {
                "name": "Hilde",
                "faction": "Aschenwulf",
                "status": "alive",
                "location": "the stone ledge",
                "inventory": ["flint spear", "river-hide cloak"],
            },
        ],
        "objects": [
            {
                "name": "the wedged slab",
                "holder": "none",
                "location": "the gorge mouth",
            },
        ],
        "facts": ["The dam has failed; the valley is flooding."],
    }


# ── parse_world_state: validate + normalize at the boundary ──────────────────


def test_parse_fills_defaults_for_partial_dict():
    # FR-499A: a partial ledger validates into the full typed shape with empty
    # lists, never a KeyError downstream.
    ws = world_state.parse_world_state({"characters": [{"name": "Hilde"}]})
    assert ws["characters"][0]["name"] == "Hilde"
    assert ws["characters"][0]["faction"] == ""
    assert ws["characters"][0]["inventory"] == []
    assert ws["objects"] == []
    assert ws["facts"] == []


def test_parse_tolerates_non_dict_input():
    # The boundary tolerates the legacy prose string / None / junk by returning an
    # empty typed ledger rather than raising mid-pipeline.
    assert world_state.parse_world_state(None) == {
        "characters": [],
        "objects": [],
        "facts": [],
    }
    assert world_state.parse_world_state("WS1: the dam holds.") == {
        "characters": [],
        "objects": [],
        "facts": [],
    }


def test_parse_roundtrips_full_structure():
    ws = world_state.parse_world_state(_structured())
    assert ws["characters"][0]["inventory"] == ["flint spear", "river-hide cloak"]
    assert ws["objects"][0]["name"] == "the wedged slab"
    assert ws["facts"] == ["The dam has failed; the valley is flooding."]


# ── format_world_state: deterministic dict → prompt text ─────────────────────


def test_format_empty_is_blank():
    # Empty ledger renders to "" so running_scene/chapter_close keep their
    # "no prior world state" opening fallback.
    assert world_state.format_world_state(None) == ""
    assert world_state.format_world_state({}) == ""
    assert (
        world_state.format_world_state({"characters": [], "objects": [], "facts": []})
        == ""
    )


def test_format_renders_characters_objects_and_facts():
    text = world_state.format_world_state(_structured())
    assert "Hilde (Aschenwulf)" in text
    assert "the stone ledge" in text
    assert "flint spear, river-hide cloak" in text
    assert "the wedged slab" in text
    assert "The dam has failed; the valley is flooding." in text


def test_format_is_deterministic():
    a = world_state.format_world_state(_structured())
    b = world_state.format_world_state(_structured())
    assert a == b


# ── forward-carry plumbing: one chapter's ledger feeds the next ──────────────


def test_inherited_world_state_returns_previous_structured_ledger():
    doc = {
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {"world_state": _structured()},
                "2": {"world_state": {"characters": [], "objects": [], "facts": []}},
            },
        }
    }
    inherited = turn_ops.inherited_world_state(doc, "2")
    assert inherited["characters"][0]["name"] == "Hilde"
    assert inherited["characters"][0]["inventory"] == [
        "flint spear",
        "river-hide cloak",
    ]


def test_inherited_world_state_empty_for_first_chapter():
    doc = {"chapters": {"order": ["1"], "cards": {"1": {"world_state": _structured()}}}}
    assert turn_ops.inherited_world_state(doc, "1") == {}


def test_running_scene_formats_structured_ledger_into_prompt_text():
    # The structured ledger reaches the play prompt as deterministic TEXT, never a
    # raw dict repr.
    doc = {
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {"world_state": _structured()},
                "2": {"title": "The Last Ledge", "summary": "They are stranded."},
            },
        }
    }
    scene = turn_ops.running_scene(doc, "2", 1)
    assert "Hilde (Aschenwulf)" in scene
    assert "flint spear" in scene
    assert "{'characters'" not in scene  # no dict repr leaked


# ── render purity: the typed ledger never reaches the manuscript ─────────────


def test_render_never_leaks_structured_world_state():
    doc = {
        "tagline": "t",
        "synopsis": {"text": "s", "reviewed": True},
        "characters": {"reviewed": True, "roster": [], "cards": {}},
        "chapters": {
            "order": ["1"],
            "cards": {
                "1": {
                    "title": "The Water Rises",
                    "text": "Hilde musters the band.",
                    "world_state": _structured(),
                },
            },
        },
    }
    md = render.render_story_markdown(doc)
    assert "the wedged slab" not in md
    assert "flint spear" not in md
    assert "{'characters'" not in md


# ── prompt-render safety: literal JSON braces must not break str.format ───────


def test_chapter_close_prompt_messages_render_without_keyerror():
    # FR-499A regression: format_prompt() runs each message independently; a
    # message with no Jinja markers ({{ }}/{% %}) falls to str.format(), where a
    # literal JSON brace ({"world_state": ...}) is read as a replacement field and
    # raises KeyError('"world_state"'). The chapter_close prompt must describe its
    # JSON shape in PROSE so every message renders cleanly with real variables.
    data = yaml.safe_load((PROMPTS / "chapter_close.yaml").read_text())
    variables = {
        "synopsis": "The thaw drowns the valley.",
        "summary": "The river breaks its banks.",
        "index": "1",
        "previous_world_state": "",
        "recaps": "Turn 1 — Hilde musters the band.",
    }
    for key in ("system", "user"):
        template = str(data.get(key, ""))
        # Must not raise KeyError on literal JSON braces.
        format_prompt(template, variables)
