"""Witness tests for the dungeon-master example (FR-466).

CAP-164 — REQ-YG-429..433.

These exercise the Layer-3 side-effect tools and assert the two graphs compile,
covering the requirements without requiring live LLM calls.
"""

import json

import pytest

from examples.dungeon_master.nodes.story_io import (
    COMMITTING_ACTIONS,
    commit_beat_tool,
    load_story_tool,
    parse_dm_tool,
    prep_turn_tool,
    save_story_tool,
)
from yamlgraph.graph_loader import compile_graph, load_graph_config

PREPLAN = "examples/dungeon_master/preplan.yaml"
TURN_LOOP = "examples/dungeon_master/turn-loop.yaml"


def _story_state(tmp_path):
    return {
        "output_dir": str(tmp_path),
        "synopsis": {"logline": "A city is a machine winding down."},
        "plot": {"acts": [{"name": "Act I"}]},
        # Wrapped LLM outputs (output_schema must be type: object).
        "chapters": {
            "chapters": [
                {"title": "The First Tick", "summary": "Elara hears the gears slow."},
                {"title": "The Last Spring", "summary": "The core is found."},
            ]
        },
        "cast": {
            "cast": [
                {"name": "Elara", "goal": "rewind the city", "voice": "precise"},
                {"name": "Cogsworth", "goal": "keep the secret", "voice": "wry"},
            ]
        },
    }


# ── Phase 1 ────────────────────────────────────────────────────────────────


@pytest.mark.req("REQ-YG-429")
def test_preplan_graph_compiles():
    """Preplan graph loads and compiles from YAML."""
    config = load_graph_config(PREPLAN)
    graph = compile_graph(config)
    assert graph is not None


@pytest.mark.req("REQ-YG-430")
def test_save_story_emits_valid_story_json(tmp_path):
    """save_story writes story.json with synopsis, plot, chapters, cast."""
    result = save_story_tool(_story_state(tmp_path))

    story_path = tmp_path / "story.json"
    assert story_path.exists()
    story = json.loads(story_path.read_text())
    assert set(story) == {"synopsis", "plot", "chapters", "cast"}
    # Wrapped LLM outputs are normalized to plain lists at the boundary.
    assert isinstance(story["chapters"], list) and len(story["chapters"]) == 2
    assert isinstance(story["cast"], list) and len(story["cast"]) == 2
    # State is normalized too, and one outline file per chapter is written.
    assert isinstance(result["chapters"], list)
    assert len(result["chapter_outlines"]) == 2
    for outline in result["chapter_outlines"]:
        assert (tmp_path / outline.split("/")[-1]).exists()


# ── Phase 2 ────────────────────────────────────────────────────────────────


@pytest.mark.req("REQ-YG-431")
def test_prep_turn_derives_chapter_goal_and_history(tmp_path):
    """prep_turn computes the current chapter goal and recent history string."""
    save_story_tool(_story_state(tmp_path))
    story = json.loads((tmp_path / "story.json").read_text())

    out = prep_turn_tool(
        {
            "chapters": story["chapters"],
            "chapter_index": 1,
            "history": ["beat one", "beat two"],
        }
    )
    assert out["chapter_goal"] == "The core is found."
    assert "beat one" in out["recent_history"]


@pytest.mark.req("REQ-YG-432")
def test_load_story_round_trips_cast_as_list(tmp_path):
    """load_story reads story.json and seeds a plain cast list for the map node."""
    save_story_tool(_story_state(tmp_path))
    loaded = load_story_tool({"output_dir": str(tmp_path)})
    assert isinstance(loaded["cast"], list)
    assert [c["name"] for c in loaded["cast"]] == ["Elara", "Cogsworth"]
    assert loaded["turn_number"] == 0


# ── Phase 3 ────────────────────────────────────────────────────────────────


@pytest.mark.req("REQ-YG-433")
def test_turn_loop_graph_compiles():
    """Turn-loop graph loads and compiles from YAML."""
    config = load_graph_config(TURN_LOOP)
    graph = compile_graph(config)
    assert graph is not None


@pytest.mark.req("REQ-YG-433")
@pytest.mark.parametrize(
    ("raw", "action", "payload"),
    [
        ("", "accept", ""),
        ("accept", "accept", ""),
        ("edit: A darker beat.", "edit", "A darker beat."),
        ("nudge: raise the stakes", "nudge", "raise the stakes"),
        ("retry", "retry", ""),
        ("next-chapter", "next-chapter", ""),
        ("end", "end", ""),
        ("just keep going somehow", "accept", ""),  # unknown → accept
    ],
)
def test_parse_dm_grammar(raw, action, payload):
    """DM input parses into the structured action + payload grammar."""
    out = parse_dm_tool({"dm_input": raw})
    assert out["dm_action"] == action
    assert out["dm_payload"] == payload


@pytest.mark.req("REQ-YG-433")
def test_accept_commits_and_advances_turn(tmp_path):
    """Accept writes the beat to file and advances the turn counter."""
    state = _base_turn_state(tmp_path, beat="Elara winds the great spring.")
    out = commit_beat_tool({**state, "dm_action": "accept", "dm_payload": ""})
    assert out["turn_number"] == 1
    assert out["history"][-1] == "Elara winds the great spring."
    assert out["steer"] == ""
    chapter_file = tmp_path / "chapter-00-the-first-tick.md"
    assert "Elara winds the great spring." in chapter_file.read_text()


@pytest.mark.req("REQ-YG-433")
def test_edit_overrides_current_beat(tmp_path):
    """Edit replaces the woven beat with the DM's text before committing."""
    state = _base_turn_state(tmp_path, beat="bland beat")
    out = commit_beat_tool(
        {**state, "dm_action": "edit", "dm_payload": "A thunderous reversal."}
    )
    assert out["beat"] == "A thunderous reversal."
    assert out["history"][-1] == "A thunderous reversal."


@pytest.mark.req("REQ-YG-433")
def test_nudge_sets_steer_for_next_turn(tmp_path):
    """Nudge commits the current beat and steers exactly the next turn."""
    state = _base_turn_state(tmp_path, beat="a quiet beat")
    out = commit_beat_tool(
        {**state, "dm_action": "nudge", "dm_payload": "bring a storm"}
    )
    assert out["steer"] == "bring a storm"
    assert out["turn_number"] == 1  # nudge still commits


@pytest.mark.req("REQ-YG-433")
def test_next_chapter_advances_chapter_index(tmp_path):
    """next-chapter commits and advances the chapter index."""
    state = _base_turn_state(tmp_path, beat="end of chapter")
    out = commit_beat_tool({**state, "dm_action": "next-chapter", "dm_payload": ""})
    assert out["chapter_index"] == 1


@pytest.mark.req("REQ-YG-433")
def test_committing_actions_are_documented():
    """The committing-action set excludes retry/end (non-committing)."""
    assert "retry" not in COMMITTING_ACTIONS
    assert "end" not in COMMITTING_ACTIONS
    assert {"accept", "edit", "nudge", "next-chapter"} <= COMMITTING_ACTIONS


def _base_turn_state(tmp_path, beat):
    return {
        "output_dir": str(tmp_path),
        "draft_beat": beat,
        "chapter_index": 0,
        "turn_number": 0,
        "history": [],
        "chapters": [
            {"title": "The First Tick", "summary": "..."},
            {"title": "The Last Spring", "summary": "..."},
        ],
    }
