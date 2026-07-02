"""RED tests for FR-642 novel_fandom wiki core types (Premise + Synopsis).

Tests:
- Premise page type validates (REQ-YG-492)
- Synopsis page type validates and references premise (REQ-YG-493)
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

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

validate_page = _canon.validate_page
Premise = _canon.Premise
Synopsis = _canon.Synopsis
check_references = _gate.check_references


# --- Premise page type (REQ-YG-492) ---


class TestPremise:
    """Premise page type validates correctly."""

    @pytest.mark.req("REQ-YG-492")
    def test_premise_validates(self) -> None:
        """Premise model accepts valid premise page."""
        data = {
            "type": "premise",
            "id": "test_premise",
            "lane": "static",
            "text": "A world scarred by ancient fire.",
        }
        page = validate_page(data)
        assert page.type == "premise"
        assert page.text == "A world scarred by ancient fire."

    @pytest.mark.req("REQ-YG-492")
    def test_premise_with_optional_fields(self) -> None:
        """Premise validates with genre_tags, era, themes populated."""
        data = {
            "type": "premise",
            "id": "test_premise_full",
            "lane": "static",
            "text": "A world scarred by ancient fire.",
            "genre_tags": ["fantasy", "drama"],
            "era": "post-cataclysm",
            "themes": ["guilt", "redemption", "legacy"],
        }
        page = validate_page(data)
        assert page.genre_tags == ["fantasy", "drama"]
        assert page.era == "post-cataclysm"
        assert page.themes == ["guilt", "redemption", "legacy"]

    @pytest.mark.req("REQ-YG-492")
    def test_premise_rejects_missing_text(self) -> None:
        """Premise requires text field."""
        data = {
            "type": "premise",
            "id": "test_premise_no_text",
            "lane": "static",
        }
        with pytest.raises(ValidationError):
            validate_page(data)

    @pytest.mark.req("REQ-YG-492")
    def test_premise_rejects_bad_lane(self) -> None:
        """Premise rejects invalid lane values."""
        data = {
            "type": "premise",
            "id": "test_premise_bad_lane",
            "lane": "frozen",
            "text": "Some text",
        }
        with pytest.raises(ValidationError):
            validate_page(data)

    @pytest.mark.req("REQ-YG-492")
    def test_premise_in_page_models(self) -> None:
        """Premise is registered in PAGE_MODELS."""
        assert "premise" in _canon.PAGE_MODELS


# --- Synopsis page type (REQ-YG-493) ---


class TestSynopsis:
    """Synopsis page type validates correctly."""

    @pytest.mark.req("REQ-YG-493")
    def test_synopsis_validates(self) -> None:
        """Synopsis model accepts valid synopsis page."""
        data = {
            "type": "synopsis",
            "id": "test_synopsis",
            "lane": "dynamic",
            "text": "The full story unfolds as follows...",
            "references": ["test_premise"],
        }
        page = validate_page(data)
        assert page.type == "synopsis"
        assert page.text == "The full story unfolds as follows..."
        assert "test_premise" in page.references

    @pytest.mark.req("REQ-YG-493")
    def test_synopsis_rejects_missing_text(self) -> None:
        """Synopsis requires text field."""
        data = {
            "type": "synopsis",
            "id": "test_synopsis_no_text",
            "lane": "dynamic",
            "references": ["test_premise"],
        }
        with pytest.raises(ValidationError):
            validate_page(data)

    @pytest.mark.req("REQ-YG-493")
    def test_synopsis_rejects_bad_lane(self) -> None:
        """Synopsis rejects invalid lane values."""
        data = {
            "type": "synopsis",
            "id": "test_synopsis_bad_lane",
            "lane": "frozen",
            "text": "Some text",
        }
        with pytest.raises(ValidationError):
            validate_page(data)

    @pytest.mark.req("REQ-YG-493")
    def test_synopsis_in_page_models(self) -> None:
        """Synopsis is registered in PAGE_MODELS."""
        assert "synopsis" in _canon.PAGE_MODELS


# --- Seed canon integrity (both REQs) ---


class TestSeedCanonWithWikiCore:
    """Seed canon includes premise and synopsis pages."""

    @pytest.fixture()
    def seed_canon(self) -> dict[str, dict]:
        """Load all seed canon YAML files into a dict keyed by id."""
        canon_dir = NOVEL_FANDOM_DIR / "canon"
        canon: dict[str, dict] = {}
        for path in sorted(canon_dir.rglob("*.yaml")):
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            canon[data["id"]] = data
        return canon

    @pytest.mark.req("REQ-YG-492")
    def test_seed_has_premise(self, seed_canon: dict[str, dict]) -> None:
        """Seed canon contains at least one premise page."""
        premise_pages = [p for p in seed_canon.values() if p.get("type") == "premise"]
        assert len(premise_pages) >= 1, "No premise page in seed canon"

    @pytest.mark.req("REQ-YG-493")
    def test_seed_has_synopsis(self, seed_canon: dict[str, dict]) -> None:
        """Seed canon contains at least one synopsis page."""
        synopsis_pages = [p for p in seed_canon.values() if p.get("type") == "synopsis"]
        assert len(synopsis_pages) >= 1, "No synopsis page in seed canon"

    @pytest.mark.req("REQ-YG-493")
    def test_seed_synopsis_references_premise(
        self, seed_canon: dict[str, dict]
    ) -> None:
        """Seed synopsis page references the premise."""
        synopsis_pages = [p for p in seed_canon.values() if p.get("type") == "synopsis"]
        assert synopsis_pages, "No synopsis found"
        synopsis = synopsis_pages[0]
        premise_ids = [
            p["id"] for p in seed_canon.values() if p.get("type") == "premise"
        ]
        assert any(
            ref in premise_ids for ref in synopsis.get("references", [])
        ), f"Synopsis does not reference any premise. refs={synopsis.get('references')}"

    @pytest.mark.req("REQ-YG-492")
    def test_seed_count_at_least_10(self, seed_canon: dict[str, dict]) -> None:
        """Seed canon has at least 10 pages (8 original + premise + synopsis)."""
        assert len(seed_canon) >= 10, f"Expected ≥10 seed pages, got {len(seed_canon)}"

    @pytest.mark.req("REQ-YG-493")
    def test_seed_synopsis_passes_gate(self, seed_canon: dict[str, dict]) -> None:
        """Synopsis page passes ref_gate (no orphan references)."""
        synopsis_pages = [p for p in seed_canon.values() if p.get("type") == "synopsis"]
        assert synopsis_pages, "No synopsis found"
        synopsis = synopsis_pages[0]
        canon_without_self = {
            k: v for k, v in seed_canon.items() if k != synopsis["id"]
        }
        state = {"drafted_page": synopsis, "canon": canon_without_self}
        result = check_references(state)
        orphans = [v for v in result["gate_result"]["violations"] if "orphan" in v]
        assert not orphans, f"Synopsis has orphan references: {orphans}"
