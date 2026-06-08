"""Prototype walkthrough tests for DM v2 play loop (FR-477).

A *visibility* harness, not a governance gate (FR-474 J3/J4): these live under the
example, carry no @pytest.mark.req, and exist so the agent can see the rendered
HTML and persisted document. The deliverable is a keep/kill/reshape decision.

FR-477 adds the play loop after the preplan tree (FR-475). Once synopsis, key
scene, and every character card are reviewed, a ``Play`` branch unlocks and spawns
dynamic ``turn:<n>`` stages. Each turn maps a private THINKING/INTENT prompt over
the cast, then consolidates the intents into one "Turn N — …" recap that reuses
the same weave / edit / accept controls as every other stage.

Run directly:
    pytest examples/dungeon_master/tests/test_turn_prototype.py --no-cov
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from examples.dungeon_master.api import session as dm_session
from examples.dungeon_master.api import story_doc
from examples.dungeon_master.api.app import app

SYNOPSIS_TEXT = "Kara leads the band against a rival raider as the floodwaters rise."
KEY_SCENE_TEXT = "Kara corners Tarek on the last dry ledge while Naru frees the herd."
ROSTER_TEXT = "Kara\nTarek"


def _mock_execute_prompt(prompt_name, variables=None, **kwargs):
    """Deterministic stand-in for every DM prompt, including the two turn prompts."""
    variables = variables or {}
    draft = variables.get("draft") or ""
    instruction = variables.get("instruction")
    if draft.strip():
        return f"[refined: {instruction}] {draft}"
    if prompt_name == "synopsis":
        return SYNOPSIS_TEXT
    if prompt_name == "key_scene":
        return KEY_SCENE_TEXT
    if prompt_name == "character_roster":
        return ROSTER_TEXT
    if prompt_name == "character":
        return f"{variables.get('name', '?')} hunts the flood-herd."
    if prompt_name == "character_intent":
        char = variables.get("char") or {}
        name = char.get("name", "?")
        prev = char.get("previous", "")
        # The DM instruction steers only the recap (frozen spec); intents re-roll
        # fresh each pass from the cast + scene + their prior intent.
        return {
            "thinking": f"{name} reads the ledge",
            "intent": f"{name} lunges (after: {prev or 'nothing'})",
        }
    if prompt_name == "turn_recap":
        cast = variables.get("cast") or []
        turn_n = variables.get("turn_n")
        names = ", ".join(c.get("name", "?") for c in cast)
        tag = f" [{instruction}]" if instruction else ""
        return f"Turn {turn_n} — {names} collide on the ledge.{tag}"
    raise AssertionError(f"unexpected prompt {prompt_name!r}")


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(dm_session, "STORY_ROOT", tmp_path)
    dm_session._reset_caches()
    with (
        patch(
            "yamlgraph.node_factory.llm_nodes.execute_prompt",
            side_effect=_mock_execute_prompt,
        ),
        patch(
            "yamlgraph.executor.execute_prompt",
            side_effect=_mock_execute_prompt,
        ),
    ):
        yield TestClient(app)


def _new_session(client) -> str:
    resp = client.get("/")
    assert resp.status_code == 200
    return resp.headers["x-session-id"]


def _accept(client, session_id, text=""):
    return client.post(
        "/story/synopsis/accept",
        data={"session_id": session_id, "text": text},
    )


def _nav(client, session_id, stage):
    return client.post(
        "/story/nav",
        data={"session_id": session_id, "stage": stage},
    )


def _doc(tmp_path, session_id):
    return story_doc.read(tmp_path / session_id)


def _reach_play(client, tmp_path, session_id):
    """Drive a session through the whole preplan so the Play branch unlocks."""
    client.post(
        "/story/synopsis/weave",
        data={"session_id": session_id, "text": "", "prompt": "a flooded valley"},
    )
    _accept(client, session_id)  # synopsis → key_scene (drafted), roster [kara, tarek]
    _accept(client, session_id)  # key_scene → char:kara (drafted)
    _accept(client, session_id, text="Kara sheet")  # kara → char:tarek
    return _accept(client, session_id, text="Tarek sheet")  # tarek → turn:1


# ── 1. Play is gated: no turn stage before the whole preplan is reviewed ─────


def test_play_locked_until_preplan_complete(client, tmp_path):
    session_id = _new_session(client)
    client.post(
        "/story/synopsis/weave",
        data={"session_id": session_id, "text": "", "prompt": "a flooded valley"},
    )
    _accept(client, session_id)  # only synopsis reviewed so far
    # The Play peer is absent and a turn cannot be navigated to.
    resp = _nav(client, session_id, "turn:1")
    doc = _doc(tmp_path, session_id)
    assert doc["stage"] != "turn:1"
    assert "Play" not in resp.text


# ── 2. Completing the preplan auto-drafts Turn 1 (intents + recap) ──────────


def test_completing_preplan_lands_on_drafted_turn_1(client, tmp_path):
    session_id = _new_session(client)
    resp = _reach_play(client, tmp_path, session_id)
    doc = _doc(tmp_path, session_id)
    # Landed on an auto-drafted Turn 1 (J5: never a blank splash).
    assert doc["stage"] == "turn:1"
    turn = doc["turns"][0]
    assert turn["n"] == 1
    # One intent per principal, each with non-empty THINKING + INTENT (J6).
    assert set(turn["intents"]) == {"kara", "tarek"}
    for cid in ("kara", "tarek"):
        assert turn["intents"][cid]["thinking"].strip()
        assert turn["intents"][cid]["intent"].strip()
    # A non-empty recap, not yet accepted, in the recap entry.
    assert turn["recap"]["text"].startswith("Turn 1 —")
    assert turn["recap"]["reviewed"] is False
    # The breadcrumb now offers Play.
    assert "Play" in resp.text


# ── 3. The turn renders two columns: intents aside + recap main ─────────────


def test_turn_renders_two_columns(client, tmp_path):
    session_id = _new_session(client)
    resp = _reach_play(client, tmp_path, session_id)
    body = resp.text
    assert 'class="story-grid"' in body
    assert 'id="story-aside"' in body
    # Each principal appears as an intent card with both labels.
    assert "Kara" in body and "Tarek" in body
    assert body.count('class="intent-card"') == 2
    assert "Thinking" in body and "Intent" in body
    # The recap fills the main editable card with Iterate/Accept.
    assert "Turn 1 —" in body
    assert "Iterate" in body and "Accept" in body


# ── 4. Accepting a turn freezes it and seeds the next, threading history ─────


def test_accept_turn_seeds_next_with_history_and_previous(client, tmp_path):
    session_id = _new_session(client)
    _reach_play(client, tmp_path, session_id)
    # Accept Turn 1 → land on an auto-drafted Turn 2.
    _accept(client, session_id)
    doc = _doc(tmp_path, session_id)
    assert doc["stage"] == "turn:2"
    assert doc["turns"][0]["recap"]["reviewed"] is True
    assert len(doc["turns"]) == 2
    # Turn 2's intents received each character's Turn 1 intent as `previous`.
    t1_kara = doc["turns"][0]["intents"]["kara"]["intent"]
    t2_kara = doc["turns"][1]["intents"]["kara"]["intent"]
    assert "after:" in t2_kara
    assert t1_kara.split(" (after:")[0] in t2_kara


# ── 5. Iterate re-rolls the whole turn (intents + recap together, J2) ───────


def test_iterate_rerolls_intents_and_recap(client, tmp_path):
    session_id = _new_session(client)
    _reach_play(client, tmp_path, session_id)
    resp = client.post(
        "/story/synopsis/weave",
        data={
            "session_id": session_id,
            "text": "Turn 1 — old",
            "prompt": "make it grim",
        },
    )
    doc = _doc(tmp_path, session_id)
    turn = doc["turns"][0]
    # The DM steer lands on the recap, the one authoritative outcome.
    assert "[make it grim]" in turn["recap"]["text"]
    assert "[make it grim]" in resp.text
    # Intents are co-generated in the SAME pass (J2): freshly produced, never a
    # frozen carry-over, so the cards always match the recap they fed.
    assert set(turn["intents"]) == {"kara", "tarek"}
    for cid in ("kara", "tarek"):
        assert turn["intents"][cid]["intent"].strip()
    assert turn["recap"]["reviewed"] is False


# ── 6. Play branch lists each turn as a navigable member ────────────────────


def test_breadcrumb_lists_turn_members(client, tmp_path):
    session_id = _new_session(client)
    _reach_play(client, tmp_path, session_id)
    _accept(client, session_id)  # now on turn:2, turns 1 & 2 exist
    resp = _nav(client, session_id, "turn:1")
    body = resp.text
    assert _doc(tmp_path, session_id)["stage"] == "turn:1"
    assert "Turn 1" in body and "Turn 2" in body
