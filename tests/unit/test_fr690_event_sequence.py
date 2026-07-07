"""FR-690: Event sequence field for intra-year ordering (REQ-YG-523).

The Floodmark canon needs a canonical total order over events so the story
pipeline's throughline walk (FR-691) and chapter plan (FR-694) do not each
invent their own ordering. `check_event_sequence` enforces completeness,
uniqueness, and year/sequence consistency.

RED contract: the real Floodmark canon must pass the check (fails before the
22 events are backfilled); the fixture tests condemn each violation class.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest
import yaml

NOVEL_FANDOM_DIR = (
    Path(__file__).parent.parent.parent / "examples" / "novel_fandom"
).resolve()
_nf_str = str(NOVEL_FANDOM_DIR)
if _nf_str not in sys.path:
    sys.path.insert(0, _nf_str)


def _load(mod_name: str, rel_path: str) -> ModuleType:
    fpath = NOVEL_FANDOM_DIR / rel_path
    spec = importlib.util.spec_from_file_location(mod_name, fpath)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


_seq = _load("novel_fandom_nodes_event_sequence", "nodes/event_sequence.py")
_canon = _load("novel_fandom_schema_canon", "schema/canon.py")

check_event_sequence = _seq.check_event_sequence
Event = _canon.Event


def _load_events() -> list[dict]:
    """Load all Floodmark event pages."""
    event_dir = NOVEL_FANDOM_DIR / "canon" / "event"
    events: list[dict] = []
    for path in sorted(event_dir.glob("*.yaml")):
        with open(path, encoding="utf-8") as f:
            events.append(yaml.safe_load(f))
    return events


class TestSchemaSequenceField:
    """Event schema carries an optional sequence field (REQ-YG-523)."""

    @pytest.mark.req("REQ-YG-523")
    def test_event_accepts_sequence(self) -> None:
        ev = Event.model_validate(
            {"id": "e", "lane": "static", "type": "event", "sequence": 10}
        )
        assert ev.sequence == 10

    @pytest.mark.req("REQ-YG-523")
    def test_event_sequence_optional(self) -> None:
        """Genesis/create_event emit no sequence — must still validate."""
        ev = Event.model_validate({"id": "e", "lane": "static", "type": "event"})
        assert ev.sequence is None


class TestCheckFunctionFixtures:
    """check_event_sequence condemns each violation class."""

    @pytest.mark.req("REQ-YG-523")
    def test_missing_sequence_fails(self) -> None:
        result = check_event_sequence(
            [
                {"id": "a", "sequence": 10, "year": 0},
                {"id": "b", "year": 0},
            ]
        )
        assert result["valid"] is False
        assert any("missing" in v for v in result["violations"])

    @pytest.mark.req("REQ-YG-523")
    def test_duplicate_sequence_fails(self) -> None:
        result = check_event_sequence(
            [
                {"id": "a", "sequence": 10, "year": 0},
                {"id": "b", "sequence": 10, "year": 0},
            ]
        )
        assert result["valid"] is False
        assert any("duplicate" in v for v in result["violations"])

    @pytest.mark.req("REQ-YG-523")
    def test_year_sequence_contradiction_fails(self) -> None:
        # b is a later year but an earlier sequence — contradiction.
        result = check_event_sequence(
            [
                {"id": "a", "sequence": 20, "year": 0},
                {"id": "b", "sequence": 10, "year": 1},
            ]
        )
        assert result["valid"] is False
        assert any("contradiction" in v for v in result["violations"])

    @pytest.mark.req("REQ-YG-523")
    def test_valid_ordering_passes(self) -> None:
        result = check_event_sequence(
            [
                {"id": "a", "sequence": 10, "year": -3},
                {"id": "b", "sequence": 20, "year": 0},
                {"id": "c", "sequence": 30, "year": 0},
                {"id": "d", "sequence": 40, "year": 1},
            ]
        )
        assert result["valid"] is True
        assert result["violations"] == []

    @pytest.mark.req("REQ-YG-523")
    def test_bool_sequence_rejected(self) -> None:
        """True is an int in Python — must not count as a valid sequence."""
        result = check_event_sequence([{"id": "a", "sequence": True, "year": 0}])
        assert result["valid"] is False


class TestFloodmarkCanonSequenced:
    """The real Floodmark canon satisfies the total-order invariant."""

    @pytest.mark.req("REQ-YG-523")
    def test_all_events_have_sequence(self) -> None:
        events = _load_events()
        missing = [e["id"] for e in events if e.get("sequence") is None]
        assert missing == [], f"events without sequence: {missing}"

    @pytest.mark.req("REQ-YG-523")
    def test_canon_passes_sequence_check(self) -> None:
        events = _load_events()
        result = check_event_sequence(events)
        assert result["valid"] is True, result["violations"]

    @pytest.mark.req("REQ-YG-523")
    def test_sequences_unique_and_gapped(self) -> None:
        events = _load_events()
        seqs = sorted(e["sequence"] for e in events if e.get("sequence") is not None)
        assert len(seqs) == len(set(seqs)), "sequences not unique"
        assert len(seqs) == 22, f"expected 22 sequenced events, got {len(seqs)}"
