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

from examples.dungeon_master.api import chapter_nav, render, turn_ops, world_state
from yamlgraph.executor_base import format_prompt

PROMPTS = Path(__file__).resolve().parent.parent / "prompts"
GRAPHS = Path(__file__).resolve().parent.parent


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
        "relationships": [],
    }
    assert world_state.parse_world_state("WS1: the dam holds.") == {
        "characters": [],
        "objects": [],
        "facts": [],
        "relationships": [],
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
    inherited = chapter_nav.inherited_world_state(doc, "2")
    assert inherited["characters"][0]["name"] == "Hilde"
    assert inherited["characters"][0]["inventory"] == [
        "flint spear",
        "river-hide cloak",
    ]


def test_inherited_world_state_empty_for_first_chapter():
    doc = {"chapters": {"order": ["1"], "cards": {"1": {"world_state": _structured()}}}}
    assert chapter_nav.inherited_world_state(doc, "1") == {}


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


def test_inherited_seam_packet_returns_previous_chapter_packet():
    doc = {
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "seam_packet": {
                        "resolved_events": ["The dam burst at dusk."],
                        "open_threads": ["Hilde distrusts Gunnar"],
                        "must_carry_facts": ["Arnulf is believed dead."],
                        "opening_constraints": ["FORBID: Arnulf returns alive"],
                    }
                },
                "2": {},
            },
        }
    }
    packet = chapter_nav.inherited_seam_packet(doc, "2")
    assert packet["must_carry_facts"] == ["Arnulf is believed dead."]


def test_running_scene_includes_seam_contract_on_turn_one_only():
    doc = {
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "world_state": _structured(),
                    "seam_packet": {
                        "resolved_events": ["The dam burst at dusk."],
                        "open_threads": ["Hilde distrusts Gunnar"],
                        "must_carry_facts": ["Arnulf is believed dead."],
                        "opening_constraints": ["FORBID: Arnulf returns alive"],
                    },
                },
                "2": {
                    "title": "The Last Ledge",
                    "summary": "They are stranded.",
                    "turns": [{"n": 1, "recap": {"text": "They reach the ledge."}}],
                },
            },
        }
    }
    scene_turn_one = turn_ops.running_scene(doc, "2", 1)
    scene_turn_two = turn_ops.running_scene(doc, "2", 2)

    assert "CHAPTER SEAM CONTRACT" in scene_turn_one
    assert "Must-Carry Facts" in scene_turn_one
    assert "CHAPTER SEAM CONTRACT" not in scene_turn_two


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
    data = yaml.safe_load((PROMPTS / "chapter_close.yaml").read_text(encoding="utf-8"))
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


def test_chapter_close_reasoning_budget_cannot_starve_the_ledger():
    # FR-499A regression: gemini-3.5-flash spends hidden reasoning tokens from the
    # same completion budget BEFORE emitting JSON. A 2000-token cap was consumed
    # entirely by reasoning (~1921 tok observed), leaving "text": "" → an empty
    # ledger that parse_world_state() silently rendered as no characters/objects.
    # Two guards must hold: a bounded reasoning threshold AND a large output budget
    # so the visible JSON always has room after thinking completes.
    defaults = yaml.safe_load((GRAPHS / "chapter_close.yaml").read_text(encoding="utf-8"))["defaults"]
    budget = defaults["thinking_budget"]
    max_tokens = defaults["max_tokens"]
    assert budget is not None, "reasoning must be capped, not unbounded"
    # Must stay under 1024: create_llm() raises on thinking_budget >= 1024 for
    # non-thinking providers (inception/mercury for fast test runs). Below the
    # threshold it bounds Gemini reasoning on vertex yet is ignored elsewhere.
    assert budget < 1024, "thinking_budget >= 1024 breaks non-thinking providers"
    # Output budget must dwarf the reasoning cap so the JSON ledger survives.
    assert max_tokens - budget >= 4000, "insufficient headroom for the ledger JSON"


