"""FR-717 witnesses: root-package seams exist and are enforced."""

from __future__ import annotations

import configparser
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestSeams:
    @pytest.mark.req("REQ-YG-546")
    def test_packages_exist_with_members(self):
        for pkg, member in [
            ("a2a", "server.py"),
            ("export", "mcp.py"),
            ("compile", "graph_loader.py"),
        ]:
            assert (REPO_ROOT / "yamlgraph" / pkg / member).exists()

    @pytest.mark.req("REQ-YG-546")
    def test_importlinter_contracts_present(self):
        cfg = configparser.ConfigParser()
        cfg.read(REPO_ROOT / ".importlinter")
        contracts = {s for s in cfg.sections() if s.startswith("importlinter:contract")}
        for needed in ("a2a-seam", "export-seam", "compile-seam"):
            assert any(needed in s for s in contracts), f"missing contract {needed}"

    @pytest.mark.req("REQ-YG-546")
    def test_root_module_count_bounded(self):
        count = len(list((REPO_ROOT / "yamlgraph").glob("*.py")))
        assert count <= 17, f"root module count grew back: {count}"

    @pytest.mark.req("REQ-YG-546")
    def test_top_level_reexports_unchanged(self):
        from yamlgraph import load_and_compile  # noqa: F401

    @pytest.mark.req("REQ-YG-546")
    def test_no_stale_deep_imports(self):
        """No code references the retired flat paths."""
        stale = []
        for py in (REPO_ROOT / "yamlgraph").rglob("*.py"):
            text = py.read_text()
            for old in (
                "yamlgraph.a2a_server",
                "yamlgraph.a2a_message",
                "yamlgraph.skill_export",
                "yamlgraph.mcp_server",
                "yamlgraph.graph_loader",
                "yamlgraph.node_compiler",
            ):
                if old in text:
                    stale.append(f"{py.name}: {old}")
        assert not stale, stale
