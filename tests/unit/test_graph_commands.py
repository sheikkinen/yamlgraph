"""Tests for universal graph runner (Phase 7.2).

TDD tests for `yamlgraph graph run <path>` command.
Extended by FR-224 for ≥ 85% coverage of cli/graph_commands.py.
"""

import argparse
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

# =============================================================================
# graph subcommand tests
# =============================================================================


class TestGraphSubcommand:
    """Tests for graph subcommand group."""

    @pytest.mark.req("REQ-YG-032", "REQ-YG-036")
    def test_graph_subparser_exists(self):
        """graph subparser should be configured."""
        from yamlgraph.cli import create_parser

        parser = create_parser()
        # Parse with graph command
        args = parser.parse_args(
            ["graph", "info", "examples/demos/yamlgraph/graph.yaml"]
        )
        assert args.command == "graph"

    @pytest.mark.req("REQ-YG-032", "REQ-YG-036")
    def test_graph_run_subcommand_exists(self):
        """graph run subcommand should exist."""
        from yamlgraph.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(
            ["graph", "run", "graphs/yamlgraph.yaml", "--var", "topic=AI"]
        )
        assert args.graph_command == "run"
        assert args.graph_path == "graphs/yamlgraph.yaml"

    @pytest.mark.req("REQ-YG-032", "REQ-YG-036")
    def test_graph_info_subcommand_exists(self):
        """graph info subcommand should exist."""
        from yamlgraph.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["graph", "info", "graphs/yamlgraph.yaml"])
        assert args.graph_command == "info"
        assert args.graph_path == "graphs/yamlgraph.yaml"


# =============================================================================
# graph run argument parsing tests
# =============================================================================


class TestGraphRunArgs:
    """Tests for graph run argument parsing."""

    @pytest.mark.req("REQ-YG-032", "REQ-YG-036")
    def test_var_single_value(self):
        """--var key=value should parse correctly."""
        from yamlgraph.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(
            ["graph", "run", "graphs/test.yaml", "--var", "topic=AI"]
        )
        assert args.var == ["topic=AI"]

    @pytest.mark.req("REQ-YG-032", "REQ-YG-036")
    def test_var_multiple_values(self):
        """Multiple --var flags should accumulate."""
        from yamlgraph.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(
            [
                "graph",
                "run",
                "graphs/test.yaml",
                "--var",
                "topic=AI",
                "--var",
                "style=casual",
            ]
        )
        assert args.var == ["topic=AI", "style=casual"]

    @pytest.mark.req("REQ-YG-032", "REQ-YG-036")
    def test_thread_argument(self):
        """--thread should set thread ID."""
        from yamlgraph.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(
            ["graph", "run", "graphs/test.yaml", "--thread", "abc123"]
        )
        assert args.thread == "abc123"

    @pytest.mark.req("REQ-YG-032", "REQ-YG-036")
    def test_export_flag(self):
        """--export flag should enable export."""
        from yamlgraph.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["graph", "run", "graphs/test.yaml", "--export"])
        assert args.export is True

    @pytest.mark.req("REQ-YG-032", "REQ-YG-036")
    def test_graph_path_required(self):
        """graph run requires a path argument."""
        from yamlgraph.cli import create_parser

        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["graph", "run"])


# =============================================================================
# parse_vars helper tests
# =============================================================================


class TestParseVars:
    """Tests for --var parsing helper."""

    @pytest.mark.req("REQ-YG-032", "REQ-YG-036")
    def test_parse_single_var(self):
        """Single var should parse to dict."""
        from yamlgraph.cli.helpers import parse_vars

        result = parse_vars(["topic=AI"])
        assert result == {"topic": "AI"}

    @pytest.mark.req("REQ-YG-032", "REQ-YG-036")
    def test_parse_multiple_vars(self):
        """Multiple vars should parse to dict."""
        from yamlgraph.cli.helpers import parse_vars

        result = parse_vars(["topic=AI", "style=casual", "count=5"])
        assert result == {"topic": "AI", "style": "casual", "count": "5"}

    @pytest.mark.req("REQ-YG-032", "REQ-YG-036")
    def test_parse_empty_list(self):
        """Empty list returns empty dict."""
        from yamlgraph.cli.helpers import parse_vars

        result = parse_vars([])
        assert result == {}

    @pytest.mark.req("REQ-YG-032", "REQ-YG-036")
    def test_parse_none_returns_empty(self):
        """None returns empty dict."""
        from yamlgraph.cli.helpers import parse_vars

        result = parse_vars(None)
        assert result == {}

    @pytest.mark.req("REQ-YG-032", "REQ-YG-036")
    def test_parse_value_with_equals(self):
        """Value containing = should preserve it."""
        from yamlgraph.cli.helpers import parse_vars

        result = parse_vars(["equation=a=b+c"])
        assert result == {"equation": "a=b+c"}

    @pytest.mark.req("REQ-YG-032", "REQ-YG-036")
    def test_parse_invalid_format_raises(self):
        """Invalid format (no =) should raise ValueError."""
        from yamlgraph.cli.helpers import parse_vars

        with pytest.raises(ValueError, match="Invalid"):
            parse_vars(["invalid"])

    @pytest.mark.req("REQ-YG-032", "REQ-YG-036")
    def test_parse_var_at_file_reads_content(self, tmp_path):
        """@file syntax reads file content into var."""
        from yamlgraph.cli.helpers import parse_vars

        test_file = tmp_path / "content.txt"
        test_file.write_text("This is the document content.\nLine 2.")

        result = parse_vars([f"document=@{test_file}"])

        assert result == {"document": "This is the document content.\nLine 2."}

    @pytest.mark.req("REQ-YG-032", "REQ-YG-036")
    def test_parse_var_at_in_value_stays_literal(self):
        """@ in middle of value (like email) stays literal."""
        from yamlgraph.cli.helpers import parse_vars

        result = parse_vars(["email=user@domain.com"])

        assert result == {"email": "user@domain.com"}

    @pytest.mark.req("REQ-YG-032", "REQ-YG-036")
    def test_parse_var_at_file_not_found_error(self, tmp_path):
        """@file with missing file raises clear error."""
        from yamlgraph.cli.helpers import parse_vars

        with pytest.raises(FileNotFoundError, match="missing.txt"):
            parse_vars(["content=@/nonexistent/missing.txt"])


