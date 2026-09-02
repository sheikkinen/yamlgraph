"""Tests for graph bench command (FR-231 Phase 2, REQ-YG-232).

TDD tests for `yamlgraph graph bench` CLI command that runs a graph
across multiple provider/model combinations and displays a comparison table.
"""

from __future__ import annotations

import json
from argparse import Namespace
from unittest.mock import MagicMock, patch

# =============================================================================
# Model spec parsing tests
# =============================================================================
import pytest

pytestmark = pytest.mark.process


class TestParseModelSpec:
    """Tests for provider/model spec parsing."""

    @pytest.mark.req("REQ-YG-232")
    def test_parse_provider_model(self):
        """'provider/model' parses to (provider, model) tuple."""
        from yamlgraph.cli.bench_commands import parse_model_spec

        result = parse_model_spec("anthropic/claude-sonnet-4-20250514")
        assert result == ("anthropic", "claude-sonnet-4-20250514")

    @pytest.mark.req("REQ-YG-232")
    def test_parse_provider_model_with_slashes(self):
        """Model names with slashes (replicate) parse correctly."""
        from yamlgraph.cli.bench_commands import parse_model_spec

        result = parse_model_spec("replicate/ibm-granite/granite-4.0-h-small")
        assert result == ("replicate", "ibm-granite/granite-4.0-h-small")

    @pytest.mark.req("REQ-YG-232")
    def test_parse_invalid_spec_raises(self):
        """Spec without '/' raises ValueError."""
        from yamlgraph.cli.bench_commands import parse_model_spec

        with pytest.raises(ValueError, match="provider/model"):
            parse_model_spec("just-a-model")


# =============================================================================
# CLI argument parsing tests
# =============================================================================


class TestBenchCLIArgs:
    """Tests for bench subcommand argument parsing."""

    @pytest.mark.req("REQ-YG-232")
    def test_bench_subcommand_exists(self):
        """graph bench subcommand should be registered."""
        from yamlgraph.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(
            [
                "graph",
                "bench",
                "test.yaml",
                "--models",
                "anthropic/claude-sonnet-4-20250514",
            ]
        )
        assert args.graph_command == "bench"

    @pytest.mark.req("REQ-YG-232")
    def test_bench_models_parsed(self):
        """--models accepts multiple provider/model specs."""
        from yamlgraph.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(
            [
                "graph",
                "bench",
                "test.yaml",
                "--models",
                "anthropic/claude-sonnet-4-20250514",
                "openai/gpt-4o",
            ]
        )
        assert args.models == ["anthropic/claude-sonnet-4-20250514", "openai/gpt-4o"]

    @pytest.mark.req("REQ-YG-232")
    def test_bench_runs_default_1(self):
        """--runs defaults to 1."""
        from yamlgraph.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(
            [
                "graph",
                "bench",
                "test.yaml",
                "--models",
                "anthropic/claude-sonnet-4-20250514",
            ]
        )
        assert args.runs == 1

    @pytest.mark.req("REQ-YG-232")
    def test_bench_runs_custom(self):
        """--runs N sets number of repetitions."""
        from yamlgraph.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(
            [
                "graph",
                "bench",
                "test.yaml",
                "--models",
                "anthropic/claude-sonnet-4-20250514",
                "--runs",
                "3",
            ]
        )
        assert args.runs == 3

    @pytest.mark.req("REQ-YG-232")
    def test_bench_export_path(self):
        """--export sets export path."""
        from yamlgraph.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(
            [
                "graph",
                "bench",
                "test.yaml",
                "--models",
                "anthropic/claude-sonnet-4-20250514",
                "--export",
                "bench.json",
            ]
        )
        assert args.bench_export == "bench.json"

    @pytest.mark.req("REQ-YG-232")
    def test_bench_full_flag(self):
        """--full flag parsed."""
        from yamlgraph.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(
            [
                "graph",
                "bench",
                "test.yaml",
                "--models",
                "anthropic/claude-sonnet-4-20250514",
                "--full",
            ]
        )
        assert args.full is True

    @pytest.mark.req("REQ-YG-232")
    def test_bench_var_flag(self):
        """--var flags parsed for bench."""
        from yamlgraph.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(
            [
                "graph",
                "bench",
                "test.yaml",
                "--models",
                "anthropic/claude-sonnet-4-20250514",
                "--var",
                "name=World",
            ]
        )
        assert args.var == ["name=World"]


