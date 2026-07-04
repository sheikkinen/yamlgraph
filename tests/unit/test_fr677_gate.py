"""Acceptance tests for FR-677 Move 3: `graph run --gate` lint gate.

The gate lints the graph before executing and refuses to run when any
error-level finding exists. Warning-level findings are reported but do not
block. In ``--json`` mode the report is machine-readable with no decorative
stdout on success.
"""

import argparse
import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import pytest

from yamlgraph.linter.checks import LintIssue
from yamlgraph.linter.graph_linter import LintResult

GATE_MODULE = "yamlgraph.linter"


def _result(issues: list[LintIssue]) -> LintResult:
    return LintResult(
        file="g.yaml",
        issues=issues,
        valid=not any(i.severity == "error" for i in issues),
    )


def _err(code: str = "E001") -> LintIssue:
    return LintIssue(severity="error", code=code, message="boom", fix="fix it")


def _warn(code: str = "W025") -> LintIssue:
    return LintIssue(severity="warning", code=code, message="meh", fix="maybe")


class TestLintGateBlocking:
    """`_run_lint_gate` blocks only on error-level findings."""

    @pytest.mark.req("REQ-YG-511")
    def test_error_finding_exits_nonzero(self):
        from yamlgraph.cli.graph_commands import _run_lint_gate

        with (
            patch(f"{GATE_MODULE}.lint_graph", return_value=_result([_err()])),
            pytest.raises(SystemExit) as exc,
            redirect_stderr(io.StringIO()),
        ):
            _run_lint_gate(Path("g.yaml"), json_mode=False)
        assert exc.value.code == 1

    @pytest.mark.req("REQ-YG-511")
    def test_warning_only_does_not_block(self):
        from yamlgraph.cli.graph_commands import _run_lint_gate

        with (
            patch(f"{GATE_MODULE}.lint_graph", return_value=_result([_warn()])),
            redirect_stderr(io.StringIO()),
        ):
            # Must return normally (no SystemExit).
            _run_lint_gate(Path("g.yaml"), json_mode=False)

    @pytest.mark.req("REQ-YG-511")
    def test_clean_graph_does_not_block(self):
        from yamlgraph.cli.graph_commands import _run_lint_gate

        with (
            patch(f"{GATE_MODULE}.lint_graph", return_value=_result([])),
            redirect_stderr(io.StringIO()),
        ):
            _run_lint_gate(Path("g.yaml"), json_mode=False)


class TestLintGateJson:
    """`--gate --json` is machine-readable."""

    @pytest.mark.req("REQ-YG-511")
    def test_json_error_emits_json_and_exits(self):
        from yamlgraph.cli.graph_commands import _run_lint_gate

        out = io.StringIO()
        with (
            patch(f"{GATE_MODULE}.lint_graph", return_value=_result([_err()])),
            pytest.raises(SystemExit) as exc,
            redirect_stdout(out),
        ):
            _run_lint_gate(Path("g.yaml"), json_mode=True)
        assert exc.value.code == 1
        assert '"severity"' in out.getvalue()

    @pytest.mark.req("REQ-YG-511")
    def test_json_clean_emits_no_decorative_stdout(self):
        from yamlgraph.cli.graph_commands import _run_lint_gate

        out = io.StringIO()
        with (
            patch(f"{GATE_MODULE}.lint_graph", return_value=_result([_warn()])),
            redirect_stdout(out),
        ):
            _run_lint_gate(Path("g.yaml"), json_mode=True)
        assert out.getvalue() == ""


class TestGateBlocksExecution:
    """When gate blocks, the graph is never compiled or invoked."""

    @pytest.mark.req("REQ-YG-511")
    def test_gate_error_aborts_before_run(self, tmp_path):
        from yamlgraph.cli.graph_commands import cmd_graph_run

        graph_file = tmp_path / "g.yaml"
        graph_file.write_text("nodes: {}\n")
        args = argparse.Namespace(
            graph_path=str(graph_file),
            gate=True,
            json=False,
            stream=False,
            var=[],
            var_file=None,
        )
        with (
            patch(f"{GATE_MODULE}.lint_graph", return_value=_result([_err()])),
            patch("yamlgraph.graph_loader.compile_graph") as mock_compile,
            pytest.raises(SystemExit) as exc,
            redirect_stderr(io.StringIO()),
        ):
            cmd_graph_run(args)
        assert exc.value.code == 1
        mock_compile.assert_not_called()


class TestGateParser:
    """CLI parser exposes --gate."""

    @pytest.mark.req("REQ-YG-511")
    def test_parser_accepts_gate(self):
        from yamlgraph.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["graph", "run", "g.yaml", "--gate"])
        assert args.gate is True

    @pytest.mark.req("REQ-YG-511")
    def test_gate_defaults_false(self):
        from yamlgraph.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["graph", "run", "g.yaml"])
        assert args.gate is False


class TestW025VerifyExpressions:
    """W025 validates graph-level verify expressions (FR-677)."""

    def _write(self, tmp_path: Path, verify_block: str) -> Path:
        graph = tmp_path / "g.yaml"
        graph.write_text(
            "nodes:\n"
            "  step:\n"
            "    type: passthrough\n"
            "edges:\n"
            "  - {from: START, to: step}\n"
            "  - {from: step, to: END}\n" + verify_block
        )
        return graph

    @pytest.mark.req("REQ-YG-511")
    def test_valid_verify_expression_passes(self, tmp_path):
        from yamlgraph.linter.checks_contracts import check_guard_expressions

        graph = self._write(
            tmp_path,
            'verify:\n  - check: "state.result >= 1"\n    on_fail: halt\n',
        )
        issues = check_guard_expressions(graph)
        assert [i for i in issues if i.code == "W025"] == []

    @pytest.mark.req("REQ-YG-511")
    def test_invalid_verify_expression_flagged(self, tmp_path):
        from yamlgraph.linter.checks_contracts import check_guard_expressions

        graph = self._write(
            tmp_path,
            'verify:\n  - check: "import os"\n    on_fail: halt\n',
        )
        issues = check_guard_expressions(graph)
        assert any(i.code == "W025" for i in issues)

    @pytest.mark.req("REQ-YG-511")
    def test_invalid_on_fail_flagged(self, tmp_path):
        from yamlgraph.linter.checks_contracts import check_guard_expressions

        graph = self._write(
            tmp_path,
            'verify:\n  - check: "state.result >= 1"\n    on_fail: retry\n',
        )
        issues = check_guard_expressions(graph)
        assert any(i.code == "W025" and "on_fail" in i.message for i in issues)

    @pytest.mark.req("REQ-YG-511")
    def test_missing_check_flagged(self, tmp_path):
        from yamlgraph.linter.checks_contracts import check_guard_expressions

        graph = self._write(tmp_path, "verify:\n  - on_fail: halt\n")
        issues = check_guard_expressions(graph)
        assert any(i.code == "W025" and "check" in i.message for i in issues)