# =============================================================================
# load_var_file tests
# =============================================================================


class TestLoadVarFile:
    """Tests for --var-file loading."""

    @pytest.mark.req("REQ-YG-032", "REQ-YG-036")
    def test_load_var_file_yaml(self, tmp_path):
        """Load variables from YAML file."""
        from yamlgraph.cli.helpers import load_var_file

        var_file = tmp_path / "vars.yaml"
        var_file.write_text("topic: AI\nstyle: casual\nitems:\n  - one\n  - two")

        result = load_var_file(str(var_file))

        assert result == {"topic": "AI", "style": "casual", "items": ["one", "two"]}

    @pytest.mark.req("REQ-YG-032", "REQ-YG-036")
    def test_load_var_file_json(self, tmp_path):
        """Load variables from JSON file."""
        from yamlgraph.cli.helpers import load_var_file

        var_file = tmp_path / "vars.json"
        var_file.write_text('{"topic": "AI", "count": 5}')

        result = load_var_file(str(var_file))

        assert result == {"topic": "AI", "count": 5}

    @pytest.mark.req("REQ-YG-032", "REQ-YG-036")
    def test_load_var_file_none_returns_empty(self):
        """None path returns empty dict."""
        from yamlgraph.cli.helpers import load_var_file

        result = load_var_file(None)

        assert result == {}

    @pytest.mark.req("REQ-YG-032", "REQ-YG-036")
    def test_load_var_file_not_found_error(self):
        """Missing file raises clear error."""
        from yamlgraph.cli.helpers import load_var_file

        with pytest.raises(FileNotFoundError, match="not found"):
            load_var_file("/nonexistent/vars.yaml")


# =============================================================================
# cmd_graph_run tests
# =============================================================================


class TestCmdGraphRun:
    """Tests for cmd_graph_run function."""

    @pytest.mark.req("REQ-YG-032", "REQ-YG-036")
    def test_cmd_graph_run_exists(self):
        """cmd_graph_run function should exist."""
        from yamlgraph.cli.graph_commands import cmd_graph_run

        assert callable(cmd_graph_run)

    @pytest.mark.req("REQ-YG-032", "REQ-YG-036")
    def test_graph_not_found_error(self):
        """Should error if graph file doesn't exist."""
        from yamlgraph.cli.graph_commands import cmd_graph_run

        args = argparse.Namespace(
            graph_path="nonexistent.yaml",
            var=[],
            thread=None,
            export=False,
        )

        with pytest.raises(SystemExit):
            cmd_graph_run(args)

    @patch("yamlgraph.graph_loader.get_checkpointer_for_graph")
    @patch("yamlgraph.graph_loader.compile_graph")
    @patch("yamlgraph.graph_loader.load_graph_config")
    @pytest.mark.req("REQ-YG-032", "REQ-YG-036")
    def test_invokes_graph_with_vars(self, mock_load_config, mock_compile, mock_get_cp):
        """Should invoke graph with parsed vars as initial state."""
        from yamlgraph.cli.graph_commands import cmd_graph_run

        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        mock_graph = MagicMock()
        mock_compile.return_value = mock_graph

        mock_get_cp.return_value = None  # No checkpointer

        mock_app = MagicMock()
        mock_app.invoke.return_value = {"result": "success"}
        mock_graph.compile.return_value = mock_app

        args = argparse.Namespace(
            graph_path="examples/demos/yamlgraph/graph.yaml",
            var=["topic=AI", "style=casual"],
            thread=None,
            export=False,
        )

        # Mock Path.exists
        with patch.object(Path, "exists", return_value=True):
            cmd_graph_run(args)

        mock_app.invoke.assert_called_once()
        call_args = mock_app.invoke.call_args[0][0]
        assert call_args["topic"] == "AI"
        assert call_args["style"] == "casual"

    @patch("yamlgraph.graph_loader.get_checkpointer_for_graph")
    @patch("yamlgraph.graph_loader.compile_graph")
    @patch("yamlgraph.graph_loader.load_graph_config")
    @pytest.mark.req("REQ-YG-032", "REQ-YG-036")
    def test_uses_checkpointer_from_graph(
        self, mock_load_config, mock_compile, mock_get_cp
    ):
        """Should use checkpointer from graph config when --thread provided."""
        from yamlgraph.cli.graph_commands import cmd_graph_run

        # Setup mocks
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        mock_graph = MagicMock()
        mock_compile.return_value = mock_graph

        mock_checkpointer = MagicMock()
        mock_get_cp.return_value = mock_checkpointer

        mock_app = MagicMock()
        mock_app.invoke.return_value = {"result": "success"}
        mock_graph.compile.return_value = mock_app

        args = argparse.Namespace(
            graph_path="graphs/interview.yaml",
            var=["input=start"],
            thread="session-123",
            export=False,
        )

        with patch.object(Path, "exists", return_value=True):
            cmd_graph_run(args)

        # Verify checkpointer was retrieved and used
        mock_get_cp.assert_called_once_with(mock_config)
        mock_graph.compile.assert_called_once_with(checkpointer=mock_checkpointer)

        # Verify thread_id was passed in config
        call_kwargs = mock_app.invoke.call_args[1]
        assert call_kwargs["config"]["configurable"]["thread_id"] == "session-123"

    @patch("yamlgraph.graph_loader.get_checkpointer_for_graph")
    @patch("yamlgraph.graph_loader.compile_graph")
    @patch("yamlgraph.graph_loader.load_graph_config")
    @pytest.mark.req("REQ-YG-032", "REQ-YG-036")
    def test_uses_checkpointer_even_without_thread(
        self, mock_load_config, mock_compile, mock_get_cp
    ):
        """Should use checkpointer from graph config even without --thread."""
        from yamlgraph.cli.graph_commands import cmd_graph_run

        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        mock_graph = MagicMock()
        mock_compile.return_value = mock_graph

        mock_checkpointer = MagicMock()
        mock_get_cp.return_value = mock_checkpointer

        mock_app = MagicMock()
        mock_app.invoke.return_value = {"result": "success"}
        mock_graph.compile.return_value = mock_app

        args = argparse.Namespace(
            graph_path="graphs/interview.yaml",
            var=["input=start"],
            thread=None,
            export=False,
        )

        with patch.object(Path, "exists", return_value=True):
            cmd_graph_run(args)

        # Verify checkpointer was retrieved and used
        mock_get_cp.assert_called_once_with(mock_config)
        mock_graph.compile.assert_called_once_with(checkpointer=mock_checkpointer)