# ── relationships: emotional state persists across chapter boundaries (FR-513) ─


def _relationships() -> dict:
    """A ledger carrying active, dormant, and archived relationships."""
    return {
        "characters": [],
        "objects": [],
        "facts": [],
        "relationships": [
            {
                "between": ["Hilde", "Gunnar"],
                "type": "romantic_bond",
                "status": "active",
                "tensions": ["clan_feud", "public_secrecy"],
                "last_interaction": "Ch2 intimate moment",
                "recap_citations": [
                    "Ch2-Turn-7-recap: 'the shape of it was already love'"
                ],
            },
            {
                "between": ["Hilde", "Svala", "Reinmar"],
                "type": "alliance",
                "status": "dormant",
                "tensions": ["survivor resentment"],
                "last_interaction": "Ch4 defended survivors",
                "recap_citations": ["Ch4-Turn-5-recap: coordinated defense"],
            },
            {
                "between": ["Hilde", "Arnulf"],
                "type": "enmity",
                "status": "archived",
                "tensions": ["honor dispute"],
                "last_interaction": "Ch5 held at truce line",
                "recap_citations": ["Ch5-Turn-8-recap: 'no longer able to reach her'"],
            },
        ],
    }


def test_parse_roundtrips_relationships():
    # A1: world_state carries a typed relationships array.
    ws = world_state.parse_world_state(_relationships())
    assert ws["relationships"][0]["between"] == ["Hilde", "Gunnar"]
    assert ws["relationships"][0]["type"] == "romantic_bond"
    assert ws["relationships"][0]["status"] == "active"


def test_relationships_are_grounded():
    # A8 (refinement 1): every persisted relationship must cite at least one recap;
    # an ungrounded bond is dropped at the boundary, not carried as a hallucination.
    raw = {
        "relationships": [
            {
                "between": ["Hilde", "Gunnar"],
                "type": "romantic_bond",
                "status": "active",
                "recap_citations": ["Ch2-Turn-7-recap: love"],
            },
            {
                "between": ["Hilde", "Reinmar"],
                "type": "romantic_bond",
                "status": "active",
                "recap_citations": [],  # ungrounded → dropped
            },
        ]
    }
    ws = world_state.parse_world_state(raw)
    assert len(ws["relationships"]) == 1
    assert ws["relationships"][0]["between"] == ["Hilde", "Gunnar"]
    assert all(r["recap_citations"] for r in ws["relationships"])


def test_detects_ungrounded_relationships():
    # A11 (refinement 4): a hallucinated relationship (no recap evidence, or fewer
    # than two named parties) never reaches turn context.
    raw = {
        "relationships": [
            {
                "between": ["Hilde"],  # only one party → not a relationship
                "type": "romantic_bond",
                "status": "active",
                "recap_citations": ["Ch9-Turn-1-recap: invented"],
            }
        ]
    }
    ws = world_state.parse_world_state(raw)
    assert ws["relationships"] == []
    assert "romantic_bond" not in world_state.format_world_state(raw)


def test_format_renders_active_relationships_compactly():
    # A4 + A10 (refinement 3): relationships reach the prompt as compact prose,
    # never a serialized dict.
    text = world_state.format_world_state(_relationships(), relationships="active")
    assert "Relationships:" in text
    assert "Hilde and Gunnar: romantic_bond" in text
    assert "clan_feud, public_secrecy" in text
    assert "{'between'" not in text  # no dict repr leaked


def test_format_active_excludes_dormant_and_archived():
    # A9 (refinement 2): the turn view carries only active bonds; dormant/archived
    # stay off the play context so stale tensions are not reinvoked.
    text = world_state.format_world_state(_relationships(), relationships="active")
    assert "Hilde and Gunnar" in text  # active
    assert "Reinmar" not in text  # dormant alliance excluded
    assert "Arnulf" not in text  # archived enmity excluded


