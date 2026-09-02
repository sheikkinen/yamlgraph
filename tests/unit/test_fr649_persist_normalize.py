"""Tests for FR-649 persist_pages normalize at boundary.

Covers: relationship variants, participant dicts, consequence dicts,
reference dicts, scalar→list coercion, Rule.domain default,
_map_index strip, persist-with-warning fallback.
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


_persist = _load("novel_fandom_nodes_persist_649", "nodes/persist_pages.py")
_canon = _load("novel_fandom_schema_canon_649", "schema/canon.py")

PAGE_MODELS = _canon.PAGE_MODELS
for m in PAGE_MODELS.values():
    m.model_rebuild()


# --- normalize_page tests ---


class TestNormalizeRelationships:
    """FR-649: Relationship normalization from LLM-varied shapes."""

    @pytest.mark.req("REQ-YG-499")
    def test_target_id_to_to(self):
        """LLM returns {target_id, type, description} -> {to, kind, valence}."""
        page = {
            "type": "character",
            "id": "x",
            "lane": "dynamic",
            "name": "X",
            "relationships": [
                {"target_id": "kaelen", "type": "mentor", "description": "teaches"},
            ],
        }
        result = _persist.normalize_page(page)
        rel = result["relationships"][0]
        assert rel["to"] == "kaelen"
        assert rel["kind"] == "mentor"
        _canon.Character(**result)  # must validate

    @pytest.mark.req("REQ-YG-499")
    def test_id_description_to_to(self):
        """LLM returns {id, description} -> {to, kind, valence}."""
        page = {
            "type": "character",
            "id": "x",
            "lane": "dynamic",
            "name": "X",
            "relationships": [
                {"id": "maren", "description": "reluctant ally"},
            ],
        }
        result = _persist.normalize_page(page)
        rel = result["relationships"][0]
        assert rel["to"] == "maren"
        assert rel["kind"] == "reluctant ally"
        _canon.Character(**result)

    @pytest.mark.req("REQ-YG-499")
    def test_dict_of_strings_relationships(self):
        """LLM returns dict[str, str] for relationships (ashguard faction)."""
        page = {
            "type": "character",
            "id": "x",
            "lane": "dynamic",
            "name": "X",
            "relationships": {"emberwrights": "former allies", "voss": "traitor"},
        }
        result = _persist.normalize_page(page)
        assert isinstance(result["relationships"], list)
        assert len(result["relationships"]) == 2
        assert result["relationships"][0]["to"] == "emberwrights"
        _canon.Character(**result)

    @pytest.mark.req("REQ-YG-499")
    def test_target_key_relationship(self):
        """LLM returns {target, type, description}."""
        page = {
            "type": "character",
            "id": "x",
            "lane": "dynamic",
            "name": "X",
            "relationships": [
                {"target": "voss", "type": "rival", "description": "bitter"},
            ],
        }
        result = _persist.normalize_page(page)
        assert result["relationships"][0]["to"] == "voss"
        _canon.Character(**result)

    @pytest.mark.req("REQ-YG-499")
    def test_seed_format_unchanged(self):
        """Seed format {to, kind, valence} passes through untouched."""
        page = {
            "type": "character",
            "id": "x",
            "lane": "dynamic",
            "name": "X",
            "relationships": [
                {"to": "maren", "kind": "mentor", "valence": "trust"},
            ],
        }
        result = _persist.normalize_page(page)
        assert result["relationships"][0] == {
            "to": "maren",
            "kind": "mentor",
            "valence": "trust",
        }
        _canon.Character(**result)


class TestNormalizeParticipants:
    """FR-649: Event.participants normalization."""

    @pytest.mark.req("REQ-YG-499")
    def test_dict_participants_to_strings(self):
        """LLM returns list[dict] with entity key."""
        page = {
            "type": "event",
            "id": "e1",
            "lane": "dynamic",
            "participants": [
                {"entity": "ashguard", "role": "defenders"},
                {"entity": "emberwrights", "role": "attackers"},
            ],
        }
        result = _persist.normalize_page(page)
        assert result["participants"] == ["ashguard", "emberwrights"]
        _canon.Event(**result)

    @pytest.mark.req("REQ-YG-499")
    def test_string_participants_unchanged(self):
        """Seed format list[str] passes through."""
        page = {
            "type": "event",
            "id": "e1",
            "lane": "dynamic",
            "participants": ["kaelen", "maren"],
        }
        result = _persist.normalize_page(page)
        assert result["participants"] == ["kaelen", "maren"]


class TestNormalizeConsequences:
    """FR-649: Event.consequences normalization."""

    @pytest.mark.req("REQ-YG-499")
    def test_dict_consequences_to_list(self):
        """LLM returns dict with faction-keyed consequences."""
        page = {
            "type": "event",
            "id": "e1",
            "lane": "dynamic",
            "consequences": {
                "ashguard": "Lost their stronghold",
                "emberwrights": "Went into hiding",
            },
        }
        result = _persist.normalize_page(page)
        assert isinstance(result["consequences"], list)
        assert len(result["consequences"]) == 2
        assert "ashguard" in result["consequences"][0]
        _canon.Event(**result)

    @pytest.mark.req("REQ-YG-499")
    def test_string_consequences_unchanged(self):
        """Seed format list[str] passes through."""
        page = {
            "type": "event",
            "id": "e1",
            "lane": "dynamic",
            "consequences": ["The old forge lies dormant"],
        }
        result = _persist.normalize_page(page)
        assert result["consequences"] == ["The old forge lies dormant"]


class TestNormalizeReferences:
    """FR-649: references normalization from dicts to strings."""

    @pytest.mark.req("REQ-YG-499")
    def test_dict_references_pageId(self):
        """LLM returns list[dict] with pageId key."""
        page = {
            "type": "location",
            "id": "loc1",
            "lane": "dynamic",
            "name": "Cave",
            "references": [
                {"pageId": "aldric_vane", "type": "inhabitant"},
                {"pageId": "the_archive", "type": "source"},
            ],
        }
        result = _persist.normalize_page(page)
        assert result["references"] == ["aldric_vane", "the_archive"]
        _canon.Location(**result)

    @pytest.mark.req("REQ-YG-499")
    def test_dict_references_id(self):
        """LLM returns list[dict] with id key."""
        page = {
            "type": "location",
            "id": "loc1",
            "lane": "dynamic",
            "name": "Cave",
            "references": [{"id": "ashguard"}, {"id": "emberwrights"}],
        }
        result = _persist.normalize_page(page)
        assert result["references"] == ["ashguard", "emberwrights"]

    @pytest.mark.req("REQ-YG-499")
    def test_string_references_unchanged(self):
        """Seed format list[str] passes through."""
        page = {
            "type": "location",
            "id": "loc1",
            "lane": "dynamic",
            "name": "Cave",
            "references": ["ashguard", "emberwrights"],
        }
        result = _persist.normalize_page(page)
        assert result["references"] == ["ashguard", "emberwrights"]


class TestNormalizeScalarToList:
    """FR-649: Scalar/list mismatch coercion."""

    @pytest.mark.req("REQ-YG-499")
    def test_atmosphere_string_to_list(self):
        """LLM returns str for atmosphere (schema expects list[str])."""
        page = {
            "type": "location",
            "id": "loc1",
            "lane": "dynamic",
            "name": "Cave",
            "atmosphere": "Dark and cold",
        }
        result = _persist.normalize_page(page)
        assert result["atmosphere"] == ["Dark and cold"]
        _canon.Location(**result)

    @pytest.mark.req("REQ-YG-499")
    def test_sensory_string_to_list(self):
        """LLM returns str for sensory."""
        page = {
            "type": "location",
            "id": "loc1",
            "lane": "dynamic",
            "name": "Cave",
            "sensory": "echoes of dripping water",
        }
        result = _persist.normalize_page(page)
        assert result["sensory"] == ["echoes of dripping water"]


class TestNormalizeRuleDomain:
    """FR-649: Rule.domain default for unrecognized values."""

    @pytest.mark.req("REQ-YG-499")
    def test_missing_domain_defaults(self):
        """Missing domain defaults to social_rule."""
        page = {
            "type": "rule",
            "id": "r1",
            "lane": "dynamic",
            "title": "Forge-Singer",
        }
        result = _persist.normalize_page(page)
        assert result["domain"] == "social_rule"
        _canon.Rule(**result)

    @pytest.mark.req("REQ-YG-499")
    def test_unrecognized_domain_defaults(self):
        """Unrecognized domain defaults to social_rule."""
        page = {
            "type": "rule",
            "id": "r1",
            "lane": "dynamic",
            "title": "Something",
            "domain": "guild_tradition",
        }
        result = _persist.normalize_page(page)
        assert result["domain"] == "social_rule"
        _canon.Rule(**result)

    @pytest.mark.req("REQ-YG-499")
    def test_valid_domain_unchanged(self):
        """Valid domain passes through."""
        page = {
            "type": "rule",
            "id": "r1",
            "lane": "dynamic",
            "title": "Emberbrand",
            "domain": "magic_system",
        }
        result = _persist.normalize_page(page)
        assert result["domain"] == "magic_system"


class TestNormalizeMapIndex:
    """FR-649: _map_index strip."""

    @pytest.mark.req("REQ-YG-499")
    def test_map_index_stripped(self):
        """_map_index is removed from page dict."""
        page = {
            "type": "character",
            "id": "x",
            "lane": "dynamic",
            "name": "X",
            "_map_index": 3,
        }
        result = _persist.normalize_page(page)
        assert "_map_index" not in result
        _canon.Character(**result)


class TestPersistFallback:
    """FR-649: Persist-with-warning fallback for pages that still fail validation."""

    @pytest.mark.req("REQ-YG-499")
    def test_invalid_page_still_persisted(self, tmp_path):
        """Page that fails validation after normalize is still written."""
        state = {
            "deepened": [
                {
                    "updated_page": {
                        "type": "character",
                        "id": "broken_char",
                        "lane": "dynamic",
                        "name": "Broken",
                        # triggers is a list but we pass a dict — unusual shape
                        "triggers": {"x": "y"},
                    },
                },
            ],
            "skeletons": [],
        }
        result = _persist._persist_impl(state, tmp_path, PAGE_MODELS)
        assert result["written_count"] >= 1
        # FR-650: pages now land in type subfolder
        written = tmp_path / "character" / "broken_char.yaml"
        assert written.exists()
        data = yaml.safe_load(written.read_text(encoding="utf-8"))
        assert data["id"] == "broken_char"
