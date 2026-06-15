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
from pathlib import Path
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
    # Book-scope chapters (FR-488) are parse_json dicts, so they must be answered
    # before the plain-string refine early-return below — otherwise a chapter
    # revision would come back as a string and break the JSON parse. The outline
    # spawns on every synopsis-accept, so this branch keeps the existing suite
    # green now that synopsis-accept derives chapters as well as the roster.
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
        # FR-480: a roster-bound key scene uses EXACTLY the rostered names. When
        # the binding threads the roster through, the scene is built from those
        # names; without it the generator drifts (KEY_SCENE_TEXT names "Naru",
        # a character the roster never sanctioned).
        roster = variables.get("roster") or ""
        names = [n.strip() for n in re.split(r"[\n,]+", roster) if n.strip()]
        if names:
            cast = "\n".join(f"- {n} — drives the scene" for n in names)
            a, b = (names + names)[:2]
            # FR-482: a parseable BEATS block gives the director a canonical beat
            # vocabulary to bind its free-text `beats_satisfied` phrases onto.
            return (
                f"SUMMARY: {a} confronts the others on the last dry ledge.\n"
                f"CHARACTERS:\n{cast}\n"
                f"BEATS:\n"
                f"- {a} corners {b} on the ledge\n"
                f"- {b} frees the herd\n"
                f"END:\n"
                f"- {a} holds the ledge\n"
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
        # fresh each pass from the cast + scene + their prior intent. FR-486 widens
        # the bundle: the single decisive `intent` stays, plus the outward layer —
        # the spoken `dialogue` and the visible `expression` that projects the
        # private `thinking`.
        return {
            "thinking": f"{name} reads the ledge",
            "intent": f"{name} lunges (after: {prev or 'nothing'})",
            "dialogue": f"{name}: 'Hold the ledge.'",
            "expression": f"{name}'s jaw sets, eyes flicking to the water",
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
    if prompt_name == "final_cut":
        # The Final Cut composes one scene from the whole arc; the mock echoes the
        # assembled arc + climax marker so a test can see what context it received.
        arc = variables.get("arc") or ""
        climax = variables.get("climax") or ""
        return f"FINAL CUT ({climax}):\n{arc}"
    if prompt_name == "final_cut_turns":
        # The turn-structured cut returns one {n, text} segment per played turn
        # (FR-485). The mock reads the turn numbers from the assembled arc and
        # emits one aligned segment each, so the alignment validator sees a 1:1
        # mapping onto the played turns.
        arc = variables.get("arc") or ""
        climax = variables.get("climax") or ""
        ns = [int(m) for m in re.findall(r"^Turn (\d+)", arc, re.M)]
        return {
            "turns": [{"n": n, "text": f"polished turn {n} ({climax})"} for n in ns]
        }
    if prompt_name == "staging":
        # The whole-arc director-staging pass (FR-487): one curtain-up `setting`
        # plus a per-turn `staging` delta keyed by the played turn numbers. The
        # mock reads the turn numbers from the assembled arc, so staging aligns
        # to the played turns exactly like the cut spine.
        arc = variables.get("arc") or ""
        ns = [int(m) for m in re.findall(r"^Turn (\d+)", arc, re.M)]
        return {
            "setting": "A flooded valley at dusk; the last dry ledge above the water.",
            "staging": [{"n": n, "text": f"staging delta {n}"} for n in ns],
        }
    if prompt_name == "walkthrough":
        # The per-turn full-text render (FR-487): one playable passage per turn,
        # composed from the authored layers — the cut spine, the FR-486
        # performance (dialogue/expression/acted intent), and the staging. The
        # mock echoes each layer so a test can prove the render composed, not
        # invented, and that `thinking` never reaches this seam.
        turn = variables.get("turn") or {}
        n = turn.get("n")
        setting = turn.get("setting", "")
        staging = turn.get("staging", "")
        cut_text = turn.get("cut_text", "")
        cast = turn.get("cast") or []
        played = " ".join(
            f'{c["name"]} says "{c["dialogue"]}" — {c["expression"]}; {c["intent"]}.'
            for c in cast
        )
        return (
            f"[setting: {setting}] [staging: {staging}] "
            f"Turn {n}: {cut_text} {played}".strip()
        )
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
    """Drive a session through the whole preplan so the Play branch unlocks.

    FR-491 reorders the preplan to cast-before-chapters: accepting the synopsis
    lands on the first character, and accepting the last character completes the
    cast (deriving the chapter outline) and lands on the Chapters overview. The
    flat turn loop still reads the key scene plan in this slice, so it is drafted
    by navigating to it before opening Play.
    """
    client.post(
        "/story/synopsis/weave",
        data={"session_id": session_id, "text": "", "prompt": "a flooded valley"},
    )
    _accept(client, session_id)  # synopsis → char:kara (roster [kara, tarek] derived)
    _accept(client, session_id, text="Kara sheet")  # kara → char:tarek
    _accept(client, session_id, text="Tarek sheet")  # tarek → chapters (cast complete)
    _nav(client, session_id, "key_scene")  # draft the scene plan the turn loop reads
    return _nav(client, session_id, "turn:1")  # open Play


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
    # Accepting a completed turn does NOT spawn turn:4 (J5); it lands on the
    # terminal Final Cut leaf instead (FR-484).
    _accept(client, session_id)
    doc2 = _doc(tmp_path, session_id)
    assert doc2["stage"] == "final_cut"
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
    _accept(client, session_id)  # synopsis → roster derived → lands on char:kara
    _nav(client, session_id, "key_scene")  # draft the roster-bound key scene
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


# ── FR-481: Director card & arc integrity ───────────────────────────────────


def _phase_execute_prompt(phases):
    """An ``execute_prompt`` mock that drives ``turn_direct.phase`` per turn.

    ``phases[n-1]`` is the phase the director "returns" for turn ``n``; every
    other prompt delegates to the default deterministic mock. Lets a test force a
    phase regression and prove the clamp (FR-481 B2).
    """

    def _inner(prompt_name, variables=None, **kwargs):
        variables = variables or {}
        draft = variables.get("draft") or ""
        if prompt_name == "turn_direct" and not draft.strip():
            turn_n = variables.get("turn_n")
            n = int(turn_n) if str(turn_n).isdigit() else 1
            phase = phases[n - 1] if 1 <= n <= len(phases) else "rising"
            return {
                "phase": phase,
                "establishing": ESTABLISHING_TEXT if phase == "opening" else "",
                "beats_satisfied": [] if phase == "opening" else ["Kara corners Tarek"],
                "scene_complete": False,
                "steer": "",
                "continuity": [],
            }
        return _mock_execute_prompt(prompt_name, variables, **kwargs)

    return _inner


# ── 13. The director's judgement is always visible as a card on a turn (A) ───


def test_director_card_always_visible_on_turn(client, tmp_path):
    session_id = _new_session(client)
    _reach_play(client, tmp_path, session_id)  # turn:1 (opening)
    # The opening turn already shows the Director card with its phase badge.
    resp1 = _nav(client, session_id, "turn:1")
    assert "director-card" in resp1.text
    assert "director-phase-opening" in resp1.text
    # Advancing to a rising turn surfaces the phase badge and the satisfied beat.
    resp2 = _accept(client, session_id)  # → turn:2 (rising, one beat)
    body = resp2.text
    assert "director-card" in body
    assert "director-phase-rising" in body
    assert "Kara corners Tarek" in body


# ── 14. Phase never runs backwards — a regress is clamped up (B2) ───────────


def test_phase_is_clamped_monotonic(client, tmp_path):
    session_id = _new_session(client)
    seq = ["opening", "climax", "rising"]  # turn 3 regresses; must be clamped
    with (
        patch(
            "yamlgraph.node_factory.llm_nodes.execute_prompt",
            side_effect=_phase_execute_prompt(seq),
        ),
        patch(
            "yamlgraph.executor.execute_prompt",
            side_effect=_phase_execute_prompt(seq),
        ),
    ):
        _reach_play(client, tmp_path, session_id)  # turn 1: opening
        _accept(client, session_id)  # turn 2: climax
        _accept(client, session_id)  # turn 3: model "rising" → clamped to climax
        doc = _doc(tmp_path, session_id)
    phases = [t["direction"]["phase"] for t in doc["turns"]]
    assert phases == ["opening", "climax", "climax"]


def test_clamp_phase_floors_at_prior_but_allows_advance():
    from examples.dungeon_master.api import turn_ops

    regressed = {"phase": "rising"}
    turn_ops._clamp_phase(regressed, {"phase": "climax"})
    assert regressed["phase"] == "climax"  # floored up

    advanced = {"phase": "resolved"}
    turn_ops._clamp_phase(advanced, {"phase": "climax"})
    assert advanced["phase"] == "resolved"  # forward advance untouched

    opening = {"phase": "opening"}
    turn_ops._clamp_phase(opening, {})  # no prior turn
    assert opening["phase"] == "opening"


# ── FR-482: cumulative beats_satisfied via canonical BEATS matching ──────────


def _beats_execute_prompt(beats_by_turn):
    """An ``execute_prompt`` mock driving ``turn_direct.beats_satisfied`` per turn.

    ``beats_by_turn[n-1]`` is the list of free-text beat phrases the director
    "returns" for turn ``n``; the mock binds them onto the canonical scene BEATS
    downstream. Every other prompt delegates to the default deterministic mock.
    """

    def _inner(prompt_name, variables=None, **kwargs):
        variables = variables or {}
        draft = variables.get("draft") or ""
        if prompt_name == "turn_direct" and not draft.strip():
            turn_n = variables.get("turn_n")
            n = int(turn_n) if str(turn_n).isdigit() else 1
            phrases = beats_by_turn[n - 1] if 1 <= n <= len(beats_by_turn) else []
            return {
                "phase": "rising",
                "establishing": "",
                "beats_satisfied": list(phrases),
                "scene_complete": False,
                "steer": "",
                "continuity": [],
            }
        return _mock_execute_prompt(prompt_name, variables, **kwargs)

    return _inner


def _canonical_beats(tmp_path, session_id):
    from examples.dungeon_master.api import turn_ops

    scene = _doc(tmp_path, session_id)["key_scene"]["text"]
    return turn_ops.parse_beats(scene)


# ── 15. beats_satisfied is cumulative and bound to the canonical scene BEATS ──


def test_beats_satisfied_is_cumulative_and_canonical(client, tmp_path):
    session_id = _new_session(client)
    # Turn 1 satisfies beat 0; turn 2 reports only beat 1 (incremental), yet the
    # recorded set must be the cumulative union, expressed in canonical terms.
    seq = [["Kara corners Tarek on the ledge"], ["Tarek frees the herd"]]
    with (
        patch(
            "yamlgraph.node_factory.llm_nodes.execute_prompt",
            side_effect=_beats_execute_prompt(seq),
        ),
        patch(
            "yamlgraph.executor.execute_prompt",
            side_effect=_beats_execute_prompt(seq),
        ),
    ):
        _reach_play(client, tmp_path, session_id)  # turn 1
        _accept(client, session_id)  # → turn 2
        doc = _doc(tmp_path, session_id)
        canonical = set(_canonical_beats(tmp_path, session_id))
    t1 = set(doc["turns"][0]["direction"]["beats_satisfied"])
    t2 = set(doc["turns"][1]["direction"]["beats_satisfied"])
    # Cumulative: turn 2 ⊇ turn 1, and the new beat was added.
    assert t1 <= t2
    assert len(t2) == len(t1) + 1
    # Every recorded beat is one of the canonical scene BEATS (no paraphrase leak).
    assert t2 <= canonical
    # The card carries a k / N count once the field is canonical.
    assert doc["turns"][1]["direction"]["beats_total"] == len(canonical)


# ── 16. Two paraphrases of one beat count once, not twice ───────────────────


def test_paraphrases_of_one_beat_dedupe_to_one(client, tmp_path):
    session_id = _new_session(client)
    # Both phrases are wordings of the SAME canonical beat ("… corners … on the
    # ledge"); the satisfied set must grow by exactly one, not two.
    seq = [["Kara corners Tarek on the ledge", "Kara corners Tarek on the dry ledge"]]
    with (
        patch(
            "yamlgraph.node_factory.llm_nodes.execute_prompt",
            side_effect=_beats_execute_prompt(seq),
        ),
        patch(
            "yamlgraph.executor.execute_prompt",
            side_effect=_beats_execute_prompt(seq),
        ),
    ):
        _reach_play(client, tmp_path, session_id)  # turn 1
        doc = _doc(tmp_path, session_id)
    beats = doc["turns"][0]["direction"]["beats_satisfied"]
    assert len(beats) == 1


# ── 17. The Director card shows the k / N beat count (FR-481 A × FR-482) ─────


def test_director_card_shows_beat_count(client, tmp_path):
    session_id = _new_session(client)
    seq = [["Kara corners Tarek on the ledge"]]
    with (
        patch(
            "yamlgraph.node_factory.llm_nodes.execute_prompt",
            side_effect=_beats_execute_prompt(seq),
        ),
        patch(
            "yamlgraph.executor.execute_prompt",
            side_effect=_beats_execute_prompt(seq),
        ),
    ):
        resp = _reach_play(client, tmp_path, session_id)  # turn 1, 1 of 2 beats
    # 1 satisfied of 2 canonical beats → the card renders "1 / 2".
    assert "1 / 2" in resp.text


# ── 18. parse_beats reads the BEATS bullets between BEATS: and the next label ─


def test_parse_beats_extracts_bullets_between_labels():
    from examples.dungeon_master.api import turn_ops

    scene = (
        "SUMMARY: a turn.\nINT/EXT: EXT\nLOCATION: a ledge\n"
        "BEATS:\n- first beat\n- second beat\nEND:\n- the result\n"
    )
    assert turn_ops.parse_beats(scene) == ["first beat", "second beat"]
    # A card with no BEATS block yields no canonical vocabulary.
    assert turn_ops.parse_beats("SUMMARY: nothing structured here") == []


def test_match_beat_drops_phrase_that_clears_nothing():
    from examples.dungeon_master.api import turn_ops

    canonical = ["Kara corners Tarek on the ledge", "Tarek frees the herd"]
    # A clear paraphrase resolves to its beat…
    assert turn_ops._match_beat("Kara corners Tarek on the dry ledge", canonical) == 0
    # …but an unrelated phrase is dropped, never invented (Commandment 6).
    assert turn_ops._match_beat("the weather turned cold overnight", canonical) is None


# ── FR-483: scene-pivotal non-roster actors (casting + continuity) ───────────


def _continuity_execute_prompt(flags):
    """An ``execute_prompt`` mock driving ``turn_direct.continuity`` for a turn.

    Returns ``flags`` verbatim as the director's continuity list so a test can
    prove the code-side filter (FR-483 B) suppresses a scene-declared actor while
    keeping a no-provenance phantom. Every other prompt delegates to the default.
    """

    def _inner(prompt_name, variables=None, **kwargs):
        variables = variables or {}
        draft = variables.get("draft") or ""
        if prompt_name == "turn_direct" and not draft.strip():
            return {
                "phase": "rising",
                "establishing": "",
                "beats_satisfied": [],
                "scene_complete": False,
                "steer": "",
                "continuity": list(flags),
            }
        return _mock_execute_prompt(prompt_name, variables, **kwargs)

    return _inner


# ── 19. The key-scene prompt permits a pivotal non-roster actor (A) ──────────


def test_key_scene_prompt_permits_non_roster_actor():
    import pathlib

    from jinja2 import Template

    prompt_path = pathlib.Path("examples/dungeon_master/prompts/key_scene.yaml")
    content = yaml.safe_load(prompt_path.read_text())
    system = content["system"]
    # The scoped permission is gated under {% if roster %}: present once a roster
    # is bound, absent when it is not (so the lone-pass path is unchanged).
    bound = Template(system).render(roster="Kara\nTarek")
    unbound = Template(system).render(roster="")
    assert "pivotal non-roster actor" in bound
    assert "pivotal non-roster actor" not in unbound


# ── 20. A scene-declared non-roster actor is not a continuity breach (B) ─────


def test_scene_declared_actor_not_flagged_but_phantom_kept(client, tmp_path):
    session_id = _new_session(client)
    _reach_play(client, tmp_path, session_id)  # turn:1, roster {kara, tarek}
    # Freeze a scene that CASTS a non-roster actor (Krog) in its CHARACTERS block.
    doc = _doc(tmp_path, session_id)
    doc["key_scene"]["text"] = (
        "SUMMARY: Kara corners Tarek as the cave bear Krog attacks.\n"
        "CHARACTERS:\n"
        "- Kara — hunter\n"
        "- Tarek — rival hunter\n"
        "- Krog — a cave bear that kills Tarek\n"
        "BEATS:\n- Kara corners Tarek on the ledge\nEND:\n- Kara holds the ledge\n"
    )
    story_doc.write(tmp_path / session_id, doc)
    # The director flags BOTH the scene-cast actor and a no-provenance phantom.
    flags = ["Krog mauls Tarek at the turn", "Zalor strikes from nowhere"]
    with (
        patch(
            "yamlgraph.node_factory.llm_nodes.execute_prompt",
            side_effect=_continuity_execute_prompt(flags),
        ),
        patch(
            "yamlgraph.executor.execute_prompt",
            side_effect=_continuity_execute_prompt(flags),
        ),
    ):
        client.post(
            "/story/synopsis/weave",
            data={"session_id": session_id, "text": "Turn 1 — x", "prompt": "re-read"},
        )
    continuity = _doc(tmp_path, session_id)["turns"][0]["direction"]["continuity"]
    # Krog is declared in the scene's CHARACTERS — acting at the turn is expected.
    assert not any("Krog" in f for f in continuity)
    # Zalor is in NEITHER roster nor scene — the breach flag is KEPT (narrow, not
    # silence): the filter must not swallow a genuinely-invented name.
    assert any("Zalor" in f for f in continuity)


# ── 21. parse_scene_characters reads the CHARACTERS bullets' names ──────────


def test_parse_scene_characters_reads_names_before_the_dash():
    from examples.dungeon_master.api import turn_ops

    scene = (
        "SUMMARY: a turn.\nCHARACTERS:\n- Tarka — hunter tracking Krog\n"
        "- Krog — a cave bear\nSTART:\n- they stand on the ledge\n"
    )
    assert turn_ops._parse_scene_characters(scene) == ["Tarka", "Krog"]
    # A card with no CHARACTERS block declares no cast.
    assert turn_ops._parse_scene_characters("SUMMARY: nothing structured") == []


def test_filter_continuity_drops_scene_actor_keeps_phantom():
    from examples.dungeon_master.api import turn_ops

    scene = "CHARACTERS:\n- Tarka — hunter\n- Krog — a cave bear\nBEATS:\n- a beat\n"
    direction = {"continuity": ["Krog kills Vane at the turn", "Zalor from nowhere"]}
    turn_ops._filter_continuity(direction, ["Tarka", "Vane"], scene)
    # Krog is scene-declared but non-roster → its flag is suppressed.
    assert not any("Krog" in f for f in direction["continuity"])
    # Zalor is in neither roster nor scene → kept (filter narrows, not silences).
    assert any("Zalor" in f for f in direction["continuity"])

    # No CHARACTERS block → no declared actor → nothing suppressed (the Vane case
    # in prose, FR-479 test 11, stays a real breach).
    prose = {"continuity": ["Naru frees the herd"]}
    turn_ops._filter_continuity(
        prose, ["Kara", "Tarek"], "Kara corners Tarek while Naru frees the herd."
    )
    assert prose["continuity"] == ["Naru frees the herd"]


# ── FR-484: post-play Final Cut leaf (de-repeat + elaborate the whole arc) ───


def _reach_scene_complete(client, tmp_path, session_id):
    """Drive a session through play until the director reports ``scene_complete``.

    The default mock flips ``scene_complete`` at turn 3, so the session lands on an
    auto-drafted turn:3 whose direction completes the scene — the point the Final
    Cut leaf unlocks (FR-484).
    """
    _reach_play(client, tmp_path, session_id)  # turn:1
    _accept(client, session_id)  # → turn:2
    return _accept(client, session_id)  # → turn:3 (scene_complete)


# ── 22. final_cut_context assembles the WHOLE arc, beats, and a climax marker ─


def test_final_cut_context_consumes_whole_arc_and_marks_climax():
    from examples.dungeon_master.api import turn_ops

    doc = {
        "key_scene": {
            "text": (
                "SUMMARY: Kara corners Tarek.\n"
                "BEATS:\n- Kara corners Tarek on the ledge\n- Tarek yields the claim\n"
                "END:\n- Kara holds the ledge\n"
            )
        },
        "turns": [
            {
                "n": 1,
                "recap": {"text": "FIRSTFACT the floodwaters rise."},
                "direction": {"phase": "opening"},
            },
            {
                "n": 2,
                "recap": {"text": "they grapple on the ledge."},
                "direction": {"phase": "climax"},
            },
            {
                "n": 3,
                "recap": {"text": "LASTFACT Tarek yields and Kara holds."},
                "direction": {"phase": "resolved", "scene_complete": True},
            },
        ],
    }
    ctx = turn_ops.final_cut_context(doc)
    # The whole arc is present — a fact from the first turn AND from the last (not
    # the 3-turn window the live recap writer sees).
    assert "FIRSTFACT" in ctx["arc"]
    assert "LASTFACT" in ctx["arc"]
    # The canonical BEATS travel with the context so the pass knows what matters.
    assert "Kara corners Tarek on the ledge" in ctx["beats"]
    assert "Tarek yields the claim" in ctx["beats"]
    # The climax marker is derived (turn 2 first reached phase "climax").
    assert ctx["climax"] == "Turn 2"
    assert "Turn 2" in ctx["arc"]


# ── 23. climax_turn derives from the phase sequence, with a defined fallback ──


def test_climax_turn_uses_phase_then_scene_complete_fallback():
    from examples.dungeon_master.api import turn_ops

    # Primary: the first turn whose phase reaches "climax".
    by_phase = {
        "turns": [
            {"n": 1, "direction": {"phase": "opening"}},
            {"n": 2, "direction": {"phase": "rising"}},
            {"n": 3, "direction": {"phase": "climax"}},
        ]
    }
    assert turn_ops.climax_turn(by_phase) == 3

    # Fallback: no climax phase recorded → the scene_complete turn.
    by_complete = {
        "turns": [
            {"n": 1, "direction": {"phase": "rising"}},
            {"n": 2, "direction": {"phase": "rising", "scene_complete": True}},
        ]
    }
    assert turn_ops.climax_turn(by_complete) == 2

    # Last resort: neither marker → the final turn.
    neither = {"turns": [{"n": 1, "direction": {"phase": "rising"}}]}
    assert turn_ops.climax_turn(neither) == 1


# ── 24. Final Cut is locked until scene_complete, then navigable (J5 unlock) ──


def test_final_cut_locked_until_scene_complete(client, tmp_path):
    session_id = _new_session(client)
    _reach_play(client, tmp_path, session_id)  # turn:1, scene NOT complete
    # Locked: not in the breadcrumb and a nav to it is refused.
    resp = _nav(client, session_id, "final_cut")
    assert _doc(tmp_path, session_id)["stage"] != "final_cut"
    assert "Final Cut" not in resp.text

    # Play on to completion → the Final Cut peer appears and is reachable.
    resp2 = _reach_scene_complete(client, tmp_path, session_id)
    assert "Final Cut" in resp2.text
    resp3 = _nav(client, session_id, "final_cut")
    assert _doc(tmp_path, session_id)["stage"] == "final_cut"
    assert resp3.status_code == 200


# ── 25. The Final Cut is additive: the played turns are left untouched ───────


def test_final_cut_is_additive_turns_untouched(client, tmp_path):
    session_id = _new_session(client)
    _reach_scene_complete(client, tmp_path, session_id)  # turn:3, scene complete
    before = _doc(tmp_path, session_id)
    recaps_before = [t["recap"]["text"] for t in before["turns"]]
    reviewed_before = [t["recap"]["reviewed"] for t in before["turns"]]

    # Compose the Final Cut (auto-draft on entry) and accept it.
    _nav(client, session_id, "final_cut")
    client.post(
        "/story/synopsis/accept",
        data={"session_id": session_id, "text": ""},
    )
    after = _doc(tmp_path, session_id)
    # The Final Cut is its own reviewed artifact…
    assert after["final_cut"]["reviewed"] is True
    assert after["final_cut"]["text"].strip()
    # …and every played turn recap is byte-for-byte unchanged and still reviewed.
    assert [t["recap"]["text"] for t in after["turns"]] == recaps_before
    assert [t["recap"]["reviewed"] for t in after["turns"]] == reviewed_before


# ── 26. Entering the Final Cut auto-drafts a populated, not-yet-reviewed leaf ─


def test_final_cut_autodrafts_on_entry(client, tmp_path):
    session_id = _new_session(client)
    _reach_scene_complete(client, tmp_path, session_id)
    resp = _nav(client, session_id, "final_cut")
    doc = _doc(tmp_path, session_id)
    fc = doc["final_cut"]
    # Landed on a populated draft, not a blank splash (J5), not yet accepted.
    assert fc["text"].strip()
    assert fc["reviewed"] is False
    # The composed draft is rendered on the page with the generic Accept control.
    assert "Accept" in resp.text


# ── 27. validate_cut_turns: 1:1 alignment, raises on any divergence (FR-485) ──


def test_validate_cut_turns_aligns_and_raises_on_divergence():
    from examples.dungeon_master.api import turn_ops

    played = [{"n": 1}, {"n": 2}, {"n": 3}]

    # Happy path: exactly one segment per played turn, returned in played order.
    aligned = turn_ops.validate_cut_turns(
        played,
        [
            {"n": 2, "text": "two"},
            {"n": 1, "text": "one"},
            {"n": 3, "text": "three"},
        ],
    )
    assert [s["n"] for s in aligned] == [1, 2, 3]
    assert [s["text"] for s in aligned] == ["one", "two", "three"]

    # A dropped turn is a defect — surfaced, never silently padded.
    with pytest.raises(ValueError, match="missing"):
        turn_ops.validate_cut_turns(
            played, [{"n": 1, "text": "a"}, {"n": 2, "text": "b"}]
        )

    # A duplicated turn is a defect — never silently re-keyed by position.
    with pytest.raises(ValueError, match="duplicat"):
        turn_ops.validate_cut_turns(
            played,
            [
                {"n": 1, "text": "a"},
                {"n": 1, "text": "a2"},
                {"n": 2, "text": "b"},
                {"n": 3, "text": "c"},
            ],
        )

    # An invented turn label (4, never played) is a defect.
    with pytest.raises(ValueError, match="invented"):
        turn_ops.validate_cut_turns(
            played,
            [
                {"n": 1, "text": "a"},
                {"n": 2, "text": "b"},
                {"n": 4, "text": "d"},
            ],
        )


# ── 28. The turn-structured cut is gated on scene_complete, like Final Cut ────


def test_final_cut_turns_locked_until_scene_complete(client, tmp_path):
    session_id = _new_session(client)
    _reach_play(client, tmp_path, session_id)  # turn:1, scene NOT complete
    # Locked: not in the breadcrumb and a nav to it is refused.
    resp = _nav(client, session_id, "final_cut_turns")
    assert _doc(tmp_path, session_id)["stage"] != "final_cut_turns"
    assert "Final Cut (Turns)" not in resp.text

    # Play on to completion → the peer appears and is reachable.
    resp2 = _reach_scene_complete(client, tmp_path, session_id)
    assert "Final Cut (Turns)" in resp2.text
    resp3 = _nav(client, session_id, "final_cut_turns")
    assert _doc(tmp_path, session_id)["stage"] == "final_cut_turns"
    assert resp3.status_code == 200


# ── 29. The cut auto-drafts one polished segment per played turn (aligned) ────


def test_final_cut_turns_autodrafts_aligned_track(client, tmp_path):
    session_id = _new_session(client)
    _reach_scene_complete(client, tmp_path, session_id)  # 3 played turns
    _nav(client, session_id, "final_cut_turns")
    doc = _doc(tmp_path, session_id)
    fct = doc["final_cut_turns"]
    # The validated structure: exactly one segment per played turn, contiguous n.
    assert [s["n"] for s in fct["turns"]] == [1, 2, 3]
    assert all(s["text"].strip() for s in fct["turns"])
    # A rendered text view exists for the generic edit control, not yet accepted.
    assert fct["text"].strip()
    assert fct["reviewed"] is False


# ── 30. Additive: composing the turn-cut leaves recaps AND the FR-484 cut alone ─


def test_final_cut_turns_is_additive_to_recaps_and_continuous_cut(client, tmp_path):
    session_id = _new_session(client)
    _reach_scene_complete(client, tmp_path, session_id)

    # Compose AND accept the FR-484 continuous Final Cut first…
    _nav(client, session_id, "final_cut")
    client.post(
        "/story/synopsis/accept",
        data={"session_id": session_id, "text": ""},
    )
    mid = _doc(tmp_path, session_id)
    continuous_before = mid["final_cut"]["text"]
    recaps_before = [t["recap"]["text"] for t in mid["turns"]]
    reviewed_before = [t["recap"]["reviewed"] for t in mid["turns"]]

    # …then compose and accept the turn-structured cut.
    _nav(client, session_id, "final_cut_turns")
    client.post(
        "/story/synopsis/accept",
        data={"session_id": session_id, "text": ""},
    )
    after = _doc(tmp_path, session_id)
    # The turn-structured cut is its own reviewed artifact under a distinct key…
    assert after["final_cut_turns"]["reviewed"] is True
    assert after["final_cut_turns"]["turns"]
    # …and it clobbers neither the continuous Final Cut…
    assert after["final_cut"]["text"] == continuous_before
    assert after["final_cut"]["reviewed"] is True
    # …nor any played turn recap (byte-for-byte, still reviewed).
    assert [t["recap"]["text"] for t in after["turns"]] == recaps_before
    assert [t["recap"]["reviewed"] for t in after["turns"]] == reviewed_before


# ── 31. A turn captures the wider per-character performance bundle (FR-486) ───


def test_turn_captures_wider_performance(client, tmp_path):
    session_id = _new_session(client)
    _reach_play(client, tmp_path, session_id)  # turn:1 drafted
    doc = _doc(tmp_path, session_id)
    intents = doc["turns"][0]["intents"]
    assert intents, "the turn must persist per-character intents"
    for cid, perf in intents.items():
        # The decision layer stays (the arc reads `intent`)…
        assert perf["thinking"].strip()
        assert perf["intent"].strip()
        # …and the new outward performance layer is captured additively.
        assert perf["dialogue"].strip(), f"{cid} should carry a spoken line"
        assert perf["expression"].strip(), f"{cid} should carry a visible tell"


# ── 32. Old turns (and silent characters) default missing performance to "" ───


def test_turn_intents_defaults_missing_performance_to_empty():
    from examples.dungeon_master.api import turn_ops

    # A turn played before FR-486: its intent bundle carries only the old two
    # keys. It must still resolve — a missing performance key is a benign empty
    # (an additive side-channel), never a raise (contrast the FR-485 alignment
    # validator, where a missing turn IS a defect).
    doc = {
        "turns": [
            {
                "n": 1,
                "intents": {"kara": {"thinking": "reads it", "intent": "lunges"}},
                "recap": {"text": "Turn 1 — Kara lunges.", "reviewed": True},
            }
        ]
    }
    chars = {"roster": ["kara"], "cards": {"kara": {"name": "Kara"}}}
    cards = turn_ops.turn_intents(doc, chars, 1)
    assert len(cards) == 1
    card = cards[0]
    assert card["name"] == "Kara"
    assert card["thinking"] == "reads it"
    assert card["intent"] == "lunges"
    # The new keys are present and default to "" — a silent character is legitimate.
    assert card["dialogue"] == ""
    assert card["expression"] == ""


# ── 33. The arc seam is frozen: director and recap ignore the new fields ─────


def test_arc_seam_ignores_wider_performance():
    """The director and dry recap must read ONLY ``intent`` per character (FR-486).

    The whole approval rests on the wider performance being a *side-channel* the
    arc never sees: FR-481/482/483 judge the arc on ``intent``, and the FR-484/485
    cuts consume the dry recaps. If ``dialogue``/``expression`` leaked into the
    director's judgement or the recap, the cut inputs would shift. This proves
    mechanically that they cannot: neither prompt template references them.
    """
    prompts = Path(__file__).resolve().parent.parent / "prompts"
    for name in ("turn_direct", "turn_recap"):
        text = (prompts / f"{name}.yaml").read_text()
        lowered = text.lower()
        # The arc still reads each character's committed intent…
        assert "intent" in lowered, f"{name} must read the committed intent"
        # …but never the outward performance layer (it stays a side-channel).
        assert "dialogue" not in lowered, f"{name} must not read dialogue"
        assert "expression" not in lowered, f"{name} must not read expression"


# ── 34. The turn card surfaces the spoken/acted performance to the DM ────────


def test_turn_card_surfaces_dialogue_and_expression(client, tmp_path):
    session_id = _new_session(client)
    resp = _reach_play(client, tmp_path, session_id)  # lands on turn:1
    # The captured dialogue and expression are rendered beside the recap so the
    # DM can read each character's spoken line and visible tell.
    assert "Hold the ledge" in resp.text
    assert "jaw sets" in resp.text


# ── FR-487: the full-text walkthrough (the rendered finish) ──────────────────


def _reach_cut(client, tmp_path, session_id):
    """Drive to scene-complete and draft the FR-485 cut spine the walkthrough needs.

    The walkthrough renders the FR-485 ``final_cut_turns`` cut as its structural
    spine, so it stays locked until that cut is *present* (FR-487 OQ1). Navigating
    to ``final_cut_turns`` auto-drafts it; this leaves the session with the spine
    available but the walkthrough not yet composed.
    """
    _reach_scene_complete(client, tmp_path, session_id)  # 3 played turns
    return _nav(client, session_id, "final_cut_turns")  # auto-drafts the cut spine


# ── 35. walkthrough_render_inputs composes the authored layers, hides thinking ─


def test_walkthrough_render_inputs_compose_authored_layers():
    from examples.dungeon_master.api import turn_ops

    doc = {
        "turns": [
            {
                "n": 1,
                "intents": {
                    "kara": {
                        "thinking": "kara reads the ledge",
                        "intent": "Kara lunges",
                        "dialogue": "Hold the ledge.",
                        "expression": "jaw sets",
                    }
                },
                "recap": {"text": "Turn 1 — they collide.", "reviewed": True},
            },
            {
                "n": 2,
                "intents": {
                    "kara": {
                        "thinking": "kara presses",
                        "intent": "Kara drives forward",
                        "dialogue": "Yield.",
                        "expression": "eyes narrow",
                    }
                },
                "recap": {"text": "Turn 2 — she presses.", "reviewed": True},
            },
        ],
        "final_cut_turns": {
            "turns": [
                {"n": 1, "text": "polished turn 1"},
                {"n": 2, "text": "polished turn 2"},
            ]
        },
    }
    chars = {"roster": ["kara"], "cards": {"kara": {"name": "Kara"}}}
    setting = "A flooded valley at dusk."
    staging_by_n = {1: "on the ledge", 2: "water rising"}
    bundles = turn_ops.walkthrough_render_inputs(doc, chars, setting, staging_by_n)

    # One bundle per played turn, in order, carrying the cut spine + staging.
    assert [b["n"] for b in bundles] == [1, 2]
    assert bundles[0]["cut_text"] == "polished turn 1"
    assert bundles[0]["setting"] == setting
    assert bundles[0]["staging"] == "on the ledge"
    # The cast carries the FR-486 outward performance — but NEVER the private
    # thinking (it is the one layer the page must not render, FR-487 OQ5).
    card = bundles[0]["cast"][0]
    assert card == {
        "name": "Kara",
        "dialogue": "Hold the ledge.",
        "expression": "jaw sets",
        "intent": "Kara lunges",
    }
    assert "thinking" not in card


# ── 36. The walkthrough is locked until the FR-485 cut spine is present ───────


def test_walkthrough_locked_until_cut_present(client, tmp_path):
    session_id = _new_session(client)
    _reach_scene_complete(client, tmp_path, session_id)  # scene complete, NO cut yet
    # Locked: the cut spine the walkthrough renders does not exist yet.
    resp = _nav(client, session_id, "walkthrough")
    assert _doc(tmp_path, session_id)["stage"] != "walkthrough"
    assert "Walkthrough" not in resp.text

    # Draft the FR-485 cut spine → the Walkthrough peer appears and is reachable.
    _nav(client, session_id, "final_cut_turns")  # auto-drafts the cut
    resp2 = _nav(client, session_id, "final_cut_turns")
    assert "Walkthrough" in resp2.text
    resp3 = _nav(client, session_id, "walkthrough")
    assert _doc(tmp_path, session_id)["stage"] == "walkthrough"
    assert resp3.status_code == 200


# ── 37. The walkthrough auto-drafts one full-text passage per played turn ─────


def test_walkthrough_autodrafts_aligned_full_text(client, tmp_path):
    session_id = _new_session(client)
    _reach_cut(client, tmp_path, session_id)  # 3 played turns + cut spine
    _nav(client, session_id, "walkthrough")
    doc = _doc(tmp_path, session_id)
    wt = doc["walkthrough"]
    # A curtain-up setting header plus exactly one passage per played turn.
    assert wt["setting"].strip()
    assert [s["n"] for s in wt["turns"]] == [1, 2, 3]
    assert all(s["text"].strip() for s in wt["turns"])
    # A rendered text view for the generic edit control, not yet accepted.
    assert wt["text"].strip()
    assert wt["reviewed"] is False


# ── 38. The full text renders the authored dialogue, expression, and staging ──


def test_walkthrough_renders_authored_layers(client, tmp_path):
    session_id = _new_session(client)
    _reach_cut(client, tmp_path, session_id)
    resp = _nav(client, session_id, "walkthrough")
    # The full text contains a character's actual spoken line (FR-486 dialogue),
    # an expression-derived gesture (FR-486 expression), and the director's
    # staging cue (FR-487) — every layer authored upstream, none invented.
    assert "Hold the ledge" in resp.text
    assert "jaw sets" in resp.text
    assert "staging delta" in resp.text
    # The private thinking is never put on the page.
    assert "reads the ledge" not in resp.text
    # The map reducer's per-branch bookkeeping must never leak into the prose —
    # the page shows the rendered passage, not the {_map_index, value} wrapper.
    assert "_map_index" not in resp.text


# ── 39. The walkthrough is additive: every prior artifact stays immutable ─────


def test_walkthrough_is_additive(client, tmp_path):
    session_id = _new_session(client)
    _reach_cut(client, tmp_path, session_id)

    # Compose and accept the FR-484 continuous cut and the FR-485 turn cut first.
    _nav(client, session_id, "final_cut")
    client.post("/story/synopsis/accept", data={"session_id": session_id, "text": ""})
    _nav(client, session_id, "final_cut_turns")
    client.post("/story/synopsis/accept", data={"session_id": session_id, "text": ""})
    mid = _doc(tmp_path, session_id)
    continuous_before = mid["final_cut"]["text"]
    cut_before = [s["text"] for s in mid["final_cut_turns"]["turns"]]
    recaps_before = [t["recap"]["text"] for t in mid["turns"]]
    intents_before = [t["intents"] for t in mid["turns"]]

    # Compose and accept the walkthrough.
    _nav(client, session_id, "walkthrough")
    client.post("/story/synopsis/accept", data={"session_id": session_id, "text": ""})
    after = _doc(tmp_path, session_id)
    # The walkthrough is its own reviewed artifact…
    assert after["walkthrough"]["reviewed"] is True
    assert after["walkthrough"]["turns"]
    # …and it clobbers neither the two cuts, the recaps, nor the performance.
    assert after["final_cut"]["text"] == continuous_before
    assert [s["text"] for s in after["final_cut_turns"]["turns"]] == cut_before
    assert [t["recap"]["text"] for t in after["turns"]] == recaps_before
    assert [t["intents"] for t in after["turns"]] == intents_before


# ── 40. Accepting the finishes chains Final Cut → Turns → Walkthrough ─────────


def test_finishes_chain_through_accept_to_walkthrough(client, tmp_path):
    """Accepting each finish lands on the next, ending on the Walkthrough.

    The three closing artifacts are terminal leaves, but Accept must walk the DM
    through all of them rather than stranding the page on the first (the reported
    "Final Cut shown, then the page closed"). The chain also drafts the FR-485 cut
    spine, so the Walkthrough — which renders it — is reachable without a manual
    detour through the breadcrumb.
    """
    session_id = _new_session(client)
    _reach_scene_complete(client, tmp_path, session_id)  # → turn:3 (scene complete)

    # Accepting the scene-complete turn lands on the continuous Final Cut.
    client.post("/story/synopsis/accept", data={"session_id": session_id, "text": ""})
    assert _doc(tmp_path, session_id)["stage"] == "final_cut"

    # Accept Final Cut → Final Cut (Turns) (which drafts the cut spine).
    client.post("/story/synopsis/accept", data={"session_id": session_id, "text": ""})
    doc = _doc(tmp_path, session_id)
    assert doc["stage"] == "final_cut_turns"
    assert doc["final_cut_turns"]["turns"], "the cut spine must be drafted on entry"

    # Accept Final Cut (Turns) → the Walkthrough, the true terminal leaf.
    client.post("/story/synopsis/accept", data={"session_id": session_id, "text": ""})
    doc = _doc(tmp_path, session_id)
    assert doc["stage"] == "walkthrough"
    assert doc["walkthrough"]["turns"], "the walkthrough must be drafted on entry"

    # Accepting the Walkthrough stays put — it is the end of the chain.
    resp = client.post(
        "/story/synopsis/accept", data={"session_id": session_id, "text": ""}
    )
    assert _doc(tmp_path, session_id)["stage"] == "walkthrough"
    assert resp.status_code == 200


# ── 41. A declined (empty) generation surfaces, never silently blanks ─────────


def test_weave_declined_empty_completion_surfaces_message(client, tmp_path):
    """An empty completion (a content-policy decline) is shown, not swallowed.

    A Vertex/Gemini SAFETY block on an explicit scene returns an *empty* string
    rather than raising. The DM must be told the request was declined — not left
    staring at a blank card that reads like a bug — and nothing blank may be
    persisted as the synopsis.
    """
    session_id = _new_session(client)

    def _decline(prompt_name, variables=None, **kwargs):
        if prompt_name == "synopsis":
            return ""  # a blocked completion comes back empty, not as an error
        return _mock_execute_prompt(prompt_name, variables, **kwargs)

    with (
        patch("yamlgraph.node_factory.llm_nodes.execute_prompt", side_effect=_decline),
        patch("yamlgraph.executor.execute_prompt", side_effect=_decline),
    ):
        resp = client.post(
            "/story/synopsis/weave",
            data={"session_id": session_id, "text": "", "prompt": "an explicit scene"},
        )

    # htmx swaps only 2xx — a dropped 400 would leave the DM with no feedback.
    assert resp.status_code == 200
    # The DM is told the request was declined.
    assert "declined" in resp.text.lower()
    # The breadcrumb survives (the card is not replaced by a dead-end).
    assert 'id="app-shell"' in resp.text
    # Nothing blank was persisted as the synopsis — the doc is either untouched
    # (never written) or carries no blank synopsis text.
    try:
        synopsis = story_doc.read(tmp_path / session_id).get("synopsis", {})
    except FileNotFoundError:
        synopsis = {}
    assert not synopsis.get("text")


# ── 42. A provider error surfaces without losing the DM's place or draft ──────


def test_weave_provider_error_surfaces_without_losing_place(client, tmp_path):
    """A raised provider error is shown in-place, preserving breadcrumb + draft."""
    session_id = _new_session(client)

    def _boom(prompt_name, variables=None, **kwargs):
        if prompt_name == "synopsis":
            raise RuntimeError("blocked by content policy")
        return _mock_execute_prompt(prompt_name, variables, **kwargs)

    with (
        patch("yamlgraph.node_factory.llm_nodes.execute_prompt", side_effect=_boom),
        patch("yamlgraph.executor.execute_prompt", side_effect=_boom),
    ):
        resp = client.post(
            "/story/synopsis/weave",
            data={"session_id": session_id, "text": "my draft", "prompt": "go"},
        )

    assert resp.status_code == 200  # swappable, not a dropped 400
    assert 'id="app-shell"' in resp.text  # breadcrumb preserved
    assert "blocked by content policy" in resp.text  # the error reaches the DM
    assert "my draft" in resp.text  # the draft is kept so the DM can rephrase
