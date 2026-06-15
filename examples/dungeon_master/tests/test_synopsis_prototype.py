"""Prototype walkthrough tests for DM v2 preplan tree (FR-474 → FR-475).

These are a *visibility* harness, not a governance gate (FR-474 J3/J4): they live
under the example, carry no @pytest.mark.req, and exist so the agent can see the
rendered HTML and persisted document it cannot otherwise inspect. The deliverable
is a keep/kill/reshape decision, not a green CI pipeline.

FR-475 reshapes the preplan from a linear ``synopsis → plot`` chain into a tree:
``synopsis`` (root) gates ``key_scene`` (leaf) and ``characters`` (a roster that
spawns one ``char:<id>`` card per character). Navigation is the breadcrumb.

Run directly:
    pytest examples/dungeon_master/tests/test_synopsis_prototype.py --no-cov
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from examples.dungeon_master.api import session as dm_session
from examples.dungeon_master.api import story_doc
from examples.dungeon_master.api.app import app

SYNOPSIS_TEXT = "Elara the clockmaker finds the city core and rewinds it; she wins."
KEY_SCENE_TEXT = "Elara climbs the seized tower as the gears grind to their last tooth."
ROSTER_TEXT = "Elara\nCoil"


def _mock_execute_prompt(prompt_name, variables=None, **kwargs):
    variables = variables or {}
    draft = variables.get("draft") or ""
    instruction = variables.get("instruction")
    # Book-scope chapters (FR-488) are parse_json dicts; answer before the plain
    # refine early-return. The outline spawns on every synopsis-accept.
    if prompt_name == "chapter_outline":
        return {
            "chapters": [
                {"title": "Chapter 1 — The Water Rises", "summary": "Kara musters."},
                {"title": "Chapter 2 — The Last Ledge", "summary": "Kara corners."},
            ]
        }
    if prompt_name == "chapter":
        prev = variables.get("previous_world_state") or "none"
        return {
            "text": f"Chapter {variables.get('index', '?')} full text.",
            "world_state": f"WS@{variables.get('index', '?')} (prev={prev})",
        }
    if draft.strip():
        return f"[refined: {instruction}] {draft}"
    if prompt_name == "synopsis":
        return SYNOPSIS_TEXT
    if prompt_name == "key_scene":
        return KEY_SCENE_TEXT
    if prompt_name == "character_roster":
        return ROSTER_TEXT
    if prompt_name == "character":
        return f"{variables.get('name', '?')} wants the wind-key."
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


def _generate(client, session_id, tagline="A clockmaker's city is winding down"):
    """First synopsis weave: empty draft + the tagline as the instruction."""
    return client.post(
        "/story/synopsis/weave",
        data={"session_id": session_id, "text": "", "prompt": tagline},
    )


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


# ── 1. Landing: seeded tagline card, no setup form ──────────────────────────


def test_landing_shows_seeded_tagline_and_generate(client):
    resp = client.get("/")
    body = resp.text
    assert resp.status_code == 200
    assert "Synopsis" in body
    assert "/story/synopsis/weave" in body
    assert "/story/synopsis/generate" not in body
    assert 'name="prompt"' in body
    assert 'name="text"' in body


# ── 2. Synopsis weave produces an iterable card ─────────────────────────────


def test_generate_produces_iterable_card(client):
    session_id = _new_session(client)
    resp = _generate(client, session_id)
    body = resp.text
    assert resp.status_code == 200
    assert SYNOPSIS_TEXT in body
    assert 'class="text-block"' in body
    assert "Iterate" in body
    assert "Accept" in body


# ── 3. Edit autosaves ───────────────────────────────────────────────────────


def test_edit_autosaves(client, tmp_path):
    session_id = _new_session(client)
    _generate(client, session_id)
    edited = "Elara fails and the city stops. The end."
    client.post("/story/synopsis/edit", data={"session_id": session_id, "text": edited})
    assert _doc(tmp_path, session_id)["synopsis"]["text"] == edited


# ── 4. Iterate applies the prompt ───────────────────────────────────────────


def test_iterate_applies_prompt(client, tmp_path):
    session_id = _new_session(client)
    _generate(client, session_id)
    resp = client.post(
        "/story/synopsis/weave",
        data={"session_id": session_id, "text": SYNOPSIS_TEXT, "prompt": "make grim"},
    )
    assert f"[refined: make grim] {SYNOPSIS_TEXT}" in resp.text


# ── 5. Accept synopsis: derive roster + land on the auto-drafted first card ──


def test_accept_synopsis_derives_roster_and_lands_on_first_character(client, tmp_path):
    session_id = _new_session(client)
    _generate(client, session_id)
    resp = _accept(client, session_id)
    doc = _doc(tmp_path, session_id)
    # Synopsis frozen; the cast is derived before chapters (FR-491 J1), so the
    # cursor lands on the first character card, auto-drafted (A4 + FR-474).
    assert doc["synopsis"]["reviewed"] is True
    assert doc["stage"] == "char:elara"
    assert doc["characters"]["roster"] == ["elara", "coil"]
    assert doc["characters"]["cards"]["elara"]["name"] == "Elara"
    assert doc["characters"]["cards"]["elara"]["text"] == "Elara wants the wind-key."
    # The chapter outline is NOT derived yet — the cast is still incomplete.
    assert doc.get("chapters", {}).get("order", []) == []
    # The breadcrumb now offers Characters as a branch peer.
    assert "Characters" in resp.text


# ── 6. A character card iterates from the accepted synopsis ─────────────────


def test_character_card_iterates(client, tmp_path):
    session_id = _new_session(client)
    _generate(client, session_id)
    _accept(client, session_id)  # lands on char:elara, auto-drafted
    resp = client.post(
        "/story/synopsis/weave",
        data={
            "session_id": session_id,
            "text": "Elara wants the wind-key.",
            "prompt": "grimmer",
        },
    )
    assert "[refined: grimmer] Elara wants the wind-key." in resp.text
    assert _doc(tmp_path, session_id)["characters"]["cards"]["elara"][
        "text"
    ].startswith("[refined:")


# ── 7. Navigate into a character card; it auto-drafts from synopsis + name ───


def test_nav_into_character_card_autodrafts(client, tmp_path):
    session_id = _new_session(client)
    _generate(client, session_id)
    _accept(client, session_id)  # roster exists
    resp = _nav(client, session_id, "char:coil")
    doc = _doc(tmp_path, session_id)
    assert doc["stage"] == "char:coil"
    # A1–A3: nested write to characters.cards, name injected into the graph.
    assert doc["characters"]["cards"]["coil"]["text"] == "Coil wants the wind-key."
    assert "Coil wants the wind-key." in resp.text


# ── 8. Weave/accept operate on the current character card ───────────────────


def test_character_card_weave_and_accept(client, tmp_path):
    session_id = _new_session(client)
    _generate(client, session_id)
    _accept(client, session_id)
    _nav(client, session_id, "char:elara")  # auto-drafts Elara
    client.post(
        "/story/synopsis/weave",
        data={
            "session_id": session_id,
            "text": "Elara wants the wind-key.",
            "prompt": "give her a debt",
        },
    )
    doc = _doc(tmp_path, session_id)
    assert doc["characters"]["cards"]["elara"]["text"].startswith("[refined: give her")
    # Accept the character; it freezes and lands on the next unreviewed character.
    _accept(client, session_id, text="Elara, settled.")
    doc = _doc(tmp_path, session_id)
    assert doc["characters"]["cards"]["elara"]["reviewed"] is True
    assert doc["characters"]["cards"]["elara"]["text"] == "Elara, settled."
    assert doc["stage"] == "char:coil"


# ── 9. Parent gate: cannot visit a child before the synopsis is reviewed ────


def test_nav_to_child_before_synopsis_reviewed_is_rejected(client, tmp_path):
    session_id = _new_session(client)
    _generate(client, session_id)  # synopsis drafted but NOT accepted
    _nav(client, session_id, "key_scene")
    assert _doc(tmp_path, session_id)["stage"] == "synopsis"


def test_nav_to_unknown_character_is_rejected(client, tmp_path):
    session_id = _new_session(client)
    _generate(client, session_id)
    _accept(client, session_id)  # roster has elara, coil; lands on char:elara
    _nav(client, session_id, "char:ghost")
    assert _doc(tmp_path, session_id)["stage"] == "char:elara"


# ── 10. No plot stage is reachable; the old generate endpoint is gone ───────


def test_no_plot_stage_reachable(client, tmp_path):
    session_id = _new_session(client)
    _generate(client, session_id)
    _accept(client, session_id)
    _nav(client, session_id, "plot")
    assert _doc(tmp_path, session_id)["stage"] == "char:elara"
    assert client.post("/story/synopsis/generate", data={}).status_code == 404