def test_format_all_preserves_dormant_for_carry_forward():
    # The close carry-forward ("all") keeps dormant/archived so the next chapter's
    # close LLM can preserve or revive them; status labels are shown.
    text = world_state.format_world_state(_relationships(), relationships="all")
    assert "Hilde and Gunnar" in text
    assert "Reinmar" in text
    assert "Arnulf" in text
    assert "[dormant]" in text
    assert "[archived]" in text


def test_running_scene_includes_active_relationships_only():
    # A3 + A9: turn-1 of chapter N+1 inherits chapter N's active relationships in
    # play context; dormant/archived inherited bonds are excluded.
    doc = {
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {"world_state": _relationships()},
                "2": {"title": "The Last Ledge", "summary": "They are stranded."},
            },
        }
    }
    scene = turn_ops.running_scene(doc, "2", 1)
    assert "Hilde and Gunnar: romantic_bond" in scene
    assert "Reinmar" not in scene  # dormant excluded from turn context
    assert "{'between'" not in scene


# ── FR-514: delta-close ledger with a carry-forward floor ────────────────────


def _grounded_edge(between, rel_type, **kw) -> dict:
    edge = {
        "between": list(between),
        "type": rel_type,
        "status": "active",
        "tensions": [],
        "last_interaction": "",
        "recap_citations": ["Ch1-Turn-1-recap: established"],
    }
    edge.update(kw)
    return edge


def _op(op, between, **kw) -> dict:
    payload = {
        "op": op,
        "between": list(between),
        "recap_citations": ["Ch2-Turn-3-recap: it changed"],
    }
    payload.update(kw)
    return payload


def test_apply_delta_adds_grounded_relationship_and_stamps_ordinal():
    # FR-514 A1: an add op opens a current edge stamped at current_index.
    inherited = {"characters": [], "objects": [], "facts": [], "relationships": []}
    out = world_state.apply_ledger_delta(
        inherited,
        [_op("add", ["Hilde", "Gunnar"], type="enmity")],
        current_index=1,
    )
    edge = out["relationships"][0]
    assert edge["between"] == ["Hilde", "Gunnar"]
    assert edge["type"] == "enmity"
    assert edge["valid_from"] == 1
    assert edge["valid_to"] is None
    assert edge["last_reaffirmed"] == 1


def test_empty_delta_preserves_inherited_ledger():
    # FR-514 A2 (the floor): zero operations carry the inherited active set
    # forward unchanged — a forgetful close can never empty the store.
    inherited = {
        "characters": [],
        "objects": [],
        "facts": [],
        "relationships": [_grounded_edge(["Hilde", "Gunnar"], "romantic_bond")],
    }
    out = world_state.apply_ledger_delta(inherited, [], current_index=5)
    assert len(out["relationships"]) == 1
    assert out["relationships"][0]["type"] == "romantic_bond"


def test_ungrounded_operation_dropped():
    # FR-514 A3: an op with no recap citation (or <2 parties) is dropped at the
    # boundary; a grounded op in the same batch is applied.
    inherited = {"characters": [], "objects": [], "facts": [], "relationships": []}
    out = world_state.apply_ledger_delta(
        inherited,
        [
            {"op": "add", "between": ["Hilde", "Gunnar"], "type": "enmity"},  # no cite
            {"op": "add", "between": ["Hilde"], "recap_citations": ["c"]},  # 1 party
            _op("add", ["Svala", "Reinmar"], type="alliance"),  # grounded
        ],
        current_index=1,
    )
    keys = {tuple(sorted(r["between"])) for r in out["relationships"]}
    assert keys == {("Reinmar", "Svala")}