# =============================================================================
# Result formatting tests
# =============================================================================


class TestFormatBenchTable:
    """Tests for bench result table formatting."""

    @pytest.mark.req("REQ-YG-232")
    def test_format_table_produces_output(self):
        """format_bench_table produces a non-empty string."""
        from yamlgraph.cli.bench_commands import BenchResult, format_bench_table

        results = [
            BenchResult(
                provider="anthropic",
                model="claude-sonnet-4-20250514",
                duration_s=1.23,
                tokens_in=312,
                tokens_out=187,
                status="success",
                output={"greeting": "Hello"},
            ),
        ]
        table = format_bench_table(results)
        assert len(table) > 0
        assert "anthropic" in table
        assert "claude-sonnet-4-20250514" in table
        assert "1.23" in table

    @pytest.mark.req("REQ-YG-232")
    def test_format_table_multiple_models(self):
        """Table includes all model results."""
        from yamlgraph.cli.bench_commands import BenchResult, format_bench_table

        results = [
            BenchResult(
                provider="anthropic",
                model="claude-sonnet-4-20250514",
                duration_s=1.23,
                tokens_in=312,
                tokens_out=187,
                status="success",
                output={},
            ),
            BenchResult(
                provider="openai",
                model="gpt-4o",
                duration_s=0.89,
                tokens_in=298,
                tokens_out=201,
                status="success",
                output={},
            ),
        ]
        table = format_bench_table(results)
        assert "anthropic" in table
        assert "openai" in table

    @pytest.mark.req("REQ-YG-232")
    def test_format_table_shows_error_status(self):
        """Failed models show error status in table."""
        from yamlgraph.cli.bench_commands import BenchResult, format_bench_table

        results = [
            BenchResult(
                provider="anthropic",
                model="claude-sonnet-4-20250514",
                duration_s=0.0,
                tokens_in=0,
                tokens_out=0,
                status="error",
                output={},
                error="API key invalid",
            ),
        ]
        table = format_bench_table(results)
        assert "error" in table.lower() or "✗" in table


# =============================================================================
# BenchResult Pydantic model tests
# =============================================================================


class TestBenchResult:
    """Tests for BenchResult data model."""

    @pytest.mark.req("REQ-YG-232")
    def test_bench_result_fields(self):
        """BenchResult has required fields."""
        from yamlgraph.cli.bench_commands import BenchResult

        result = BenchResult(
            provider="anthropic",
            model="claude-sonnet-4-20250514",
            duration_s=1.23,
            tokens_in=312,
            tokens_out=187,
            status="success",
            output={"greeting": "Hello"},
        )
        assert result.provider == "anthropic"
        assert result.model == "claude-sonnet-4-20250514"
        assert result.duration_s == 1.23
        assert result.tokens_in == 312
        assert result.tokens_out == 187
        assert result.status == "success"

    @pytest.mark.req("REQ-YG-232")
    def test_bench_result_error_field(self):
        """BenchResult supports optional error field."""
        from yamlgraph.cli.bench_commands import BenchResult

        result = BenchResult(
            provider="openai",
            model="gpt-4o",
            duration_s=0.0,
            tokens_in=0,
            tokens_out=0,
            status="error",
            output={},
            error="Connection timeout",
        )
        assert result.error == "Connection timeout"


# =============================================================================
# JSON export tests
# =============================================================================


