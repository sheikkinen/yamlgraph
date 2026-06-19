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
ROSTER_TEXT = "Kara\nTarek"
ESTABLISHING_TEXT = (
    "A flooded valley at dusk; the last dry ledge stands slick above the water."
)

# FR-491 retires the single-scene finishes: a chapter now dead-ends into the Book
# (slice 4), so the play → Final Cut / Walkthrough route no longer exists, and the
# finish composition helpers (which still read the flat ``doc["turns"]`` and call
# the pre-FR-491 ``turn_intents`` arity) are dead pending slice 4's deletion. The
# directly-constructed unit tests for the still-pure helpers (final_cut_context,
# climax_turn, validate_cut_turns) stay green; the routing tests and the helpers
# coupled to the old turn shape are skipped until slice 4 deletes them.
_FINISH_RETIRED = pytest.mark.skip(
    reason="FR-491 slice 4: the single-scene finishes are being retired"
)


def _mock_direction(variables: dict) -> dict:
    """Deterministic director output mirroring the structured turn_direct schema.

    ``opening`` is read from the running-scene marker; the director reports
    satisfied beats as 1-based NUMBERS over the chapter's finite beat list (FR-503),
    progressing to the full set by turn 3 so the COMPUTED ``phase`` /
    ``scene_complete`` (``_apply_beat_ledger``) reproduce the old opening → rising →
    resolved timeline. Beat 2 is "Kara corners Tarek", so it resolves to that
    canonical text downstream. A *phantom* is any title-cased name in the scene
    that no rostered character owns (``Naru`` here — the Vane case), surfaced as a
    continuity flag and deliberately NOT folded into ``steer`` (FR-479 J2).
    """
    scene = variables.get("scene") or ""
    cast = variables.get("cast") or []
    turn_n = variables.get("turn_n")
    n = int(turn_n) if str(turn_n).isdigit() else 0
    opening = "Nothing has happened yet" in scene
    cast_names = {c.get("name") for c in cast}
    titlecased = set(re.findall(r"\b[A-Z][a-z]+\b", scene))
    phantoms = sorted(titlecased - cast_names - {"Nothing", "Only", "Turn"})
    if opening:
        satisfied: list[int] = []
    elif n >= 3:
        satisfied = [1, 2, 3, 4]  # every beat → resolved + scene_complete (computed)
    else:
        satisfied = [2]  # "Kara corners Tarek" → rising (computed)
    return {
        "phase": "opening" if opening else ("resolved" if n >= 3 else "rising"),
        "establishing": ESTABLISHING_TEXT if opening else "",
        "beats_satisfied": satisfied,
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
        # FR-504: every chapter carries a non-empty, ordered ``beats`` list (the
        # boundary contract). Beat 2 is "Kara corners Tarek" so the default
        # director mock's satisfied beat resolves to canonical text downstream;
        # only Kara/Tarek are capitalized so the scene introduces no phantoms.
        return {
            "chapters": [
                {
                    "title": "Chapter 1 — The Water Rises",
                    "summary": "Kara musters.",
                    "beats": [
                        "Kara musters the band",
                        "Kara corners Tarek",
                        "the floodwaters rise",
                        "Tarek frees the herd",
                    ],
                },
                {
                    "title": "Chapter 2 — The Last Ledge",
                    "summary": "Kara corners.",
                    "beats": [
                        "Kara reaches the ledge",
                        "Kara corners Tarek",
                        "the ledge floods",
                        "Tarek yields",
                    ],
                },
            ]
        }
    if prompt_name == "chapter_reoutline":
        # FR-523: after chapter 1 closes, chapter 2's beats are re-authored from the
        # carried state. The harness echoes chapter 2's existing beats so the play
        # path stays behavior-preserving (the real graph would bridge a lethal seam).
        return {
            "beats": [
                "Kara reaches the ledge",
                "Kara corners Tarek",
                "the ledge floods",
                "Tarek yields",
            ]
        }
    if prompt_name == "chapter_close":
        prev = variables.get("previous_world_state") or "none"
        return {
            "world_state": {
                "characters": [
                    {
                        "name": "Kara",
                        "faction": "Aschenwulf",
                        "status": "alive",
                        "location": "the ledge",
                        "inventory": ["flint spear"],
                    },
                ],
                "objects": [],
                "facts": [f"WS@{variables.get('index', '?')} (prev={prev})"],
            },
        }
    if draft.strip():
        return f"[refined: {instruction}] {draft}"
    if prompt_name == "synopsis":
        return SYNOPSIS_TEXT
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


CID = "1"  # tests play through the first chapter by default


def _turns(doc, cid: str = CID):
    """Chapter ``cid``'s played turns (FR-491 C: stored per chapter, not flat)."""
    return doc.get("chapters", {}).get("cards", {}).get(cid, {}).get("turns", [])


def _reach_play(client, tmp_path, session_id):
    """Drive a session through the whole preplan and open the first chapter's play.

    FR-491 reorders the preplan to cast-before-chapters and plays each chapter in
    place: accepting the synopsis lands on the first character, and accepting the
    last character completes the cast (deriving the chapter outline) and lands on
    the Chapters overview. Navigating to the first chapter opens its turn loop
    (``chapter:1`` redirects to ``turn:1:1``).
    """
    client.post(
        "/story/synopsis/weave",
        data={"session_id": session_id, "text": "", "prompt": "a flooded valley"},
    )
    _accept(client, session_id)  # synopsis → char:kara (roster [kara, tarek] derived)
    _accept(client, session_id, text="Kara sheet")  # kara → char:tarek
    _accept(client, session_id, text="Tarek sheet")  # tarek → chapters (cast complete)
    return _nav(client, session_id, "chapter:1")  # open chapter 1's play (→ turn:1:1)


# ── 1. Play is gated: no turn stage before the whole preplan is reviewed ─────


def test_play_locked_until_preplan_complete(client, tmp_path):
    session_id = _new_session(client)
    client.post(
        "/story/synopsis/weave",
        data={"session_id": session_id, "text": "", "prompt": "a flooded valley"},
    )
    _accept(client, session_id)  # only synopsis reviewed so far
    # The Play peer is absent and a turn cannot be navigated to.
    resp = _nav(client, session_id, "turn:1:1")
    doc = _doc(tmp_path, session_id)
    assert doc["stage"] != "turn:1:1"
    assert "Play" not in resp.text


# ── 2. Completing the preplan auto-drafts Turn 1 (intents + recap) ──────────


def test_completing_preplan_lands_on_drafted_turn_1(client, tmp_path):
    session_id = _new_session(client)
    resp = _reach_play(client, tmp_path, session_id)
    doc = _doc(tmp_path, session_id)
    # Landed on an auto-drafted Turn 1 (J5: never a blank splash).
    assert doc["stage"] == "turn:1:1"
    turn = _turns(doc)[0]
    assert turn["n"] == 1
    # One intent per principal, each with non-empty THINKING + INTENT (J6).
    assert set(turn["intents"]) == {"kara", "tarek"}
    for cid in ("kara", "tarek"):
        assert turn["intents"][cid]["thinking"].strip()
        assert turn["intents"][cid]["intent"].strip()
    # A non-empty recap, not yet accepted, in the recap entry.
    assert turn["recap"]["text"].startswith("Turn 1 —")
    assert turn["recap"]["reviewed"] is False
    # The breadcrumb now lists the chapter's first turn.
    assert "Turn 1" in resp.text


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
    assert doc["stage"] == "turn:1:2"
    assert _turns(doc)[0]["recap"]["reviewed"] is True
    assert len(_turns(doc)) == 2
    # Turn 2's intents received each character's Turn 1 intent as `previous`.
    t1_kara = _turns(doc)[0]["intents"]["kara"]["intent"]
    t2_kara = _turns(doc)[1]["intents"]["kara"]["intent"]
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
    turn = _turns(doc)[0]
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
    _accept(client, session_id)  # now on turn:1:2, turns 1 & 2 exist
    resp = _nav(client, session_id, "turn:1:1")
    body = resp.text
    assert _doc(tmp_path, session_id)["stage"] == "turn:1:1"
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
    resp = _reach_play(client, tmp_path, session_id)  # lands on turn:1:1
    doc = _doc(tmp_path, session_id)
    direction = _turns(doc)[0]["direction"]
    assert direction["phase"] == "opening"
    assert direction["establishing"].strip()
    # The director's establishing description is rendered into the opening recap…
    assert direction["establishing"] in _turns(doc)[0]["recap"]["text"]
    # …and is visible on the page.
    assert direction["establishing"] in resp.text


# ── 10. Reaching the END flips scene_complete, which stops plain advance (J5) ─


def test_scene_complete_stops_advance_and_surfaces(client, tmp_path):
    session_id = _new_session(client)
    _reach_play(client, tmp_path, session_id)  # turn:1:1 drafted
    _accept(client, session_id)  # → turn:1:2
    resp = _accept(client, session_id)  # → turn:1:3 (director reports scene_complete)
    doc = _doc(tmp_path, session_id)
    assert doc["stage"] == "turn:1:3"
    assert _turns(doc)[2]["direction"]["scene_complete"] is True
    # The completed state is surfaced on the turn page.
    assert "scene-complete" in resp.text
    # Accepting a completed turn does NOT spawn turn:1:4 (J5); it closes the
    # chapter (recording its end-of-chapter world_state) and lands on the NEXT
    # chapter's first turn (FR-491) — the single-scene Final Cut is retired from
    # the play loop.
    _accept(client, session_id)
    doc2 = _doc(tmp_path, session_id)
    assert doc2["stage"] == "turn:2:1"
    assert len(_turns(doc2, "1")) == 3
    ch1 = doc2["chapters"]["cards"]["1"]
    assert ch1["reviewed"] is True
    assert ch1["world_state"]["characters"]


# ── 11. A non-roster name acting raises a continuity flag, surfaced not steered ─


def test_phantom_actor_raises_continuity_flag(client, tmp_path):
    session_id = _new_session(client)
    _reach_play(client, tmp_path, session_id)
    # The roster is the authoritative cast (FR-491 D): a name in the chapter plan
    # that no rostered character owns must surface as a continuity flag. Inject a
    # stray non-roster name into the chapter plan and prove the director catches
    # it on the next read (defense in depth — the breach is reported, not silenced).
    doc = _doc(tmp_path, session_id)
    doc["chapters"]["cards"]["1"]["summary"] = (
        "Kara musters the band while Naru frees the herd."  # "Naru" absent from roster
    )
    story_doc.write(tmp_path / session_id, doc)
    resp = client.post(
        "/story/synopsis/weave",
        data={"session_id": session_id, "text": "Turn 1 — x", "prompt": "re-read"},
    )
    doc = _doc(tmp_path, session_id)
    direction = _turns(doc)[0]["direction"]
    # "Naru" is named in the chapter plan but absent from the roster (the Vane case).
    assert any("Naru" in f for f in direction["continuity"])
    # The flag is surfaced to the DM, and NOT silently applied as a steer (J2).
    assert "Naru" in resp.text
    assert direction["steer"] == ""


# ── FR-481: Director card & arc integrity ───────────────────────────────────


# ── 13. The director's judgement is always visible as a card on a turn (A) ───


def test_director_card_always_visible_on_turn(client, tmp_path):
    session_id = _new_session(client)
    _reach_play(client, tmp_path, session_id)  # turn:1 (opening)
    # The opening turn already shows the Director card with its phase badge.
    resp1 = _nav(client, session_id, "turn:1:1")
    assert "director-card" in resp1.text
    assert "director-phase-opening" in resp1.text
    # Advancing to a rising turn surfaces the phase badge and the satisfied beat.
    resp2 = _accept(client, session_id)  # → turn:2 (rising, one beat)
    body = resp2.text
    assert "director-card" in body
    assert "director-phase-rising" in body
    assert "Kara corners Tarek" in body


# ── FR-483: non-roster actors surface as continuity flags (roster-authoritative) ─


def _continuity_execute_prompt(flags):
    """An ``execute_prompt`` mock driving ``turn_direct.continuity`` for a turn.

    Returns ``flags`` verbatim as the director's continuity list so a test can
    prove the code keeps every non-roster flag the director raises (FR-491 D: the
    roster is the authoritative cast). Every other prompt delegates to the default.
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


# ── 19. A non-roster actor surfaces as a continuity flag (roster-authoritative) ─


def test_scene_declared_actor_not_flagged_but_phantom_kept(client, tmp_path):
    session_id = _new_session(client)
    _reach_play(client, tmp_path, session_id)  # turn:1, roster {kara, tarek}
    # FR-491 D: the roster is the authoritative cast — there is no separate
    # "scene-declared CHARACTERS" provenance any more. Every name acting at the
    # turn that the roster does not own is surfaced as a continuity flag; the
    # director prompt owns the judgement and the code keeps the flags verbatim.
    # Accepted residual: a synopsis-supported non-roster actor over-flags.
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
    continuity = _turns(_doc(tmp_path, session_id))[0]["direction"]["continuity"]
    # Both non-roster names are kept verbatim — the code never silences a flag.
    assert any("Krog" in f for f in continuity)
    assert any("Zalor" in f for f in continuity)


# ── 31. A turn captures the wider per-character performance bundle (FR-486) ───


def test_turn_captures_wider_performance(client, tmp_path):
    session_id = _new_session(client)
    _reach_play(client, tmp_path, session_id)  # turn:1 drafted
    doc = _doc(tmp_path, session_id)
    intents = _turns(doc)[0]["intents"]
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
        "chapters": {
            "cards": {
                "1": {
                    "turns": [
                        {
                            "n": 1,
                            "intents": {
                                "kara": {"thinking": "reads it", "intent": "lunges"}
                            },
                            "recap": {
                                "text": "Turn 1 — Kara lunges.",
                                "reviewed": True,
                            },
                        }
                    ]
                }
            }
        }
    }
    chars = {"roster": ["kara"], "cards": {"kara": {"name": "Kara"}}}
    cards = turn_ops.turn_intents(doc, chars, "1", 1)
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


# ── FR-503: finite, computed beat ledger (the unanchored-phase stall cure) ───
#
# The director stops inventing free-text beats and instead selects from a finite,
# enumerated list. ``phase`` and ``scene_complete`` are COMPUTED from k / N in
# Python (J3 truth table), not guessed by the model. ``_direction_dict`` resolves
# the returned indices back to canonical beat TEXT so every downstream consumer
# (Final Cut, the card, ``chapter_beats``) reads the same shape as before (J1).
# ``beats`` is a non-empty boundary contract (FR-504 ``_require_beats``); the
# FR-491 free-text ``N == 0`` fallback has been retired.


def test_phase_for_count_truth_table():
    from examples.dungeon_master.api import turn_ops

    # N == 5: opening at 0, rising while partial, climax on the last beat,
    # resolved only when every beat is satisfied (J3).
    assert turn_ops._phase_for_count(0, 5) == "opening"
    assert turn_ops._phase_for_count(1, 5) == "rising"
    assert turn_ops._phase_for_count(3, 5) == "rising"
    assert turn_ops._phase_for_count(4, 5) == "climax"
    assert turn_ops._phase_for_count(5, 5) == "resolved"
    # N == 1 collapses to opening → resolved (no rising/climax room).
    assert turn_ops._phase_for_count(0, 1) == "opening"
    assert turn_ops._phase_for_count(1, 1) == "resolved"
    # N == 2 jumps opening → climax → resolved (no rising room).
    assert turn_ops._phase_for_count(0, 2) == "opening"
    assert turn_ops._phase_for_count(1, 2) == "climax"
    assert turn_ops._phase_for_count(2, 2) == "resolved"


def test_satisfied_indices_parses_numbers_and_ignores_out_of_range():
    from examples.dungeon_master.api import turn_ops

    beats = ["alpha event", "beta event", "gamma event", "delta event"]
    # 1-based numbers as the scene presents them → 0-based index set.
    assert turn_ops._satisfied_indices([1, 3], beats) == {0, 2}
    # Numeric strings are accepted too.
    assert turn_ops._satisfied_indices(["2"], beats) == {1}
    # Out-of-range / non-numeric junk is ignored, never crashes (boundary).
    assert turn_ops._satisfied_indices([0, 99, "x", None], beats) == set()
    # A model that echoes the beat text instead of its number still resolves.
    assert turn_ops._satisfied_indices(["gamma event"], beats) == {2}


def test_apply_beat_ledger_resolves_indices_to_text_and_computes_phase():
    from examples.dungeon_master.api import turn_ops

    beats = ["a", "b", "c", "d", "e"]
    direction = {
        "phase": "resolved",  # a wrong model guess — must be overwritten
        "beats_satisfied": [1, 2],  # 1-based → indices 0,1
        "scene_complete": True,  # wrong model guess — must be recomputed
    }
    turn_ops._apply_beat_ledger(direction, beats, prior={})
    # Indices resolved back to canonical TEXT so consumers read list[str] (J1).
    assert direction["beats_satisfied"] == ["a", "b"]
    assert direction["beats_total"] == 5
    # phase + completion COMPUTED from k / N, not read from the model (J3).
    assert direction["phase"] == "rising"
    assert direction["scene_complete"] is False


def test_apply_beat_ledger_accumulates_with_prior_and_resolves():
    from examples.dungeon_master.api import turn_ops

    beats = ["a", "b", "c"]
    prior = {"beats_satisfied": ["a", "b"]}  # already-text from a past turn
    direction = {"phase": "rising", "beats_satisfied": [3], "scene_complete": False}
    turn_ops._apply_beat_ledger(direction, beats, prior=prior)
    # Cumulative union of prior text + this turn's index → every beat satisfied.
    assert direction["beats_satisfied"] == ["a", "b", "c"]
    assert direction["beats_total"] == 3
    assert direction["phase"] == "resolved"
    assert direction["scene_complete"] is True


def test_apply_beat_ledger_phase_is_monotonic_under_accumulation():
    """The computed phase never runs backwards as beats accumulate (FR-504).

    Re-homes the retired FR-481 ``_clamp_phase`` guarantee onto the computed
    ledger: because the satisfied set only grows (union with the prior turn) and
    ``_phase_for_count`` is monotonic in k, the recorded phase is monotonic by
    construction — even when the model "reports" fewer beats on a later turn.
    """
    from examples.dungeon_master.api import turn_ops

    beats = ["a", "b", "c", "d"]
    order = {"opening": 0, "rising": 1, "climax": 2, "resolved": 3}
    prior: dict = {}
    phases: list[str] = []
    # Turn-by-turn the model reports a shrinking selection, yet accumulation wins.
    for reported in ([], [1], [2], [1], [1, 2, 3, 4]):
        direction = {"beats_satisfied": list(reported)}
        turn_ops._apply_beat_ledger(direction, beats, prior=prior)
        phases.append(direction["phase"])
        prior = direction
    assert phases == ["opening", "rising", "rising", "rising", "resolved"]
    # Monotonic: each phase rank ≥ the previous (never regresses).
    ranks = [order[p] for p in phases]
    assert ranks == sorted(ranks)


def test_running_scene_surfaces_pending_beats(tmp_path):
    from examples.dungeon_master.api import turn_ops

    beats = [
        "Hilde raids at dawn",
        "The river breaks its banks",
        "Arnulf is swept downriver",
    ]
    doc = {
        "chapters": {
            "order": ["1"],
            "cards": {
                "1": {
                    "title": "The Water Rises",
                    "summary": "Hilde raids; the flood strands her.",
                    "beats": beats,
                    "turns": [
                        {
                            "n": 1,
                            "intents": {},
                            "recap": {
                                "text": "Hilde charges the camp.",
                                "reviewed": True,
                            },
                            "direction": {
                                "phase": "rising",
                                "beats_satisfied": ["Hilde raids at dawn"],
                                "beats_total": 3,
                            },
                        }
                    ],
                }
            },
        }
    }
    scene = turn_ops.running_scene(doc, "1", 2)
    # The finite, numbered beat list is shown so the director can return indices.
    assert "Hilde raids at dawn" in scene
    # There is an explicit "drive toward the first pending beat" block.
    marker = "BEATS STILL TO PORTRAY"
    assert marker in scene
    pending_block = scene.split(marker, 1)[1]
    # The unsatisfied beats appear in the pending block…
    assert "The river breaks its banks" in pending_block
    assert "Arnulf is swept downriver" in pending_block
    # …and the already-satisfied beat is NOT re-listed as still-to-portray.
    assert "Hilde raids at dawn" not in pending_block


# ── FR-504: beats are a required, non-empty boundary contract ────────────────


def test_outline_requires_nonempty_beats():
    """Every chapter must carry a non-empty ``beats`` list (FR-504 boundary contract).

    FR-503 kept the FR-491 free-text path alive as the ``N == 0`` fallback. FR-504
    retires it: a chapter outline that emits no beats is rejected at the parse
    boundary (``the_one_law`` — normalize where the outline enters), never silently
    fallen back, so there is exactly one beat-judgement regime downstream.
    """
    from examples.dungeon_master.api import outline_ops

    ok = [{"title": "C1", "summary": "s", "beats": ["b1", "b2"]}]
    assert outline_ops._require_beats(ok) == ok
    with pytest.raises(ValueError):
        outline_ops._require_beats([{"title": "C1", "summary": "s", "beats": []}])
