"""Tests for graph validation and linting commands (FR-224).

Unit tests for `yamlgraph/cli/graph_validate.py` covering:
- _validate_required_fields
- _validate_edges
- _validate_nodes
- _report_validation_result
- cmd_graph_validate
- cmd_graph_lint
"""

import argparse
from pathlib import Path
from unittest.mock import patch

import pytest

from yamlgraph.cli.graph_validate import (
    _report_validation_result,
    _validate_edges,
    _validate_nodes,
    _validate_required_fields,
    cmd_graph_lint,
    cmd_graph_validate,
)

# =============================================================================
# _validate_required_fields tests
# =============================================================================


class TestValidateRequiredFields:
    """Tests for _validate_required_fields helper."""

    @pytest.mark.req("REQ-YG-033")
    def test_missing_name_returns_error(self):
        """Config without 'name' should produce an error."""
        config = {"nodes": {"a": {}}, "edges": []}
        errors, warnings = _validate_required_fields(config)
        assert any("name" in e for e in errors)

    @pytest.mark.req("REQ-YG-033")
    def test_missing_nodes_returns_error(self):
        """Config without 'nodes' should produce an error."""
        config = {"name": "test", "edges": []}
        errors, warnings = _validate_required_fields(config)
        assert any("nodes" in e for e in errors)

    @pytest.mark.req("REQ-YG-033")
    def test_no_edges_returns_warning(self):
        """Config without 'edges' should produce a warning."""
        config = {"name": "test", "nodes": {"a": {}}}
        errors, warnings = _validate_required_fields(config)
        assert len(errors) == 0
        assert any("edges" in w.lower() for w in warnings)

    @pytest.mark.req("REQ-YG-033")
    def test_valid_config_no_issues(self):
        """Fully valid config should produce no errors or warnings."""
        config = {
            "name": "test",
            "nodes": {"a": {}},
            "edges": [{"from": "a", "to": "b"}],
        }
        errors, warnings = _validate_required_fields(config)
        assert errors == []
        assert warnings == []


# =============================================================================
# _validate_edges tests
# =============================================================================


class TestValidateEdges:
    """Tests for _validate_edges helper."""

    @pytest.mark.req("REQ-YG-033")
    def test_unknown_from_node(self):
        """Edge referencing unknown 'from' node should be flagged."""
        edges = [{"from": "ghost", "to": "END"}]
        node_names = {"a", "START", "END"}
        errors = _validate_edges(edges, node_names)
        assert any("ghost" in e for e in errors)

    @pytest.mark.req("REQ-YG-033")
    def test_unknown_to_node(self):
        """Edge referencing unknown 'to' node should be flagged."""
        edges = [{"from": "START", "to": "ghost"}]
        node_names = {"a", "START", "END"}
        errors = _validate_edges(edges, node_names)
        assert any("ghost" in e for e in errors)

    @pytest.mark.req("REQ-YG-033")
    def test_conditional_edge_list_unknown_target(self):
        """Conditional edge list with unknown target should be flagged."""
        edges = [{"from": "START", "to": ["a", "ghost"]}]
        node_names = {"a", "START", "END"}
        errors = _validate_edges(edges, node_names)
        assert any("ghost" in e for e in errors)
        # 'a' is valid — should not appear in errors
        assert not any("'a'" in e for e in errors)

    @pytest.mark.req("REQ-YG-033")
    def test_valid_edges_no_errors(self):
        """All-valid edges should produce no errors."""
        edges = [
            {"from": "START", "to": "a"},
            {"from": "a", "to": "END"},
        ]
        node_names = {"a", "START", "END"}
        errors = _validate_edges(edges, node_names)
        assert errors == []


# =============================================================================
# _validate_nodes tests
# =============================================================================


class TestValidateNodes:
    """Tests for _validate_nodes helper."""

    @pytest.mark.req("REQ-YG-033")
    def test_agent_without_tools_warning(self):
        """Agent node without tools should produce a warning."""
        nodes = {"bot": {"type": "agent"}}
        warnings = _validate_nodes(nodes)
        assert any("bot" in w and "tools" in w for w in warnings)

    @pytest.mark.req("REQ-YG-033")
    def test_agent_with_tools_no_warning(self):
        """Agent node with tools should not produce a warning."""
        nodes = {"bot": {"type": "agent", "tools": ["search"]}}
        warnings = _validate_nodes(nodes)
        assert warnings == []

    @pytest.mark.req("REQ-YG-033")
    def test_non_agent_node_no_warning(self):
        """Non-agent node without tools should not produce a warning."""
        nodes = {"gen": {"type": "llm"}}
        warnings = _validate_nodes(nodes)
        assert warnings == []