# =============================================================================
# cmd_graph_info tests
# =============================================================================


class TestCmdGraphInfo:
    """Tests for cmd_graph_info function."""

    @pytest.mark.req("REQ-YG-032", "REQ-YG-036")
    def test_cmd_graph_info_exists(self):
        """cmd_graph_info function should exist."""
        from yamlgraph.cli.graph_commands import cmd_graph_info

        assert callable(cmd_graph_info)

    @pytest.mark.req("REQ-YG-032", "REQ-YG-036")
    def test_info_file_not_found(self):
        """Should error if graph file doesn't exist."""
        from yamlgraph.cli.graph_commands import cmd_graph_info

        args = argparse.Namespace(graph_path="nonexistent.yaml")

        with pytest.raises(SystemExit):
            cmd_graph_info(args)


# =============================================================================
# cmd_graph_validate tests
# =============================================================================


class TestCmdGraphValidate:
    """Tests for cmd_graph_validate function."""

    @pytest.mark.req("REQ-YG-032", "REQ-YG-036")
    def test_cmd_graph_validate_exists(self):
        """cmd_graph_validate function should exist."""
        from yamlgraph.cli.graph_commands import cmd_graph_validate

        assert callable(cmd_graph_validate)

    @pytest.mark.req("REQ-YG-032", "REQ-YG-036")
    def test_validate_file_not_found(self):
        """Should error if graph file doesn't exist."""
        from yamlgraph.cli.graph_commands import cmd_graph_validate

        args = argparse.Namespace(graph_path="nonexistent.yaml")

        with pytest.raises(SystemExit):
            cmd_graph_validate(args)

    @pytest.mark.req("REQ-YG-032", "REQ-YG-036")
    def test_validate_valid_graph(self):
        """Should validate a correct graph without errors."""
        from yamlgraph.cli.graph_commands import cmd_graph_validate

        args = argparse.Namespace(graph_path="examples/demos/yamlgraph/graph.yaml")

        # Should not raise
        cmd_graph_validate(args)

    @pytest.mark.req("REQ-YG-032", "REQ-YG-036")
    def test_validate_subparser_exists(self):
        """graph validate subcommand should exist."""
        from yamlgraph.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(
            ["graph", "validate", "examples/demos/yamlgraph/graph.yaml"]
        )
        assert args.graph_command == "validate"
        assert args.graph_path == "examples/demos/yamlgraph/graph.yaml"


# =============================================================================
# --share-trace flag and _print_trace_url (FR-022)
# =============================================================================


class TestShareTraceFlag:
    """Tests for --share-trace CLI flag and trace URL printing."""

    @pytest.mark.req("REQ-YG-047")
    def test_share_trace_flag_parsed(self):
        """--share-trace flag should be recognized."""
        from yamlgraph.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["graph", "run", "graphs/test.yaml", "--share-trace"])
        assert args.share_trace is True

    @pytest.mark.req("REQ-YG-047")
    def test_share_trace_flag_default_false(self):
        """--share-trace should default to False."""
        from yamlgraph.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["graph", "run", "graphs/test.yaml"])
        assert args.share_trace is False

    @pytest.mark.req("REQ-YG-047")
    def test_print_trace_url_authenticated(self, capsys):
        """_print_trace_url should print authenticated URL when share=False."""
        from yamlgraph.cli.graph_commands import _print_trace_url

        tracer = MagicMock()
        with patch(
            "yamlgraph.utils.tracing.get_trace_url",
            return_value="https://smith.langchain.com/o/xxx/r/yyy",
        ):
            _print_trace_url(tracer, share=False)

        captured = capsys.readouterr()
        assert "🔗 Trace: https://smith.langchain.com/o/xxx/r/yyy" in captured.out

    @pytest.mark.req("REQ-YG-047")
    def test_print_trace_url_shared(self, capsys):
        """_print_trace_url should print public URL when share=True."""
        from yamlgraph.cli.graph_commands import _print_trace_url

        tracer = MagicMock()
        with patch(
            "yamlgraph.utils.tracing.share_trace",
            return_value="https://smith.langchain.com/public/xxx/r/yyy",
        ):
            _print_trace_url(tracer, share=True)

        captured = capsys.readouterr()
        assert (
            "🔗 Trace (public): https://smith.langchain.com/public/xxx/r/yyy"
            in captured.out
        )

    @pytest.mark.req("REQ-YG-047")
    def test_print_trace_url_no_tracer(self, capsys):
        """_print_trace_url should print nothing when tracer is None."""
        from yamlgraph.cli.graph_commands import _print_trace_url

        _print_trace_url(None, share=False)
        captured = capsys.readouterr()
        assert captured.out == ""

    @pytest.mark.req("REQ-YG-047")
    def test_print_trace_url_no_url(self, capsys):
        """_print_trace_url should print nothing when URL is None."""
        from yamlgraph.cli.graph_commands import _print_trace_url

        tracer = MagicMock()
        with patch("yamlgraph.utils.tracing.get_trace_url", return_value=None):
            _print_trace_url(tracer, share=False)

        captured = capsys.readouterr()
        assert captured.out == ""


# =============================================================================
# _display_result tests (FR-224)
# =============================================================================


