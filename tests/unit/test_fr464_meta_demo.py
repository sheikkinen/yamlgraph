"""FR-464 Meta Self-Reflective Demo — Unit tests.

Tests that the meta demo graph loads, lints, and has correct structure:
a `read_file` shell tool feeding a tool node, then an LLM node that applies
a natural-language `verb` to the read `target` and returns typed output.

The headline is self-reference: pointing `target` at the graph's own YAML.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

GRAPH_PATH = "examples/demos/meta/graph.yaml"
DEMO_DIR = Path(__file__).resolve().parent.parent.parent / "examples" / "demos" / "meta"


class TestMetaDemoGraphStructure:
    """Test graph.yaml structure matches FR-464 spec."""

    @pytest.mark.req("REQ-YG-467")
    def test_graph_config_loads(self) -> None:
        """Graph config loads via yamlgraph."""
        from yamlgraph.compile.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        assert config.name == "meta"

    @pytest.mark.req("REQ-YG-467")
    def test_has_two_nodes(self) -> None:
        """Graph must have exactly 2 nodes: load (tool) and transform (llm)."""
        from yamlgraph.compile.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        assert set(config.nodes) == {"load", "transform"}

    @pytest.mark.req("REQ-YG-467")
    def test_load_is_tool_node(self) -> None:
        """load node must be type: tool using the read_file shell tool."""
        from yamlgraph.compile.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        assert config.nodes["load"]["type"] == "tool"
        assert config.nodes["load"]["tool"] == "read_file"
        assert config.nodes["load"].get("state_key") == "source"

    @pytest.mark.req("REQ-YG-467")
    def test_load_passes_target_to_read_file(self) -> None:
        """load node must pass the target variable into the read_file command."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        variables = raw["nodes"]["load"]["variables"]
        assert variables["target"] == "{state.target}"

    @pytest.mark.req("REQ-YG-467")
    def test_read_file_is_shell_tool(self) -> None:
        """read_file must be a shell tool (cat {target}) per judge/enforcer convention."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        tool = raw["tools"]["read_file"]
        assert tool["type"] == "shell"
        assert "cat {target}" in tool["command"]

    @pytest.mark.req("REQ-YG-467")
    def test_transform_is_llm_node(self) -> None:
        """transform node must be type: llm using the meta_transform prompt."""
        from yamlgraph.compile.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        assert config.nodes["transform"]["type"] == "llm"
        assert config.nodes["transform"]["prompt"] == "meta_transform"
        assert config.nodes["transform"].get("state_key") == "result"

    @pytest.mark.req("REQ-YG-467")
    def test_transform_receives_verb_and_source(self) -> None:
        """transform node must receive verb and source from state."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        variables = raw["nodes"]["transform"]["variables"]
        assert variables["verb"] == "{state.verb}"
        assert variables["source"] == "{state.source}"

    @pytest.mark.req("REQ-YG-467")
    def test_transform_requires_source(self) -> None:
        """transform must declare it requires source (no LLM call before read)."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        assert "source" in raw["nodes"]["transform"]["requires"]

    @pytest.mark.req("REQ-YG-467")
    def test_state_declares_verb_and_target(self) -> None:
        """State block must declare verb and target as inputs."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        assert raw["state"]["verb"] == "str"
        assert raw["state"]["target"] == "str"

    @pytest.mark.req("REQ-YG-467")
    def test_no_hardcoded_model(self) -> None:
        """No hardcoded model — uses PROVIDER/MODEL env var fallthrough."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        assert "model" not in raw["nodes"]["transform"]

    @pytest.mark.req("REQ-YG-467")
    def test_prompt_has_structured_schema(self) -> None:
        """meta_transform prompt must define a typed schema (no free-text output)."""
        prompt = yaml.safe_load(
            (DEMO_DIR / "prompts" / "meta_transform.yaml").read_text()
        )
        schema = prompt["schema"]
        assert schema["name"] == "MetaResult"
        expected_fields = {"summary", "findings", "suggested_code"}
        assert set(schema["fields"].keys()) == expected_fields

    @pytest.mark.req("REQ-YG-467")
    def test_prompt_uses_verb_and_source(self) -> None:
        """Prompt must reference the verb and source variables."""
        prompt_text = (DEMO_DIR / "prompts" / "meta_transform.yaml").read_text()
        assert "{verb}" in prompt_text
        assert "{source}" in prompt_text

    @pytest.mark.req("REQ-YG-467")
    def test_graph_compiles(self) -> None:
        """Graph compiles to a LangGraph StateGraph."""
        from yamlgraph.compile.graph_loader import compile_graph, load_graph_config

        config = load_graph_config(GRAPH_PATH)
        graph = compile_graph(config)
        assert graph is not None

    @pytest.mark.req("REQ-YG-467")
    def test_demo_sh_exists_and_executable(self) -> None:
        """demo.sh must exist and be executable."""
        demo_sh = DEMO_DIR / "demo.sh"
        assert demo_sh.is_file()
        assert demo_sh.stat().st_mode & 0o111

    @pytest.mark.req("REQ-YG-467")
    def test_demo_sh_accepts_verb_and_target(self) -> None:
        """demo.sh must accept verb and target arguments and run the graph."""
        content = (DEMO_DIR / "demo.sh").read_text()
        assert "yamlgraph graph run" in content
        assert "examples/demos/meta/graph.yaml" in content
        assert "--var verb=" in content
        assert "--var target=" in content

    @pytest.mark.req("REQ-YG-467")
    def test_readme_documents_meta_js_lineage(self) -> None:
        """README must document the meta.js lineage and the typed/traced upgrade."""
        content = (DEMO_DIR / "README.md").read_text()
        assert "meta.js" in content
        assert "self-ref" in content.lower() or "self-reference" in content.lower()
