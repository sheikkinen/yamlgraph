"""Acceptance tests for FR-269: CLI inter-run state chaining."""

import argparse
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _make_run_args(graph_path: Path, **overrides) -> argparse.Namespace:
    """Create cmd_graph_run args namespace with safe defaults for unit tests."""
    data = {
        "graph_path": str(graph_path),
        "var": [],
        "var_file": None,
        "thread": None,
        "export": False,
        "full": False,
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
    """Prepare graph loader mocks for cmd_graph_run execution tests."""
    mock_load_config.return_value = MagicMock()
    mock_graph = MagicMock()
    mock_compile.return_value = mock_graph
    mock_get_cp.return_value = None
    mock_app = MagicMock()
    mock_app.invoke.return_value = {"result": "ok"}
    mock_graph.compile.return_value = mock_app
    return mock_app


class TestFR269ParserAndHelp:
    """CLI parser contracts for --import-state and --export-state."""

    @pytest.mark.req("REQ-YG-032", "REQ-YG-036", "REQ-YG-267", "REQ-YG-268")
    def test_graph_run_accepts_import_and_export_state_independently(self):
        """AC-07: both new flags are usable alone and together."""
        from yamlgraph.cli import create_parser

        parser = create_parser()

        args_import_only = parser.parse_args(
            ["graph", "run", "graphs/test.yaml", "--import-state", "in.json"]
        )
        assert args_import_only.import_state == "in.json"
        assert args_import_only.export_state is None

        args_export_only = parser.parse_args(
            ["graph", "run", "graphs/test.yaml", "--export-state", "out.json"]
        )
        assert args_export_only.import_state is None
        assert args_export_only.export_state == "out.json"

        args_both = parser.parse_args(
            [
                "graph",
                "run",
                "graphs/test.yaml",
                "--import-state",
                "in.json",
                "--export-state",
                "out.json",
            ]
        )
        assert args_both.import_state == "in.json"
        assert args_both.export_state == "out.json"

    @pytest.mark.req("REQ-YG-032", "REQ-YG-036", "REQ-YG-267", "REQ-YG-268")
    def test_graph_run_help_lists_import_and_export_state(self, capsys):
        """AC-11: graph run --help documents both flags."""
        from yamlgraph.cli import create_parser

        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["graph", "run", "--help"])

        out = capsys.readouterr().out
        assert "--import-state" in out
        assert "--export-state" in out
        assert "Load initial state from JSON file" in out
        assert "Write full state JSON" in out


class TestFR269StorageExportContracts:
    """State export/import helpers for inter-run chaining."""

    @pytest.mark.req("REQ-YG-038", "REQ-YG-268")
    def test_export_state_to_path_writes_full_state_json(self, tmp_path: Path):
        """AC-01: --export-state writes full post-run state to explicit JSON path."""
        from yamlgraph.models.schemas import CopilotResult
        from yamlgraph.storage.export import export_state_to_path

        state = {
            "topic": "acceptance",
            "steps": ["plan", "enforce"],
            "prev_result": CopilotResult(
                output="done",
                backend="cli",
                session_id="session-123",
            ),
        }
        output_path = tmp_path / "state.json"

        written = export_state_to_path(state, output_path)
        assert written == output_path

        data = json.loads(output_path.read_text())
        assert data["topic"] == "acceptance"
        assert data["steps"] == ["plan", "enforce"]
        assert data["prev_result"]["session_id"] == "session-123"

    @pytest.mark.req("REQ-YG-038", "REQ-YG-268")
    def test_export_state_to_path_creates_parent_directories(self, tmp_path: Path):
        """AC-02: --export-state creates missing parent directories."""
        from yamlgraph.storage.export import export_state_to_path

        output_path = tmp_path / "nested" / "deeper" / "state.json"
        export_state_to_path({"k": "v"}, output_path)

        assert output_path.exists()
        assert json.loads(output_path.read_text()) == {"k": "v"}

    @pytest.mark.req("REQ-YG-038", "REQ-YG-267", "REQ-YG-268")
    def test_export_import_round_trip_preserves_copilot_session_id(
        self, tmp_path: Path
    ):
        """AC-06: session_id survives export/import and resolves in state expressions."""
        from yamlgraph.models.schemas import CopilotResult
        from yamlgraph.storage.export import export_state_to_path, load_export
        from yamlgraph.utils.expressions import resolve_state_expression

        state = {
            "prev_result": CopilotResult(
                output="ready",
                backend="cli",
                session_id="copilot-session-42",
            )
        }
        output_path = tmp_path / "roundtrip.json"

        export_state_to_path(state, output_path)
        loaded = load_export(output_path)

        assert (
            resolve_state_expression("{state.prev_result.session_id}", loaded)
            == "copilot-session-42"
        )