class TestDisplayResult:
    """Tests for _display_result helper."""

    @pytest.mark.req("REQ-YG-033")
    def test_truncates_long_values(self, capsys):
        """Values >200 chars should be truncated with '...'."""
        from yamlgraph.cli.graph_commands import _display_result

        long_text = "x" * 300
        _display_result({"summary": long_text}, truncate=True)
        captured = capsys.readouterr()
        assert "..." in captured.out
        assert len(long_text) != len(captured.out)

    @pytest.mark.req("REQ-YG-033")
    def test_full_output_no_truncation(self, capsys):
        """With truncate=False, long values should not be truncated."""
        from yamlgraph.cli.graph_commands import _display_result

        long_text = "x" * 300
        _display_result({"summary": long_text}, truncate=False)
        captured = capsys.readouterr()
        assert "..." not in captured.out
        assert long_text in captured.out

    @pytest.mark.req("REQ-YG-033")
    def test_skips_internal_keys(self, capsys):
        """Keys starting with '_' and skip_keys should be omitted."""
        from yamlgraph.cli.graph_commands import _display_result

        _display_result(
            {
                "summary": "hello",
                "_loop_counts": {},
                "messages": ["m1"],
                "errors": ["e1"],
                "_internal": True,
            }
        )
        captured = capsys.readouterr()
        assert "summary" in captured.out
        assert "_loop_counts" not in captured.out
        assert "messages" not in captured.out
        assert "errors" not in captured.out
        assert "_internal" not in captured.out

    @pytest.mark.req("REQ-YG-033")
    def test_skips_none_values(self, capsys):
        """None values should be omitted."""
        from yamlgraph.cli.graph_commands import _display_result

        _display_result({"present": "yes", "absent": None})
        captured = capsys.readouterr()
        assert "present" in captured.out
        assert "absent" not in captured.out

    @pytest.mark.req("REQ-YG-033")
    def test_prints_header(self, capsys):
        """Should print RESULT header."""
        from yamlgraph.cli.graph_commands import _display_result

        _display_result({"a": "b"})
        captured = capsys.readouterr()
        assert "RESULT" in captured.out


# =============================================================================
# _get_interrupt_message tests (FR-224)
# =============================================================================


class TestGetInterruptMessage:
    """Tests for _get_interrupt_message helper."""

    @pytest.mark.req("REQ-YG-033")
    def test_string_value(self):
        """String interrupt value should be returned directly."""
        from yamlgraph.cli.graph_commands import _get_interrupt_message

        interrupt_obj = SimpleNamespace(value="What is your name?")
        result = {"__interrupt__": (interrupt_obj,)}
        assert _get_interrupt_message(result) == "What is your name?"

    @pytest.mark.req("REQ-YG-033")
    def test_dict_with_message(self):
        """Dict interrupt value with 'message' key should return it."""
        from yamlgraph.cli.graph_commands import _get_interrupt_message

        interrupt_obj = SimpleNamespace(value={"message": "Pick an option"})
        result = {"__interrupt__": (interrupt_obj,)}
        assert _get_interrupt_message(result) == "Pick an option"

    @pytest.mark.req("REQ-YG-033")
    def test_dict_with_question(self):
        """Dict interrupt value with 'question' key should return it."""
        from yamlgraph.cli.graph_commands import _get_interrupt_message

        interrupt_obj = SimpleNamespace(value={"question": "Continue?"})
        result = {"__interrupt__": (interrupt_obj,)}
        assert _get_interrupt_message(result) == "Continue?"

    @pytest.mark.req("REQ-YG-033")
    def test_fallback_to_response(self):
        """Missing interrupt should fallback to 'response' in state."""
        from yamlgraph.cli.graph_commands import _get_interrupt_message

        result = {"response": "Please confirm"}
        assert _get_interrupt_message(result) == "Please confirm"

    @pytest.mark.req("REQ-YG-033")
    def test_empty_interrupt_fallback(self):
        """Empty interrupt tuple should fallback to default."""
        from yamlgraph.cli.graph_commands import _get_interrupt_message

        result = {"__interrupt__": ()}
        assert _get_interrupt_message(result) == "Please provide input:"

    @pytest.mark.req("REQ-YG-033")
    def test_dict_without_message_or_question(self):
        """Dict without message/question should stringify."""
        from yamlgraph.cli.graph_commands import _get_interrupt_message

        interrupt_obj = SimpleNamespace(value={"data": "raw"})
        result = {"__interrupt__": (interrupt_obj,)}
        msg = _get_interrupt_message(result)
        assert "data" in msg


# =============================================================================
# _setup_timeout / _teardown_timeout tests (FR-224)
# =============================================================================


class TestSetupTimeout:
    """Tests for _setup_timeout helper."""

    @pytest.mark.req("REQ-YG-033")
    def test_none_returns_none(self):
        """None timeout should return None."""
        from yamlgraph.cli.graph_commands import _setup_timeout

        assert _setup_timeout(None) is None

    @pytest.mark.req("REQ-YG-033")
    @patch("platform.system", return_value="Linux")
    def test_sets_alarm_on_unix(self, _mock_platform):
        """Should set signal.alarm on Unix."""
        from yamlgraph.cli.graph_commands import _setup_timeout

        with patch("signal.signal") as mock_signal, patch("signal.alarm") as mock_alarm:
            mock_signal.return_value = "old_handler"
            ctx = _setup_timeout(30)

        mock_alarm.assert_called_once_with(30)
        assert ctx is not None
        assert ctx["old_handler"] == "old_handler"

    @pytest.mark.req("REQ-YG-033")
    @patch("platform.system", return_value="Windows")
    def test_windows_skips_with_warning(self, _mock_platform):
        """Windows should skip timeout and return None."""
        from yamlgraph.cli.graph_commands import _setup_timeout

        ctx = _setup_timeout(30)
        assert ctx is None


