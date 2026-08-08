"""FR-215 Research Agent Demo — Unit tests.

Tests that the 5-step agentic research graph (extract → plan → execute →
validate → respond) loads, lints, and has correct structure.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.process

GRAPH_PATH = "examples/demos/research-agent/graph.yaml"
DEMO_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "examples"
    / "demos"
    / "research-agent"
)


class TestResearchAgentGraphStructure:
    """Test graph.yaml structure matches FR-215 spec."""

    @pytest.mark.req("REQ-YG-217")
    def test_graph_config_loads(self) -> None:
        """Graph config loads via yamlgraph."""
        from yamlgraph.compile.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        assert config.name == "research-agent"

    @pytest.mark.req("REQ-YG-217")
    def test_has_five_nodes(self) -> None:
        """Graph must have exactly 5 nodes."""
        from yamlgraph.compile.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        assert len(config.nodes) == 5

    @pytest.mark.req("REQ-YG-217")
    def test_node_names_match_spec(self) -> None:
        """Nodes match the 5-step pattern names."""
        from yamlgraph.compile.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        expected = {
            "extract_intent",
            "plan_research",
            "execute_research",
            "validate_findings",
            "synthesize_report",
        }
        assert set(config.nodes.keys()) == expected

    @pytest.mark.req("REQ-YG-217")
    def test_extract_intent_is_llm(self) -> None:
        """extract_intent must be type: llm."""
        from yamlgraph.compile.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        assert config.nodes["extract_intent"]["type"] == "llm"

    @pytest.mark.req("REQ-YG-217")
    def test_plan_research_is_agent(self) -> None:
        """plan_research must be type: agent."""
        from yamlgraph.compile.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        assert config.nodes["plan_research"]["type"] == "agent"

    @pytest.mark.req("REQ-YG-217")
    def test_execute_research_is_agent(self) -> None:
        """execute_research must be type: agent."""
        from yamlgraph.compile.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        assert config.nodes["execute_research"]["type"] == "agent"

    @pytest.mark.req("REQ-YG-217")
    def test_validate_findings_is_llm(self) -> None:
        """validate_findings must be type: llm."""
        from yamlgraph.compile.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        assert config.nodes["validate_findings"]["type"] == "llm"

    @pytest.mark.req("REQ-YG-217")
    def test_synthesize_report_is_llm(self) -> None:
        """synthesize_report must be type: llm."""
        from yamlgraph.compile.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        assert config.nodes["synthesize_report"]["type"] == "llm"

    @pytest.mark.req("REQ-YG-217")
    def test_plan_gets_subset_of_tools(self) -> None:
        """plan_research gets only discovery tools (search, list_dir)."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        plan_tools = raw["nodes"]["plan_research"]["tools"]
        assert set(plan_tools) == {"search", "list_dir"}

    @pytest.mark.req("REQ-YG-217")
    def test_execute_gets_all_tools(self) -> None:
        """execute_research gets all five tools."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        exec_tools = raw["nodes"]["execute_research"]["tools"]
        assert set(exec_tools) == {
            "search",
            "list_dir",
            "read_file",
            "count_lines",
            "git_log",
        }

    @pytest.mark.req("REQ-YG-217")
    def test_edge_flow_start_to_end(self) -> None:
        """Edges: START → extract → plan → execute → validate → synthesize → END."""
        from yamlgraph.compile.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        edge_pairs = [(e["from"], e["to"]) for e in config.edges]
        assert ("START", "extract_intent") in edge_pairs
        assert ("extract_intent", "plan_research") in edge_pairs
        assert ("plan_research", "execute_research") in edge_pairs
        assert ("execute_research", "validate_findings") in edge_pairs
        assert ("validate_findings", "synthesize_report") in edge_pairs
        assert ("synthesize_report", "END") in edge_pairs

    @pytest.mark.req("REQ-YG-217")
    def test_graph_lint_passes(self) -> None:
        """Graph passes yamlgraph lint."""
        from yamlgraph.linter.graph_linter import lint_graph

        result = lint_graph(GRAPH_PATH)
        errors = [i for i in result.issues if i.severity == "error"]
        assert errors == [], f"Lint errors: {errors}"

    @pytest.mark.req("REQ-YG-217")
    def test_prompts_relative_true(self) -> None:
        """Graph uses prompts_relative: true."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        assert raw.get("prompts_relative") is True

    @pytest.mark.req("REQ-YG-217")
    def test_prompts_dir_exists(self) -> None:
        """Demo has a prompts/ directory."""
        assert (DEMO_DIR / "prompts").is_dir()

    @pytest.mark.req("REQ-YG-217")
    def test_all_prompt_files_exist(self) -> None:
        """Each node's prompt file exists."""
        expected = [
            "extract_intent.yaml",
            "plan_research.yaml",
            "execute_research.yaml",
            "validate_findings.yaml",
            "synthesize_report.yaml",
        ]
        for name in expected:
            assert (DEMO_DIR / "prompts" / name).exists(), f"Missing prompt: {name}"

    @pytest.mark.req("REQ-YG-217")
    def test_has_readme(self) -> None:
        """Demo has a README.md."""
        assert (DEMO_DIR / "README.md").exists()

    @pytest.mark.req("REQ-YG-217")
    def test_extract_intent_has_schema(self) -> None:
        """extract_intent prompt defines a Pydantic schema."""
        prompt = yaml.safe_load(
            (DEMO_DIR / "prompts" / "extract_intent.yaml").read_text()
        )
        assert "schema" in prompt
        fields = prompt["schema"]["fields"]
        assert "topic" in fields
        assert "key_questions" in fields

    @pytest.mark.req("REQ-YG-217")
    def test_validate_findings_has_schema(self) -> None:
        """validate_findings prompt defines a Pydantic schema."""
        prompt = yaml.safe_load(
            (DEMO_DIR / "prompts" / "validate_findings.yaml").read_text()
        )
        assert "schema" in prompt
        fields = prompt["schema"]["fields"]
        assert "gaps" in fields
        assert "confidence" in fields

    @pytest.mark.req("REQ-YG-217")
    def test_variables_declared(self) -> None:
        """Graph declares query and scope variables."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        variables = raw.get("variables", {})
        assert "query" in variables
        assert "scope" in variables