class TestBenchExport:
    """Tests for bench result JSON export."""

    @pytest.mark.req("REQ-YG-232")
    def test_export_bench_results_creates_file(self, tmp_path):
        """export_bench_results writes valid JSON."""
        from yamlgraph.cli.bench_commands import BenchResult, export_bench_results

        results = [
            BenchResult(
                provider="anthropic",
                model="claude-sonnet-4-20250514",
                duration_s=1.23,
                tokens_in=312,
                tokens_out=187,
                status="success",
                output={"greeting": "Hello"},
            ),
        ]
        output_path = tmp_path / "bench.json"
        export_bench_results(
            results=results,
            graph_path="examples/demos/hello/graph.yaml",
            variables={"name": "World"},
            output_path=str(output_path),
        )

        assert output_path.exists()
        data = json.loads(output_path.read_text(encoding="utf-8"))
        assert data["graph"] == "examples/demos/hello/graph.yaml"
        assert data["variables"] == {"name": "World"}
        assert len(data["results"]) == 1
        assert data["results"][0]["provider"] == "anthropic"
        assert "timestamp" in data

    @pytest.mark.req("REQ-YG-232")
    def test_export_bench_results_multiple_models(self, tmp_path):
        """Export includes all model results."""
        from yamlgraph.cli.bench_commands import BenchResult, export_bench_results

        results = [
            BenchResult(
                provider="anthropic",
                model="claude-sonnet-4-20250514",
                duration_s=1.23,
                tokens_in=312,
                tokens_out=187,
                status="success",
                output={},
            ),
            BenchResult(
                provider="openai",
                model="gpt-4o",
                duration_s=0.89,
                tokens_in=298,
                tokens_out=201,
                status="success",
                output={},
            ),
        ]
        output_path = tmp_path / "bench.json"
        export_bench_results(
            results=results,
            graph_path="test.yaml",
            variables={},
            output_path=str(output_path),
        )

        data = json.loads(output_path.read_text(encoding="utf-8"))
        assert len(data["results"]) == 2


# =============================================================================
# Bench execution tests (mock LLM)
# =============================================================================


class TestRunBenchmark:
    """Tests for run_benchmark core function."""

    @pytest.mark.req("REQ-YG-232")
    def test_run_single_model_returns_result(self):
        """run_benchmark with one model returns one BenchResult."""
        from yamlgraph.cli.bench_commands import BenchResult, run_benchmark

        mock_app = MagicMock()
        mock_app.invoke.return_value = {"greeting": "Hello"}

        results = run_benchmark(
            app=mock_app,
            initial_state={"name": "World"},
            model_specs=[("anthropic", "claude-sonnet-4-20250514")],
            runs=1,
            config={},
        )

        assert len(results) == 1
        assert isinstance(results[0], BenchResult)
        assert results[0].provider == "anthropic"
        assert results[0].status == "success"

    @pytest.mark.req("REQ-YG-232")
    def test_run_model_error_captured_gracefully(self):
        """Model failures are captured, not raised."""
        from yamlgraph.cli.bench_commands import run_benchmark

        mock_app = MagicMock()
        mock_app.invoke.side_effect = RuntimeError("API key invalid")

        results = run_benchmark(
            app=mock_app,
            initial_state={},
            model_specs=[("anthropic", "claude-sonnet-4-20250514")],
            runs=1,
            config={},
        )

        assert len(results) == 1
        assert results[0].status == "error"
        assert "API key invalid" in results[0].error

    @pytest.mark.req("REQ-YG-232")
    def test_run_multiple_models_all_attempted(self):
        """All models are attempted even if one fails."""
        from yamlgraph.cli.bench_commands import run_benchmark

        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("fail")
            return {"result": "ok"}

        mock_app = MagicMock()
        mock_app.invoke.side_effect = side_effect

        results = run_benchmark(
            app=mock_app,
            initial_state={},
            model_specs=[
                ("anthropic", "claude-sonnet-4-20250514"),
                ("openai", "gpt-4o"),
            ],
            runs=1,
            config={},
        )

        assert len(results) == 2
        assert results[0].status == "error"
        assert results[1].status == "success"

    @pytest.mark.req("REQ-YG-232")
    def test_run_multiple_runs_averages(self):
        """Multiple runs per model accumulate correctly."""
        from yamlgraph.cli.bench_commands import run_benchmark

        mock_app = MagicMock()
        mock_app.invoke.return_value = {"result": "ok"}

        results = run_benchmark(
            app=mock_app,
            initial_state={},
            model_specs=[("anthropic", "claude-sonnet-4-20250514")],
            runs=3,
            config={},
        )

        assert len(results) == 1
        assert results[0].status == "success"
        assert results[0].duration_s >= 0


# =============================================================================
# Dispatch integration test
# =============================================================================


class TestBenchDispatch:
    """Tests for bench subcommand dispatch."""

    @pytest.mark.req("REQ-YG-232")
    def test_dispatch_routes_to_bench(self):
        """cmd_graph_dispatch routes 'bench' to cmd_graph_bench."""
        from yamlgraph.cli.graph_commands import cmd_graph_dispatch

        args = Namespace(graph_command="bench")

        with patch("yamlgraph.cli.bench_commands.cmd_graph_bench") as mock_bench:
            cmd_graph_dispatch(args)
            mock_bench.assert_called_once_with(args)
