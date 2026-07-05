"""Tests for FR-684 — Semantic dedup as graph-tool.

REQ-YG-517: Semantic entity deduplication graph-tool
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


# ---------- AC-1: semantic_dedup.yaml exists and lints ----------


class TestSemanticDedupGraph:
    """AC-1: semantic_dedup.yaml is a valid graph."""

    @pytest.mark.req("REQ-YG-517")
    def test_semantic_dedup_yaml_exists(self) -> None:
        path = NOVEL_FANDOM_DIR / "semantic_dedup.yaml"
        assert path.exists(), f"semantic_dedup.yaml missing: {path}"

    @pytest.mark.req("REQ-YG-517")
    def test_semantic_dedup_yaml_lints(self) -> None:
        from yamlgraph.graph_loader import load_graph_config

        path = NOVEL_FANDOM_DIR / "semantic_dedup.yaml"
        config = load_graph_config(str(path))
        assert config.name is not None


# ---------- AC-2: worldgen has semantic_dedup graph-tool ----------


class TestWorldgenSemanticDedup:
    """AC-2/AC-4: worldgen.yaml has semantic_dedup and dedup_check tools."""

    @pytest.mark.req("REQ-YG-517")
    def test_worldgen_has_semantic_dedup_tool(self) -> None:
        with open(NOVEL_FANDOM_DIR / "worldgen.yaml") as f:
            config = yaml.safe_load(f)
        tool = config["tools"].get("semantic_dedup")
        assert tool is not None, "semantic_dedup tool missing"
        assert tool["type"] == "graph"
        assert "semantic_dedup" in tool["path"]

    @pytest.mark.req("REQ-YG-517")
    def test_worldgen_has_dedup_check_tool(self) -> None:
        """AC-4: dedup_check is the same graph registered for the agent."""
        with open(NOVEL_FANDOM_DIR / "worldgen.yaml") as f:
            config = yaml.safe_load(f)
        tool = config["tools"].get("dedup_check")
        assert tool is not None, "dedup_check tool missing"
        assert tool["type"] == "graph"
        assert "semantic_dedup" in tool["path"]

    @pytest.mark.req("REQ-YG-517")
    def test_deepen_events_has_dedup_check(self) -> None:
        """AC-4: deepen_events agent includes dedup_check."""
        with open(NOVEL_FANDOM_DIR / "worldgen.yaml") as f:
            config = yaml.safe_load(f)
        deepen_node = config["nodes"]["deepen_events"]["node"]
        assert "dedup_check" in deepen_node["tools"]


# ---------- AC-3: Graph-level routing after dedup ----------


class TestWorldgenDedupRouting:
    """AC-3: Router after dedup → semantic_dedup subgraph → apply_merge."""

    @pytest.mark.req("REQ-YG-517")
    def test_semantic_dedup_subgraph_node_exists(self) -> None:
        """Subgraph node for semantic dedup invocation exists."""
        with open(NOVEL_FANDOM_DIR / "worldgen.yaml") as f:
            config = yaml.safe_load(f)
        node = config["nodes"].get("semantic_dedup_call")
        assert node is not None, "semantic_dedup_call node missing"
        assert node["type"] == "subgraph"

    @pytest.mark.req("REQ-YG-517")
    def test_apply_merge_node_exists(self) -> None:
        """apply_merge python node exists."""
        with open(NOVEL_FANDOM_DIR / "worldgen.yaml") as f:
            config = yaml.safe_load(f)
        node = config["nodes"].get("apply_merge")
        assert node is not None, "apply_merge node missing"

    @pytest.mark.req("REQ-YG-517")
    def test_dedup_routes_to_semantic_when_above_threshold(self) -> None:
        """dedup → semantic_dedup_call when red_link_count > 5."""
        with open(NOVEL_FANDOM_DIR / "worldgen.yaml") as f:
            config = yaml.safe_load(f)
        edges = config["edges"]
        edge = next(
            (
                e
                for e in edges
                if e.get("from") == "dedup" and e.get("to") == "semantic_dedup_call"
            ),
            None,
        )
        assert edge is not None, "Missing dedup→semantic_dedup_call edge"
        assert "red_link_count" in edge.get("condition", "")

    @pytest.mark.req("REQ-YG-517")
    def test_semantic_dedup_routes_to_apply_merge(self) -> None:
        """semantic_dedup_call → apply_merge edge exists."""
        with open(NOVEL_FANDOM_DIR / "worldgen.yaml") as f:
            config = yaml.safe_load(f)
        edges = config["edges"]
        edge = next(
            (
                e
                for e in edges
                if e.get("from") == "semantic_dedup_call"
                and e.get("to") == "apply_merge"
            ),
            None,
        )
        assert edge is not None, "Missing semantic_dedup_call→apply_merge edge"

    @pytest.mark.req("REQ-YG-517")
    def test_apply_merge_routes_to_create_skeletons(self) -> None:
        """apply_merge → create_skeletons edge exists."""
        with open(NOVEL_FANDOM_DIR / "worldgen.yaml") as f:
            config = yaml.safe_load(f)
        edges = config["edges"]
        edge = next(
            (
                e
                for e in edges
                if e.get("from") == "apply_merge" and e.get("to") == "create_skeletons"
            ),
            None,
        )
        assert edge is not None, "Missing apply_merge→create_skeletons edge"


# ---------- AC-5: Prompt has negative example ----------


class TestSemanticDedupPrompt:
    """AC-5/AC-6: Prompt compares summaries and includes negative example."""

    @pytest.mark.req("REQ-YG-517")
    def test_prompt_exists(self) -> None:
        path = NOVEL_FANDOM_DIR / "prompts" / "semantic_dedup.yaml"
        assert path.exists()

    @pytest.mark.req("REQ-YG-517")
    def test_prompt_has_negative_example(self) -> None:
        """AC-6: Prompt includes the ulf/ulfs false positive example."""
        path = NOVEL_FANDOM_DIR / "prompts" / "semantic_dedup.yaml"
        content = path.read_text()
        assert "ulf" in content.lower()
        assert "different roles" in content.lower() or "NOT duplicates" in content


# ---------- AC-7: dedup_entities.py cleanup ----------


class TestDedupEntitiesCleanup:
    """AC-3: TODO stub and threshold removed from dedup_entities.py."""

    @pytest.mark.req("REQ-YG-517")
    def test_no_llm_dedup_threshold(self) -> None:
        """_LLM_DEDUP_THRESHOLD removed — threshold in YAML router."""
        source = (NOVEL_FANDOM_DIR / "nodes" / "dedup_entities.py").read_text()
        assert "_LLM_DEDUP_THRESHOLD" not in source

    @pytest.mark.req("REQ-YG-517")
    def test_no_todo_stub(self) -> None:
        """TODO stub removed."""
        source = (NOVEL_FANDOM_DIR / "nodes" / "dedup_entities.py").read_text()
        assert "TODO" not in source


# ---------- AC-7: apply_merge_map module ----------


class TestApplyMergeMap:
    """AC-3: apply_merge_map.py node applies merge decisions."""

    @pytest.mark.req("REQ-YG-517")
    def test_module_loads(self) -> None:
        mod = _load("nf_apply_merge_684", "nodes/apply_merge_map.py")
        assert hasattr(mod, "apply_merge_map")

    @pytest.mark.req("REQ-YG-517")
    def test_applies_merge_map_to_red_links(self) -> None:
        """Merged IDs removed from red_links."""
        mod = _load("nf_apply_merge_684b", "nodes/apply_merge_map.py")
        state = {
            "red_links": [
                {"id": "gunnars_father", "type": "character"},
                {"id": "ulfs", "type": "character"},
                {"id": "hilde", "type": "character"},
            ],
            "semantic_merge_map": {"gunnars_father": "ulfs"},
            "deepened": [],
        }
        result = mod.apply_merge_map(state)
        surviving_ids = {r["id"] for r in result["red_links"]}
        assert "gunnars_father" not in surviving_ids
        assert "ulfs" in surviving_ids
        assert "hilde" in surviving_ids

    @pytest.mark.req("REQ-YG-517")
    def test_rewrites_references_in_deepened(self) -> None:
        """Merged IDs rewritten in deepened page references."""
        mod = _load("nf_apply_merge_684c", "nodes/apply_merge_map.py")
        state = {
            "red_links": [
                {"id": "gunnars_father", "type": "character"},
                {"id": "ulfs", "type": "character"},
            ],
            "semantic_merge_map": {"gunnars_father": "ulfs"},
            "deepened": [
                {
                    "updated_page": {
                        "id": "flood",
                        "participants": ["gunnars_father", "hilde"],
                    },
                },
            ],
        }
        result = mod.apply_merge_map(state)
        participants = result["deepened"][0]["updated_page"]["participants"]
        assert "gunnars_father" not in participants
        assert "ulfs" in participants

    @pytest.mark.req("REQ-YG-517")
    def test_empty_merge_map_is_noop(self) -> None:
        """No merge map → pass through unchanged."""
        mod = _load("nf_apply_merge_684d", "nodes/apply_merge_map.py")
        state = {
            "red_links": [{"id": "a", "type": "character"}],
            "semantic_merge_map": {},
            "deepened": [],
        }
        result = mod.apply_merge_map(state)
        assert result["red_links"] == [{"id": "a", "type": "character"}]
        assert result["red_link_count"] == 1


# ---------- AC-3: worldgen still lints ----------


class TestWorldgenLints:
    """Worldgen.yaml still passes lint after rewiring."""

    @pytest.mark.req("REQ-YG-517")
    def test_worldgen_yaml_lints(self) -> None:
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(str(NOVEL_FANDOM_DIR / "worldgen.yaml"))
        assert config.name == "novel-fandom-worldgen"
