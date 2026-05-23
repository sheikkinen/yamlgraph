"""FR-447 Judge Demo — Unit tests.

Tests that the standalone FR judge agent graph loads, lints, and has
correct structure: single agent node with 4 read-only tools and
structured JudgeVerdict output schema.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

GRAPH_PATH = "examples/demos/judge/graph.yaml"
DEMO_DIR = (
    Path(__file__).resolve().parent.parent.parent / "examples" / "demos" / "judge"
)


class TestJudgeDemoGraphStructure:
    """Test graph.yaml structure matches FR-447 spec."""

    @pytest.mark.req("REQ-YG-408")
    def test_graph_config_loads(self) -> None:
        """Graph config loads via yamlgraph."""
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        assert config.name == "fr-judge"

    @pytest.mark.req("REQ-YG-408")
    def test_has_one_node(self) -> None:
        """Graph must have exactly 1 node (judge)."""
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        assert len(config.nodes) == 1
        assert "judge" in config.nodes

    @pytest.mark.req("REQ-YG-408")
    def test_judge_is_agent_type(self) -> None:
        """Judge node must be type: agent."""
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        assert config.nodes["judge"]["type"] == "agent"

    @pytest.mark.req("REQ-YG-408")
    def test_judge_has_four_tools(self) -> None:
        """Judge node must reference exactly 4 read-only tools."""
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        tools = config.nodes["judge"]["tools"]
        assert len(tools) == 4
        expected = {"read_fr", "check_architecture", "search_existing_frs", "read_file"}
        assert set(tools) == expected

    @pytest.mark.req("REQ-YG-408")
    def test_graph_has_four_tool_definitions(self) -> None:
        """Graph tools section defines exactly 4 shell tools."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        assert len(raw["tools"]) == 4
        for tool_cfg in raw["tools"].values():
            assert tool_cfg["type"] == "shell"

    @pytest.mark.req("REQ-YG-408")
    def test_judge_state_key_is_verdict(self) -> None:
        """Judge node writes to state_key: verdict."""
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        assert config.nodes["judge"].get("state_key") == "verdict"

    @pytest.mark.req("REQ-YG-408")
    def test_prompt_has_structured_schema(self) -> None:
        """Prompt must define JudgeVerdict schema with 5 fields."""
        prompt = yaml.safe_load((DEMO_DIR / "prompts" / "judge.yaml").read_text())
        schema = prompt["schema"]
        assert schema["name"] == "JudgeVerdict"
        expected_fields = {
            "verdict",
            "classification",
            "reasoning",
            "criteria_results",
            "issues",
        }
        assert set(schema["fields"].keys()) == expected_fields

    @pytest.mark.req("REQ-YG-408")
    def test_graph_compiles(self) -> None:
        """Graph compiles to a LangGraph StateGraph."""
        from yamlgraph.graph_loader import compile_graph, load_graph_config

        config = load_graph_config(GRAPH_PATH)
        graph = compile_graph(config)
        assert graph is not None