# =============================================================================
# _report_validation_result tests
# =============================================================================


class TestReportValidationResult:
    """Tests for _report_validation_result helper."""

    @pytest.mark.req("REQ-YG-033")
    def test_errors_prints_invalid_and_exits(self, capsys):
        """Errors should print INVALID and exit(1)."""
        config = {"name": "broken", "nodes": {"a": {}}, "edges": []}
        with pytest.raises(SystemExit, match="1"):
            _report_validation_result(
                Path("graph.yaml"),
                config,
                errors=["Missing field: X"],
                warnings=[],
            )
        captured = capsys.readouterr()
        assert "INVALID" in captured.out

    @pytest.mark.req("REQ-YG-033")
    def test_warnings_prints_valid_with_warnings(self, capsys):
        """Warnings without errors should print VALID with warnings."""
        config = {"name": "test", "nodes": {"a": {}}, "edges": []}
        _report_validation_result(
            Path("graph.yaml"),
            config,
            errors=[],
            warnings=["No edges defined"],
        )
        captured = capsys.readouterr()
        assert "VALID with warnings" in captured.out

    @pytest.mark.req("REQ-YG-033")
    def test_clean_prints_valid(self, capsys):
        """Clean config should print VALID with node/edge counts."""
        config = {
            "name": "test",
            "nodes": {"a": {}, "b": {}},
            "edges": [{"from": "a", "to": "b"}],
        }
        _report_validation_result(
            Path("graph.yaml"),
            config,
            errors=[],
            warnings=[],
        )
        captured = capsys.readouterr()
        assert "VALID" in captured.out
        assert "Nodes: 2" in captured.out
        assert "Edges: 1" in captured.out

    @pytest.mark.req("REQ-YG-033")
    def test_errors_with_warnings_shows_both(self, capsys):
        """Errors + warnings should show both in output."""
        config = {"name": "test", "nodes": {}, "edges": []}
        with pytest.raises(SystemExit):
            _report_validation_result(
                Path("graph.yaml"),
                config,
                errors=["err1"],
                warnings=["warn1"],
            )
        captured = capsys.readouterr()
        assert "err1" in captured.out
        assert "warn1" in captured.out

    @pytest.mark.req("REQ-YG-033")
    def test_uses_stem_when_name_missing(self, capsys):
        """Should use file stem when config has no name."""
        config = {"nodes": {}, "edges": []}
        _report_validation_result(
            Path("my-graph.yaml"),
            config,
            errors=[],
            warnings=[],
        )
        captured = capsys.readouterr()
        assert "my-graph" in captured.out


# =============================================================================
# cmd_graph_validate tests
# =============================================================================


class TestCmdGraphValidate:
    """Tests for cmd_graph_validate command."""

    @pytest.mark.req("REQ-YG-033")
    @patch("yamlgraph.cli.graph_validate.require_graph_config")
    def test_validate_valid_graph(self, mock_require, capsys):
        """Valid graph should print VALID."""
        mock_require.return_value = {
            "name": "test",
            "nodes": {"gen": {"type": "llm"}},
            "edges": [{"from": "START", "to": "gen"}, {"from": "gen", "to": "END"}],
        }
        args = argparse.Namespace(graph_path="graph.yaml")
        cmd_graph_validate(args)
        captured = capsys.readouterr()
        assert "VALID" in captured.out

    @pytest.mark.req("REQ-YG-033")
    @patch("yamlgraph.cli.graph_validate.require_graph_config")
    def test_validate_graph_load_error(self, mock_require):
        """GraphLoadError should print error and exit(1)."""
        from yamlgraph.cli.helpers import GraphLoadError

        mock_require.side_effect = GraphLoadError("File not found: x.yaml")
        args = argparse.Namespace(graph_path="x.yaml")
        with pytest.raises(SystemExit, match="1"):
            cmd_graph_validate(args)

    @pytest.mark.req("REQ-YG-033")
    @patch("yamlgraph.cli.graph_validate.require_graph_config")
    def test_validate_generic_exception(self, mock_require):
        """Generic exception should print error and exit(1)."""
        mock_require.side_effect = RuntimeError("unexpected")
        args = argparse.Namespace(graph_path="x.yaml")
        with pytest.raises(SystemExit, match="1"):
            cmd_graph_validate(args)


# =============================================================================
# cmd_graph_lint tests
# =============================================================================


