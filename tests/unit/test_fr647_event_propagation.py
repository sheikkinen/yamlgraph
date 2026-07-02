"""Tests for FR-647 event propagation pre-pass in worldgen.

Tests:
- Schema: birth_year on Character, year/scope/affected_locations on Event,
  calendar_note on Premise (REQ-YG-497)
- anchor_events: world scope → all characters, local → participants only,
  regional → faction/location match, age arithmetic (REQ-YG-497)
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

NOVEL_FANDOM_DIR = (
    Path(__file__).parent.parent.parent / "examples" / "novel_fandom"
).resolve()

_nf_str = str(NOVEL_FANDOM_DIR)
if _nf_str not in sys.path:
    sys.path.insert(0, _nf_str)


def _load(mod_name: str, rel_path: str):  # noqa: ANN202
    fpath = NOVEL_FANDOM_DIR / rel_path
    spec = importlib.util.spec_from_file_location(mod_name, fpath)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


_canon = _load("novel_fandom_schema_canon_647", "schema/canon.py")
_anchor = _load("novel_fandom_nodes_anchor_events", "nodes/anchor_events.py")

Character = _canon.Character
Event = _canon.Event
Premise = _canon.Premise
anchor_events = _anchor.anchor_events


# --- Schema (REQ-YG-497) ---


class TestSchemaFR647:
    @pytest.mark.req("REQ-YG-497")
    def test_character_has_birth_year(self):
        c = Character(id="test", lane="dynamic", name="Test")
        assert c.birth_year is None

    @pytest.mark.req("REQ-YG-497")
    def test_character_birth_year_accepts_int(self):
        c = Character(id="test", lane="dynamic", name="Test", birth_year=824)
        assert c.birth_year == 824

    @pytest.mark.req("REQ-YG-497")
    def test_event_has_year(self):
        e = Event(id="test", lane="dynamic")
        assert e.year is None

    @pytest.mark.req("REQ-YG-497")
    def test_event_year_accepts_int(self):
        e = Event(id="test", lane="dynamic", year=847)
        assert e.year == 847

    @pytest.mark.req("REQ-YG-497")
    def test_event_has_scope(self):
        e = Event(id="test", lane="dynamic")
        assert e.scope == "world"

    @pytest.mark.req("REQ-YG-497")
    def test_event_scope_accepts_local(self):
        e = Event(id="test", lane="dynamic", scope="local")
        assert e.scope == "local"

    @pytest.mark.req("REQ-YG-497")
    def test_event_has_affected_locations(self):
        e = Event(id="test", lane="dynamic")
        assert e.affected_locations == []

    @pytest.mark.req("REQ-YG-497")
    def test_premise_has_calendar_note(self):
        p = Premise(id="test", lane="dynamic", text="test")
        assert p.calendar_note == ""

    @pytest.mark.req("REQ-YG-497")
    def test_premise_calendar_note_accepts_str(self):
        p = Premise(
            id="test",
            lane="dynamic",
            text="test",
            calendar_note="Year 0 = founding of Ashguard",
        )
        assert "Year 0" in p.calendar_note


# --- anchor_events (REQ-YG-497) ---


def _make_canon(characters, events):
    """Build a canon_pages dict from lists of character/event dicts."""
    pages = {}
    for c in characters:
        pages[c["id"]] = {
            "type": "character",
            "id": c["id"],
            "name": c.get("name", c["id"]),
            "faction": c.get("faction", ""),
            "references": c.get("references", []),
            "birth_year": c.get("birth_year"),
        }
    for e in events:
        pages[e["id"]] = {
            "type": "event",
            "id": e["id"],
            "year": e.get("year"),
            "window": e.get("window", ""),
            "scope": e.get("scope", "world"),
            "affected_locations": e.get("affected_locations", []),
            "participants": e.get("participants", []),
            "consequences": e.get("consequences", []),
        }
    return pages


class TestAnchorEventsWorldScope:
    @pytest.mark.req("REQ-YG-497")
    def test_world_scope_includes_all_characters(self):
        canon = _make_canon(
            characters=[
                {"id": "kaelen", "birth_year": 824},
                {"id": "maren", "birth_year": 830},
                {"id": "voss", "birth_year": 810},
            ],
            events=[
                {
                    "id": "ashfall",
                    "year": 847,
                    "scope": "world",
                    "participants": ["kaelen", "maren"],
                },
            ],
        )
        result = anchor_events({"canon_pages": canon})
        ctx = result["event_context"]
        assert "kaelen" in ctx
        assert "maren" in ctx
        assert "voss" in ctx  # world scope: even non-participants
        assert len(ctx["kaelen"]) == 1
        assert len(ctx["voss"]) == 1


class TestAnchorEventsLocalScope:
    @pytest.mark.req("REQ-YG-497")
    def test_local_scope_only_participants(self):
        canon = _make_canon(
            characters=[
                {"id": "kaelen", "birth_year": 824},
                {"id": "maren", "birth_year": 830},
                {"id": "voss", "birth_year": 810},
            ],
            events=[
                {
                    "id": "duel",
                    "year": 850,
                    "scope": "local",
                    "participants": ["kaelen", "voss"],
                },
            ],
        )
        result = anchor_events({"canon_pages": canon})
        ctx = result["event_context"]
        assert len(ctx["kaelen"]) == 1
        assert len(ctx["voss"]) == 1
        assert len(ctx["maren"]) == 0  # not a participant


class TestAnchorEventsRegionalScope:
    @pytest.mark.req("REQ-YG-497")
    def test_regional_scope_matches_faction(self):
        canon = _make_canon(
            characters=[
                {"id": "kaelen", "faction": "ashguard", "birth_year": 824},
                {"id": "maren", "faction": "emberwrights", "birth_year": 830},
            ],
            events=[
                {
                    "id": "siege",
                    "year": 849,
                    "scope": "regional",
                    "affected_locations": ["ashguard"],
                    "participants": [],
                },
            ],
        )
        result = anchor_events({"canon_pages": canon})
        ctx = result["event_context"]
        assert len(ctx["kaelen"]) == 1  # faction matches
        assert len(ctx["maren"]) == 0  # different faction

    @pytest.mark.req("REQ-YG-497")
    def test_regional_scope_includes_explicit_participant(self):
        canon = _make_canon(
            characters=[
                {"id": "maren", "faction": "emberwrights", "birth_year": 830},
            ],
            events=[
                {
                    "id": "siege",
                    "year": 849,
                    "scope": "regional",
                    "affected_locations": ["ashguard"],
                    "participants": ["maren"],
                },
            ],
        )
        result = anchor_events({"canon_pages": canon})
        ctx = result["event_context"]
        assert len(ctx["maren"]) == 1  # explicit participant overrides faction


class TestAnchorEventsAgeArithmetic:
    @pytest.mark.req("REQ-YG-497")
    def test_age_at_event_computed(self):
        canon = _make_canon(
            characters=[{"id": "kaelen", "birth_year": 824}],
            events=[{"id": "ashfall", "year": 847, "scope": "world"}],
        )
        result = anchor_events({"canon_pages": canon})
        entry = result["event_context"]["kaelen"][0]
        assert entry["age_at_event"] == 23

    @pytest.mark.req("REQ-YG-497")
    def test_age_none_when_birth_year_missing(self):
        canon = _make_canon(
            characters=[{"id": "kaelen"}],  # no birth_year
            events=[{"id": "ashfall", "year": 847, "scope": "world"}],
        )
        result = anchor_events({"canon_pages": canon})
        entry = result["event_context"]["kaelen"][0]
        assert entry["age_at_event"] is None

    @pytest.mark.req("REQ-YG-497")
    def test_age_none_when_event_year_missing(self):
        canon = _make_canon(
            characters=[{"id": "kaelen", "birth_year": 824}],
            events=[{"id": "ashfall", "scope": "world"}],  # no year
        )
        result = anchor_events({"canon_pages": canon})
        entry = result["event_context"]["kaelen"][0]
        assert entry["age_at_event"] is None


class TestAnchorEventsTemporalOrder:
    @pytest.mark.req("REQ-YG-497")
    def test_events_sorted_by_year(self):
        canon = _make_canon(
            characters=[{"id": "kaelen", "birth_year": 824}],
            events=[
                {"id": "late_event", "year": 900, "scope": "world"},
                {"id": "early_event", "year": 800, "scope": "world"},
            ],
        )
        result = anchor_events({"canon_pages": canon})
        entries = result["event_context"]["kaelen"]
        assert entries[0]["event_id"] == "early_event"
        assert entries[1]["event_id"] == "late_event"


class TestAnchorEventsNoCharacters:
    @pytest.mark.req("REQ-YG-497")
    def test_empty_canon_returns_empty_context(self):
        result = anchor_events({"canon_pages": {}})
        assert result["event_context"] == {}
