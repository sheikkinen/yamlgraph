"""Tests for CLI --stream flag (FR-633).

Verifies that `yamlgraph graph run --stream` uses run_graph_streaming_native()
and prints tokens to stdout.
"""

from argparse import Namespace
from unittest.mock import patch

import pytest


@pytest.mark.req("REQ-YG-480")
def test_stream_flag_prints_tokens(capsys, tmp_path):
    """--stream should print tokens to stdout as they arrive."""
    graph_file = tmp_path / "graph.yaml"
    graph_file.write_text("""
name: test-stream
nodes:
  greet:
    prompt: greet
edges:
  - from: START
    to: greet
  - from: greet
    to: END
""")

    async def mock_stream(*args, **kwargs):
        for token in ["Hello", " ", "World"]:
            yield token

    args = Namespace(
        graph_path=str(graph_file),
        var=[],
        var_file=None,
        thread=None,
        export=False,
        full=False,
        json=False,
        stream=True,
        use_async=False,
        share_trace=False,
        recursion_limit=None,
        timeout=None,
        token_usage=False,
        timing=False,
        import_state=None,
        export_state=None,
    )

    with patch(
        "yamlgraph.cli.graph_commands.run_graph_streaming_native",
        side_effect=mock_stream,
    ):
        from yamlgraph.cli.graph_commands import cmd_graph_run

        cmd_graph_run(args)

    captured = capsys.readouterr()
    assert "Hello World" in captured.out


@pytest.mark.req("REQ-YG-480")
def test_stream_and_json_mutually_exclusive(capsys, tmp_path):
    """--stream + --json should exit with error."""
    graph_file = tmp_path / "graph.yaml"
    graph_file.write_text("""
name: test
nodes:
  greet:
    prompt: greet
edges:
  - from: START
    to: greet
  - from: greet
    to: END
""")

    args = Namespace(
        graph_path=str(graph_file),
        var=[],
        var_file=None,
        thread=None,
        export=False,
        full=False,
        json=True,
        stream=True,
        use_async=False,
        share_trace=False,
        recursion_limit=None,
        timeout=None,
        token_usage=False,
        timing=False,
        import_state=None,
        export_state=None,
    )

    from yamlgraph.cli.graph_commands import cmd_graph_run

    with pytest.raises(SystemExit):
        cmd_graph_run(args)

    captured = capsys.readouterr()
    assert "mutually exclusive" in captured.err or "mutually exclusive" in captured.out


@pytest.mark.req("REQ-YG-480")
def test_stream_error_event_prints_to_stderr(capsys, tmp_path):
    """StreamEvent errors should print to stderr."""
    from yamlgraph.models.streaming import StreamEvent

    graph_file = tmp_path / "graph.yaml"
    graph_file.write_text("""
name: test-stream-err
nodes:
  greet:
    prompt: greet
edges:
  - from: START
    to: greet
  - from: greet
    to: END
""")

    async def mock_stream_with_error(*args, **kwargs):
        yield "partial"
        yield StreamEvent(type="error", error="LLM timeout", error_type="TimeoutError")

    args = Namespace(
        graph_path=str(graph_file),
        var=[],
        var_file=None,
        thread=None,
        export=False,
        full=False,
        json=False,
        stream=True,
        use_async=False,
        share_trace=False,
        recursion_limit=None,
        timeout=None,
        token_usage=False,
        timing=False,
        import_state=None,
        export_state=None,
    )

    with patch(
        "yamlgraph.cli.graph_commands.run_graph_streaming_native",
        side_effect=mock_stream_with_error,
    ):
        from yamlgraph.cli.graph_commands import cmd_graph_run

        cmd_graph_run(args)

    captured = capsys.readouterr()
    assert "partial" in captured.out
    assert "LLM timeout" in captured.err
