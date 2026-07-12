"""Tests for shared graph discovery — REQ-YG-206.

Verifies that discover_graphs() works from the shared module,
and that mcp_server.py re-exports it correctly.
"""

from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# REQ-YG-206: Shared discovery module
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-206")
def test_discover_graphs_importable_from_discovery():
    """discover_graphs is importable from yamlgraph.discovery."""
    from yamlgraph.discovery import discover_graphs

    assert callable(discover_graphs)


@pytest.mark.req("REQ-YG-206")
def test_default_patterns_importable_from_discovery():
    """DEFAULT_GRAPH_PATTERNS is importable from yamlgraph.discovery."""
    from yamlgraph.discovery import DEFAULT_GRAPH_PATTERNS

    assert isinstance(DEFAULT_GRAPH_PATTERNS, list)
    assert len(DEFAULT_GRAPH_PATTERNS) > 0


@pytest.mark.req("REQ-YG-206")
def test_mcp_server_uses_shared_discovery():
    """mcp_server.discover_graphs is the same function as discovery.discover_graphs."""
    mcp = pytest.importorskip("mcp")  # noqa: F841 (CONF-034)
    from yamlgraph.discovery import discover_graphs as shared_discover
    from yamlgraph.export.mcp import discover_graphs as mcp_discover

    assert shared_discover is mcp_discover


@pytest.mark.req("REQ-YG-206")
def test_discover_graphs_finds_yaml(tmp_path: Path):
    """discover_graphs finds graph YAML files via shared module."""
    from yamlgraph.discovery import discover_graphs

    graph_dir = tmp_path / "demo"
    graph_dir.mkdir()
    (graph_dir / "graph.yaml").write_text(
        "version: '1.0'\nname: test-graph\n"
        "description: A test graph\n"
        "state:\n  topic: str\n"
        "nodes:\n  greet:\n    type: llm\n    prompt: greet\n    state_key: greeting\n"
        "edges:\n  - from: START\n    to: greet\n  - from: greet\n    to: END\n"
    )

    graphs = discover_graphs([str(tmp_path / "*/graph.yaml")])
    assert len(graphs) == 1
    assert graphs[0]["name"] == "test-graph"
    assert graphs[0]["description"] == "A test graph"
    assert "topic" in graphs[0]["required_vars"]


@pytest.mark.req("REQ-YG-206")
def test_discover_graphs_deduplicates(tmp_path: Path):
    """Multiple patterns matching same file produce only one entry."""
    from yamlgraph.discovery import discover_graphs

    graph_dir = tmp_path / "demo"
    graph_dir.mkdir()
    (graph_dir / "graph.yaml").write_text(
        "nodes:\n  n1:\n    type: llm\n    prompt: p\n    state_key: out\n"
        "edges:\n  - from: START\n    to: n1\n  - from: n1\n    to: END\n"
    )

    # Two patterns that match the same file
    graphs = discover_graphs(
        [
            str(tmp_path / "*/graph.yaml"),
            str(tmp_path / "demo/*.yaml"),
        ]
    )
    assert len(graphs) == 1