def test_invalidate_removes_from_active():
    # FR-514 A4: an invalidate op archives the edge and closes it, so it leaves
    # turn context (current + non-paused only).
    inherited = {
        "characters": [],
        "objects": [],
        "facts": [],
        "relationships": [_grounded_edge(["Hilde", "Arnulf"], "alliance")],
    }
    out = world_state.apply_ledger_delta(
        inherited, [_op("invalidate", ["Hilde", "Arnulf"])], current_index=3
    )
    edge = out["relationships"][0]
    assert edge["status"] == "archived"
    assert edge["valid_to"] == 3
    text = world_state.format_world_state(out, relationships="active")
    assert "Arnulf" not in text


def test_single_current_edge_per_pair():
    # FR-514 A7 (J1): two adds for the same participant set fold onto one current
    # edge, never two concurrent edges.
    inherited = {"characters": [], "objects": [], "facts": [], "relationships": []}
    out = world_state.apply_ledger_delta(
        inherited,
        [
            _op("add", ["Hilde", "Gunnar"], type="alliance"),
            _op("add", ["Gunnar", "Hilde"], type="alliance"),  # same pair, reordered
        ],
        current_index=1,
    )
    current = [r for r in out["relationships"] if r["valid_to"] is None]
    assert len(current) == 1


def test_missing_lane_carries_forward():
    # FR-514 A8: a close that empties characters/objects/facts carries the
    # inherited lane forward rather than zeroing established state.
    inherited = {
        "characters": [{"name": "Hilde", "faction": "Aschenwulf"}],
        "objects": [{"name": "the slab", "holder": "none"}],
        "facts": ["The dam failed."],
        "relationships": [],
    }
    emitted = {"characters": [], "objects": [], "facts": ["A new truce was struck."]}
    out = world_state.apply_lane_floor(emitted, inherited)
    assert out["characters"][0]["name"] == "Hilde"  # floored
    assert out["objects"][0]["name"] == "the slab"  # floored
    assert out["facts"] == ["A new truce was struck."]  # emitted wins when present


# ── FR-515: bi-temporal reconciliation ───────────────────────────────────────


def test_legacy_edge_normalizes_to_current():
    # FR-515 A1: an edge stored before temporal markers existed reads as current.
    ws = world_state.parse_world_state(
        {"relationships": [_grounded_edge(["Hilde", "Gunnar"], "enmity")]}
    )
    edge = ws["relationships"][0]
    assert edge["valid_from"] == 0
    assert edge["valid_to"] is None


def test_contradiction_closes_old_opens_new():
    # FR-515 A2: an update that changes the type closes the old edge (valid_to set)
    # and opens a new current one — never a silent overwrite.
    inherited = {
        "characters": [],
        "objects": [],
        "facts": [],
        "relationships": [_grounded_edge(["Hilde", "Gunnar"], "enmity", valid_from=1)],
    }
    out = world_state.apply_ledger_delta(
        inherited,
        [_op("update", ["Hilde", "Gunnar"], type="romantic_bond")],
        current_index=2,
    )
    closed = [r for r in out["relationships"] if r["valid_to"] is not None]
    current = [r for r in out["relationships"] if r["valid_to"] is None]
    assert len(closed) == 1 and closed[0]["type"] == "enmity"
    assert closed[0]["valid_to"] == 2
    assert len(current) == 1 and current[0]["type"] == "romantic_bond"
    assert current[0]["valid_from"] == 2


def test_invalidated_edge_retained_for_history():
    # FR-515 A3: the closed edge stays in the stored ledger (history), not deleted.
    inherited = {
        "characters": [],
        "objects": [],
        "facts": [],
        "relationships": [_grounded_edge(["Hilde", "Arnulf"], "alliance")],
    }
    out = world_state.apply_ledger_delta(
        inherited, [_op("invalidate", ["Hilde", "Arnulf"])], current_index=4
    )
    assert len(out["relationships"]) == 1
    assert out["relationships"][0]["valid_to"] == 4


