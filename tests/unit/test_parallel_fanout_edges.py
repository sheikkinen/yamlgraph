"""Tests for parallel fan-out edges (FR-234).

TDD RED phase: These tests define the expected behavior for parallel fan-out
edges where `to: [a, b, c]` without `type: conditional` means "run all targets
concurrently" — as opposed to conditional routing which picks one target.

REQ-YG-235: Parallel fan-out edges compile to multiple add_edge() calls,
handle interrupt/map node targets, work from START, and pass linter checks.
"""

from unittest.mock import MagicMock, call

import pytest

from yamlgraph.edge_compiler import _process_edge
from yamlgraph.graph_loader import compile_graph, load_graph_config

# =============================================================================
# Fixtures
# =============================================================================


def _make_fanout_yaml(tmp_path, *, extra_nodes="", extra_edges="", extra_top=""):
    """Create a YAML graph with parallel fan-out edges."""
    yaml_content = f"""
version: "1.0"
name: fanout_test
{extra_top}

nodes:
  generate:
    type: llm
    prompt: generate
    state_key: generated

  analyze:
    type: llm
    prompt: analyze
    state_key: analysis

  summarize:
    type: llm
    prompt: summarize
    state_key: summary

  translate:
    type: llm
    prompt: translate
    state_key: translation

  final:
    type: llm
    prompt: final
    state_key: result
{extra_nodes}

edges:
  - from: START
    to: generate
  - from: generate
    to: [analyze, summarize, translate]
  - from: analyze
    to: final
  - from: summarize
    to: final
  - from: translate
    to: final
  - from: final
    to: END
{extra_edges}
"""
    yaml_file = tmp_path / "fanout.yaml"
    yaml_file.write_text(yaml_content)
    return yaml_file


# =============================================================================
# TestParallelFanOutEdgeCompilation
# =============================================================================


class TestParallelFanOutEdgeCompilation:
    """Tests for parallel fan-out edge compilation (FR-234)."""

    @pytest.mark.req("REQ-YG-235")
    def test_parallel_fanout_compiles_graph(self, tmp_path):
        """Graph with to: [a, b, c] (no type: conditional) should compile."""
        yaml_file = _make_fanout_yaml(tmp_path)
        config = load_graph_config(yaml_file)
        graph = compile_graph(config)
        compiled = graph.compile()

        assert compiled is not None
        assert "analyze" in graph.nodes
        assert "summarize" in graph.nodes
        assert "translate" in graph.nodes

    @pytest.mark.req("REQ-YG-235")
    def test_parallel_fanout_adds_multiple_edges(self):
        """Fan-out edge should add one edge per target, not a single list edge."""
        mock_graph = MagicMock()

        edge = {"from": "generate", "to": ["analyze", "summarize", "translate"]}
        _process_edge(edge, mock_graph, {}, {}, {})

        # Should have called add_edge three times — one per target
        add_edge_calls = mock_graph.add_edge.call_args_list
        assert call("generate", "analyze") in add_edge_calls
        assert call("generate", "summarize") in add_edge_calls
        assert call("generate", "translate") in add_edge_calls
        assert len(add_edge_calls) == 3

    @pytest.mark.req("REQ-YG-235")
    def test_parallel_fanout_not_confused_with_conditional(self):
        """Fan-out edge without type: conditional must NOT create router edges."""
        mock_graph = MagicMock()
        router_edges: dict = {}

        edge = {"from": "generate", "to": ["analyze", "summarize"]}
        _process_edge(edge, mock_graph, {}, router_edges, {})

        # Should NOT add to router_edges
        assert "generate" not in router_edges
        # Should add direct edges
        assert mock_graph.add_edge.call_count == 2

    @pytest.mark.req("REQ-YG-235")
    def test_conditional_edge_still_routes_to_one(self):
        """type: conditional with list targets must still be router (not fan-out)."""
        mock_graph = MagicMock()
        router_edges: dict = {}

        edge = {
            "from": "classify",
            "to": ["positive", "negative"],
            "type": "conditional",
        }
        _process_edge(edge, mock_graph, {}, router_edges, {})

        # Should add to router_edges, NOT add direct edges
        assert "classify" in router_edges
        assert mock_graph.add_edge.call_count == 0

    @pytest.mark.req("REQ-YG-235")
    def test_parallel_fanout_with_end_target(self):
        """Fan-out with END as one target should use END constant."""
        mock_graph = MagicMock()

        edge = {"from": "generate", "to": ["analyze", "END"]}
        _process_edge(edge, mock_graph, {}, {}, {})

        from langgraph.graph import END

        add_edge_calls = mock_graph.add_edge.call_args_list
        assert call("generate", "analyze") in add_edge_calls
        assert call("generate", END) in add_edge_calls

    @pytest.mark.req("REQ-YG-235")
    def test_parallel_fanout_with_interrupt_redirect(self):
        """Fan-out targets in interrupt_nodes should be redirected to _prepare."""
        mock_graph = MagicMock()
        interrupt_nodes = {"analyze"}

        edge = {"from": "generate", "to": ["analyze", "summarize"]}
        _process_edge(edge, mock_graph, {}, {}, {}, interrupt_nodes)

        add_edge_calls = mock_graph.add_edge.call_args_list
        assert call("generate", "analyze_prepare") in add_edge_calls
        assert call("generate", "summarize") in add_edge_calls

    @pytest.mark.req("REQ-YG-235")
    def test_parallel_fanout_with_map_target(self):
        """Fan-out with a map node target uses map edge function."""
        mock_graph = MagicMock()
        mock_map_fn = MagicMock()
        map_nodes = {"expand": (mock_map_fn, "expand_sub")}

        edge = {"from": "generate", "to": ["analyze", "expand"]}
        _process_edge(edge, mock_graph, map_nodes, {}, {})

        # Regular target gets add_edge
        assert call("generate", "analyze") in mock_graph.add_edge.call_args_list
        # Map target gets conditional edge with map function
        mock_graph.add_conditional_edges.assert_called_once_with(
            "generate", mock_map_fn, ["expand_sub"]
        )

    @pytest.mark.req("REQ-YG-235")
    def test_parallel_fanout_single_target_list(self):
        """to: [single] should work the same as to: single."""
        mock_graph = MagicMock()

        edge = {"from": "generate", "to": ["analyze"]}
        _process_edge(edge, mock_graph, {}, {}, {})

        mock_graph.add_edge.assert_called_once_with("generate", "analyze")


