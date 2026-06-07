"""Prototype walkthrough tests for DM v2 story-stage loop (FR-474, Phases 1–2).

These are a *visibility* harness, not a governance gate (FR-474 J3/J4): they live
under the example, carry no @pytest.mark.req, and exist so the agent can see the
rendered HTML and persisted document it cannot otherwise inspect. The deliverable
of FR-474 is a keep/kill/reshape decision, not a green CI pipeline.

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
PLOT_TEXT = (
    "Act One: Elara finds the core. Act Two: she resists. Act Three: she rewinds it."
)


def _mock_execute_prompt(prompt_name, variables=None, **kwargs):
    variables = variables or {}
    if prompt_name in ("synopsis", "plot"):
        draft = variables.get("draft") or ""
        instruction = variables.get("instruction")
        if draft.strip():
            return f"[refined: {instruction}] {draft}"
        return SYNOPSIS_TEXT if prompt_name == "synopsis" else PLOT_TEXT
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
    """Land on the app and return a fresh session id."""
    resp = client.get("/")
    assert resp.status_code == 200
    return resp.headers["x-session-id"]


def _generate(client, session_id, tagline="A clockmaker's city is winding down"):
    """First weave: empty draft + the tagline as the instruction."""
    return client.post(
        "/story/synopsis/weave",
        data={"session_id": session_id, "text": "", "prompt": tagline},
    )


def _doc(tmp_path, session_id):
    return story_doc.read(tmp_path / session_id)


# ── 1. Landing: seeded tagline card, no setup form ──────────────────────────


def test_landing_shows_seeded_tagline_and_generate(client):
    resp = client.get("/")
    body = resp.text
    assert resp.status_code == 200
    assert "Synopsis" in body
    # One screen, one action: an Iterate control that weaves, the seeded prompt
    # box, the empty draft surface — no separate Generate button, no setup form.
    assert "/story/synopsis/weave" in body
    assert "/story/synopsis/generate" not in body
    assert 'name="prompt"' in body
    assert 'name="text"' in body
    assert 'name="chapter_count"' not in body
    assert 'name="cast_size"' not in body


# ── 2. Generate produces a synopsis in the iterable card ────────────────────


def test_generate_produces_iterable_card(client):
    session_id = _new_session(client)
    resp = _generate(client, session_id)
    body = resp.text
    assert resp.status_code == 200
    assert SYNOPSIS_TEXT in body
    assert 'class="text-block"' in body
    assert 'name="prompt"' in body
    assert "Iterate" in body
    assert "Accept" in body


# ── 3. Edit autosaves ───────────────────────────────────────────────────────


def test_edit_autosaves(client, tmp_path):
    session_id = _new_session(client)
    _generate(client, session_id)
    edited = "Elara fails and the city stops. The end."
    client.post(
        "/story/synopsis/edit",
        data={"session_id": session_id, "text": edited},
    )
    assert _doc(tmp_path, session_id)["synopsis"]["text"] == edited


# ── 4. Iterate applies the prompt; empty prompt is a pure save ──────────────


def test_iterate_applies_prompt(client, tmp_path):
    session_id = _new_session(client)
    _generate(client, session_id)
    resp = client.post(
        "/story/synopsis/weave",
        data={
            "session_id": session_id,
            "text": SYNOPSIS_TEXT,
            "prompt": "make it grimmer",
        },
    )
    assert f"[refined: make it grimmer] {SYNOPSIS_TEXT}" in resp.text
    assert _doc(tmp_path, session_id)["synopsis"]["text"].startswith(
        "[refined: make it grimmer]"
    )


def test_iterate_empty_prompt_is_pure_save(client, tmp_path):
    session_id = _new_session(client)
    _generate(client, session_id)
    resp = client.post(
        "/story/synopsis/weave",
        data={"session_id": session_id, "text": SYNOPSIS_TEXT, "prompt": ""},
    )
    assert "[refined:" not in resp.text
    assert _doc(tmp_path, session_id)["synopsis"]["text"] == SYNOPSIS_TEXT


# ── 5. Accept freezes the synopsis and auto-drafts the plot stage ───────────


def test_accept_advances_to_plot_stage(client, tmp_path):
    session_id = _new_session(client)
    _generate(client, session_id)
    resp = client.post(
        "/story/synopsis/accept",
        data={"session_id": session_id},
    )
    doc = _doc(tmp_path, session_id)
    # Synopsis is frozen reviewed, and the cursor has advanced to plot.
    assert doc["synopsis"]["reviewed"] is True
    assert doc["stage"] == "plot"
    # Auto-draft on entry: the plot card lands populated, not blank, so the DM
    # has something to react to immediately (FR-474 Phase 2 continuity).
    assert doc["plot"]["text"] == PLOT_TEXT
    assert doc["plot"]["reviewed"] is False
    # The plot card is now showing: drafted prose, breadcrumb has Plot, and an
    # editable prompt box to iterate further.
    assert "Plot" in resp.text
    assert PLOT_TEXT in resp.text
    assert 'name="prompt"' in resp.text


# ── 6. Phase 2: the auto-drafted plot iterates from the accepted synopsis ────


def test_plot_stage_weaves_from_synopsis(client, tmp_path):
    session_id = _new_session(client)
    _generate(client, session_id)
    # Accept auto-drafts the plot from the accepted synopsis.
    client.post("/story/synopsis/accept", data={"session_id": session_id})
    assert _doc(tmp_path, session_id)["plot"]["text"] == PLOT_TEXT
    # Iterating the drafted plot applies the writer's change.
    resp = client.post(
        "/story/synopsis/weave",
        data={
            "session_id": session_id,
            "text": PLOT_TEXT,
            "prompt": "make it grimmer",
        },
    )
    assert f"[refined: make it grimmer] {PLOT_TEXT}" in resp.text
    doc = _doc(tmp_path, session_id)
    assert doc["plot"]["text"].startswith("[refined: make it grimmer]")
    # The accepted synopsis is preserved untouched alongside the new plot.
    assert doc["synopsis"]["reviewed"] is True
    assert doc["synopsis"]["text"] == SYNOPSIS_TEXT


# ── 7. No outline/beat path is reachable ────────────────────────────────────


def test_no_outline_or_beat_routes(client):
    assert client.get("/story/outline?session_id=x").status_code == 404
    assert client.get("/story/nav?session_id=x&chapter=0").status_code == 404
    # The old two-mode generate endpoint is gone — weave is the only mode.
    assert client.post("/story/synopsis/generate", data={}).status_code == 404
