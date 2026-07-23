"""RED tests for FR-640 novel_fandom enriched world model.

Tests:
- Character enriched fields validate (REQ-YG-484)
- Location enriched fields validate (REQ-YG-485)
- Rule page type validates and participates in gate (REQ-YG-486)
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

pytestmark = pytest.mark.process

NOVEL_FANDOM_DIR = (
    Path(__file__).parent.parent.parent / "examples" / "novel_fandom"
).resolve()

_nf_str = str(NOVEL_FANDOM_DIR)
if _nf_str not in sys.path:
    sys.path.insert(0, _nf_str)


def _load(mod_name: str, rel_path: str):  # noqa: ANN202
    """Load a module from examples/novel_fandom by file path."""
    fpath = NOVEL_FANDOM_DIR / rel_path
    spec = importlib.util.spec_from_file_location(mod_name, fpath)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


_canon = _load("novel_fandom_schema_canon", "schema/canon.py")
_gate = _load("novel_fandom_nodes_ref_gate", "nodes/ref_gate.py")

Character = _canon.Character
Location = _canon.Location
Rule = _canon.Rule
validate_page = _canon.validate_page
check_references = _gate.check_references


# --- Character enriched fields (REQ-YG-484) ---


class TestCharacterEnriched:
    """Character model accepts enriched motivation triad fields."""

    @pytest.mark.req("REQ-YG-484")
    def test_character_with_motivation_triad(self) -> None:
        """Character validates with all enriched fields populated."""
        data = {
            "type": "character",
            "id": "hero",
            "lane": "static",
            "name": "Hero",
            "role": "protagonist",
            "driving_force": "Revenge",
            "wants": "Power",
            "needs": "Forgiveness",
            "fears": ["failure", "betrayal"],
            "arc_summary": "avenger → forgiver",
            "triggers": ["If insulted → attacks"],
            "references": [],
        }
        char = Character.model_validate(data)
        assert char.role == "protagonist"
        assert char.wants == "Power"
        assert char.needs == "Forgiveness"
        assert len(char.fears) == 2
        assert len(char.triggers) == 1

    @pytest.mark.req("REQ-YG-484")
    def test_character_defaults_without_enriched_fields(self) -> None:
        """Character validates without enriched fields (all optional)."""
        data = {
            "type": "character",
            "id": "minimal",
            "lane": "dynamic",
            "name": "Minimal",
            "references": [],
        }
        char = Character.model_validate(data)
        assert char.role == "supporting"
        assert char.driving_force == ""
        assert char.wants == ""
        assert char.needs == ""
        assert char.fears == []
        assert char.arc_summary == ""
        assert char.triggers == []

    @pytest.mark.req("REQ-YG-484")
    def test_character_rejects_invalid_role(self) -> None:
        """Character rejects role value outside the allowed Literal."""
        data = {
            "type": "character",
            "id": "bad",
            "lane": "static",
            "name": "Bad",
            "role": "sidekick",
            "references": [],
        }
        with pytest.raises(ValidationError):
            Character.model_validate(data)


# --- Location enriched fields (REQ-YG-485) ---


class TestLocationEnriched:
    """Location model accepts enriched atmosphere/sensory fields."""

    @pytest.mark.req("REQ-YG-485")
    def test_location_with_enriched_fields(self) -> None:
        """Location validates with all enriched fields populated."""
        data = {
            "type": "location",
            "id": "forge",
            "lane": "static",
            "name": "The Forge",
            "location_type": "supernatural",
            "atmosphere": ["eerie", "hot"],
            "sensory": ["crackling flame", "sulfur smell"],
            "significance": "Where the Emberbrand was first forged",
            "references": [],
        }
        loc = Location.model_validate(data)
        assert loc.location_type == "supernatural"
        assert len(loc.atmosphere) == 2
        assert len(loc.sensory) == 2
        assert loc.significance != ""

    @pytest.mark.req("REQ-YG-485")
    def test_location_defaults_without_enriched_fields(self) -> None:
        """Location validates without enriched fields (all optional)."""
        data = {
            "type": "location",
            "id": "place",
            "lane": "dynamic",
            "name": "Place",
            "references": [],
        }
        loc = Location.model_validate(data)
        assert loc.location_type == ""
        assert loc.atmosphere == []
        assert loc.sensory == []
        assert loc.significance == ""

    @pytest.mark.req("REQ-YG-485")
    def test_location_type_accepts_any_string(self) -> None:
        """location_type is str, not Literal — any value accepted."""
        data = {
            "type": "location",
            "id": "ship",
            "lane": "dynamic",
            "name": "The Ship",
            "location_type": "airship",
            "references": [],
        }
        loc = Location.model_validate(data)
        assert loc.location_type == "airship"


# --- Rule page type (REQ-YG-486) ---


class TestRulePageType:
    """Rule model validates and participates in gate."""

    @pytest.mark.req("REQ-YG-486")
    def test_rule_validates(self) -> None:
        """Rule model accepts valid rule page."""
        data = {
            "type": "rule",
            "id": "no_fire",
            "lane": "static",
            "domain": "magic_system",
            "title": "No Fire in the Library",
            "description": "Fire spells are nullified within the Library walls.",
            "references": [],
        }
        rule = Rule.model_validate(data)
        assert rule.domain == "magic_system"
        assert rule.title == "No Fire in the Library"

    @pytest.mark.req("REQ-YG-486")
    def test_rule_rejects_invalid_domain(self) -> None:
        """Rule rejects domain value outside the allowed Literal."""
        data = {
            "type": "rule",
            "id": "bad",
            "lane": "static",
            "domain": "cooking",
            "title": "Bad",
            "references": [],
        }
        with pytest.raises(ValidationError):
            Rule.model_validate(data)

    @pytest.mark.req("REQ-YG-486")
    def test_rule_rejects_missing_title(self) -> None:
        """Rule rejects page missing required title."""
        data = {
            "type": "rule",
            "id": "bad",
            "lane": "static",
            "domain": "social_rule",
            "references": [],
        }
        with pytest.raises(ValidationError):
            Rule.model_validate(data)

    @pytest.mark.req("REQ-YG-486")
    def test_validate_page_dispatches_rule(self) -> None:
        """validate_page() routes rule type to Rule model."""
        data = {
            "type": "rule",
            "id": "test_rule",
            "lane": "static",
            "domain": "temporal_rule",
            "title": "Test",
            "references": [],
        }
        page = validate_page(data)
        assert isinstance(page, Rule)

    @pytest.mark.req("REQ-YG-486")
    def test_gate_rejects_orphan_rule_reference(self) -> None:
        """Gate rejects a rule page with orphan references."""
        state = {
            "drafted_page": {
                "type": "rule",
                "id": "new_rule",
                "lane": "dynamic",
                "domain": "physical_constraint",
                "title": "Gravity",
                "references": ["existing_char", "phantom_entity"],
            },
            "canon": {
                "existing_char": {"id": "existing_char", "type": "character"},
            },
        }
        result = check_references(state)
        assert result["gate_result"]["valid"] is False
        assert any("phantom_entity" in v for v in result["gate_result"]["violations"])

    @pytest.mark.req("REQ-YG-486")
    def test_gate_validates_rule_lane_immutability(self) -> None:
        """Gate rejects writes to existing static rule pages."""
        state = {
            "drafted_page": {
                "type": "rule",
                "id": "old_rule",
                "lane": "static",
                "domain": "social_rule",
                "title": "Updated",
                "references": [],
            },
            "canon": {
                "old_rule": {
                    "id": "old_rule",
                    "type": "rule",
                    "lane": "static",
                },
            },
        }
        result = check_references(state)
        assert result["gate_result"]["valid"] is False
        assert any("immutable" in v for v in result["gate_result"]["violations"])
