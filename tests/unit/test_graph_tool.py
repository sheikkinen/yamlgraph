"""Tests for graph-as-tool: type: graph tool that invokes a pipeline in-process.

FR-658: Graph-as-Tool — In-Process Pipeline Invocation.
"""

from contextvars import ContextVar
from unittest.mock import MagicMock

import pytest

from yamlgraph.tools.graph_tool import build_graph_tool, make_graph_tool_fn

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_loading_stack():
    """A fresh ContextVar for circular reference detection."""
    return ContextVar("test_loading_stack")


@pytest.fixture
def mock_compiled():
    """A mock compiled graph that returns a result dict."""
    compiled = MagicMock()
    compiled.invoke.return_value = {"result": "ok", "tone": "formal"}
    return compiled


@pytest.fixture
def graph_path(tmp_path):
    return (tmp_path / "child.yaml").resolve()


# ---------------------------------------------------------------------------
# AC-3: StructuredTool with inputSchema from input_mapping keys
# ---------------------------------------------------------------------------


class TestBuildGraphTool:
    """AC-3: Schema generated from input_mapping keys."""

    @pytest.mark.req("REQ-YG-510")
    def test_returns_structured_tool(
        self, mock_compiled, graph_path, mock_loading_stack
    ):
        from langchain_core.tools import StructuredTool

        fn = make_graph_tool_fn(
            mock_compiled,
            {"text": "text", "style": "style"},
            "result",
            graph_path,
            mock_loading_stack,
        )
        config = {
            "description": "Analyze tone",
            "input_mapping": {"text": "text", "style": "style"},
        }
        tool = build_graph_tool("analyzer", config, fn)
        assert isinstance(tool, StructuredTool)
        assert tool.name == "analyzer"
        assert tool.description == "Analyze tone"

    @pytest.mark.req("REQ-YG-510")
    def test_schema_fields_from_input_mapping_keys(
        self, mock_compiled, graph_path, mock_loading_stack
    ):
        fn = make_graph_tool_fn(
            mock_compiled,
            {"text": "text", "style": "style"},
            "result",
            graph_path,
            mock_loading_stack,
        )
        config = {
            "description": "Analyze tone",
            "input_mapping": {"text": "text", "style": "style"},
        }
        tool = build_graph_tool("analyzer", config, fn)
        schema = tool.args_schema.model_json_schema()
        assert "text" in schema["properties"]
        assert "style" in schema["properties"]


# ---------------------------------------------------------------------------
# AC-4: Circular reference detection at invocation time
# ---------------------------------------------------------------------------


class TestCircularReferenceDetection:
    """AC-4: Circular reference guard at invocation time."""

    @pytest.mark.req("REQ-YG-510")
    def test_circular_reference_returns_error_text(
        self, mock_compiled, graph_path, mock_loading_stack
    ):
        """Circular reference is caught and returned as error text, not raised."""
        fn = make_graph_tool_fn(
            mock_compiled,
            {"x": "x"},
            "result",
            graph_path,
            mock_loading_stack,
        )

        # Simulate parent already on the stack
        token = mock_loading_stack.set([graph_path])
        try:
            result = fn(x="hello")
            assert "Error" in result
            assert "Circular" in result
        finally:
            mock_loading_stack.reset(token)


# ---------------------------------------------------------------------------
# AC-8: Compile once, invoke many
# ---------------------------------------------------------------------------


class TestCompileOnceInvokeMany:
    """AC-8: Child graph compiled once at parse time."""

    @pytest.mark.req("REQ-YG-510")
    def test_callable_invokes_precompiled_graph(
        self, mock_compiled, graph_path, mock_loading_stack
    ):
        """The callable should use the pre-compiled graph, not re-compile."""
        fn = make_graph_tool_fn(
            mock_compiled,
            {"text": "text"},
            "result",
            graph_path,
            mock_loading_stack,
        )

        # Invoke twice — same compiled graph used both times
        fn(text="hello")
        fn(text="world")
        assert mock_compiled.invoke.call_count == 2

    @pytest.mark.req("REQ-YG-510")
    def test_input_mapping_applied(self, mock_compiled, graph_path, mock_loading_stack):
        """Tool kwargs are mapped to graph variables via input_mapping."""
        fn = make_graph_tool_fn(
            mock_compiled,
            {"user_text": "input_text"},
            "result",
            graph_path,
            mock_loading_stack,
        )
        fn(user_text="hello world")
        mock_compiled.invoke.assert_called_once_with({"input_text": "hello world"})

    @pytest.mark.req("REQ-YG-510")
    def test_output_key_extraction(self, mock_compiled, graph_path, mock_loading_stack):
        """Tool extracts the specified output_key from the result."""
        fn = make_graph_tool_fn(
            mock_compiled,
            {"text": "text"},
            "tone",
            graph_path,
            mock_loading_stack,
        )
        result = fn(text="hello")
        assert result == "formal"

    @pytest.mark.req("REQ-YG-510")
    def test_default_variables_injected(
        self, mock_compiled, graph_path, mock_loading_stack
    ):
        """Graph-level variables from child config are injected as defaults."""
        fn = make_graph_tool_fn(
            mock_compiled,
            {"name": "name"},
            "result",
            graph_path,
            mock_loading_stack,
            default_variables={"entity_type": "faction"},
        )
        fn(name="The Order")
        mock_compiled.invoke.assert_called_once_with(
            {"entity_type": "faction", "name": "The Order"}
        )

    @pytest.mark.req("REQ-YG-510")
    def test_tool_kwargs_override_default_variables(
        self, mock_compiled, graph_path, mock_loading_stack
    ):
        """Tool kwargs override default_variables if same key is mapped."""
        fn = make_graph_tool_fn(
            mock_compiled,
            {"entity_type": "entity_type", "name": "name"},
            "result",
            graph_path,
            mock_loading_stack,
            default_variables={"entity_type": "faction"},
        )
        fn(entity_type="character", name="Alice")
        mock_compiled.invoke.assert_called_once_with(
            {"entity_type": "character", "name": "Alice"}
        )


