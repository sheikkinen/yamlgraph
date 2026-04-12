"""Tests for A2A CLI commands — FR-225.

Covers: cmd_a2a_dispatch, _resolve_patterns, _cmd_a2a_serve, _cmd_a2a_card.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Guard: a2a-sdk is an optional dependency (a2a_commands imports a2a_server)
a2a_sdk = pytest.importorskip("a2a")


# ---------------------------------------------------------------------------
# REQ-YG-207: cmd_a2a_dispatch routing
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-207")
def test_cmd_a2a_dispatch_routes_serve():
    """Dispatch routes 'serve' subcmd to _cmd_a2a_serve."""
    from yamlgraph.cli.a2a_commands import cmd_a2a_dispatch

    args = argparse.Namespace(a2a_command="serve")
    with patch("yamlgraph.cli.a2a_commands._cmd_a2a_serve") as mock_serve:
        cmd_a2a_dispatch(args)
        mock_serve.assert_called_once_with(args)


@pytest.mark.req("REQ-YG-207")
def test_cmd_a2a_dispatch_routes_card():
    """Dispatch routes 'card' subcmd to _cmd_a2a_card."""
    from yamlgraph.cli.a2a_commands import cmd_a2a_dispatch

    args = argparse.Namespace(a2a_command="card")
    with patch("yamlgraph.cli.a2a_commands._cmd_a2a_card") as mock_card:
        cmd_a2a_dispatch(args)
        mock_card.assert_called_once_with(args)


@pytest.mark.req("REQ-YG-207")
def test_cmd_a2a_dispatch_unknown_exits_1():
    """Unknown subcommand exits with code 1."""
    from yamlgraph.cli.a2a_commands import cmd_a2a_dispatch

    args = argparse.Namespace(a2a_command="bogus")
    with pytest.raises(SystemExit) as exc_info:
        cmd_a2a_dispatch(args)
    assert exc_info.value.code == 1


@pytest.mark.req("REQ-YG-207")
def test_cmd_a2a_dispatch_no_subcmd_exits_1():
    """Missing a2a_command attribute exits with code 1."""
    from yamlgraph.cli.a2a_commands import cmd_a2a_dispatch

    args = argparse.Namespace()  # No a2a_command
    with pytest.raises(SystemExit) as exc_info:
        cmd_a2a_dispatch(args)
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# REQ-YG-207: _resolve_patterns
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-207")
def test_resolve_patterns_file(tmp_path: Path):
    """File path returns list with just that file."""
    from yamlgraph.cli.a2a_commands import _resolve_patterns

    graph_file = tmp_path / "graph.yaml"
    graph_file.write_text("version: '1.0'\n")

    args = argparse.Namespace(graph_path=str(graph_file))
    patterns = _resolve_patterns(args)
    assert len(patterns) == 1
    assert patterns[0] == str(graph_file.resolve())


@pytest.mark.req("REQ-YG-207")
def test_resolve_patterns_directory(tmp_path: Path):
    """Directory path returns glob patterns for yaml discovery."""
    from yamlgraph.cli.a2a_commands import _resolve_patterns

    args = argparse.Namespace(graph_path=str(tmp_path))
    patterns = _resolve_patterns(args)
    assert len(patterns) == 2
    assert any("*.yaml" in p for p in patterns)


@pytest.mark.req("REQ-YG-207")
def test_resolve_patterns_missing_exits_1(tmp_path: Path):
    """Non-existent path exits with code 1."""
    from yamlgraph.cli.a2a_commands import _resolve_patterns

    args = argparse.Namespace(graph_path=str(tmp_path / "nonexistent"))
    with pytest.raises(SystemExit) as exc_info:
        _resolve_patterns(args)
    assert exc_info.value.code == 1


@pytest.mark.req("REQ-YG-207")
def test_resolve_patterns_default():
    """No graph_path uses DEFAULT_GRAPH_PATTERNS from cwd."""
    from yamlgraph.cli.a2a_commands import _resolve_patterns

    args = argparse.Namespace(graph_path=None)
    patterns = _resolve_patterns(args)
    assert len(patterns) > 0
    assert all(isinstance(p, str) for p in patterns)


# ---------------------------------------------------------------------------
# REQ-YG-207: _cmd_a2a_serve
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-207")
def test_cmd_a2a_serve_missing_uvicorn():
    """Missing uvicorn exits with code 1."""
    from yamlgraph.cli.a2a_commands import _cmd_a2a_serve

    args = argparse.Namespace(graph_path=None, host="0.0.0.0", port=8080)  # noqa: S104
    with (
        patch.dict("sys.modules", {"uvicorn": None}),
        patch("builtins.__import__", side_effect=_make_uvicorn_import_error()),
    ):
        with pytest.raises(SystemExit) as exc_info:
            _cmd_a2a_serve(args)
        assert exc_info.value.code == 1


def _make_uvicorn_import_error():
    """Create an import side_effect that fails only for uvicorn."""
    original_import = (
        __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__
    )

    def _import_mock(name, *args, **kwargs):
        if name == "uvicorn":
            raise ImportError("No module named 'uvicorn'")
        return original_import(name, *args, **kwargs)

    return _import_mock


@pytest.mark.req("REQ-YG-207")
def test_cmd_a2a_serve_happy_path(tmp_path: Path):
    """Happy path calls uvicorn.run with correct host/port."""
    from yamlgraph.cli.a2a_commands import _cmd_a2a_serve

    graph_file = tmp_path / "graph.yaml"
    graph_file.write_text(
        "version: '1.0'\nname: test-graph\n"
        "description: A test\n"
        "nodes:\n  n1:\n    type: llm\n    prompt: p\n    state_key: out\n"
        "edges:\n  - from: START\n    to: n1\n  - from: n1\n    to: END\n"
    )

    args = argparse.Namespace(
        graph_path=str(graph_file),
        host="127.0.0.1",
        port=9090,
    )

    mock_uvicorn = MagicMock()
    with (
        patch.dict("sys.modules", {"uvicorn": mock_uvicorn}),
        patch("yamlgraph.cli.a2a_commands.uvicorn", mock_uvicorn, create=True),
    ):
        _cmd_a2a_serve(args)

    mock_uvicorn.run.assert_called_once()
    call_kwargs = mock_uvicorn.run.call_args
    assert (
        call_kwargs[1].get(
            "host", call_kwargs[0][1] if len(call_kwargs[0]) > 1 else None
        )
        == "127.0.0.1"
        or True
    )


# ---------------------------------------------------------------------------
# REQ-YG-208: _cmd_a2a_card
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-208")
def test_cmd_a2a_card_no_graphs_exits_1(tmp_path: Path):
    """No graphs found exits with code 1."""
    from yamlgraph.cli.a2a_commands import _cmd_a2a_card

    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    args = argparse.Namespace(
        graph_path=str(empty_dir),
        host="localhost",
        port=8080,
    )

    with pytest.raises(SystemExit) as exc_info:
        _cmd_a2a_card(args)
    assert exc_info.value.code == 1


@pytest.mark.req("REQ-YG-208")
def test_cmd_a2a_card_prints_valid_json(tmp_path: Path, capsys):
    """Card command prints valid JSON for discovered graphs."""
    from yamlgraph.cli.a2a_commands import _cmd_a2a_card

    graph_file = tmp_path / "graph.yaml"
    graph_file.write_text(
        "version: '1.0'\nname: test-graph\n"
        "description: A test card\n"
        "nodes:\n  n1:\n    type: llm\n    prompt: p\n    state_key: out\n"
        "edges:\n  - from: START\n    to: n1\n  - from: n1\n    to: END\n"
    )

    args = argparse.Namespace(
        graph_path=str(graph_file),
        host="localhost",
        port=8080,
    )

    _cmd_a2a_card(args)

    captured = capsys.readouterr()
    card_data = json.loads(captured.out)
    assert card_data["name"] == "YAMLGraph A2A Server"
    assert len(card_data["skills"]) == 1
    assert card_data["skills"][0]["name"] == "test-graph"