def test_turn_context_excludes_closed_edges():
    # FR-515 A4: a closed edge (valid_to set) is history, not present truth —
    # turn context (active) excludes it even if its status is still "active".
    ledger = {
        "relationships": [
            _grounded_edge(["Hilde", "Gunnar"], "enmity", valid_from=1, valid_to=2),
            _grounded_edge(["Hilde", "Gunnar"], "romantic_bond", valid_from=2),
        ]
    }
    text = world_state.format_world_state(ledger, relationships="active")
    assert "romantic_bond" in text
    assert "enmity" not in text


def test_enmity_to_romantic_reconciled_same_chapter():
    # FR-515 A5 (the type-lag regression): an intimate recap over a prior enmity
    # edge yields a current romantic_bond and a closed enmity in the SAME close.
    inherited = {
        "characters": [],
        "objects": [],
        "facts": [],
        "relationships": [_grounded_edge(["Hilde", "Gunnar"], "enmity", valid_from=1)],
    }
    out = world_state.apply_ledger_delta(
        inherited,
        [_op("update", ["Hilde", "Gunnar"], type="romantic_bond")],
        current_index=2,
    )
    current = [r for r in out["relationships"] if r["valid_to"] is None]
    assert current[0]["type"] == "romantic_bond"
    assert any(
        r["type"] == "enmity" and r["valid_to"] == 2 for r in out["relationships"]
    )


# ── FR-517: mechanical relationship decay ────────────────────────────────────


def test_reaffirm_updates_clock():
    # FR-517 A1: add and reaffirm set last_reaffirmed to the current chapter.
    inherited = {
        "characters": [],
        "objects": [],
        "facts": [],
        "relationships": [
            _grounded_edge(["Hilde", "Gunnar"], "alliance", last_reaffirmed=1)
        ],
    }
    out = world_state.apply_ledger_delta(
        inherited, [_op("reaffirm", ["Hilde", "Gunnar"])], current_index=4
    )
    assert out["relationships"][0]["last_reaffirmed"] == 4


def test_stale_edge_decays_to_dormant():
    # FR-517 A2: an active edge unrefreshed beyond decay_after is demoted to
    # dormant by code, with no LLM op.
    inherited = {
        "characters": [],
        "objects": [],
        "facts": [],
        "relationships": [
            _grounded_edge(["Hilde", "Gunnar"], "alliance", last_reaffirmed=1)
        ],
    }
    out = world_state.apply_ledger_delta(inherited, [], current_index=5, decay_after=2)
    assert out["relationships"][0]["status"] == "dormant"


def test_reaffirm_prevents_decay():
    # FR-517 A3: a reaffirm within the window keeps the edge active.
    inherited = {
        "characters": [],
        "objects": [],
        "facts": [],
        "relationships": [
            _grounded_edge(["Hilde", "Gunnar"], "alliance", last_reaffirmed=1)
        ],
    }
    out = world_state.apply_ledger_delta(
        inherited,
        [_op("reaffirm", ["Hilde", "Gunnar"])],
        current_index=3,
        decay_after=2,
    )
    assert out["relationships"][0]["status"] == "active"


def test_decayed_edge_not_in_turn_context():
    # FR-517 A4: a decayed edge leaves active turn context.
    inherited = {
        "characters": [],
        "objects": [],
        "facts": [],
        "relationships": [
            _grounded_edge(["Hilde", "Gunnar"], "alliance", last_reaffirmed=0)
        ],
    }
    out = world_state.apply_ledger_delta(inherited, [], current_index=5, decay_after=2)
    text = world_state.format_world_state(out, relationships="active")
    assert "Hilde and Gunnar" not in text


# ── FR-516: ranked top-K retrieval ───────────────────────────────────────────


def test_offstage_relationship_excluded():
    # FR-516 A1: a relationship with no on-stage party is excluded.
    rels = [
        _grounded_edge(["Hilde", "Gunnar"], "romantic_bond"),
        _grounded_edge(["Svala", "Reinmar"], "alliance"),
    ]
    ranked = world_state.rank_relationships(rels, cast_names=["Hilde", "Gunnar"], k=6)
    keys = {tuple(sorted(r["between"])) for r in ranked}
    assert keys == {("Gunnar", "Hilde")}