# ---------------------------------------------------------------------------
# AC-9: Error surfacing
# ---------------------------------------------------------------------------


class TestErrorSurfacing:
    """AC-9: Pipeline errors returned as text, not raised."""

    @pytest.mark.req("REQ-YG-510")
    def test_pipeline_error_returns_error_text(self, graph_path, mock_loading_stack):
        compiled = MagicMock()
        compiled.invoke.side_effect = RuntimeError("Pipeline exploded")
        fn = make_graph_tool_fn(
            compiled,
            {"x": "x"},
            "result",
            graph_path,
            mock_loading_stack,
        )
        result = fn(x="boom")
        assert "Error" in result
        assert "Pipeline exploded" in result


# ---------------------------------------------------------------------------
# AC-1 / AC-2 / AC-8: Integration via _parse_graph_tools (Layer 2)
# ---------------------------------------------------------------------------


class TestParseGraphToolsIntegration:
    """Test _parse_graph_tools in graph_loader parses type: graph tools."""

    @pytest.mark.req("REQ-YG-510")
    def test_parse_filters_graph_type(self, tmp_path):
        """Only type: graph tools are parsed; Python tools are ignored."""
        child_yaml = tmp_path / "child.yaml"
        child_yaml.write_text(
            """\
version: "1.0"
name: child-pipeline
description: A test child pipeline

nodes:
  echo:
    type: passthrough
    state_key: result

edges:
  - from: START
    to: echo
  - from: echo
    to: END
"""
        )
        parent_yaml = tmp_path / "parent.yaml"
        # Create a minimal GraphConfig-like object
        from yamlgraph.graph_loader import GraphConfig, _parse_graph_tools

        config = GraphConfig(
            {
                "version": "1.0",
                "name": "parent",
                "nodes": {"dummy": {"type": "passthrough", "state_key": "x"}},
                "edges": [
                    {"from": "START", "to": "dummy"},
                    {"from": "dummy", "to": "END"},
                ],
                "tools": {
                    "my_graph_tool": {
                        "type": "graph",
                        "path": str(child_yaml),
                        "description": "Test graph tool",
                        "input_mapping": {"text": "text"},
                        "output_key": "result",
                    },
                    "my_python_tool": {
                        "type": "python",
                        "path": "some_module.py",
                        "function": "do_thing",
                    },
                },
            },
            source_path=parent_yaml,
        )
        graph_tools, callables = _parse_graph_tools(config)
        assert "my_graph_tool" in graph_tools
        assert "my_python_tool" not in graph_tools
        assert "my_graph_tool" in callables

    @pytest.mark.req("REQ-YG-510")
    def test_description_defaults_to_child_graph(self, tmp_path):
        """When description is omitted, use child graph's description."""
        child_yaml = tmp_path / "child.yaml"
        child_yaml.write_text(
            """\
version: "1.0"
name: child-pipeline
description: A test child pipeline

nodes:
  echo:
    type: passthrough
    state_key: result

edges:
  - from: START
    to: echo
  - from: echo
    to: END
"""
        )
        parent_yaml = tmp_path / "parent.yaml"
        from yamlgraph.graph_loader import GraphConfig, _parse_graph_tools

        config = GraphConfig(
            {
                "version": "1.0",
                "name": "parent",
                "nodes": {"dummy": {"type": "passthrough", "state_key": "x"}},
                "edges": [
                    {"from": "START", "to": "dummy"},
                    {"from": "dummy", "to": "END"},
                ],
                "tools": {
                    "analyzer": {
                        "type": "graph",
                        "path": str(child_yaml),
                        "input_mapping": {"text": "text"},
                    },
                },
            },
            source_path=parent_yaml,
        )
        graph_tools, _ = _parse_graph_tools(config)
        assert graph_tools["analyzer"]["description"] == "A test child pipeline"
