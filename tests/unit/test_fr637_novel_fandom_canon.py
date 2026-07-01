"""RED tests for FR-637 novel_fandom canon schema + gate.

Tests:
- Schema validation for all page types (REQ-YG-481)
- Orphan reference detection (REQ-YG-482)
- Lane-immutability rejection (REQ-YG-483)
- Seed canon integrity (all pages validate, no orphans)
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

# Load example-local modules via importlib to avoid name collisions with other
# 'nodes' and 'schema' packages in the workspace (e.g. projects/*/nodes/).
NOVEL_FANDOM_DIR = (
    Path(__file__).parent.parent.parent / "examples" / "novel_fandom"
).resolve()

# schema.canon needs pydantic which is already on sys.path.
# We add NOVEL_FANDOM_DIR so that the schema package's relative imports work.
_nf_str = str(NOVEL_FANDOM_DIR)
if _nf_str not in sys.path:
    sys.path.insert(0, _nf_str)


def _load(mod_name: str, rel_path: str):  # noqa: ANN202
    """Load a module from examples/novel_fandom by file path."""
    fpath = NOVEL_FANDOM_DIR / rel_path
    spec = importlib.util.spec_from_file_location(mod_name, fpath)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod  # register so sub-imports resolve
    spec.loader.exec_module(mod)
    return mod


_canon = _load("novel_fandom_schema_canon", "schema/canon.py")
_gate = _load("novel_fandom_nodes_ref_gate", "nodes/ref_gate.py")

Character = _canon.Character
Event = _canon.Event
Faction = _canon.Faction
Location = _canon.Location
validate_page = _canon.validate_page
check_references = _gate.check_references

# --- Fixtures ---


@pytest.fixture()
def seed_canon() -> dict[str, dict]:
    """Load all seed canon YAML files into a dict keyed by id."""
    canon_dir = NOVEL_FANDOM_DIR / "canon"
    canon: dict[str, dict] = {}
    for path in sorted(canon_dir.glob("*.yaml")):
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        canon[data["id"]] = data
    return canon


# --- Schema validation tests (REQ-YG-481) ---


class TestCanonSchema:
    """Pydantic models validate canon pages."""

    @pytest.mark.req("REQ-YG-481")
    def test_character_validates(self) -> None:
        """Character model accepts valid character page."""
        data = {
            "type": "character",
            "id": "test_char",
            "lane": "static",
            "name": "Test",
            "goals": ["survive"],
            "personality": "brave",
            "faction": "none",
            "relationships": [{"to": "other", "kind": "ally", "valence": "trust"}],
            "references": ["other"],
        }
        char = Character.model_validate(data)
        assert char.id == "test_char"
        assert char.goals == ["survive"]
        assert len(char.relationships) == 1

    @pytest.mark.req("REQ-YG-481")
    def test_event_validates(self) -> None:
        """Event model accepts valid event page."""
        data = {
            "type": "event",
            "id": "battle",
            "lane": "dynamic",
            "window": "age_1",
            "participants": ["a", "b"],
            "consequences": ["a wins"],
            "valid_from": "2026-01-01",
            "valid_to": None,
            "references": ["a", "b"],
        }
        event = Event.model_validate(data)
        assert event.window == "age_1"
        assert event.valid_to is None

    @pytest.mark.req("REQ-YG-481")
    def test_faction_validates(self) -> None:
        """Faction model accepts valid faction page."""
        data = {
            "type": "faction",
            "id": "guild",
            "lane": "static",
            "name": "The Guild",
            "description": "A guild",
            "members": ["a"],
            "references": ["a"],
        }
        faction = Faction.model_validate(data)
        assert faction.name == "The Guild"

    @pytest.mark.req("REQ-YG-481")
    def test_location_validates(self) -> None:
        """Location model accepts valid location page."""
        data = {
            "type": "location",
            "id": "forge",
            "lane": "static",
            "name": "The Forge",
            "description": "Ancient forge",
            "references": [],
        }
        location = Location.model_validate(data)
        assert location.name == "The Forge"

    @pytest.mark.req("REQ-YG-481")
    def test_character_rejects_missing_required(self) -> None:
        """Character model rejects page missing required fields."""
        data = {"type": "character", "lane": "static"}  # missing id, name
        with pytest.raises(ValidationError):
            Character.model_validate(data)

    @pytest.mark.req("REQ-YG-481")
    def test_character_rejects_invalid_lane(self) -> None:
        """Character model rejects invalid lane value."""
        data = {
            "type": "character",
            "id": "x",
            "lane": "invalid",
            "name": "X",
        }
        with pytest.raises(ValidationError):
            Character.model_validate(data)

    @pytest.mark.req("REQ-YG-481")
    def test_validate_page_dispatches_by_type(self) -> None:
        """validate_page() routes to correct model by type field."""
        data = {
            "type": "faction",
            "id": "test",
            "lane": "static",
            "name": "Test",
            "references": [],
        }
        page = validate_page(data)
        assert isinstance(page, Faction)

    @pytest.mark.req("REQ-YG-481")
    def test_validate_page_rejects_unknown_type(self) -> None:
        """validate_page() raises on unknown type."""
        with pytest.raises(ValueError, match="Unknown page type"):
            validate_page({"type": "spaceship", "id": "x"})

    @pytest.mark.req("REQ-YG-481")
    def test_all_seed_pages_validate(self, seed_canon: dict[str, dict]) -> None:
        """Every seed canon page validates against its Pydantic model."""
        assert len(seed_canon) >= 8, f"Expected ≥8 seed pages, got {len(seed_canon)}"
        for page_id, data in seed_canon.items():
            page = validate_page(data)
            assert page.id == page_id


# --- Reference gate tests (REQ-YG-482) ---


class TestReferenceGate:
    """Gate rejects orphan references."""

    @pytest.mark.req("REQ-YG-482")
    def test_valid_references_pass(self) -> None:
        """Page with all references resolving passes the gate."""
        state = {
            "drafted_page": {
                "type": "character",
                "id": "new_char",
                "lane": "dynamic",
                "references": ["existing_a", "existing_b"],
            },
            "canon": {
                "existing_a": {"id": "existing_a", "type": "faction"},
                "existing_b": {"id": "existing_b", "type": "faction"},
            },
        }
        result = check_references(state)
        assert result["gate_result"]["valid"] is True
        assert result["gate_result"]["violations"] == []

    @pytest.mark.req("REQ-YG-482")
    def test_orphan_reference_rejected(self) -> None:
        """Page with a reference to non-existent entity is rejected."""
        state = {
            "drafted_page": {
                "type": "character",
                "id": "new_char",
                "lane": "dynamic",
                "references": ["existing_a", "phantom"],
            },
            "canon": {
                "existing_a": {"id": "existing_a", "type": "faction"},
            },
        }
        result = check_references(state)
        assert result["gate_result"]["valid"] is False
        assert any("phantom" in v for v in result["gate_result"]["violations"])

    @pytest.mark.req("REQ-YG-482")
    def test_seed_canon_no_orphans(self, seed_canon: dict[str, dict]) -> None:
        """Every seed canon page passes reference check (no orphans).

        Excludes the page under test from the existing canon to avoid
        lane-immutability false positives — we're testing references, not lanes.
        """
        for page_id, data in seed_canon.items():
            # Simulate "this page doesn't exist yet" by removing it from canon
            canon_without_self = {k: v for k, v in seed_canon.items() if k != page_id}
            state = {"drafted_page": data, "canon": canon_without_self}
            result = check_references(state)
            # Filter to only orphan violations (ignore lane violations for this test)
            orphan_violations = [
                v for v in result["gate_result"]["violations"] if "orphan" in v
            ]
            assert (
                not orphan_violations
            ), f"Seed page '{page_id}' has orphan references: {orphan_violations}"


# --- Lane immutability tests (REQ-YG-483) ---


class TestLaneImmutability:
    """Gate rejects writes to existing lane:static pages."""

    @pytest.mark.req("REQ-YG-483")
    def test_static_page_write_rejected(self) -> None:
        """Writing to an existing lane:static page is rejected."""
        state = {
            "drafted_page": {
                "type": "character",
                "id": "kaelen",
                "lane": "static",
                "references": [],
            },
            "canon": {
                "kaelen": {
                    "id": "kaelen",
                    "type": "character",
                    "lane": "static",
                },
            },
        }
        result = check_references(state)
        assert result["gate_result"]["valid"] is False
        assert any("immutable" in v for v in result["gate_result"]["violations"])

    @pytest.mark.req("REQ-YG-483")
    def test_dynamic_page_write_allowed(self) -> None:
        """Writing to an existing lane:dynamic page is allowed."""
        state = {
            "drafted_page": {
                "type": "event",
                "id": "battle",
                "lane": "dynamic",
                "references": [],
            },
            "canon": {
                "battle": {
                    "id": "battle",
                    "type": "event",
                    "lane": "dynamic",
                },
            },
        }
        result = check_references(state)
        assert result["gate_result"]["valid"] is True

    @pytest.mark.req("REQ-YG-483")
    def test_new_page_write_allowed(self) -> None:
        """Writing a brand new page (not in canon) is allowed."""
        state = {
            "drafted_page": {
                "type": "location",
                "id": "new_place",
                "lane": "dynamic",
                "references": [],
            },
            "canon": {},
        }
        result = check_references(state)
        assert result["gate_result"]["valid"] is True
