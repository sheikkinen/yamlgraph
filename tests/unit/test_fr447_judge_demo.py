"""FR-447/FR-450 Judge Demo — Unit tests.

Tests that the standalone FR judge agent graph loads, lints, and has
correct structure: single agent node with 5 task-shaped tools and
structured JudgeVerdict output schema.

FR-450 promotes the demo from facade tools to real investigation tools.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.process

GRAPH_PATH = "examples/demos/judge/graph.yaml"
DEMO_DIR = (
    Path(__file__).resolve().parent.parent.parent / "examples" / "demos" / "judge"
)


class TestJudgeDemoGraphStructure:
    """Test graph.yaml structure matches FR-447 spec."""

    @pytest.mark.req("REQ-YG-408")
    def test_graph_config_loads(self) -> None:
        """Graph config loads via yamlgraph."""
        from yamlgraph.compile.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        assert config.name == "fr-judge"

    @pytest.mark.req("REQ-YG-408")
    def test_has_one_node(self) -> None:
        """Graph must have exactly 1 node (judge)."""
        from yamlgraph.compile.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        assert len(config.nodes) == 1
        assert "judge" in config.nodes

    @pytest.mark.req("REQ-YG-408")
    def test_judge_is_agent_type(self) -> None:
        """Judge node must be type: agent."""
        from yamlgraph.compile.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        assert config.nodes["judge"]["type"] == "agent"

    @pytest.mark.req("REQ-YG-408")
    def test_judge_has_five_tools(self) -> None:
        """FR-450: Judge node must reference exactly 5 task-shaped tools."""
        from yamlgraph.compile.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        tools = config.nodes["judge"]["tools"]
        assert len(tools) == 5
        expected = {"read_file", "search", "list_dir", "git_log", "run_tests"}
        assert set(tools) == expected

    @pytest.mark.req("REQ-YG-408")
    def test_graph_has_five_tool_definitions(self) -> None:
        """FR-450: Graph tools section defines exactly 5 shell tools."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        assert len(raw["tools"]) == 5
        for tool_cfg in raw["tools"].values():
            # FR-777: shared shell tools are declared via toolbelt manifest refs
            assert tool_cfg.get("type") == "shell" or "toolbelt" in tool_cfg.get(
                "manifest", ""
            )

    @pytest.mark.req("REQ-YG-408")
    def test_no_head_truncation_except_run_tests(self) -> None:
        """FR-450: No tool uses | head -N truncation."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        for name, tool_cfg in raw["tools"].items():
            cmd = tool_cfg.get("command", "")
            assert "| head" not in cmd, f"Tool '{name}' uses | head truncation: {cmd}"

    @pytest.mark.req("REQ-YG-408")
    def test_search_uses_rg(self) -> None:
        """FR-450: search tool uses rg with --glob (via FR-777 manifest)."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        manifest_path = DEMO_DIR / raw["tools"]["search"]["manifest"]
        manifest = yaml.safe_load(manifest_path.read_text())
        cmd = manifest["runtime"]["command"]
        assert "rg" in cmd
        assert "--glob" in cmd

    @pytest.mark.req("REQ-YG-408")
    def test_run_tests_tool_exists(self) -> None:
        """FR-450: run_tests tool runs pytest."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        cmd = raw["tools"]["run_tests"]["command"]
        assert "pytest" in cmd

    @pytest.mark.req("REQ-YG-408")
    def test_max_iterations_is_12(self) -> None:
        """FR-450: max_iterations set to 12 for genuine investigation."""
        from yamlgraph.compile.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        assert config.nodes["judge"].get("max_iterations") == 12

    @pytest.mark.req("REQ-YG-408")
    def test_no_hardcoded_model(self) -> None:
        """FR-453: No hardcoded model — uses env var fallthrough."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        assert (
            "model" not in raw["nodes"]["judge"]
        ), "Judge node must not hardcode model — use PROVIDER/MODEL env vars"

    @pytest.mark.req("REQ-YG-408")
    def test_judge_state_key_is_verdict(self) -> None:
        """Judge node writes to state_key: verdict."""
        from yamlgraph.compile.graph_loader import load_graph_config

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
        from yamlgraph.compile.graph_loader import compile_graph, load_graph_config

        config = load_graph_config(GRAPH_PATH)
        graph = compile_graph(config)
        assert graph is not None
