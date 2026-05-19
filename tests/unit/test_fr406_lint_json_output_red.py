"""RED acceptance tests for FR-406: graph lint --json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import patch

import pytest


def _make_lint_args(paths: list[str], json_mode: bool) -> argparse.Namespace:
    return argparse.Namespace(graph_path=paths, json=json_mode)


@pytest.mark.req("REQ-YG-406")
def test_ac01_parser_accepts_lint_json_flag_default_false() -> None:
    from yamlgraph.cli import create_parser

    parser = create_parser()
    args_default = parser.parse_args(["graph", "lint", "graphs/test.yaml"])
    args_json = parser.parse_args(["graph", "lint", "--json", "graphs/test.yaml"])

    assert args_default.json is False
    assert args_json.json is True


@pytest.mark.req("REQ-YG-406")
@patch("yamlgraph.cli.graph_validate.lint_graph")
def test_ac02_json_single_file_emits_valid_lintresult_to_stdout(
    mock_lint,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from yamlgraph.cli.graph_validate import cmd_graph_lint
    from yamlgraph.linter.graph_linter import LintResult

    mock_lint.return_value = LintResult(file="g.yaml", issues=[], valid=True)
    args = _make_lint_args(["g.yaml"], json_mode=True)

    with patch.object(Path, "exists", return_value=True):
        cmd_graph_lint(args)

    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["file"] == "g.yaml"
    assert payload["issues"] == []
    assert payload["valid"] is True


@pytest.mark.req("REQ-YG-406")
@patch("yamlgraph.cli.graph_validate.lint_graph")
def test_ac03_json_multi_file_emits_ndjson_one_object_per_file(
    mock_lint,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from yamlgraph.cli.graph_validate import cmd_graph_lint
    from yamlgraph.linter.graph_linter import LintResult

    mock_lint.side_effect = [
        LintResult(file="a.yaml", issues=[], valid=True),
        LintResult(file="b.yaml", issues=[], valid=True),
    ]
    args = _make_lint_args(["a.yaml", "b.yaml"], json_mode=True)

    with patch.object(Path, "exists", return_value=True):
        cmd_graph_lint(args)

    lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert len(lines) == 2
    assert json.loads(lines[0])["file"] == "a.yaml"
    assert json.loads(lines[1])["file"] == "b.yaml"


@pytest.mark.req("REQ-YG-406")
def test_ac04_json_mode_routes_diagnostics_to_stderr_only(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from yamlgraph.cli.graph_validate import cmd_graph_lint

    args = _make_lint_args(["/nonexistent/graph.yaml"], json_mode=True)

    with pytest.raises(SystemExit, match="1"):
        cmd_graph_lint(args)

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "not found" in captured.err.lower()


@pytest.mark.req("REQ-YG-406")
def test_ac05_traceability_entries_for_cap151_and_reqyg406_exist() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    cap_path = repo_root / "capabilities" / "CAP-151-lint-json-output.yaml"
    architecture = (repo_root / "ARCHITECTURE.md").read_text(encoding="utf-8")

    assert cap_path.exists()
    assert "REQ-YG-406" in architecture