# =============================================================================
# TestParallelFanOutFromStart
# =============================================================================


class TestParallelFanOutFromStart:
    """Tests for parallel fan-out from START node (FR-234)."""

    @pytest.mark.req("REQ-YG-235")
    def test_start_fanout_compiles(self, tmp_path):
        """START -> [a, b] should compile into a working graph."""
        yaml_content = """
version: "1.0"
name: start_fanout

nodes:
  analyze:
    type: llm
    prompt: analyze
    state_key: analysis
  summarize:
    type: llm
    prompt: summarize
    state_key: summary
  final:
    type: llm
    prompt: final
    state_key: result

edges:
  - from: START
    to: [analyze, summarize]
  - from: analyze
    to: final
  - from: summarize
    to: final
  - from: final
    to: END
"""
        yaml_file = tmp_path / "start_fanout.yaml"
        yaml_file.write_text(yaml_content)

        config = load_graph_config(yaml_file)
        graph = compile_graph(config)
        compiled = graph.compile()

        assert compiled is not None
        assert "analyze" in graph.nodes
        assert "summarize" in graph.nodes


# =============================================================================
# TestParallelFanOutLinter
# =============================================================================


class TestParallelFanOutLinter:
    """Tests that linter works correctly with parallel fan-out edges."""

    @pytest.mark.req("REQ-YG-235")
    def test_fanout_nodes_reachable(self, tmp_path):
        """All fan-out targets should be reachable from START (no W002)."""
        from yamlgraph.linter.checks import check_edge_coverage

        yaml_file = _make_fanout_yaml(tmp_path)
        issues = check_edge_coverage(yaml_file)

        # No unreachable node warnings
        w002_issues = [i for i in issues if i.code == "W002"]
        assert w002_issues == [], f"Unexpected W002 issues: {w002_issues}"

    @pytest.mark.req("REQ-YG-235")
    def test_fanout_nodes_reach_end(self, tmp_path):
        """All fan-out targets should have paths to END (no W003)."""
        from yamlgraph.linter.checks import check_edge_coverage

        yaml_file = _make_fanout_yaml(tmp_path)
        issues = check_edge_coverage(yaml_file)

        # No dead-end warnings
        w003_issues = [i for i in issues if i.code == "W003"]
        assert w003_issues == [], f"Unexpected W003 issues: {w003_issues}"