class TestFR269CmdGraphRunStateMerging:
    """cmd_graph_run contracts for import/export state flags."""

    @pytest.mark.req("REQ-YG-033", "REQ-YG-267")
    @patch("yamlgraph.cli.graph_commands._setup_timeout", return_value=None)
    @patch("yamlgraph.cli.graph_commands._teardown_timeout")
    @patch("yamlgraph.cli.graph_commands._build_run_config")
    @patch("yamlgraph.storage.export.load_export", return_value={"imported": "state"})
    @patch("yamlgraph.compile.graph_loader.get_checkpointer_for_graph")
    @patch("yamlgraph.compile.graph_loader.compile_graph")
    @patch("yamlgraph.compile.graph_loader.load_graph_config")
    def test_import_state_is_base_initial_state(
        self,
        mock_load_config,
        mock_compile,
        mock_get_cp,
        mock_load_export,
        mock_build,
        _mock_teardown_timeout,
        _mock_setup_timeout,
        tmp_path: Path,
    ):
        """AC-03: imported JSON state is used as base initial state."""
        from yamlgraph.cli.graph_commands import cmd_graph_run

        graph_path = tmp_path / "graph.yaml"
        graph_path.write_text("name: test\nnodes: {}\nedges: []\n")
        state_path = tmp_path / "state.json"
        state_path.write_text('{"imported": "state"}')

        mock_app = _setup_graph_loader_mocks(
            mock_load_config, mock_compile, mock_get_cp
        )
        captured_initial_state = {}

        def _fake_build_run_config(_args, _graph_config, initial_state):
            captured_initial_state.update(initial_state)
            return dict(initial_state), {}, None, None, None, False, None

        mock_build.side_effect = _fake_build_run_config
        args = _make_run_args(graph_path, import_state=str(state_path))

        cmd_graph_run(args)

        mock_load_export.assert_called_once()
        assert captured_initial_state["imported"] == "state"
        invoked_state = mock_app.invoke.call_args[0][0]
        assert invoked_state["imported"] == "state"

    @pytest.mark.req("REQ-YG-033", "REQ-YG-267")
    @patch("yamlgraph.cli.graph_commands._setup_timeout", return_value=None)
    @patch("yamlgraph.cli.graph_commands._teardown_timeout")
    @patch("yamlgraph.cli.graph_commands._build_run_config")
    @patch(
        "yamlgraph.storage.export.load_export",
        return_value={"shared": "imported", "i": 1},
    )
    @patch(
        "yamlgraph.cli.graph_commands.parse_vars",
        return_value={"shared": "cli", "c": 3},
    )
    @patch(
        "yamlgraph.cli.graph_commands.load_var_file",
        return_value={"shared": "file", "f": 2},
    )
    @patch("yamlgraph.compile.graph_loader.get_checkpointer_for_graph")
    @patch("yamlgraph.compile.graph_loader.compile_graph")
    @patch("yamlgraph.compile.graph_loader.load_graph_config")
    def test_merge_order_is_import_then_var_file_then_var(
        self,
        mock_load_config,
        mock_compile,
        mock_get_cp,
        _mock_load_var_file,
        _mock_parse_vars,
        mock_load_export,
        mock_build,
        _mock_teardown_timeout,
        _mock_setup_timeout,
        tmp_path: Path,
    ):
        """AC-04: merge precedence is imported < --var-file < --var."""
        from yamlgraph.cli.graph_commands import cmd_graph_run

        graph_path = tmp_path / "graph.yaml"
        graph_path.write_text("name: test\nnodes: {}\nedges: []\n")
        state_path = tmp_path / "state.json"
        state_path.write_text('{"shared": "imported", "i": 1}')

        _setup_graph_loader_mocks(mock_load_config, mock_compile, mock_get_cp)
        captured_initial_state = {}

        def _fake_build_run_config(_args, _graph_config, initial_state):
            captured_initial_state.update(initial_state)
            return dict(initial_state), {}, None, None, None, False, None

        mock_build.side_effect = _fake_build_run_config
        args = _make_run_args(
            graph_path,
            var=["shared=cli", "c=3"],
            var_file=str(tmp_path / "vars.yaml"),
            import_state=str(state_path),
        )

        cmd_graph_run(args)

        mock_load_export.assert_called_once()
        assert captured_initial_state == {"shared": "cli", "i": 1, "f": 2, "c": 3}

    @pytest.mark.req("REQ-YG-033", "REQ-YG-267")
    @patch("yamlgraph.cli.graph_commands._setup_timeout", return_value=None)
    @patch("yamlgraph.cli.graph_commands._teardown_timeout")
    @patch("yamlgraph.cli.graph_commands._build_run_config")
    @patch(
        "yamlgraph.storage.export.load_export",
        return_value={"topic": "from-import", "session_id": "abc"},
    )
    @patch(
        "yamlgraph.cli.graph_commands.parse_vars", return_value={"topic": "from-cli"}
    )
    @patch("yamlgraph.cli.graph_commands.load_var_file", return_value={})
    @patch("yamlgraph.compile.graph_loader.get_checkpointer_for_graph")
    @patch("yamlgraph.compile.graph_loader.compile_graph")
    @patch("yamlgraph.compile.graph_loader.load_graph_config")
    def test_cli_vars_override_imported_keys(
        self,
        mock_load_config,
        mock_compile,
        mock_get_cp,
        _mock_load_var_file,
        _mock_parse_vars,
        mock_load_export,
        mock_build,
        _mock_teardown_timeout,
        _mock_setup_timeout,
        tmp_path: Path,
    ):
        """AC-05: --var values overwrite matching imported keys."""
        from yamlgraph.cli.graph_commands import cmd_graph_run

        graph_path = tmp_path / "graph.yaml"
        graph_path.write_text("name: test\nnodes: {}\nedges: []\n")
        state_path = tmp_path / "state.json"
        state_path.write_text('{"topic": "from-import", "session_id": "abc"}')

        _setup_graph_loader_mocks(mock_load_config, mock_compile, mock_get_cp)
        captured_initial_state = {}

        def _fake_build_run_config(_args, _graph_config, initial_state):
            captured_initial_state.update(initial_state)
            return dict(initial_state), {}, None, None, None, False, None

        mock_build.side_effect = _fake_build_run_config
        args = _make_run_args(
            graph_path, var=["topic=from-cli"], import_state=str(state_path)
        )

        cmd_graph_run(args)

        mock_load_export.assert_called_once()
        assert captured_initial_state["topic"] == "from-cli"
        assert captured_initial_state["session_id"] == "abc"

    @pytest.mark.req("REQ-YG-033", "REQ-YG-267")
    @patch("yamlgraph.cli.graph_commands._setup_timeout", return_value=None)
    @patch("yamlgraph.cli.graph_commands._teardown_timeout")
    @patch("yamlgraph.cli.graph_commands._build_run_config")
    @patch("yamlgraph.compile.graph_loader.get_checkpointer_for_graph")
    @patch("yamlgraph.compile.graph_loader.compile_graph")
    @patch("yamlgraph.compile.graph_loader.load_graph_config")
    def test_import_state_missing_file_exits_with_clear_error(
        self,
        mock_load_config,
        mock_compile,
        mock_get_cp,
        mock_build,
        _mock_teardown_timeout,
        _mock_setup_timeout,
        tmp_path: Path,
        capsys,
    ):
        """AC-08: missing --import-state file exits with clear message and code 1."""
        from yamlgraph.cli.graph_commands import cmd_graph_run

        graph_path = tmp_path / "graph.yaml"
        graph_path.write_text("name: test\nnodes: {}\nedges: []\n")
        missing_state = tmp_path / "missing-state.json"

        _setup_graph_loader_mocks(mock_load_config, mock_compile, mock_get_cp)
        mock_build.return_value = ({}, {}, None, None, None, False, None)
        args = _make_run_args(graph_path, import_state=str(missing_state))

        with pytest.raises(SystemExit, match="1"):
            cmd_graph_run(args)

        out = capsys.readouterr().out
        assert "--import-state" in out
        assert "not found" in out.lower()
        assert str(missing_state) in out

    @pytest.mark.req("REQ-YG-038", "REQ-YG-268")
    @patch("yamlgraph.cli.graph_commands._setup_timeout", return_value=None)
    @patch("yamlgraph.cli.graph_commands._teardown_timeout")
    @patch("yamlgraph.cli.graph_commands._build_run_config")
    @patch("yamlgraph.compile.graph_loader.get_checkpointer_for_graph")
    @patch("yamlgraph.compile.graph_loader.compile_graph")
    @patch("yamlgraph.compile.graph_loader.load_graph_config")
    def test_export_state_write_failure_exits_with_clear_error(
        self,
        mock_load_config,
        mock_compile,
        mock_get_cp,
        mock_build,
        _mock_teardown_timeout,
        _mock_setup_timeout,
        tmp_path: Path,
        capsys,
    ):
        """AC-09: --export-state write failures exit with clear message and code 1."""
        from yamlgraph.cli.graph_commands import cmd_graph_run

        graph_path = tmp_path / "graph.yaml"
        graph_path.write_text("name: test\nnodes: {}\nedges: []\n")

        export_target = tmp_path / "as-directory"
        export_target.mkdir()

        _setup_graph_loader_mocks(mock_load_config, mock_compile, mock_get_cp)
        mock_build.return_value = ({}, {}, None, None, None, False, None)
        args = _make_run_args(graph_path, export_state=str(export_target))

        with pytest.raises(SystemExit, match="1"):
            cmd_graph_run(args)

        out = capsys.readouterr().out
        assert "error" in out.lower()
        assert str(export_target) in out


@pytest.mark.req("REQ-YG-121")
def test_architecture_declares_req_yg_267_and_268():
    """AC-12: ARCHITECTURE.md includes REQ-YG-267 and REQ-YG-268 entries."""
    text = (REPO_ROOT / "ARCHITECTURE.md").read_text()
    assert "REQ-YG-267" in text
    assert "REQ-YG-268" in text