class TestTeardownTimeout:
    """Tests for _teardown_timeout helper."""

    @pytest.mark.req("REQ-YG-033")
    def test_none_context_noop(self):
        """None context should be a no-op."""
        from yamlgraph.cli.graph_commands import _teardown_timeout

        _teardown_timeout(None)  # Should not raise

    @pytest.mark.req("REQ-YG-033")
    def test_cancels_alarm(self):
        """Should cancel alarm and restore handler."""
        from yamlgraph.cli.graph_commands import _teardown_timeout

        old_handler = MagicMock()
        with patch("signal.alarm") as mock_alarm, patch("signal.signal") as mock_signal:
            _teardown_timeout({"old_handler": old_handler})

        mock_alarm.assert_called_once_with(0)
        mock_signal.assert_called_once()


# =============================================================================
# _build_run_config tests (FR-224)
# =============================================================================


class TestBuildRunConfig:
    """Tests for _build_run_config helper."""

    @pytest.mark.req("REQ-YG-033")
    @patch("yamlgraph.utils.tracing.create_tracer", return_value=None)
    @patch("yamlgraph.utils.tracing.inject_tracer_config")
    def test_merges_data_files(self, _mock_inject, _mock_tracer):
        """Graph config data should be merged into initial_state."""
        from yamlgraph.cli.graph_commands import _build_run_config

        graph_config = MagicMock()
        graph_config.data = {"base_key": "base_val"}
        graph_config.recursion_limit = 25
        graph_config.timeout = None

        args = argparse.Namespace(
            thread=None,
            recursion_limit=None,
            timeout=None,
            share_trace=False,
            token_usage=False,
        )

        state, config, *_ = _build_run_config(args, graph_config, {"user_key": "uv"})
        assert state["base_key"] == "base_val"
        assert state["user_key"] == "uv"

    @pytest.mark.req("REQ-YG-033")
    @patch("yamlgraph.utils.tracing.create_tracer", return_value=None)
    @patch("yamlgraph.utils.tracing.inject_tracer_config")
    def test_cli_recursion_limit_overrides_yaml(self, _mock_inject, _mock_tracer):
        """CLI --recursion-limit should override YAML config."""
        from yamlgraph.cli.graph_commands import _build_run_config

        graph_config = MagicMock()
        graph_config.data = {}
        graph_config.recursion_limit = 25
        graph_config.timeout = None

        args = argparse.Namespace(
            thread=None,
            recursion_limit=100,
            timeout=None,
            share_trace=False,
            token_usage=False,
        )

        _, config, *_ = _build_run_config(args, graph_config, {})
        assert config["recursion_limit"] == 100

    @pytest.mark.req("REQ-YG-033")
    @patch("yamlgraph.utils.tracing.create_tracer", return_value=None)
    @patch("yamlgraph.utils.tracing.inject_tracer_config")
    def test_yaml_recursion_limit_when_cli_not_set(self, _mock_inject, _mock_tracer):
        """YAML recursion_limit should be used when CLI not set."""
        from yamlgraph.cli.graph_commands import _build_run_config

        graph_config = MagicMock()
        graph_config.data = {}
        graph_config.recursion_limit = 50
        graph_config.timeout = None

        args = argparse.Namespace(
            thread=None,
            recursion_limit=None,
            timeout=None,
            share_trace=False,
            token_usage=False,
        )

        _, config, *_ = _build_run_config(args, graph_config, {})
        assert config["recursion_limit"] == 50

    @pytest.mark.req("REQ-YG-033")
    @patch("yamlgraph.utils.tracing.create_tracer", return_value=None)
    @patch("yamlgraph.utils.tracing.inject_tracer_config")
    def test_thread_id_in_config(self, _mock_inject, _mock_tracer):
        """Thread ID should be set in configurable and initial_state."""
        from yamlgraph.cli.graph_commands import _build_run_config

        graph_config = MagicMock()
        graph_config.data = {}
        graph_config.recursion_limit = 25
        graph_config.timeout = None

        args = argparse.Namespace(
            thread="t-42",
            recursion_limit=None,
            timeout=None,
            share_trace=False,
            token_usage=False,
        )

        state, config, *_ = _build_run_config(args, graph_config, {})
        assert config["configurable"]["thread_id"] == "t-42"
        assert state["thread_id"] == "t-42"

    @pytest.mark.req("REQ-YG-033")
    @patch("yamlgraph.utils.tracing.create_tracer", return_value=None)
    @patch("yamlgraph.utils.tracing.inject_tracer_config")
    def test_token_usage_callback_added(self, _mock_inject, _mock_tracer):
        """Token usage flag should add tracker to callbacks."""
        from yamlgraph.cli.graph_commands import _build_run_config

        graph_config = MagicMock()
        graph_config.data = {}
        graph_config.recursion_limit = 25
        graph_config.timeout = None

        args = argparse.Namespace(
            thread=None,
            recursion_limit=None,
            timeout=None,
            share_trace=False,
            token_usage=True,
        )

        with patch("yamlgraph.utils.token_tracker.create_token_tracker") as mock_create:
            mock_tracker = MagicMock()
            mock_create.return_value = mock_tracker
            _, config, tracker, *_ = _build_run_config(args, graph_config, {})

        assert tracker is mock_tracker
        assert mock_tracker in config["callbacks"]

    @pytest.mark.req("REQ-YG-033")
    @patch("yamlgraph.utils.tracing.create_tracer", return_value=None)
    @patch("yamlgraph.utils.tracing.inject_tracer_config")
    def test_cli_vars_override_data(self, _mock_inject, _mock_tracer):
        """CLI vars (initial_state) should override graph_config.data on collision."""
        from yamlgraph.cli.graph_commands import _build_run_config

        graph_config = MagicMock()
        graph_config.data = {"topic": "old", "extra": "kept"}
        graph_config.recursion_limit = 25
        graph_config.timeout = None

        args = argparse.Namespace(
            thread=None,
            recursion_limit=None,
            timeout=None,
            share_trace=False,
            token_usage=False,
        )

        state, *_ = _build_run_config(args, graph_config, {"topic": "new"})
        assert state["topic"] == "new"
        assert state["extra"] == "kept"


# =============================================================================
# _invoke_graph tests (FR-224)
# =============================================================================