class TestCmdGraphLint:
    """Tests for cmd_graph_lint command."""

    @pytest.mark.req("REQ-YG-033")
    @patch("yamlgraph.cli.graph_validate.lint_graph")
    def test_lint_valid_graph(self, mock_lint, capsys):
        """Valid graph should print no-issues message."""
        from yamlgraph.linter.graph_linter import LintResult

        mock_lint.return_value = LintResult(file="g.yaml", issues=[], valid=True)
        args = argparse.Namespace(graph_path=["examples/demos/hello/graph.yaml"])
        with patch.object(Path, "exists", return_value=True):
            cmd_graph_lint(args)
        captured = capsys.readouterr()
        assert "No issues found" in captured.out

    @pytest.mark.req("REQ-YG-033")
    def test_lint_missing_file(self, capsys):
        """Missing file should count as error and not crash."""
        args = argparse.Namespace(graph_path=["/nonexistent/graph.yaml"])
        # Should not exit(1) — individual file errors accumulate
        # but exit only if total_errors > 0 at summary time
        with pytest.raises(SystemExit, match="1"):
            cmd_graph_lint(args)
        captured = capsys.readouterr()
        assert "not found" in captured.out

    @pytest.mark.req("REQ-YG-033")
    @patch("yamlgraph.cli.graph_validate.lint_graph")
    def test_lint_multiple_files(self, mock_lint, capsys):
        """Multiple files should each be linted and summary printed."""
        from yamlgraph.linter.graph_linter import LintResult

        mock_lint.return_value = LintResult(file="g.yaml", issues=[], valid=True)
        args = argparse.Namespace(graph_path=["a.yaml", "b.yaml"])
        with patch.object(Path, "exists", return_value=True):
            cmd_graph_lint(args)
        captured = capsys.readouterr()
        assert mock_lint.call_count == 2
        assert "All graphs passed" in captured.out

    @pytest.mark.req("REQ-YG-033")
    @patch("yamlgraph.cli.graph_validate.lint_graph")
    def test_lint_errors_exit_code_1(self, mock_lint):
        """Lint errors should cause exit code 1."""
        from yamlgraph.linter.checks import LintIssue
        from yamlgraph.linter.graph_linter import LintResult

        issue = LintIssue(
            severity="error", code="E001", message="bad node", fix="fix it"
        )
        mock_lint.return_value = LintResult(file="g.yaml", issues=[issue], valid=False)
        args = argparse.Namespace(graph_path=["g.yaml"])
        with (
            patch.object(Path, "exists", return_value=True),
            pytest.raises(SystemExit, match="1"),
        ):
            cmd_graph_lint(args)

    @pytest.mark.req("REQ-YG-033")
    @patch("yamlgraph.cli.graph_validate.lint_graph")
    def test_lint_warnings_only_exit_code_0(self, mock_lint, capsys):
        """Warnings only should not cause exit(1)."""
        from yamlgraph.linter.checks import LintIssue
        from yamlgraph.linter.graph_linter import LintResult

        issue = LintIssue(severity="warning", code="W001", message="missing prompt")
        mock_lint.return_value = LintResult(file="g.yaml", issues=[issue], valid=True)
        args = argparse.Namespace(graph_path=["g.yaml"])
        with patch.object(Path, "exists", return_value=True):
            cmd_graph_lint(args)
        captured = capsys.readouterr()
        assert "1 warning" in captured.out

    @pytest.mark.req("REQ-YG-033")
    @patch("yamlgraph.cli.graph_validate.lint_graph")
    def test_lint_exception_counts_as_error(self, mock_lint):
        """Exception during lint should count as error."""
        mock_lint.side_effect = RuntimeError("parse fail")
        args = argparse.Namespace(graph_path=["g.yaml"])
        with (
            patch.object(Path, "exists", return_value=True),
            pytest.raises(SystemExit, match="1"),
        ):
            cmd_graph_lint(args)

    @pytest.mark.req("REQ-YG-033")
    @patch("yamlgraph.cli.graph_validate.lint_graph")
    def test_lint_shows_fix_suggestions(self, mock_lint, capsys):
        """Lint issues with fix suggestions should display them."""
        from yamlgraph.linter.checks import LintIssue
        from yamlgraph.linter.graph_linter import LintResult

        issue = LintIssue(
            severity="error", code="E001", message="bad node", fix="Add tools"
        )
        mock_lint.return_value = LintResult(file="g.yaml", issues=[issue], valid=False)
        args = argparse.Namespace(graph_path=["g.yaml"])
        with patch.object(Path, "exists", return_value=True), pytest.raises(SystemExit):
            cmd_graph_lint(args)
        captured = capsys.readouterr()
        assert "Fix: Add tools" in captured.out
