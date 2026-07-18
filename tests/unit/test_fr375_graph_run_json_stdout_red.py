"""Acceptance tests for FR-375: graph run --json stdout mode."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _make_run_args(graph_path: Path, **overrides) -> argparse.Namespace:
    data = {
        "graph_path": str(graph_path),
        "var": [],
        "var_file": None,
        "thread": None,
        "export": False,
        "full": False,
        "json": False,
        "import_state": None,
        "export_state": None,
        "use_async": False,
        "share_trace": False,
        "recursion_limit": None,
        "timeout": None,
        "token_usage": False,
        "timing": False,
    }
    data.update(overrides)
    return argparse.Namespace(**data)


def _setup_graph_loader_mocks(mock_load_config, mock_compile, mock_get_cp):
    mock_load_config.return_value = MagicMock()
    mock_graph = MagicMock()
    mock_compile.return_value = mock_graph
    mock_get_cp.return_value = None
    mock_app = MagicMock()
    mock_graph.compile.return_value = mock_app
    return mock_app


@pytest.mark.req("REQ-YG-348")
def test_ac01_registry_entries_for_cap147_and_reqyg348_355_exist() -> None:
    cap_files = sorted((REPO_ROOT / "capabilities").glob("CAP-147-*.yaml"))
    assert cap_files, "Expected CAP-147 capability file to exist"

    architecture = (REPO_ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")
    for req_id in (
        "REQ-YG-348",
        "REQ-YG-349",
        "REQ-YG-350",
        "REQ-YG-351",
        "REQ-YG-352",
        "REQ-YG-353",
        "REQ-YG-354",
        "REQ-YG-355",
    ):
        assert req_id in architecture


@pytest.mark.req("REQ-YG-348")
def test_ac02_parser_accepts_json_flag_default_false() -> None:
    from yamlgraph.cli import create_parser

    parser = create_parser()
    args_default = parser.parse_args(["graph", "run", "graphs/test.yaml"])
    args_json = parser.parse_args(["graph", "run", "graphs/test.yaml", "--json"])

    assert args_default.json is False
    assert args_json.json is True


@pytest.mark.req("REQ-YG-349")
@patch("yamlgraph.cli.graph_commands._setup_timeout", return_value=None)
@patch("yamlgraph.cli.graph_commands._teardown_timeout")
@patch("yamlgraph.cli.graph_commands._build_run_config")
@patch("yamlgraph.compile.graph_loader.get_checkpointer_for_graph")
@patch("yamlgraph.compile.graph_loader.compile_graph")
@patch("yamlgraph.compile.graph_loader.load_graph_config")
def test_ac03_json_success_stdout_contains_only_valid_json(
    mock_load_config,
    mock_compile,
    mock_get_cp,
    mock_build,
    _mock_teardown_timeout,
    _mock_setup_timeout,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from yamlgraph.cli.graph_commands import cmd_graph_run

    graph_path = tmp_path / "graph.yaml"
    graph_path.write_text("name: test\nnodes: {}\nedges: []\n")

    mock_app = _setup_graph_loader_mocks(mock_load_config, mock_compile, mock_get_cp)
    mock_app.invoke.return_value = {"answer": "ok", "nested": {"value": 1}}
    mock_build.return_value = ({}, {}, None, None, None, False, None)

    args = _make_run_args(graph_path, json=True)
    cmd_graph_run(args)

    captured = capsys.readouterr()
    assert "Running graph" not in captured.out
    assert "RESULT" not in captured.out
    assert captured.err == ""

    payload = json.loads(captured.out)
    assert payload["answer"] == "ok"
    assert payload["nested"]["value"] == 1


@pytest.mark.req("REQ-YG-350")
@patch("yamlgraph.cli.graph_commands._setup_timeout", return_value=None)
@patch("yamlgraph.cli.graph_commands._teardown_timeout")
@patch("yamlgraph.compile.graph_loader.load_graph_config")
@patch("yamlgraph.compile.graph_loader.compile_graph")
def test_ac04_json_failure_writes_stderr_and_leaves_stdout_empty(
    mock_compile,
    mock_load_config,
    _mock_teardown_timeout,
    _mock_setup_timeout,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from yamlgraph.cli.graph_commands import cmd_graph_run

    graph_path = tmp_path / "graph.yaml"
    graph_path.write_text("name: test\nnodes: {}\nedges: []\n")

    mock_load_config.return_value = MagicMock()
    mock_compile.side_effect = RuntimeError("boom")

    with pytest.raises(SystemExit, match="1"):
        cmd_graph_run(_make_run_args(graph_path, json=True))

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "boom" in captured.err


@pytest.mark.req("REQ-YG-351")
@patch("yamlgraph.cli.graph_commands._setup_timeout", return_value=None)
@patch("yamlgraph.cli.graph_commands._teardown_timeout")
@patch("yamlgraph.cli.graph_commands._build_run_config")
@patch("yamlgraph.compile.graph_loader.get_checkpointer_for_graph")
@patch("yamlgraph.compile.graph_loader.compile_graph")
@patch("yamlgraph.compile.graph_loader.load_graph_config")
def test_ac05_json_mode_rejects_interrupt_without_input_prompt(
    mock_load_config,
    mock_compile,
    mock_get_cp,
    mock_build,
    _mock_teardown_timeout,
    _mock_setup_timeout,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from yamlgraph.cli.graph_commands import cmd_graph_run

    graph_path = tmp_path / "graph.yaml"
    graph_path.write_text("name: test\nnodes: {}\nedges: []\n")

    mock_app = _setup_graph_loader_mocks(mock_load_config, mock_compile, mock_get_cp)
    mock_app.invoke.return_value = {
        "__interrupt__": (SimpleNamespace(value={"question": "Continue?"}),)
    }
    mock_build.return_value = ({}, {}, None, None, None, False, None)

    with patch("builtins.input") as mock_input, pytest.raises(SystemExit, match="1"):
        cmd_graph_run(_make_run_args(graph_path, json=True))

    mock_input.assert_not_called()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "interrupt" in captured.err.lower()


@pytest.mark.req("REQ-YG-352")
@patch("yamlgraph.cli.graph_commands._setup_timeout", return_value=None)
@patch("yamlgraph.cli.graph_commands._teardown_timeout")
@patch("yamlgraph.cli.graph_commands._build_run_config")
@patch("yamlgraph.compile.graph_loader.get_checkpointer_for_graph")
@patch("yamlgraph.compile.graph_loader.compile_graph")
@patch("yamlgraph.compile.graph_loader.load_graph_config")
def test_ac06_json_mode_emits_full_untruncated_serialized_state(
    mock_load_config,
    mock_compile,
    mock_get_cp,
    mock_build,
    _mock_teardown_timeout,
    _mock_setup_timeout,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from yamlgraph.cli.graph_commands import cmd_graph_run
    from yamlgraph.models.schemas import CopilotResult

    graph_path = tmp_path / "graph.yaml"
    graph_path.write_text("name: test\nnodes: {}\nedges: []\n")

    mock_app = _setup_graph_loader_mocks(mock_load_config, mock_compile, mock_get_cp)
    mock_app.invoke.return_value = {
        "long_text": "x" * 300,
        "copilot": CopilotResult(
            output="done",
            backend="cli",
            session_id="session-375",
        ),
    }
    mock_build.return_value = ({}, {}, None, None, None, False, None)

    cmd_graph_run(_make_run_args(graph_path, json=True))

    payload = json.loads(capsys.readouterr().out)
    assert len(payload["long_text"]) == 300
    assert "..." not in payload["long_text"]
    assert payload["copilot"]["session_id"] == "session-375"


@pytest.mark.req("REQ-YG-353")
@patch("yamlgraph.cli.graph_commands._setup_timeout", return_value=None)
@patch("yamlgraph.cli.graph_commands._teardown_timeout")
@patch("yamlgraph.cli.graph_commands._build_run_config")
@patch("yamlgraph.compile.graph_loader.get_checkpointer_for_graph")
@patch("yamlgraph.compile.graph_loader.compile_graph")
@patch("yamlgraph.compile.graph_loader.load_graph_config")
def test_ac07_json_mode_preserves_import_var_merge_and_export_state_compatibility(
    mock_load_config,
    mock_compile,
    mock_get_cp,
    mock_build,
    _mock_teardown_timeout,
    _mock_setup_timeout,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from yamlgraph.cli.graph_commands import cmd_graph_run

    graph_path = tmp_path / "graph.yaml"
    graph_path.write_text("name: test\nnodes: {}\nedges: []\n")

    import_path = tmp_path / "import-state.json"
    import_path.write_text(json.dumps({"shared": "imported", "i": 1}))
    var_file = tmp_path / "vars.yaml"
    var_file.write_text("shared: file\nf: 2\n")
    export_path = tmp_path / "export-state.json"

    mock_app = _setup_graph_loader_mocks(mock_load_config, mock_compile, mock_get_cp)
    mock_app.invoke.return_value = {"done": True, "source": "json-mode"}

    captured_initial_state: dict[str, object] = {}

    def _fake_build_run_config(_args, _graph_config, initial_state):
        captured_initial_state.update(initial_state)
        return dict(initial_state), {}, None, None, None, False, None

    mock_build.side_effect = _fake_build_run_config

    args = _make_run_args(
        graph_path,
        json=True,
        var=["shared=cli", "c=3"],
        var_file=str(var_file),
        import_state=str(import_path),
        export_state=str(export_path),
    )
    cmd_graph_run(args)

    payload = json.loads(capsys.readouterr().out)
    assert payload["done"] is True
    assert captured_initial_state == {"shared": "cli", "i": 1, "f": 2, "c": "3"}
    assert export_path.exists()
    assert json.loads(export_path.read_text())["source"] == "json-mode"
