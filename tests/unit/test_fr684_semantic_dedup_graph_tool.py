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


# ---------- AC-2: worldgen has dedup_check graph-tool (FR-686) ----------


class TestWorldgenSemanticDedup:
    """AC-2/AC-4: worldgen dedup — superseded by FR-689 integrated gate."""

    @pytest.mark.req("REQ-YG-517")
    def test_worldgen_has_no_standalone_dedup_check(self) -> None:
        """FR-689: dedup_check removed from worldgen tools (integrated into create_* pipelines)."""
        with open(NOVEL_FANDOM_DIR / "worldgen.yaml") as f:
            config = yaml.safe_load(f)
        assert "dedup_check" not in config.get("tools", {})

    @pytest.mark.req("REQ-YG-517")
    def test_worldgen_agent_has_update_refs(self) -> None:
        """FR-689: Agent uses update_refs instead of standalone dedup_check."""
        with open(NOVEL_FANDOM_DIR / "worldgen.yaml") as f:
            config = yaml.safe_load(f)
        agent = config["nodes"]["worldgen"]
        assert "update_refs" in agent["tools"]


# ---------- AC-3: worldgen uses agent-first dedup (FR-686) ----------
# The old routing tests (subgraph nodes, apply_merge, conditional edges)
# are superseded by FR-686 agent-first architecture. The agent calls
# dedup_check as a graph-tool; worldgen has no routing nodes.


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


# ---------- AC-7: apply_merge_map retired (FR-686) ----------
# apply_merge_map.py was deleted — the agent-first architecture handles
# merge decisions at the tool level (dedup_check graph-tool returns
# merge_map; agent acts on it). No graph-level merge node needed.


# ---------- AC-3: worldgen still lints ----------


class TestWorldgenLints:
    """Worldgen.yaml still passes lint after rewiring."""

    @pytest.mark.req("REQ-YG-517")
    def test_worldgen_yaml_lints(self) -> None:
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(str(NOVEL_FANDOM_DIR / "worldgen.yaml"))
        assert config.name == "novel-fandom-worldgen"
