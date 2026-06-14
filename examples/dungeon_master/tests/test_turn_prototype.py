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

import re
from unittest.mock import patch

import pytest
import yaml
from fastapi.testclient import TestClient

from examples.dungeon_master.api import session as dm_session
from examples.dungeon_master.api import story_doc
from examples.dungeon_master.api.app import app

SYNOPSIS_TEXT = "Kara leads the band against a rival raider as the floodwaters rise."
KEY_SCENE_TEXT = "Kara corners Tarek on the last dry ledge while Naru frees the herd."
ROSTER_TEXT = "Kara\nTarek"
ESTABLISHING_TEXT = (
    "A flooded valley at dusk; the last dry ledge stands slick above the water."
)


def _mock_direction(variables: dict) -> dict:
    """Deterministic director output mirroring the structured turn_direct schema.

    ``opening`` is read from the running-scene marker; ``scene_complete`` flips at
    turn 3; a *phantom* is any title-cased name in the scene that no rostered
    character owns (``Naru`` here — the Vane case), surfaced as a continuity flag
    and deliberately NOT folded into ``steer`` (FR-479 J2).
    """
    scene = variables.get("scene") or ""
    cast = variables.get("cast") or []
    turn_n = variables.get("turn_n")
    n = int(turn_n) if str(turn_n).isdigit() else 0
    opening = "Nothing has happened yet" in scene
    cast_names = {c.get("name") for c in cast}
    titlecased = set(re.findall(r"\b[A-Z][a-z]+\b", scene))
    phantoms = sorted(titlecased - cast_names - {"Nothing", "Only", "Turn"})
    return {
        "phase": "opening" if opening else ("resolved" if n >= 3 else "rising"),
        "establishing": ESTABLISHING_TEXT if opening else "",
        "beats_satisfied": [] if opening else ["Kara corners Tarek"],
        "scene_complete": n >= 3,
        "steer": "",
        "continuity": [f"{p} acts but is not a rostered character" for p in phantoms],
    }


def _mock_execute_prompt(prompt_name, variables=None, **kwargs):
    """Deterministic stand-in for every DM prompt, including the three turn prompts."""
    variables = variables or {}
    draft = variables.get("draft") or ""
    instruction = variables.get("instruction")
    if draft.strip():
        return f"[refined: {instruction}] {draft}"
    if prompt_name == "synopsis":
        return SYNOPSIS_TEXT
    if prompt_name == "key_scene":
        # FR-480: a roster-bound key scene uses EXACTLY the rostered names. When
        # the binding threads the roster through, the scene is built from those
        # names; without it the generator drifts (KEY_SCENE_TEXT names "Naru",
        # a character the roster never sanctioned).
        roster = variables.get("roster") or ""
        names = [n.strip() for n in re.split(r"[\n,]+", roster) if n.strip()]
        if names:
            cast = "\n".join(f"- {n} — drives the scene" for n in names)
            return (
                f"SUMMARY: {names[0]} confronts the others on the last dry ledge.\n"
                f"CHARACTERS:\n{cast}"
            )
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
    if prompt_name == "turn_direct":
        return _mock_direction(variables)
    if prompt_name == "turn_recap":
        cast = variables.get("cast") or []
        turn_n = variables.get("turn_n")
        names = ", ".join(c.get("name", "?") for c in cast)
        tag = f" [{instruction}]" if instruction else ""
        # The render-only recap consumes the director's establishing description
        # on the opening turn (FR-479 J6).
        direction = variables.get("direction") or {}
        establishing = direction.get("establishing") or ""
        est = f" {establishing}" if establishing else ""
        return f"Turn {turn_n} — {names} collide on the ledge.{est}{tag}"
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


# ── 7. Every slow press shows the busy overlay; no dead inline spinner (FR-478) ─


def test_busy_overlay_wires_every_slow_press(client, tmp_path):
    session_id = _new_session(client)
    # The full page shell carries the single #busy overlay, outside #app-body,
    # and the retired inline spinner is gone.
    page = client.get("/").text
    assert 'id="busy"' in page
    assert 'id="app-body"' in page
    assert page.index('id="busy"') < page.index('id="app-body"')
    assert "gen-spinner" not in page
    # Iterate and Accept on the synopsis card point at the overlay.
    assert page.count('hx-indicator="#busy"') >= 2

    # On a turn page, Iterate/Accept and every breadcrumb nav link point at it.
    body = _reach_play(client, tmp_path, session_id).text
    assert "gen-spinner" not in body
    # Every slow control carries the overlay: the 2 card buttons + each nav link
    # (the fast `edit` textarea deliberately does not).
    nav_count = body.count('hx-post="/story/nav"')
    assert nav_count >= 1, "expected clickable breadcrumb nav links on a turn page"
    assert body.count('hx-indicator="#busy"') == nav_count + 2