def test_turn_context_bounded_to_k():
    # FR-516 A2: more than K cast-relevant edges yields at most K rows.
    rels = [
        _grounded_edge(["Hilde", f"Ally{i}"], "alliance", tensions=[f"t{i}"])
        for i in range(10)
    ]
    ranked = world_state.rank_relationships(rels, cast_names=["Hilde"], k=3)
    assert len(ranked) == 3


def test_ranking_prefers_salient_relationships():
    # FR-516 A3: among cast-relevant edges, higher-tension / more-recent rank first.
    rels = [
        _grounded_edge(["Hilde", "Gunnar"], "enmity", tensions=[], valid_from=1),
        _grounded_edge(
            ["Hilde", "Svala"], "alliance", tensions=["a", "b", "c"], valid_from=4
        ),
    ]
    ranked = world_state.rank_relationships(rels, cast_names=["Hilde"], k=1)
    assert tuple(sorted(ranked[0]["between"])) == ("Hilde", "Svala")


def test_short_story_ranking_keeps_all_relevant_edges():
    # FR-516 A4: with ≤K cast-relevant edges all on stage, none are dropped.
    rels = [
        _grounded_edge(["Hilde", "Gunnar"], "romantic_bond"),
        _grounded_edge(["Hilde", "Svala"], "alliance"),
    ]
    ranked = world_state.rank_relationships(
        rels, cast_names=["Hilde", "Gunnar", "Svala"], k=6
    )
    assert len(ranked) == 2


# ── FR-518: consolidation merge pass ─────────────────────────────────────────


def test_overlapping_edges_merged():
    # FR-518 A1: a grounded merge collapses sources into one edge; the sources are
    # closed with valid_to (history), not deleted.
    ledger = {
        "relationships": [
            _grounded_edge(["Hilde", "Arnulf"], "hierarchy", valid_from=1),
            _grounded_edge(["Hilde", "Arnulf", "Reinmar"], "alliance", valid_from=2),
        ]
    }
    merges = [
        {
            "merge": [
                {"between": ["Hilde", "Arnulf"]},
                {"between": ["Hilde", "Arnulf", "Reinmar"]},
            ],
            "into": {
                "between": ["Hilde", "Arnulf", "Reinmar"],
                "type": "alliance",
                "recap_citations": ["Ch8-Turn-2-recap: the line fell in behind him"],
            },
        }
    ]
    out = world_state.apply_merges(ledger, merges, current_index=8)
    current = [r for r in out["relationships"] if r["valid_to"] is None]
    closed = [r for r in out["relationships"] if r["valid_to"] == 8]
    assert len(current) == 1 and current[0]["type"] == "alliance"
    assert len(closed) == 2


def test_ungrounded_merge_rejected():
    # FR-518 A2: a merge whose result lacks citations is rejected; ledger unchanged.
    ledger = {
        "relationships": [
            _grounded_edge(["Hilde", "Arnulf"], "hierarchy"),
            _grounded_edge(["Hilde", "Gunnar"], "alliance"),
        ]
    }
    merges = [
        {
            "merge": [
                {"between": ["Hilde", "Arnulf"]},
                {"between": ["Hilde", "Gunnar"]},
            ],
            "into": {"between": ["Hilde", "Arnulf"], "type": "alliance"},  # no cite
        }
    ]
    out = world_state.apply_merges(ledger, merges, current_index=8)
    assert all(r["valid_to"] is None for r in out["relationships"])


def test_consolidation_noop_on_clean_ledger():
    # FR-518 A3: with no merges, the pass leaves the ledger unchanged.
    ledger = {"relationships": [_grounded_edge(["Hilde", "Gunnar"], "romantic_bond")]}
    out = world_state.apply_merges(ledger, [], current_index=8)
    assert len(out["relationships"]) == 1
    assert out["relationships"][0]["valid_to"] is None
