"""Tests for FR-651 through FR-654 worldgen improvements.

FR-651: Deepen prompt temporal field instructions
FR-652: Role enum normalization in normalize_page
FR-653: Flat-dict deepen output handled in persist_pages
FR-654: Seed depth-0 thin_score bonus in select_thin
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


_persist = _load("novel_fandom_nodes_persist_651", "nodes/persist_pages.py")
_canon = _load("novel_fandom_schema_canon_651", "schema/canon.py")
_select_path = NOVEL_FANDOM_DIR / "nodes/select_thin.py"
_select = (
    _load("novel_fandom_nodes_select_651", "nodes/select_thin.py")
    if _select_path.exists()
    else None
)

PAGE_MODELS = _canon.PAGE_MODELS
for m in PAGE_MODELS.values():
    m.model_rebuild()


# --- FR-651: Deepen prompt temporal instructions ---


class TestDeepenPromptTemporal:
    """FR-651: Deepen prompt includes temporal field instructions."""

    @pytest.mark.req("REQ-YG-501")
    def test_character_section_mentions_birth_year(self):
        prompt_path = NOVEL_FANDOM_DIR / "prompts" / "deepen_entity.yaml"
        content = prompt_path.read_text(encoding="utf-8")
        assert "birth_year" in content

    @pytest.mark.req("REQ-YG-501")
    def test_event_section_mentions_year(self):
        prompt_path = NOVEL_FANDOM_DIR / "prompts" / "deepen_entity.yaml"
        content = prompt_path.read_text(encoding="utf-8")
        assert "Set year (integer)" in content

    @pytest.mark.req("REQ-YG-501")
    def test_event_section_mentions_scope(self):
        prompt_path = NOVEL_FANDOM_DIR / "prompts" / "deepen_entity.yaml"
        content = prompt_path.read_text(encoding="utf-8")
        assert "Set scope:" in content

    @pytest.mark.req("REQ-YG-501")
    def test_event_section_mentions_affected_locations(self):
        prompt_path = NOVEL_FANDOM_DIR / "prompts" / "deepen_entity.yaml"
        content = prompt_path.read_text(encoding="utf-8")
        assert "affected_locations" in content


# --- FR-652: Role enum normalization ---


class TestNormalizeRole:
    """FR-652: normalize_page coerces invalid role to 'supporting'."""

    @pytest.mark.req("REQ-YG-502")
    def test_freetext_role_coerced_to_supporting(self):
        page = {"type": "character", "id": "x", "role": "Elder scholar"}
        _persist.normalize_page(page)
        assert page["role"] == "supporting"

    @pytest.mark.req("REQ-YG-502")
    def test_valid_role_unchanged(self):
        page = {"type": "character", "id": "x", "role": "antagonist"}
        _persist.normalize_page(page)
        assert page["role"] == "antagonist"

    @pytest.mark.req("REQ-YG-502")
    def test_missing_role_defaults_to_supporting(self):
        page = {"type": "character", "id": "x"}
        _persist.normalize_page(page)
        assert page["role"] == "supporting"

    @pytest.mark.req("REQ-YG-502")
    def test_non_character_role_not_touched(self):
        page = {"type": "event", "id": "x", "role": "whatever"}
        _persist.normalize_page(page)
        assert page["role"] == "whatever"


# --- FR-653: Flat-dict deepen output ---


class TestFlatDictDeepenOutput:
    """FR-653: persist_pages handles flat-dict deepen results."""

    @pytest.mark.req("REQ-YG-503")
    def test_flat_dict_deepened_persisted(self, tmp_path):
        """When deepen returns a flat page dict (no updated_page wrapper),
        persist_pages should still write it."""
        canon_dir = tmp_path / "canon"
        canon_dir.mkdir()
        state = {
            "deepened": [
                {
                    # Flat dict — no updated_page wrapper
                    "id": "flat_hero",
                    "type": "character",
                    "lane": "dynamic",
                    "name": "Flat Hero",
                    "depth": 1,
                }
            ],
            "skeletons": [],
        }
        result = _persist._persist_impl(state, canon_dir, PAGE_MODELS)
        assert result["written_count"] == 1
        assert (canon_dir / "character" / "flat_hero.yaml").exists()

    @pytest.mark.req("REQ-YG-503")
    def test_wrapped_dict_still_works(self, tmp_path):
        """Normal {updated_page, new_entities} shape still works."""
        canon_dir = tmp_path / "canon"
        canon_dir.mkdir()
        state = {
            "deepened": [
                {
                    "updated_page": {
                        "id": "wrapped_hero",
                        "type": "character",
                        "lane": "dynamic",
                        "name": "Wrapped Hero",
                    },
                    "new_entities": [],
                }
            ],
            "skeletons": [],
        }
        result = _persist._persist_impl(state, canon_dir, PAGE_MODELS)
        assert result["written_count"] == 1
        assert (canon_dir / "character" / "wrapped_hero.yaml").exists()


# --- FR-654: Seed depth-0 thin bonus ---


@pytest.mark.skipif(_select is None, reason="select_thin.py retired by FR-686")
class TestSeedDepthBonus:
    """FR-654: Depth-0 pages get thin_score bonus."""

    @pytest.mark.req("REQ-YG-504")
    def test_depth_0_gets_bonus(self):
        """A depth-0 character with 2 thin reasons gets score 2 + bonus."""
        state = {
            "canon_pages": {
                "seed_char": {
                    "id": "seed_char",
                    "type": "character",
                    "depth": 0,
                    "lane": "dynamic",
                },
            },
            "max_depth": 2,
        }
        result = _select.select_thin(state)
        entities = result["thin_entities"]
        assert len(entities) == 1
        # Should have reasons + _SEED_DEPTH_BONUS (2)
        assert entities[0]["thin_score"] >= 4  # 3 reasons + 2 bonus - at least

    @pytest.mark.req("REQ-YG-504")
    def test_depth_1_no_bonus(self):
        """A depth-1 character does NOT get the bonus."""
        state = {
            "canon_pages": {
                "deep_char": {
                    "id": "deep_char",
                    "type": "character",
                    "depth": 1,
                    "lane": "dynamic",
                },
            },
            "max_depth": 2,
        }
        result = _select.select_thin(state)
        entities = result["thin_entities"]
        assert len(entities) == 1
        # No bonus — just raw reason count
        assert entities[0]["thin_score"] == 3  # backstory, triggers, relationships

    @pytest.mark.req("REQ-YG-504")
    def test_missing_depth_gets_bonus(self):
        """Page without depth field also gets bonus (treated as seed)."""
        state = {
            "canon_pages": {
                "no_depth": {
                    "id": "no_depth",
                    "type": "character",
                    "lane": "dynamic",
                    # No depth field
                },
            },
            "max_depth": 2,
        }
        result = _select.select_thin(state)
        entities = result["thin_entities"]
        assert len(entities) == 1
        assert entities[0]["thin_score"] >= 4  # reasons + bonus

    @pytest.mark.req("REQ-YG-504")
    def test_seed_sorted_before_depth_1(self):
        """Seed pages sort before depth-1 pages with same reason count."""
        state = {
            "canon_pages": {
                "seed": {
                    "id": "seed",
                    "type": "character",
                    "depth": 0,
                    "lane": "dynamic",
                },
                "deep": {
                    "id": "deep",
                    "type": "character",
                    "depth": 1,
                    "lane": "dynamic",
                },
            },
            "max_depth": 2,
        }
        result = _select.select_thin(state)
        entities = result["thin_entities"]
        assert len(entities) == 2
        assert entities[0]["entity_id"] == "seed"
        assert entities[1]["entity_id"] == "deep"