class TestInvokeGraph:
    """Tests for _invoke_graph helper."""

    @pytest.mark.req("REQ-YG-033")
    def test_sync_invoke(self):
        """Sync invoke should call app.invoke."""
        from yamlgraph.cli.graph_commands import _invoke_graph

        app = MagicMock()
        app.invoke.return_value = {"result": "ok"}
        result = _invoke_graph(app, {"input": "x"}, {"key": "val"}, use_async=False)
        app.invoke.assert_called_once_with({"input": "x"}, config={"key": "val"})
        assert result == {"result": "ok"}

    @pytest.mark.req("REQ-YG-033")
    def test_async_invoke(self):
        """Async invoke should call asyncio.run(app.ainvoke(...))."""
        from yamlgraph.cli.graph_commands import _invoke_graph

        app = MagicMock()

        async def fake_ainvoke(data, config=None):
            return {"async": True}

        app.ainvoke = fake_ainvoke
        result = _invoke_graph(app, {"input": "x"}, {"key": "val"}, use_async=True)
        assert result == {"async": True}


# =============================================================================
# cmd_graph_codegen tests (FR-224)
# =============================================================================


class TestCmdGraphCodegen:
    """Tests for cmd_graph_codegen command."""

    @pytest.mark.req("REQ-YG-036")
    @patch("yamlgraph.cli.graph_commands.load_graph_config")
    @patch("yamlgraph.cli.graph_commands.generate_typeddict_code")
    def test_codegen_stdout(self, mock_gen, mock_load, capsys):
        """Codegen without --output should print to stdout."""
        from yamlgraph.cli.graph_commands import cmd_graph_codegen

        mock_load.return_value = {"name": "test", "nodes": {}}
        mock_gen.return_value = "class TestState(TypedDict):\n    pass\n"

        args = argparse.Namespace(
            graph_path="graph.yaml",
            output=None,
            include_base=False,
        )
        cmd_graph_codegen(args)

        captured = capsys.readouterr()
        assert "TestState" in captured.out

    @pytest.mark.req("REQ-YG-036")
    @patch("yamlgraph.cli.graph_commands.load_graph_config")
    @patch("yamlgraph.cli.graph_commands.generate_typeddict_code")
    def test_codegen_to_file(self, mock_gen, mock_load, tmp_path):
        """Codegen with --output should write to file."""
        from yamlgraph.cli.graph_commands import cmd_graph_codegen

        mock_load.return_value = {"name": "test", "nodes": {}}
        mock_gen.return_value = "class TestState(TypedDict):\n    pass\n"

        output_file = tmp_path / "state.py"
        args = argparse.Namespace(
            graph_path="graph.yaml",
            output=str(output_file),
            include_base=False,
        )
        cmd_graph_codegen(args)

        assert output_file.read_text() == "class TestState(TypedDict):\n    pass\n"

    @pytest.mark.req("REQ-YG-036")
    @patch("yamlgraph.cli.graph_commands.load_graph_config")
    def test_codegen_graph_load_error(self, mock_load):
        """GraphLoadError should print error and exit(1)."""
        from yamlgraph.cli.graph_commands import cmd_graph_codegen
        from yamlgraph.cli.helpers import GraphLoadError

        mock_load.side_effect = GraphLoadError("not found")
        args = argparse.Namespace(
            graph_path="missing.yaml",
            output=None,
            include_base=False,
        )
        with pytest.raises(SystemExit, match="1"):
            cmd_graph_codegen(args)

    @pytest.mark.req("REQ-YG-036")
    @patch("yamlgraph.cli.graph_commands.load_graph_config")
    def test_codegen_generic_error(self, mock_load):
        """Generic exception should print error and exit(1)."""
        from yamlgraph.cli.graph_commands import cmd_graph_codegen

        mock_load.side_effect = RuntimeError("unexpected")
        args = argparse.Namespace(
            graph_path="bad.yaml",
            output=None,
            include_base=False,
        )
        with pytest.raises(SystemExit, match="1"):
            cmd_graph_codegen(args)


# =============================================================================
# cmd_graph_dispatch tests (FR-224)
# =============================================================================


class TestCmdGraphDispatch:
    """Tests for cmd_graph_dispatch command routing."""

    @pytest.mark.req("REQ-YG-033")
    @patch("yamlgraph.cli.graph_commands.cmd_graph_run")
    def test_dispatches_run(self, mock_run):
        """Should dispatch 'run' to cmd_graph_run."""
        from yamlgraph.cli.graph_commands import cmd_graph_dispatch

        args = argparse.Namespace(graph_command="run")
        cmd_graph_dispatch(args)
        mock_run.assert_called_once_with(args)

    @pytest.mark.req("REQ-YG-033")
    @patch("yamlgraph.cli.graph_commands.cmd_graph_info")
    def test_dispatches_info(self, mock_info):
        """Should dispatch 'info' to cmd_graph_info."""
        from yamlgraph.cli.graph_commands import cmd_graph_dispatch

        args = argparse.Namespace(graph_command="info")
        cmd_graph_dispatch(args)
        mock_info.assert_called_once_with(args)

    @pytest.mark.req("REQ-YG-033")
    @patch("yamlgraph.cli.graph_commands.cmd_graph_validate")
    def test_dispatches_validate(self, mock_validate):
        """Should dispatch 'validate' to cmd_graph_validate."""
        from yamlgraph.cli.graph_commands import cmd_graph_dispatch

        args = argparse.Namespace(graph_command="validate")
        cmd_graph_dispatch(args)
        mock_validate.assert_called_once_with(args)

    @pytest.mark.req("REQ-YG-033")
    @patch("yamlgraph.cli.graph_commands.cmd_graph_lint")
    def test_dispatches_lint(self, mock_lint):
        """Should dispatch 'lint' to cmd_graph_lint."""
        from yamlgraph.cli.graph_commands import cmd_graph_dispatch

        args = argparse.Namespace(graph_command="lint")
        cmd_graph_dispatch(args)
        mock_lint.assert_called_once_with(args)

    @pytest.mark.req("REQ-YG-033")
    @patch("yamlgraph.cli.graph_commands.cmd_graph_codegen")
    def test_dispatches_codegen(self, mock_codegen):
        """Should dispatch 'codegen' to cmd_graph_codegen."""
        from yamlgraph.cli.graph_commands import cmd_graph_dispatch

        args = argparse.Namespace(graph_command="codegen")
        cmd_graph_dispatch(args)
        mock_codegen.assert_called_once_with(args)

    @pytest.mark.req("REQ-YG-033")
    def test_unknown_command_exits(self):
        """Unknown subcommand should exit(1)."""
        from yamlgraph.cli.graph_commands import cmd_graph_dispatch

        args = argparse.Namespace(graph_command="foobar")
        with pytest.raises(SystemExit, match="1"):
            cmd_graph_dispatch(args)


