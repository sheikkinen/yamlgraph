"""Tests for FR-657 agentic event deepening with canon tools.

Tests:
- canon_tools: lookup_canon_page, list_canon_ids, validate_draft (REQ-YG-509)
- split_thin_by_type: partitions thin_entities by type (REQ-YG-509)
- worldgen.yaml lints clean with new nodes (REQ-YG-509)
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

NOVEL_FANDOM_DIR = (
    Path(__file__).parent.parent.parent / "examples" / "novel_fandom"
).resolve()
CANON_DIR = NOVEL_FANDOM_DIR / "canon"

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


_canon_tools = _load("novel_fandom_nodes_canon_tools", "nodes/canon_tools.py")
_split = _load("novel_fandom_nodes_split_thin", "nodes/split_thin_by_type.py")

lookup_canon_page = _canon_tools.lookup_canon_page
list_canon_ids = _canon_tools.list_canon_ids
validate_draft = _canon_tools.validate_draft
split_thin_by_type = _split.split_thin_by_type


# ── lookup_canon_page ─────────────────────────────────────────


@pytest.mark.req("REQ-YG-509")
class TestLookupCanonPage:
    """AC-1, AC-5: lookup returns full YAML + calendar header."""

    def test_returns_existing_page(self) -> None:
        result = lookup_canon_page(id="great_flood", canon_dir=str(CANON_DIR))
        assert "great_flood" in result
        assert "year: 0" in result

    def test_includes_calendar_convention(self) -> None:
        result = lookup_canon_page(id="great_flood", canon_dir=str(CANON_DIR))
        assert "Year 0" in result
        assert "negative" in result.lower() or "before" in result.lower()

    def test_nonexistent_id_returns_not_found(self) -> None:
        result = lookup_canon_page(id="does_not_exist", canon_dir=str(CANON_DIR))
        assert "not found" in result.lower()

    def test_returns_character_page(self) -> None:
        result = lookup_canon_page(id="hilde", canon_dir=str(CANON_DIR))
        assert "hilde" in result
        assert "character" in result


# ── list_canon_ids ────────────────────────────────────────────


@pytest.mark.req("REQ-YG-509")
class TestListCanonIds:
    """AC-1: list returns all IDs with types."""

    def test_returns_all_ids(self) -> None:
        result = list_canon_ids(canon_dir=str(CANON_DIR))
        # Should contain known IDs from the seed canon
        assert "hilde" in result
        assert "great_flood" in result
        assert "aschenwulf" in result

    def test_includes_types(self) -> None:
        result = list_canon_ids(canon_dir=str(CANON_DIR))
        assert "character" in result
        assert "event" in result
        assert "faction" in result


# ── validate_draft ────────────────────────────────────────────


@pytest.mark.req("REQ-YG-509")
class TestValidateDraft:
    """AC-1, AC-6: validate_draft returns {valid, errors}."""

    def test_valid_event_passes(self) -> None:
        draft = yaml.dump(
            {
                "id": "ashfall",
                "type": "event",
                "year": -28,
                "scope": "world",
                "participants": ["hilde", "gunnar"],
                "affected_locations": ["wittensee_valley"],
            }
        )
        result = validate_draft(page_yaml=draft, canon_dir=str(CANON_DIR))
        assert result["valid"] is True
        assert result["errors"] == []

    def test_rejects_positive_event_year(self) -> None:
        draft = yaml.dump(
            {
                "id": "ashfall",
                "type": "event",
                "year": 28,
                "scope": "world",
                "participants": ["hilde"],
                "affected_locations": ["wittensee_valley"],
            }
        )
        result = validate_draft(page_yaml=draft, canon_dir=str(CANON_DIR))
        assert result["valid"] is False
        assert any(
            "year" in e.lower() or "positive" in e.lower() for e in result["errors"]
        )

    def test_rejects_unknown_participant(self) -> None:
        draft = yaml.dump(
            {
                "id": "some_event",
                "type": "event",
                "year": -5,
                "scope": "local",
                "participants": ["hilde", "nonexistent_person"],
                "affected_locations": [],
            }
        )
        result = validate_draft(page_yaml=draft, canon_dir=str(CANON_DIR))
        assert result["valid"] is False
        assert any("nonexistent_person" in e for e in result["errors"])

    def test_rejects_duplicate_the_prefix_id(self) -> None:
        """great_flood exists, so the_great_flood should be flagged."""
        draft = yaml.dump(
            {
                "id": "the_great_flood",
                "type": "event",
            }
        )
        result = validate_draft(page_yaml=draft, canon_dir=str(CANON_DIR))
        assert result["valid"] is False
        assert any("duplicate" in e.lower() or "the_" in e for e in result["errors"])

    def test_returns_dict_with_valid_and_errors(self) -> None:
        draft = yaml.dump({"id": "test", "type": "event", "year": -1})
        result = validate_draft(page_yaml=draft, canon_dir=str(CANON_DIR))
        assert "valid" in result
        assert "errors" in result
        assert isinstance(result["valid"], bool)
        assert isinstance(result["errors"], list)


# ── split_thin_by_type ────────────────────────────────────────


@pytest.mark.req("REQ-YG-509")
class TestSplitThinByType:
    """AC-2: partitions thin_entities into thin_events and thin_other."""

    def test_splits_events_from_characters(self) -> None:
        thin = [
            {
                "entity_id": "e1",
                "entity_type": "event",
                "entity": {"id": "e1", "type": "event"},
            },
            {
                "entity_id": "c1",
                "entity_type": "character",
                "entity": {"id": "c1", "type": "character"},
            },
            {
                "entity_id": "e2",
                "entity_type": "event",
                "entity": {"id": "e2", "type": "event"},
            },
            {
                "entity_id": "l1",
                "entity_type": "location",
                "entity": {"id": "l1", "type": "location"},
            },
        ]
        result = split_thin_by_type({"thin_entities": thin})
        assert len(result["thin_events"]) == 2
        assert len(result["thin_other"]) == 2
        assert all(e["entity_type"] == "event" for e in result["thin_events"])
        assert all(e["entity_type"] != "event" for e in result["thin_other"])

    def test_empty_input(self) -> None:
        result = split_thin_by_type({"thin_entities": []})
        assert result["thin_events"] == []
        assert result["thin_other"] == []

    def test_all_events(self) -> None:
        thin = [
            {
                "entity_id": "e1",
                "entity_type": "event",
                "entity": {"id": "e1", "type": "event"},
            },
        ]
        result = split_thin_by_type({"thin_entities": thin})
        assert len(result["thin_events"]) == 1
        assert len(result["thin_other"]) == 0

    def test_no_events(self) -> None:
        thin = [
            {
                "entity_id": "c1",
                "entity_type": "character",
                "entity": {"id": "c1", "type": "character"},
            },
        ]
        result = split_thin_by_type({"thin_entities": thin})
        assert len(result["thin_events"]) == 0
        assert len(result["thin_other"]) == 1


# ── worldgen.yaml lints clean ─────────────────────────────────


@pytest.mark.req("REQ-YG-509")
def test_worldgen_yaml_lints_clean() -> None:
    """Updated worldgen.yaml with split/deepen_events/deepen_other must lint clean."""
    from yamlgraph.cli.graph_validate import lint_graph

    graph_path = NOVEL_FANDOM_DIR / "worldgen.yaml"
    result = lint_graph(str(graph_path))
    errors = [d for d in result.issues if d.severity == "error"]
    assert errors == [], f"Lint errors: {errors}"
