"""FR-548: World Codex — faction/location backstory stage (deterministic RED).

The codex is an outline-time, non-visitable, *immutable reference* derived from the
accepted synopsis: ``doc_ops.expand_codex`` runs ``world_codex.yaml`` (parse_json
output-shape, mirroring ``expand_chapters``/``outline_ops`` — NOT the line-split
roster), normalizes the parsed ``{factions, locations}`` object at the boundary, and
persists it under ``doc["codex"]`` with no ``reviewed`` gate. ``final_cut`` weaves it
as grounding texture through a ``{% if %}``-guarded block, so a doc with no codex
renders a byte-identical prompt.

These are the deterministic gate (stubbed graph + fixtures); the length/continuity
claim is visibility evidence captured in ``demo-output.log``, never a test. Example
tests are requirement-exempt (FR-474 J3): no ``@pytest.mark.req``.
"""

from __future__ import annotations

import asyncio

from examples.dungeon_master.api import doc_ops, story_doc
from examples.dungeon_master.api.final_cut import final_cut_context


def _run(coro):
    return asyncio.run(coro)


class _StubCodexApp:
    """A stub compiled graph whose ``ainvoke`` returns a fixed parsed codex."""

    def __init__(self, codex: object):
        self._codex = codex

    async def ainvoke(self, payload: dict) -> dict:
        return {"codex": self._codex}


class _ExplodingApp:
    """A stub that fails if invoked — proves the idempotent no-op never calls the LLM."""

    async def ainvoke(self, payload: dict) -> dict:  # pragma: no cover - must not run
        raise AssertionError("expand_codex must not re-derive a populated codex")


def _synopsis_doc() -> dict:
    return {"synopsis": {"text": "the Aschenwulf clan fights the flood for the valley"}}


_WELL_FORMED = {
    "factions": [
        {
            "name": "Aschenwulf",
            "identity": "the river clan who keep the ford",
            "history": "broke from the Barenschadel after the salt war",
            "stance": "holding the high valley as the waters rise",
        }
    ],
    "locations": [
        {
            "name": "the flood zone",
            "description": "the drowned lowland where the salt road vanishes",
            "significance": "whoever holds the ford controls the valley",
        }
    ],
}


def test_expand_codex_persists_factions_and_locations(tmp_path, monkeypatch):
    """A well-formed codex is normalized, persisted, and carries no ``reviewed`` gate."""
    monkeypatch.setattr(doc_ops, "get_app", lambda _graph: _StubCodexApp(_WELL_FORMED))
    doc = _synopsis_doc()

    _run(doc_ops.expand_codex(doc, tmp_path))

    codex = doc["codex"]
    assert "reviewed" not in codex  # immutable reference, no review gate (C3)
    assert len(codex["factions"]) >= 1
    assert len(codex["locations"]) >= 1
    assert codex["factions"][0]["name"] == "Aschenwulf"
    assert codex["locations"][0]["name"] == "the flood zone"
    # persisted to story.json, not just mutated in memory
    assert story_doc.read(tmp_path)["codex"]["factions"][0]["name"] == "Aschenwulf"


def test_expand_codex_normalizes_malformed_object(tmp_path, monkeypatch):
    """Missing string fields default to "", unknown keys drop, a non-list coerces to []."""
    malformed = {
        "factions": [{"name": "Aschenwulf", "bogus": "drop me"}],
        "locations": "not a list",
    }
    monkeypatch.setattr(doc_ops, "get_app", lambda _graph: _StubCodexApp(malformed))
    doc = _synopsis_doc()

    _run(doc_ops.expand_codex(doc, tmp_path))

    faction = doc["codex"]["factions"][0]
    assert faction == {
        "name": "Aschenwulf",
        "identity": "",
        "history": "",
        "stance": "",
    }
    assert "bogus" not in faction
    assert doc["codex"]["locations"] == []


def test_expand_codex_is_idempotent_for_immutable_reference(tmp_path, monkeypatch):
    """A populated codex is a no-op — re-accept never re-derives (immutable reference)."""
    monkeypatch.setattr(doc_ops, "get_app", lambda _graph: _ExplodingApp())
    doc = _synopsis_doc()
    doc["codex"] = {"factions": [{"name": "Kept"}], "locations": []}

    _run(doc_ops.expand_codex(doc, tmp_path))

    assert doc["codex"]["factions"][0]["name"] == "Kept"


def _final_cut_doc() -> dict:
    """A minimal two-chapter doc ``final_cut_context(doc, "2")`` can assemble."""
    return {
        "synopsis": {"text": "synopsis"},
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "summary": "c1",
                    "beats": ["Hilde holds the ridge"],
                    "cast": ["Hilde"],
                    "text": "Hilde held the ridge.",
                    "world_state": {"characters": []},
                },
                "2": {
                    "summary": "c2",
                    "beats": ["Hilde presses on"],
                    "cast": ["Hilde"],
                    "turns": [
                        {
                            "n": 1,
                            "direction": {"beats_satisfied": ["beat"]},
                            "recap": {"text": "recap"},
                        }
                    ],
                },
            },
        },
        "characters": {
            "roster": ["hilde"],
            "cards": {"hilde": {"name": "Hilde", "reviewed": True}},
        },
    }


def test_final_cut_world_codex_empty_when_absent():
    """Byte-identical absence: no codex -> empty ``world_codex`` var -> guard renders nothing."""
    ctx = final_cut_context(_final_cut_doc(), "2")
    assert ctx["world_codex"] == ""


def test_final_cut_world_codex_present_when_codex_set():
    """A populated codex reaches the prompt as grounding texture (faction + location)."""
    doc = _final_cut_doc()
    doc["codex"] = _WELL_FORMED
    ctx = final_cut_context(doc, "2")
    assert "Aschenwulf" in ctx["world_codex"]
    assert "the flood zone" in ctx["world_codex"]
