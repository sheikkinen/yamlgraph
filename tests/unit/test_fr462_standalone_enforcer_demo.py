"""FR-462 Standalone Enforcer Demo — Unit tests.

Tests that the standalone FR enforcer agent graph loads, lints, and has
correct structure: single agent node with 6 task-shaped tools (5 shell + 1 python)
and structured ImplementationResult output schema.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

GRAPH_PATH = "examples/demos/enforcer/graph.yaml"
DEMO_DIR = (
    Path(__file__).resolve().parent.parent.parent / "examples" / "demos" / "enforcer"
)


class TestEnforcerDemoGraphStructure:
    """Test graph.yaml structure matches FR-462 spec."""

    @pytest.mark.req("REQ-YG-426")
    def test_graph_config_loads(self) -> None:
        """Graph config loads via yamlgraph."""
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        assert config.name == "fr-enforcer"

    @pytest.mark.req("REQ-YG-426")
    def test_has_one_node(self) -> None:
        """Graph must have exactly 1 node (enforcer)."""
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        assert len(config.nodes) == 1
        assert "enforcer" in config.nodes

    @pytest.mark.req("REQ-YG-426")
    def test_enforcer_is_agent_type(self) -> None:
        """Enforcer node must be type: agent."""
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        assert config.nodes["enforcer"]["type"] == "agent"

    @pytest.mark.req("REQ-YG-426")
    def test_enforcer_has_ten_tools(self) -> None:
        """Enforcer node must reference exactly 10 task-shaped tools."""
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        tools = config.nodes["enforcer"]["tools"]
        assert len(tools) == 10
        expected = {
            "read_file",
            "search",
            "list_dir",
            "git_log",
            "git_diff",
            "lint",
            "run_tests",
            "write_file",
            "edit_file",
            "run_command",
        }
        assert set(tools) == expected

    @pytest.mark.req("REQ-YG-426")
    def test_graph_has_ten_tool_definitions(self) -> None:
        """Graph tools section defines exactly 10 tools (7 shell + 3 python)."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        assert len(raw["tools"]) == 10
        shell_tools = [n for n, c in raw["tools"].items() if c["type"] == "shell"]
        python_tools = [n for n, c in raw["tools"].items() if c["type"] == "python"]
        assert len(shell_tools) == 7
        assert len(python_tools) == 3

    @pytest.mark.req("REQ-YG-426")
    def test_write_file_is_python_tool(self) -> None:
        """write_file must be type: python, not shell."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        wf = raw["tools"]["write_file"]
        assert wf["type"] == "python"
        assert "write_file" in wf.get("function", "")

    @pytest.mark.req("REQ-YG-426")
    def test_max_iterations_is_25(self) -> None:
        """max_iterations set to 25 for implementation + testing + fixes."""
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        assert config.nodes["enforcer"].get("max_iterations") == 25

    @pytest.mark.req("REQ-YG-426")
    def test_temperature_is_0_3(self) -> None:
        """temperature set to 0.3 for deterministic implementation."""
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        assert config.nodes["enforcer"].get("temperature") == 0.3

    @pytest.mark.req("REQ-YG-426")
    def test_no_hardcoded_model(self) -> None:
        """No hardcoded model — uses env var fallthrough."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        assert (
            "model" not in raw["nodes"]["enforcer"]
        ), "Enforcer node must not hardcode model — use PROVIDER/MODEL env vars"

    @pytest.mark.req("REQ-YG-426")
    def test_enforcer_state_key_is_implementation_result(self) -> None:
        """Enforcer node writes to state_key: implementation_result."""
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        assert config.nodes["enforcer"].get("state_key") == "implementation_result"

    @pytest.mark.req("REQ-YG-426")
    def test_prompt_has_structured_schema(self) -> None:
        """Prompt must define ImplementationResult schema with 4 fields."""
        prompt = yaml.safe_load((DEMO_DIR / "prompts" / "enforcer.yaml").read_text())
        schema = prompt["schema"]
        assert schema["name"] == "ImplementationResult"
        expected_fields = {
            "success",
            "files_changed",
            "tests_passed",
            "summary",
        }
        assert set(schema["fields"].keys()) == expected_fields

    @pytest.mark.req("REQ-YG-426")
    def test_prompt_instructs_implementation_steps(self) -> None:
        """Prompt must instruct agent through implementation steps."""
        prompt_text = (DEMO_DIR / "prompts" / "enforcer.yaml").read_text()
        assert "Read the FR" in prompt_text
        assert "Explore" in prompt_text
        assert "Implement" in prompt_text
        assert "Test" in prompt_text
        assert "Lint" in prompt_text or "lint" in prompt_text

    @pytest.mark.req("REQ-YG-426")
    def test_graph_compiles(self) -> None:
        """Graph compiles to a LangGraph StateGraph."""
        from yamlgraph.graph_loader import compile_graph, load_graph_config

        config = load_graph_config(GRAPH_PATH)
        graph = compile_graph(config)
        assert graph is not None

    @pytest.mark.req("REQ-YG-426")
    def test_demo_sh_exists_and_executable(self) -> None:
        """demo.sh must exist and be executable."""
        demo_sh = DEMO_DIR / "demo.sh"
        assert demo_sh.is_file()
        assert demo_sh.stat().st_mode & 0o111  # executable bit

    @pytest.mark.req("REQ-YG-426")
    def test_demo_sh_accepts_fr_path_argument(self) -> None:
        """demo.sh must accept FR path as first argument."""
        demo_sh = DEMO_DIR / "demo.sh"
        content = demo_sh.read_text()
        assert "$1" in content or "$FR_PATH" in content

    @pytest.mark.req("REQ-YG-426")
    def test_demo_sh_runs_graph(self) -> None:
        """demo.sh must run the enforcer graph."""
        demo_sh = DEMO_DIR / "demo.sh"
        content = demo_sh.read_text()
        assert "yamlgraph graph run" in content
        assert "examples/demos/enforcer/graph.yaml" in content

    @pytest.mark.req("REQ-YG-426")
    def test_demo_sh_uses_json_output(self) -> None:
        """demo.sh must use --json flag for structured output."""
        demo_sh = DEMO_DIR / "demo.sh"
        content = demo_sh.read_text()
        assert "--json" in content

    @pytest.mark.req("REQ-YG-426")
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

    @pytest.mark.req("REQ-YG-426")
    def test_readme_exists(self) -> None:
        """README.md must exist."""
        readme = DEMO_DIR / "README.md"
        assert readme.is_file()

    @pytest.mark.req("REQ-YG-426")
    def test_readme_documents_usage(self) -> None:
        """README must document enforcer usage."""
        readme = DEMO_DIR / "README.md"
        content = readme.read_text()
        assert "Quick Start" in content
        assert "./demo.sh" in content
        assert "Architecture" in content
