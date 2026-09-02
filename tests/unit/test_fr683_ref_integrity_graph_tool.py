"""Tests for FR-683 — Referential integrity as graph-tool.

REQ-YG-515: Referential integrity graph-tool extraction
"""

from __future__ import annotations

import importlib.util
import json
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


# ---------- AC-5: ref_integrity.py loads as standalone module ----------


class TestRefIntegrityModule:
    """AC-5: ref_integrity.py is self-contained, no importlib hack."""

    @pytest.mark.req("REQ-YG-515")
    def test_module_loads_without_importlib(self) -> None:
        """ref_integrity.py loads via spec_from_file_location (path-based tool)."""
        mod = _load("nf_ref_integrity_683", "nodes/ref_integrity.py")
        assert hasattr(mod, "validate_referential_integrity")
        assert hasattr(mod, "ref_check")

    @pytest.mark.req("REQ-YG-515")
    def test_validate_with_list_input(self) -> None:
        """validate_referential_integrity accepts list of dicts."""
        mod = _load("nf_ref_integrity_683b", "nodes/ref_integrity.py")
        pages = [
            {"id": "a", "type": "character", "references": ["b"]},
            {"id": "b", "type": "event"},
        ]
        result = mod.validate_referential_integrity(pages)
        assert result["valid"] is True
        assert result["orphan_ids"] == []

    @pytest.mark.req("REQ-YG-515")
    def test_validate_detects_orphan(self) -> None:
        """validate_referential_integrity catches orphan IDs."""
        mod = _load("nf_ref_integrity_683c", "nodes/ref_integrity.py")
        pages = [
            {"id": "a", "type": "character", "references": ["missing"]},
        ]
        result = mod.validate_referential_integrity(pages)
        assert result["valid"] is False
        assert "missing" in result["orphan_ids"]

    @pytest.mark.req("REQ-YG-515")
    def test_ref_check_state_wrapper_with_structured_world(self) -> None:
        """ref_check(state) flattens structured_world and validates."""
        mod = _load("nf_ref_integrity_683d", "nodes/ref_integrity.py")
        state = {
            "structured_world": {
                "characters": [
                    {"id": "h", "type": "character", "references": ["e"]},
                ],
                "events": [
                    {"id": "e", "type": "event"},
                ],
            }
        }
        result = mod.ref_check(state)
        assert result["gate_result"]["valid"] is True

    @pytest.mark.req("REQ-YG-515")
    def test_ref_check_json_string_input(self) -> None:
        """ref_check handles pages as JSON string (graph-tool boundary)."""
        mod = _load("nf_ref_integrity_683e", "nodes/ref_integrity.py")
        pages = [
            {"id": "a", "type": "character", "references": ["orphan"]},
        ]
        state = {"pages": json.dumps(pages)}
        result = mod.ref_check(state)
        assert result["gate_result"]["valid"] is False
        assert "orphan" in result["gate_result"]["orphan_ids"]

    @pytest.mark.req("REQ-YG-515")
    def test_ref_check_empty_world(self) -> None:
        """ref_check returns valid for empty input."""
        mod = _load("nf_ref_integrity_683f", "nodes/ref_integrity.py")
        result = mod.ref_check({})
        assert result["gate_result"]["valid"] is True


# ---------- AC-4: validate_genesis.py deleted ----------


class TestValidateGenesisDeleted:
    """AC-4: validate_genesis.py no longer exists."""

    @pytest.mark.req("REQ-YG-515")
    def test_validate_genesis_py_deleted(self) -> None:
        """The importlib hack file is gone."""
        path = NOVEL_FANDOM_DIR / "nodes" / "validate_genesis.py"
        assert not path.exists(), f"validate_genesis.py should be deleted: {path}"


# ---------- AC-4: genesis.yaml points to ref_integrity ----------


class TestGenesisUsesRefIntegrity:
    """AC-4: genesis uses ref_check graph-tool (FR-686: agent has it in tools)."""

    @pytest.mark.req("REQ-YG-515")
    def test_genesis_agent_has_ref_check_tool(self) -> None:
        """genesis.yaml agent node includes ref_check in its tools list."""
        import yaml

        genesis_path = NOVEL_FANDOM_DIR / "genesis.yaml"
        with open(genesis_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
        agent = config["nodes"]["genesis"]
        assert "ref_check" in agent["tools"]
        # Also verify ref_check is a graph-tool
        ref_check = config["tools"]["ref_check"]
        assert ref_check["type"] == "graph"


# ---------- AC-2/AC-3: worldgen has ref_check graph-tool ----------


class TestWorldgenRefCheck:
    """AC-2/AC-3: worldgen.yaml has ref_check graph-tool for deepen_events."""

    @pytest.mark.req("REQ-YG-515")
    def test_worldgen_has_ref_check_tool(self) -> None:
        """worldgen.yaml tools section includes ref_check as type: graph."""
        import yaml

        worldgen_path = NOVEL_FANDOM_DIR / "worldgen.yaml"
        with open(worldgen_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
        ref_check = config["tools"].get("ref_check")
        assert ref_check is not None, "ref_check tool missing from worldgen.yaml"
        assert ref_check["type"] == "graph"
        assert "ref_check" in ref_check["path"]

    @pytest.mark.req("REQ-YG-515")
    def test_worldgen_agent_has_ref_check(self) -> None:
        """worldgen agent node includes ref_check in its tools list (FR-686)."""
        import yaml

        worldgen_path = NOVEL_FANDOM_DIR / "worldgen.yaml"
        with open(worldgen_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
        agent = config["nodes"]["worldgen"]
        assert "ref_check" in agent["tools"]


# ---------- AC-1: ref_check.yaml exists ----------


class TestRefCheckGraph:
    """AC-1: ref_check.yaml is a valid graph."""

    @pytest.mark.req("REQ-YG-515")
    def test_ref_check_yaml_exists(self) -> None:
        """ref_check.yaml exists in novel_fandom."""
        path = NOVEL_FANDOM_DIR / "ref_check.yaml"
        assert path.exists(), f"ref_check.yaml missing: {path}"

    @pytest.mark.req("REQ-YG-515")
    def test_ref_check_yaml_lints(self) -> None:
        """ref_check.yaml passes graph lint."""
        from yamlgraph.compile.graph_loader import load_graph_config

        path = NOVEL_FANDOM_DIR / "ref_check.yaml"
        config = load_graph_config(str(path))
        assert config.name is not None


# ---------- AC-5: persist_genesis imports from ref_integrity ----------


class TestPersistGenesisImport:
    """AC-5: persist_genesis.py imports from ref_integrity, no importlib."""

    @pytest.mark.req("REQ-YG-515")
    def test_persist_genesis_no_importlib_for_validation(self) -> None:
        """persist_genesis.py does not use importlib for validation function."""
        source = (NOVEL_FANDOM_DIR / "nodes" / "persist_genesis.py").read_text(encoding="utf-8")
        # Should not have importlib load for validation anymore
        assert "validate_referential_integrity" in source
        # The importlib usage should only be for persist_pages, not validation
        lines_with_importlib = [
            line
            for line in source.splitlines()
            if "importlib" in line and "validate" in line.lower()
        ]
        assert (
            len(lines_with_importlib) == 0
        ), f"importlib still used for validation: {lines_with_importlib}"
