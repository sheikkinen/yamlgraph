"""FR-452 Standalone Planner Demo — Unit tests.

Tests that the standalone FR planner agent graph loads, lints, and has
correct structure: single agent node with 5 task-shaped tools (4 shell + 1 python)
and structured PlanResult output schema.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

GRAPH_PATH = "examples/demos/planner/graph.yaml"
DEMO_DIR = (
    Path(__file__).resolve().parent.parent.parent / "examples" / "demos" / "planner"
)


class TestPlannerDemoGraphStructure:
    """Test graph.yaml structure matches FR-452 spec."""

    @pytest.mark.req("REQ-YG-424")
    def test_graph_config_loads(self) -> None:
        """Graph config loads via yamlgraph."""
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        assert config.name == "fr-planner"

    @pytest.mark.req("REQ-YG-424")
    def test_has_one_node(self) -> None:
        """Graph must have exactly 1 node (planner)."""
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        assert len(config.nodes) == 1
        assert "planner" in config.nodes

    @pytest.mark.req("REQ-YG-424")
    def test_planner_is_agent_type(self) -> None:
        """Planner node must be type: agent."""
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        assert config.nodes["planner"]["type"] == "agent"

    @pytest.mark.req("REQ-YG-424")
    def test_planner_has_five_tools(self) -> None:
        """Planner node must reference exactly 5 task-shaped tools."""
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        tools = config.nodes["planner"]["tools"]
        assert len(tools) == 5
        expected = {"read_file", "search", "list_dir", "git_log", "write_file"}
        assert set(tools) == expected

    @pytest.mark.req("REQ-YG-424")
    def test_graph_has_five_tool_definitions(self) -> None:
        """Graph tools section defines exactly 5 tools (4 shell + 1 python)."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        assert len(raw["tools"]) == 5
        shell_tools = [n for n, c in raw["tools"].items() if c["type"] == "shell"]
        python_tools = [n for n, c in raw["tools"].items() if c["type"] == "python"]
        assert len(shell_tools) == 4
        assert len(python_tools) == 1
        assert python_tools[0] == "write_file"

    @pytest.mark.req("REQ-YG-424")
    def test_write_file_is_python_tool(self) -> None:
        """write_file must be type: python, not shell (heredoc rejected)."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        wf = raw["tools"]["write_file"]
        assert wf["type"] == "python"
        assert "write_file" in wf.get("function", "")

    @pytest.mark.req("REQ-YG-424")
    def test_no_head_truncation(self) -> None:
        """No tool uses | head -N truncation."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        for name, tool_cfg in raw["tools"].items():
            cmd = tool_cfg.get("command", "")
            assert "| head" not in cmd, f"Tool '{name}' uses | head truncation: {cmd}"

    @pytest.mark.req("REQ-YG-424")
    def test_max_iterations_is_15(self) -> None:
        """max_iterations set to 15 for research + drafting."""
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        assert config.nodes["planner"].get("max_iterations") == 15

    @pytest.mark.req("REQ-YG-424")
    def test_no_hardcoded_model(self) -> None:
        """No hardcoded model — uses env var fallthrough."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        assert (
            "model" not in raw["nodes"]["planner"]
        ), "Planner node must not hardcode model — use PROVIDER/MODEL env vars"

    @pytest.mark.req("REQ-YG-424")
    def test_planner_state_key_is_plan_result(self) -> None:
        """Planner node writes to state_key: plan_result."""
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        assert config.nodes["planner"].get("state_key") == "plan_result"

    @pytest.mark.req("REQ-YG-424")
    def test_prompt_has_structured_schema(self) -> None:
        """Prompt must define PlanResult schema with 6 fields."""
        prompt = yaml.safe_load((DEMO_DIR / "prompts" / "planner.yaml").read_text())
        schema = prompt["schema"]
        assert schema["name"] == "PlanResult"
        expected_fields = {
            "fr_path",
            "title",
            "summary",
            "research_findings",
            "scope_assessment",
            "estimated_effort",
        }
        assert set(schema["fields"].keys()) == expected_fields

    @pytest.mark.req("REQ-YG-424")
    def test_prompt_instructs_template_and_architecture(self) -> None:
        """Prompt must instruct agent to read FR template and architecture doc."""
        prompt_text = (DEMO_DIR / "prompts" / "planner.yaml").read_text()
        assert "TEMPLATE.md" in prompt_text
        assert "ARCHITECTURE.md" in prompt_text

    @pytest.mark.req("REQ-YG-424")
    def test_graph_compiles(self) -> None:
        """Graph compiles to a LangGraph StateGraph."""
        from yamlgraph.graph_loader import compile_graph, load_graph_config

        config = load_graph_config(GRAPH_PATH)
        graph = compile_graph(config)
        assert graph is not None

    @pytest.mark.req("REQ-YG-424")
    def test_demo_sh_exists_and_executable(self) -> None:
        """demo.sh must exist and be executable."""
        demo_sh = DEMO_DIR / "demo.sh"
        assert demo_sh.is_file()
        assert demo_sh.stat().st_mode & 0o111  # executable bit

    @pytest.mark.req("REQ-YG-424")
    def test_write_file_tool_creates_file(self, tmp_path: Path, monkeypatch) -> None:
        """write_file Python tool creates files with content."""
        import importlib.util

        monkeypatch.chdir(tmp_path)
        spec = importlib.util.spec_from_file_location(
            "write_file_tool", DEMO_DIR / "tools" / "write_file.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        target = tmp_path / "subdir" / "test.md"
        result = mod.write_file(str(target), "hello world")
        assert target.read_text() == "hello world"
        assert "11 bytes" in result
