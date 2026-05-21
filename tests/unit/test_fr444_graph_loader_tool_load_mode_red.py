"""RED acceptance tests for FR-444 strict tool-load mode."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from yamlgraph.graph_loader import load_and_compile


def _write_graph(path: Path, body: str) -> None:
    path.write_text(body.strip() + "\n", encoding="utf-8")


@pytest.mark.req("REQ-YG-420")
def test_ac01_default_mode_is_strict_and_fails_on_broken_python_tool(
    tmp_path: Path,
) -> None:
    graph_path = tmp_path / "graph.yaml"
    _write_graph(
        graph_path,
        """
version: "1.0"
name: fr444_default_strict

tools:
  broken_tool:
    type: python
    module: does.not.exist
    function: run

nodes:
  execute:
    type: tool_call
    tool: "{state.task.tool}"
    args: "{state.task.args}"
    state_key: result

edges:
  - from: START
    to: execute
  - from: execute
    to: END
""",
    )

    with pytest.raises(ValueError, match="broken_tool|does.not.exist|tool load"):
        load_and_compile(graph_path)


@pytest.mark.req("REQ-YG-420")
def test_ac02_strict_mode_reports_all_failed_tools(tmp_path: Path) -> None:
    graph_path = tmp_path / "graph.yaml"
    _write_graph(
        graph_path,
        """
version: "1.0"
name: fr444_explicit_strict

config:
  tool_load_mode: strict

tools:
  broken_module:
    type: python
    module: module.that.does.not.exist
    function: run
  broken_symbol:
    type: python
    module: json
    function: not_a_real_function

nodes:
  execute:
    type: tool_call
    tool: "{state.task.tool}"
    args: "{state.task.args}"
    state_key: result

edges:
  - from: START
    to: execute
  - from: execute
    to: END
""",
    )

    with pytest.raises(ValueError) as exc_info:
        load_and_compile(graph_path)

    message = str(exc_info.value)
    assert "broken_module" in message
    assert "broken_symbol" in message


@pytest.mark.req("REQ-YG-421")
def test_ac03_warn_mode_compiles_and_returns_runtime_unknown_tool_error(
    tmp_path: Path,
) -> None:
    graph_path = tmp_path / "graph.yaml"
    _write_graph(
        graph_path,
        """
version: "1.0"
name: fr444_warn_mode

config:
  tool_load_mode: warn

tools:
  broken_tool:
    type: python
    module: does.not.exist
    function: run

nodes:
  execute:
    type: tool_call
    tool: "{state.task.tool}"
    args: "{state.task.args}"
    state_key: result

edges:
  - from: START
    to: execute
  - from: execute
    to: END
""",
    )

    app = load_and_compile(graph_path).compile()
    result = app.invoke({"task": {"tool": "broken_tool", "args": {}}})

    assert result["result"]["success"] is False
    assert "Unknown tool" in result["result"]["error"]


@pytest.mark.req("REQ-YG-421")
def test_ac04_warn_mode_logs_tool_load_failures(
    tmp_path: Path,
) -> None:
    graph_path = tmp_path / "graph.yaml"
    _write_graph(
        graph_path,
        """
version: "1.0"
name: fr444_warn_logs

config:
  tool_load_mode: warn

tools:
  broken_module:
    type: python
    module: module.that.does.not.exist
    function: run
  broken_symbol:
    type: python
    module: json
    function: not_a_real_function

nodes:
  execute:
    type: tool_call
    tool: "{state.task.tool}"
    args: "{state.task.args}"
    state_key: result

edges:
  - from: START
    to: execute
  - from: execute
    to: END
""",
    )

    with patch("yamlgraph.graph_loader.logger.warning") as mock_warning:
        load_and_compile(graph_path)

    warning_messages = [call.args[0] for call in mock_warning.call_args_list]
    assert any("Failed to load tool 'broken_module'" in msg for msg in warning_messages)
    assert any("Failed to load tool 'broken_symbol'" in msg for msg in warning_messages)