# =============================================================================
# cmd_graph_info extended tests (FR-224)
# =============================================================================


class TestCmdGraphInfoExtended:
    """Extended tests for cmd_graph_info command (FR-224)."""

    @pytest.mark.req("REQ-YG-033")
    @patch("yamlgraph.cli.graph_commands.require_graph_config")
    def test_displays_nodes_and_edges(self, mock_require, capsys):
        """Should display node list and edge list."""
        from yamlgraph.cli.graph_commands import cmd_graph_info

        mock_require.return_value = {
            "name": "MyGraph",
            "description": "A test graph",
            "nodes": {
                "gen": {"type": "llm"},
                "review": {"type": "prompt"},
            },
            "edges": [
                {"from": "START", "to": "gen"},
                {"from": "gen", "to": "review"},
                {"from": "review", "to": "END"},
            ],
        }
        args = argparse.Namespace(graph_path="graph.yaml")
        cmd_graph_info(args)

        captured = capsys.readouterr()
        assert "MyGraph" in captured.out
        assert "A test graph" in captured.out
        assert "gen (llm)" in captured.out
        assert "review (prompt)" in captured.out
        assert "Nodes (2)" in captured.out
        assert "Edges (3)" in captured.out

    @pytest.mark.req("REQ-YG-033")
    @patch("yamlgraph.cli.graph_commands.require_graph_config")
    def test_displays_inputs(self, mock_require, capsys):
        """Should display required inputs."""
        from yamlgraph.cli.graph_commands import cmd_graph_info

        mock_require.return_value = {
            "name": "TestGraph",
            "description": "desc",
            "nodes": {"a": {"type": "llm"}},
            "edges": [],
            "inputs": {
                "topic": {"required": True},
                "style": {"required": False, "default": "casual"},
            },
        }
        args = argparse.Namespace(graph_path="graph.yaml")
        cmd_graph_info(args)

        captured = capsys.readouterr()
        assert "Inputs (2)" in captured.out
        assert "--var topic=<value>" in captured.out
        assert "(required)" in captured.out
        assert "--var style=<value>" in captured.out
        assert "(default: casual)" in captured.out

    @pytest.mark.req("REQ-YG-033")
    @patch("yamlgraph.cli.graph_commands.require_graph_config")
    def test_displays_conditional_edges(self, mock_require, capsys):
        """Should display conditional edges correctly."""
        from yamlgraph.cli.graph_commands import cmd_graph_info

        mock_require.return_value = {
            "name": "Router",
            "description": "desc",
            "nodes": {"a": {"type": "llm"}},
            "edges": [
                {"from": "a", "to": "b", "condition": "state.x > 0"},
            ],
        }
        args = argparse.Namespace(graph_path="graph.yaml")
        cmd_graph_info(args)

        captured = capsys.readouterr()
        assert "(conditional)" in captured.out

    @pytest.mark.req("REQ-YG-033")
    @patch("yamlgraph.cli.graph_commands.require_graph_config")
    def test_generic_error_exits(self, mock_require):
        """Generic exception should exit(1)."""
        from yamlgraph.cli.graph_commands import cmd_graph_info

        mock_require.side_effect = RuntimeError("boom")
        args = argparse.Namespace(graph_path="graph.yaml")
        with pytest.raises(SystemExit, match="1"):
            cmd_graph_info(args)

    @pytest.mark.req("REQ-YG-033")
    @patch("yamlgraph.cli.graph_commands.require_graph_config")
    def test_graph_load_error_exits(self, mock_require):
        """GraphLoadError should exit(1)."""
        from yamlgraph.cli.graph_commands import cmd_graph_info
        from yamlgraph.cli.helpers import GraphLoadError

        mock_require.side_effect = GraphLoadError("missing")
        args = argparse.Namespace(graph_path="graph.yaml")
        with pytest.raises(SystemExit, match="1"):
            cmd_graph_info(args)

    @pytest.mark.req("REQ-YG-033")
    @patch("yamlgraph.cli.graph_commands.require_graph_config")
    def test_no_inputs_section(self, mock_require, capsys):
        """Graph without inputs section should not show Inputs."""
        from yamlgraph.cli.graph_commands import cmd_graph_info

        mock_require.return_value = {
            "name": "Simple",
            "description": "desc",
            "nodes": {"a": {"type": "llm"}},
            "edges": [],
        }
        args = argparse.Namespace(graph_path="graph.yaml")
        cmd_graph_info(args)

        captured = capsys.readouterr()
        assert "Inputs" not in captured.out


# =============================================================================
# cmd_graph_run extended tests (FR-224)
# =============================================================================


