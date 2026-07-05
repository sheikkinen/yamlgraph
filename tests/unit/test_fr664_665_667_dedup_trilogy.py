"""Tests for FR-664, FR-665, FR-667 — genesis/worldgen duplicate fix trilogy.

REQ-YG-512: Genesis referential integrity validation
REQ-YG-513: Genesis stub pipeline (2 LLM calls)
REQ-YG-514: Worldgen semantic entity dedup
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


_persist_genesis = _load("nf_persist_genesis_664", "nodes/persist_genesis.py")
_dedup_entities = _load("nf_dedup_entities_665", "nodes/dedup_entities.py")


# ---------- FR-664: Referential Integrity ----------


class TestReferentialIntegrity:
    """FR-664: validate_referential_integrity catches orphan IDs."""

    @pytest.mark.req("REQ-YG-512")
    def test_valid_canon_passes(self) -> None:
        pages = [
            {
                "id": "hilde",
                "type": "character",
                "relationships": [{"to": "gunnar", "kind": "ally"}],
            },
            {"id": "gunnar", "type": "character", "participants": []},
            {"id": "flood", "type": "event", "participants": ["hilde", "gunnar"]},
        ]
        result = _persist_genesis.validate_referential_integrity(pages)
        assert result["valid"] is True
        assert result["orphan_ids"] == []

    @pytest.mark.req("REQ-YG-512")
    def test_orphan_relationship_to(self) -> None:
        pages = [
            {
                "id": "hilde",
                "type": "character",
                "relationships": [{"to": "aldric", "kind": "father"}],
            },
        ]
        result = _persist_genesis.validate_referential_integrity(pages)
        assert result["valid"] is False
        assert "aldric" in result["orphan_ids"]

    @pytest.mark.req("REQ-YG-512")
    def test_orphan_participant(self) -> None:
        pages = [
            {"id": "flood", "type": "event", "participants": ["hilde", "ghost"]},
            {"id": "hilde", "type": "character"},
        ]
        result = _persist_genesis.validate_referential_integrity(pages)
        assert result["valid"] is False
        assert "ghost" in result["orphan_ids"]

    @pytest.mark.req("REQ-YG-512")
    def test_orphan_reference(self) -> None:
        pages = [
            {"id": "hilde", "type": "character", "references": ["missing_rule"]},
        ]
        result = _persist_genesis.validate_referential_integrity(pages)
        assert result["valid"] is False
        assert "missing_rule" in result["orphan_ids"]

    @pytest.mark.req("REQ-YG-512")
    def test_orphan_member(self) -> None:
        pages = [
            {"id": "clan", "type": "faction", "members": ["hilde", "phantom"]},
            {"id": "hilde", "type": "character"},
        ]
        result = _persist_genesis.validate_referential_integrity(pages)
        assert result["valid"] is False
        assert "phantom" in result["orphan_ids"]

    @pytest.mark.req("REQ-YG-512")
    def test_orphan_affected_location(self) -> None:
        pages = [
            {
                "id": "flood",
                "type": "event",
                "affected_locations": ["high_valley", "lost_city"],
            },
            {"id": "high_valley", "type": "location"},
        ]
        result = _persist_genesis.validate_referential_integrity(pages)
        assert result["valid"] is False
        assert "lost_city" in result["orphan_ids"]

    @pytest.mark.req("REQ-YG-512")
    def test_persist_logs_warnings(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """persist_genesis logs orphan warnings but still writes."""
        _persist_pages = _load("nf_persist_pages_664", "nodes/persist_pages.py")
        _canon = _load("nf_canon_664", "schema/canon.py")
        page_models = _canon.PAGE_MODELS
        for m in page_models.values():
            m.model_rebuild()

        world = {
            "characters": [
                {
                    "type": "character",
                    "id": "hilde",
                    "name": "Hilde",
                    "birth_year": -25,
                    "role": "protagonist",
                    "faction": "aschenwulf",
                    "lane": "dynamic",
                    "depth": 0,
                    "relationships": [{"to": "ghost_dad", "kind": "father"}],
                },
            ],
            "events": [],
            "factions": [],
            "rules": [],
            "locations": [],
        }
        state = {"structured_world": world}
        import logging

        with caplog.at_level(logging.WARNING):
            result = _persist_genesis._persist_genesis_impl(
                state, tmp_path, page_models
            )
        assert result["written_count"] == 1
        assert "ghost_dad" in caplog.text


# ---------- FR-667: Genesis Stub Pipeline ----------


class TestGenesisStubPipeline:
    """FR-667: genesis.yaml is streamlined to 2 LLM calls."""

    @pytest.mark.req("REQ-YG-513")
    def test_genesis_graph_structure(self) -> None:
        """Genesis graph has 6 nodes: load, synopsis, stubs, validate, fix_stubs, persist."""
        graph_path = NOVEL_FANDOM_DIR / "genesis.yaml"
        with open(graph_path) as f:
            config = yaml.safe_load(f)
        node_names = set(config["nodes"].keys())
        assert node_names == {
            "load",
            "synopsis",
            "stubs",
            "validate",
            "fix_stubs",
            "persist",
        }

    @pytest.mark.req("REQ-YG-513")
    def test_genesis_has_two_happy_path_llm_nodes(self) -> None:
        """Happy path: synopsis and stubs are LLM nodes; fix_stubs is repair."""
        graph_path = NOVEL_FANDOM_DIR / "genesis.yaml"
        with open(graph_path) as f:
            config = yaml.safe_load(f)
        llm_nodes = [
            name for name, node in config["nodes"].items() if node.get("type") == "llm"
        ]
        assert sorted(llm_nodes) == ["fix_stubs", "stubs", "synopsis"]

    @pytest.mark.req("REQ-YG-513")
    def test_retired_prompts_deleted(self) -> None:
        """genesis_roster, genesis_character, structure_world prompts removed."""
        prompts_dir = NOVEL_FANDOM_DIR / "prompts"
        assert not (prompts_dir / "genesis_roster.yaml").exists()
        assert not (prompts_dir / "genesis_character.yaml").exists()
        assert not (prompts_dir / "structure_world.yaml").exists()

    @pytest.mark.req("REQ-YG-513")
    def test_generate_stubs_prompt_exists(self) -> None:
        """generate_stubs.yaml prompt exists with ref integrity constraint."""
        prompt_path = NOVEL_FANDOM_DIR / "prompts" / "generate_stubs.yaml"
        assert prompt_path.exists()
        with open(prompt_path) as f:
            prompt = yaml.safe_load(f)
        assert "REFERENTIAL INTEGRITY" in prompt["system"]

    @pytest.mark.req("REQ-YG-513")
    def test_parse_roster_removed(self) -> None:
        """parse_roster function no longer in genesis_tools."""
        assert not hasattr(
            _load("nf_genesis_tools_667", "nodes/genesis_tools.py"), "parse_roster"
        )

    @pytest.mark.req("REQ-YG-513")
    def test_genesis_no_roster_state(self) -> None:
        """Genesis graph state has no roster_text or character_names."""
        graph_path = NOVEL_FANDOM_DIR / "genesis.yaml"
        with open(graph_path) as f:
            config = yaml.safe_load(f)
        state_keys = set(config["state"].keys())
        assert "roster_text" not in state_keys
        assert "character_names" not in state_keys
        assert "character_cards" not in state_keys


# ---------- FR-665: Semantic Entity Dedup ----------


class TestDeterministicDedup:
    """FR-665: _deterministic_dedup merges obvious ID variants."""

    @pytest.mark.req("REQ-YG-514")
    def test_the_prefix_dedup(self) -> None:
        """the_flood and flood merge (keep flood)."""
        red_links = [
            {"id": "flood", "type": "event"},
            {"id": "the_flood", "type": "event"},
        ]
        survivors, merge_map = _dedup_entities._deterministic_dedup(red_links)
        assert len(survivors) == 1
        assert survivors[0]["id"] == "flood"
        assert merge_map["the_flood"] == "flood"

    @pytest.mark.req("REQ-YG-514")
    def test_possessive_dedup(self) -> None:
        """egils_wife and egil_wife merge (keep shorter)."""
        red_links = [
            {"id": "egil_wife", "type": "character"},
            {"id": "egils_wife", "type": "character"},
        ]
        survivors, merge_map = _dedup_entities._deterministic_dedup(red_links)
        assert len(survivors) == 1
        assert survivors[0]["id"] == "egil_wife"

    @pytest.mark.req("REQ-YG-514")
    def test_possessive_does_not_corrupt_interior(self) -> None:
        """crisis_management is NOT matched with crii_management."""
        red_links = [
            {"id": "crisis_management", "type": "event"},
            {"id": "criis_management", "type": "event"},
        ]
        survivors, _merge_map = _dedup_entities._deterministic_dedup(red_links)
        # These should NOT merge — different first segments
        assert len(survivors) == 2

    @pytest.mark.req("REQ-YG-514")
    def test_prefix_match_stop_words(self) -> None:
        """ulf_death_bear_hunt and ulf_death_in_bear_hunt merge."""
        red_links = [
            {"id": "ulf_death_bear_hunt", "type": "event"},
            {"id": "ulf_death_in_bear_hunt", "type": "event"},
        ]
        survivors, merge_map = _dedup_entities._deterministic_dedup(red_links)
        assert len(survivors) == 1

    @pytest.mark.req("REQ-YG-514")
    def test_no_false_merge(self) -> None:
        """Distinct entities stay distinct."""
        red_links = [
            {"id": "hilde", "type": "character"},
            {"id": "gunnar", "type": "character"},
            {"id": "flood", "type": "event"},
        ]
        survivors, merge_map = _dedup_entities._deterministic_dedup(red_links)
        assert len(survivors) == 3
        assert merge_map == {}


class TestDedupEntities:
    """FR-665: dedup_entities node integration."""

    @pytest.mark.req("REQ-YG-514")
    def test_dedup_node_reduces_red_links(self) -> None:
        state = {
            "red_links": [
                {"id": "egil_wife", "type": "character"},
                {"id": "egils_wife", "type": "character"},
                {"id": "hilde", "type": "character"},
            ],
            "deepened": [],
        }
        result = _dedup_entities.dedup_entities(state)
        assert result["red_link_count"] == 2
        ids = {e["id"] for e in result["red_links"]}
        assert "egils_wife" not in ids
        assert "egil_wife" in ids

    @pytest.mark.req("REQ-YG-514")
    def test_reference_rewriting(self) -> None:
        """Dropped IDs in deepened pages get rewritten to survivors."""
        state = {
            "red_links": [
                {"id": "egil_wife", "type": "character"},
                {"id": "egils_wife", "type": "character"},
            ],
            "deepened": [
                {
                    "updated_page": {
                        "id": "egil",
                        "references": ["egils_wife"],
                        "relationships": [{"to": "egils_wife", "kind": "spouse"}],
                    },
                    "new_entities": [
                        {"id": "egils_wife", "type": "character"},
                    ],
                },
            ],
        }
        result = _dedup_entities.dedup_entities(state)
        page = result["deepened"][0]["updated_page"]
        assert page["references"] == ["egil_wife"]
        assert page["relationships"][0]["to"] == "egil_wife"
        # Dropped entity removed from new_entities
        assert len(result["deepened"][0]["new_entities"]) == 0

    @pytest.mark.req("REQ-YG-514")
    def test_empty_red_links(self) -> None:
        state = {"red_links": [], "deepened": []}
        result = _dedup_entities.dedup_entities(state)
        assert result["red_link_count"] == 0

    @pytest.mark.req("REQ-YG-514")
    def test_worldgen_graph_has_dedup_node(self) -> None:
        """worldgen.yaml includes dedup node between collect and create_skeletons."""
        graph_path = NOVEL_FANDOM_DIR / "worldgen.yaml"
        with open(graph_path) as f:
            config = yaml.safe_load(f)
        assert "dedup" in config["nodes"]
        assert config["nodes"]["dedup"]["tool"] == "dedup_entities"
        # Check edges: collect → dedup → create_skeletons
        edges = config["edges"]
        collect_to_dedup = any(
            e.get("from") == "collect" and e.get("to") == "dedup" for e in edges
        )
        dedup_to_skeletons = any(
            e.get("from") == "dedup" and e.get("to") == "create_skeletons"
            for e in edges
        )
        assert collect_to_dedup
        assert dedup_to_skeletons
