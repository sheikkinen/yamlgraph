"""Tests for shared invoke_graph — FR-255.

RED phase: tests written before implementation.
Verifies that graph_loader.invoke_graph provides a single entry point
for synchronous graph invocation, replacing duplicated _invoke_graph
functions in mcp_server and a2a_server.
"""

from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# REQ-YG-258: Shared invoke_graph function
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-258")
def test_invoke_graph_exists_in_graph_loader():
    """invoke_graph is importable from graph_loader."""
    from yamlgraph.graph_loader import invoke_graph

    assert callable(invoke_graph)


@pytest.mark.req("REQ-YG-258")
def test_invoke_graph_calls_pipeline():
    """invoke_graph calls load_graph_config → compile_graph → compile → invoke."""
    mock_compiled = MagicMock()
    mock_compiled.invoke.return_value = {"greeting": "Hello!"}

    mock_sg = MagicMock()
    mock_sg.compile.return_value = mock_compiled

    mock_config = MagicMock()

    with (
        patch(
            "yamlgraph.graph_loader.load_graph_config", return_value=mock_config
        ) as mock_load,
        patch(
            "yamlgraph.graph_loader.compile_graph", return_value=mock_sg
        ) as mock_compile,
    ):
        from yamlgraph.graph_loader import invoke_graph

        result = invoke_graph("/fake/graph.yaml", {"name": "World"})

    mock_load.assert_called_once_with("/fake/graph.yaml")
    mock_compile.assert_called_once_with(mock_config)
    mock_sg.compile.assert_called_once()
    mock_compiled.invoke.assert_called_once_with({"name": "World"}, config={})
    assert result == {"greeting": "Hello!"}


@pytest.mark.req("REQ-YG-258")
def test_invoke_graph_passes_config():
    """invoke_graph forwards optional config to compiled.invoke."""
    mock_compiled = MagicMock()
    mock_compiled.invoke.return_value = {}

    mock_sg = MagicMock()
    mock_sg.compile.return_value = mock_compiled

    with (
        patch("yamlgraph.graph_loader.load_graph_config", return_value=MagicMock()),
        patch("yamlgraph.graph_loader.compile_graph", return_value=mock_sg),
    ):
        from yamlgraph.graph_loader import invoke_graph

        run_config = {"configurable": {"thread_id": "t1"}}
        invoke_graph("/fake/graph.yaml", {"x": "1"}, config=run_config)

    mock_compiled.invoke.assert_called_once_with({"x": "1"}, config=run_config)


@pytest.mark.req("REQ-YG-258")
def test_invoke_graph_accepts_path_object():
    """invoke_graph accepts pathlib.Path as well as str."""
    from pathlib import Path

    mock_compiled = MagicMock()
    mock_compiled.invoke.return_value = {"out": "ok"}

    mock_sg = MagicMock()
    mock_sg.compile.return_value = mock_compiled

    with (
        patch("yamlgraph.graph_loader.load_graph_config", return_value=MagicMock()),
        patch("yamlgraph.graph_loader.compile_graph", return_value=mock_sg),
    ):
        from yamlgraph.graph_loader import invoke_graph

        result = invoke_graph(Path("/fake/graph.yaml"), {"key": "val"})

    assert result == {"out": "ok"}


# ---------------------------------------------------------------------------
# Consumer delegation tests
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-258")
def test_mcp_server_delegates_to_shared_invoke_graph():
    """mcp_server._invoke_graph delegates to graph_loader.invoke_graph."""
    pytest.importorskip("mcp")

    with patch(
        "yamlgraph.graph_loader.invoke_graph", return_value={"greeting": "Hi"}
    ) as mock_invoke:
        from yamlgraph.mcp_server import _invoke_graph

        result = _invoke_graph("/path/graph.yaml", {"name": "Test"})

    mock_invoke.assert_called_once_with("/path/graph.yaml", {"name": "Test"})
    assert result == {"greeting": "Hi"}


@pytest.mark.req("REQ-YG-258")
def test_a2a_server_delegates_to_shared_invoke_graph():
    """a2a_server._invoke_graph delegates to graph_loader.invoke_graph."""
    pytest.importorskip("a2a")

    with patch(
        "yamlgraph.graph_loader.invoke_graph", return_value={"out": "done"}
    ) as mock_invoke:
        from yamlgraph.a2a.server import _invoke_graph

        result = _invoke_graph("/path/graph.yaml", {"x": "1"})

    mock_invoke.assert_called_once_with("/path/graph.yaml", {"x": "1"})
    assert result == {"out": "done"}