class TestCmdGraphRunExtended:
    """Extended tests for cmd_graph_run covering timeout, token usage, etc."""

    @pytest.mark.req("REQ-YG-033")
    @patch("yamlgraph.cli.graph_commands._build_run_config")
    @patch("yamlgraph.graph_loader.load_graph_config")
    @patch("yamlgraph.graph_loader.compile_graph")
    @patch("yamlgraph.graph_loader.get_checkpointer_for_graph")
    def test_var_file_loading(
        self, mock_cp, mock_compile, mock_load, mock_build, tmp_path
    ):
        """--var-file should be loaded and merged."""
        from yamlgraph.cli.graph_commands import cmd_graph_run

        var_file = tmp_path / "vars.yaml"
        var_file.write_text("base: value")

        mock_load.return_value = MagicMock()
        mock_graph = MagicMock()
        mock_compile.return_value = mock_graph
        mock_cp.return_value = None

        mock_app = MagicMock()
        mock_app.invoke.return_value = {"result": "ok"}
        mock_graph.compile.return_value = mock_app

        mock_build.return_value = (
            {"base": "value", "topic": "AI"},
            {},
            None,  # tracker
            None,  # timeout
            None,  # tracer
            False,  # share
        )

        (tmp_path / "graph.yaml").write_text("name: test\nnodes: {}\nedges: []")
        args = argparse.Namespace(
            graph_path=str(tmp_path / "graph.yaml"),
            var=["topic=AI"],
            var_file=str(var_file),
            thread=None,
            export=False,
        )

        cmd_graph_run(args)
        mock_app.invoke.assert_called_once()

    @pytest.mark.req("REQ-YG-033")
    @patch("yamlgraph.cli.graph_commands._build_run_config")
    @patch("yamlgraph.graph_loader.load_graph_config")
    @patch("yamlgraph.graph_loader.compile_graph")
    @patch("yamlgraph.graph_loader.get_checkpointer_for_graph")
    def test_timeout_error_exits(
        self, mock_cp, mock_compile, mock_load, mock_build, tmp_path, capsys
    ):
        """TimeoutError during invoke should exit(1)."""
        from yamlgraph.cli.graph_commands import cmd_graph_run

        mock_load.return_value = MagicMock()
        mock_graph = MagicMock()
        mock_compile.return_value = mock_graph
        mock_cp.return_value = None

        mock_app = MagicMock()
        mock_app.invoke.side_effect = TimeoutError("timed out after 5s")
        mock_graph.compile.return_value = mock_app

        mock_build.return_value = (
            {},
            {},
            None,
            5,  # timeout
            None,
            False,
        )

        (tmp_path / "graph.yaml").write_text("name: test\nnodes: {}\nedges: []")
        args = argparse.Namespace(
            graph_path=str(tmp_path / "graph.yaml"),
            var=[],
            var_file=None,
            thread=None,
            export=False,
        )

        with (
            patch("yamlgraph.cli.graph_commands._setup_timeout", return_value=None),
            patch("yamlgraph.cli.graph_commands._teardown_timeout"),
            pytest.raises(SystemExit, match="1"),
        ):
            cmd_graph_run(args)

        captured = capsys.readouterr()
        assert "timed out" in captured.out

    @pytest.mark.req("REQ-YG-033")
    @patch("yamlgraph.cli.graph_commands._build_run_config")
    @patch("yamlgraph.graph_loader.load_graph_config")
    @patch("yamlgraph.graph_loader.compile_graph")
    @patch("yamlgraph.graph_loader.get_checkpointer_for_graph")
    def test_token_usage_summary(
        self, mock_cp, mock_compile, mock_load, mock_build, tmp_path, capsys
    ):
        """Token usage summary should be printed when tracker has calls."""
        from yamlgraph.cli.graph_commands import cmd_graph_run

        mock_load.return_value = MagicMock()
        mock_graph = MagicMock()
        mock_compile.return_value = mock_graph
        mock_cp.return_value = None

        mock_app = MagicMock()
        mock_app.invoke.return_value = {"output": "done"}
        mock_graph.compile.return_value = mock_app

        mock_tracker = MagicMock()
        mock_tracker.total_calls = 2
        mock_tracker.summary.return_value = {
            "total_input_tokens": 100,
            "total_output_tokens": 50,
            "total_calls": 2,
        }

        mock_build.return_value = (
            {},
            {},
            mock_tracker,
            None,
            None,
            False,
        )

        (tmp_path / "graph.yaml").write_text("name: test\nnodes: {}\nedges: []")
        args = argparse.Namespace(
            graph_path=str(tmp_path / "graph.yaml"),
            var=[],
            var_file=None,
            thread=None,
            export=False,
            full=False,
        )

        with (
            patch("yamlgraph.cli.graph_commands._setup_timeout", return_value=None),
            patch("yamlgraph.cli.graph_commands._teardown_timeout"),
        ):
            cmd_graph_run(args)

        captured = capsys.readouterr()
        assert "Token usage" in captured.out
        assert "100 in" in captured.out
        assert "50 out" in captured.out

    @pytest.mark.req("REQ-YG-033")
    @patch("yamlgraph.cli.graph_commands._handle_export")
    @patch("yamlgraph.cli.graph_commands._build_run_config")
    @patch("yamlgraph.graph_loader.load_graph_config")
    @patch("yamlgraph.graph_loader.compile_graph")
    @patch("yamlgraph.graph_loader.get_checkpointer_for_graph")
    def test_export_flag_triggers_export(
        self, mock_cp, mock_compile, mock_load, mock_build, mock_export, tmp_path
    ):
        """--export flag should trigger _handle_export."""
        from yamlgraph.cli.graph_commands import cmd_graph_run

        mock_load.return_value = MagicMock()
        mock_graph = MagicMock()
        mock_compile.return_value = mock_graph
        mock_cp.return_value = None

        mock_app = MagicMock()
        mock_app.invoke.return_value = {"output": "done"}
        mock_graph.compile.return_value = mock_app

        mock_build.return_value = ({}, {}, None, None, None, False)

        (tmp_path / "graph.yaml").write_text("name: test\nnodes: {}\nedges: []")
        args = argparse.Namespace(
            graph_path=str(tmp_path / "graph.yaml"),
            var=[],
            var_file=None,
            thread=None,
            export=True,
            full=False,
        )

        with (
            patch("yamlgraph.cli.graph_commands._setup_timeout", return_value=None),
            patch("yamlgraph.cli.graph_commands._teardown_timeout"),
        ):
            cmd_graph_run(args)

        mock_export.assert_called_once()