# ── 8. The turn graph runs a director between the intents map and the recap ──


def test_turn_graph_has_director_between_intents_and_recap():
    with open("examples/dungeon_master/turn.yaml") as fh:
        cfg = yaml.safe_load(fh)
    assert {"intents", "direct", "recap"} <= set(cfg["nodes"])
    # The director is structured; the final node still emits `recap` (FR-479 J3).
    assert cfg["nodes"]["direct"]["state_key"] == "direction"
    assert cfg["nodes"]["recap"]["state_key"] == "recap"
    edges = {(e["from"], e["to"]) for e in cfg["edges"]}
    assert ("intents", "direct") in edges
    assert ("direct", "recap") in edges


# ── 9. The opening turn carries an establishing description (FR-479 J6) ──────


def test_opening_turn_carries_establishing_description(client, tmp_path):
    session_id = _new_session(client)
    resp = _reach_play(client, tmp_path, session_id)  # lands on turn:1
    doc = _doc(tmp_path, session_id)
    direction = doc["turns"][0]["direction"]
    assert direction["phase"] == "opening"
    assert direction["establishing"].strip()
    # The director's establishing description is rendered into the opening recap…
    assert direction["establishing"] in doc["turns"][0]["recap"]["text"]
    # …and is visible on the page.
    assert direction["establishing"] in resp.text


# ── 10. Reaching the END flips scene_complete, which stops plain advance (J5) ─


def test_scene_complete_stops_advance_and_surfaces(client, tmp_path):
    session_id = _new_session(client)
    _reach_play(client, tmp_path, session_id)  # turn:1 drafted
    _accept(client, session_id)  # → turn:2
    resp = _accept(client, session_id)  # → turn:3 (director reports scene_complete)
    doc = _doc(tmp_path, session_id)
    assert doc["stage"] == "turn:3"
    assert doc["turns"][2]["direction"]["scene_complete"] is True
    # The completed state is surfaced on the turn page.
    assert "scene-complete" in resp.text
    # Accepting a completed turn does NOT spawn turn:4 (J5).
    _accept(client, session_id)
    doc2 = _doc(tmp_path, session_id)
    assert doc2["stage"] == "turn:3"
    assert len(doc2["turns"]) == 3


# ── 11. A non-roster name acting raises a continuity flag, surfaced not steered ─


def test_phantom_actor_raises_continuity_flag(client, tmp_path):
    session_id = _new_session(client)
    _reach_play(client, tmp_path, session_id)
    # FR-480 binds the *generator* to the roster, so a phantom can no longer be
    # minted into the scene. The director's detection is now defense in depth:
    # inject a stray non-roster name straight into the frozen scene and prove the
    # director still catches it on the next read.
    doc = _doc(tmp_path, session_id)
    doc["key_scene"]["text"] = KEY_SCENE_TEXT  # names "Naru", absent from roster
    story_doc.write(tmp_path / session_id, doc)
    resp = client.post(
        "/story/synopsis/weave",
        data={"session_id": session_id, "text": "Turn 1 — x", "prompt": "re-read"},
    )
    doc = _doc(tmp_path, session_id)
    direction = doc["turns"][0]["direction"]
    # "Naru" is named in the scene but absent from the roster (the Vane case).
    assert any("Naru" in f for f in direction["continuity"])
    # The flag is surfaced to the DM, and NOT silently applied as a steer (J2).
    assert "Naru" in resp.text
    assert direction["steer"] == ""


# ── 12. The key scene is generated bound to the roster's names (FR-480) ──────


def test_key_scene_binds_to_roster_names(client, tmp_path):
    session_id = _new_session(client)
    client.post(
        "/story/synopsis/weave",
        data={"session_id": session_id, "text": "", "prompt": "a flooded valley"},
    )
    _accept(client, session_id)  # synopsis → roster derived → key_scene drafted
    doc = _doc(tmp_path, session_id)
    assert doc["stage"] == "key_scene"
    cards = doc["characters"]["cards"]
    roster_names = {cards[cid]["name"] for cid in doc["characters"]["roster"]}
    scene = doc["key_scene"]["text"]
    # Every proper name in the generated scene is one the roster sanctioned: the
    # unbound generator's drift name "Naru" cannot appear once the roster is bound.
    scene_names = set(re.findall(r"\b[A-Z][a-z]+\b", scene))
    assert "Naru" not in scene
    assert scene_names <= roster_names
