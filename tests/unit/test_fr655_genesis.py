"""Tests for FR-655 genesis pipeline (updated for FR-667 stub pipeline).

REQ-YG-505: Genesis graph structure
REQ-YG-506: Structure world prompt schema → replaced by generate_stubs (FR-667)
REQ-YG-507: persist_genesis flattening
REQ-YG-508: parse_roster splitting → removed (FR-667)
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


_genesis_tools = _load("novel_fandom_genesis_tools_655", "nodes/genesis_tools.py")
_persist_genesis = _load("novel_fandom_persist_genesis_655", "nodes/persist_genesis.py")
_persist_pages = _load("novel_fandom_persist_pages_655", "nodes/persist_pages.py")
_canon = _load("novel_fandom_schema_canon_655", "schema/canon.py")

PAGE_MODELS = _canon.PAGE_MODELS
for m in PAGE_MODELS.values():
    m.model_rebuild()


# --- REQ-YG-508: parse_roster (removed by FR-667) ---
# parse_roster tests removed — function deleted in FR-667.


# --- REQ-YG-505: load_premise ---


class TestLoadPremise:
    """FR-655: load_premise reads premise file."""

    @pytest.mark.req("REQ-YG-505")
    def test_load_floodmark_premise(self) -> None:
        premise_path = (
            NOVEL_FANDOM_DIR.parent
            / "dungeon_master"
            / "premises"
            / "floodmark-saga.txt"
        )
        if not premise_path.exists():
            pytest.skip("floodmark-saga.txt not found")
        state = {"premise_file": str(premise_path)}
        result = _genesis_tools.load_premise(state)
        assert "Hilde" in result["premise_text"]
        assert "Aschenwulf" in result["premise_text"]

    @pytest.mark.req("REQ-YG-505")
    def test_load_premise_missing_file_raises(self) -> None:
        state = {"premise_file": "/nonexistent/path.txt"}
        with pytest.raises((FileNotFoundError, ValueError)):
            _genesis_tools.load_premise(state)


# --- REQ-YG-507: persist_genesis ---


class TestPersistGenesis:
    """FR-655: persist_genesis flattens structured_world and writes canon."""

    @pytest.mark.req("REQ-YG-507")
    def test_flatten_and_persist(self, tmp_path: Path) -> None:
        world = {
            "premise": {
                "type": "premise",
                "id": "test_premise",
                "lane": "dynamic",
                "depth": 0,
                "text": "Test premise text",
                "genre_tags": ["fantasy"],
                "era": "ancient",
                "themes": ["survival"],
                "calendar_note": "Year 0 = the flood",
            },
            "synopsis": {
                "type": "synopsis",
                "id": "test_synopsis",
                "lane": "dynamic",
                "depth": 0,
                "text": "Test synopsis text",
            },
            "characters": [
                {
                    "type": "character",
                    "id": "hilde",
                    "lane": "dynamic",
                    "depth": 0,
                    "name": "Hilde",
                    "birth_year": -25,
                    "role": "protagonist",
                    "faction": "aschenwulf",
                },
            ],
            "events": [
                {
                    "type": "event",
                    "id": "the_flood",
                    "lane": "dynamic",
                    "depth": 0,
                    "year": 0,
                    "scope": "world",
                    "participants": ["hilde", "gunnar"],
                    "consequences": ["clans forced upland"],
                },
            ],
            "factions": [
                {
                    "type": "faction",
                    "id": "aschenwulf",
                    "lane": "dynamic",
                    "depth": 0,
                    "name": "Aschenwulf",
                    "members": ["hilde"],
                },
            ],
            "rules": [
                {
                    "type": "rule",
                    "id": "survival_truce",
                    "lane": "dynamic",
                    "depth": 0,
                    "domain": "social_rule",
                    "title": "Survival Truce",
                    "description": "Enemies must cooperate when flood threatens both",
                },
            ],
            "locations": [
                {
                    "type": "location",
                    "id": "high_valley",
                    "lane": "dynamic",
                    "depth": 0,
                    "name": "The High Valley",
                    "description": "Last dry ground above the flood line",
                },
            ],
        }

        state = {"structured_world": world}
        result = _persist_genesis._persist_genesis_impl(state, tmp_path, PAGE_MODELS)
        assert result["written_count"] == 7

        # Check type subfolders
        assert (tmp_path / "premise" / "test_premise.yaml").exists()
        assert (tmp_path / "synopsis" / "test_synopsis.yaml").exists()
        assert (tmp_path / "character" / "hilde.yaml").exists()
        assert (tmp_path / "event" / "the_flood.yaml").exists()
        assert (tmp_path / "faction" / "aschenwulf.yaml").exists()
        assert (tmp_path / "rule" / "survival_truce.yaml").exists()
        assert (tmp_path / "location" / "high_valley.yaml").exists()

        # Verify content
        with open(tmp_path / "character" / "hilde.yaml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["birth_year"] == -25
        assert data["role"] == "protagonist"

    @pytest.mark.req("REQ-YG-507")
    def test_empty_world(self, tmp_path: Path) -> None:
        state = {"structured_world": {}}
        result = _persist_genesis._persist_genesis_impl(state, tmp_path, PAGE_MODELS)
        assert result["written_count"] == 0

    @pytest.mark.req("REQ-YG-507")
    def test_missing_world(self, tmp_path: Path) -> None:
        state = {}
        result = _persist_genesis._persist_genesis_impl(state, tmp_path, PAGE_MODELS)
        assert result["written_count"] == 0


# --- REQ-YG-505: genesis.yaml graph structure ---


class TestGenesisGraph:
    """FR-655/FR-667/FR-686: genesis.yaml graph structure (updated for agent-first)."""

    @pytest.mark.req("REQ-YG-505")
    def test_genesis_yaml_loads(self) -> None:
        graph_path = NOVEL_FANDOM_DIR / "genesis.yaml"
        with open(graph_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        assert cfg["name"] == "novel-fandom-genesis"
        assert "load" in cfg["nodes"]
        assert "synopsis" in cfg["nodes"]
        assert "genesis" in cfg["nodes"]  # FR-686: agent node
        assert "persist_synopsis" in cfg["nodes"]  # FR-686
        assert "final_gate" in cfg["nodes"]  # FR-686

    @pytest.mark.req("REQ-YG-505")
    def test_genesis_edge_sequence(self) -> None:
        graph_path = NOVEL_FANDOM_DIR / "genesis.yaml"
        with open(graph_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        edges = cfg["edges"]
        edge_pairs = [(e["from"], e["to"]) for e in edges]
        assert ("START", "load") in edge_pairs
        assert ("load", "synopsis") in edge_pairs
        assert ("synopsis", "persist_synopsis") in edge_pairs  # FR-686
        assert ("persist_synopsis", "genesis") in edge_pairs  # FR-686
        assert ("genesis", "final_gate") in edge_pairs  # FR-686
        assert ("final_gate", "END") in edge_pairs

    @pytest.mark.req("REQ-YG-505")
    def test_genesis_prompts_exist(self) -> None:
        """FR-686: genesis_synopsis and genesis_agent are the prompts."""
        for name in ("genesis_synopsis", "genesis_agent"):
            path = NOVEL_FANDOM_DIR / "prompts" / f"{name}.yaml"
            assert path.exists(), f"Missing prompt: {name}"
