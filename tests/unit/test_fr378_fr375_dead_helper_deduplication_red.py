"""Acceptance tests for FR-378: remove dead duplicate _handle_optional_exports.

RED tests — all must fail before implementation, pass after.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GRAPH_COMMANDS = REPO_ROOT / "yamlgraph" / "cli" / "graph_commands.py"
GRAPH_RUN_HELPERS = REPO_ROOT / "yamlgraph" / "cli" / "graph_run_helpers.py"

FN_NAME = "_handle_optional_exports"


def _count_defs(path: Path, name: str) -> int:
    tree = ast.parse(path.read_text())
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


def _has_alias(path: Path, name: str) -> bool:
    """Return True if `name = _graph_run_helpers.<name>` alias exists."""
    source = path.read_text()
    return f"{name} = _graph_run_helpers.{name}" in source


@pytest.mark.req("REQ-YG-033")
def test_ac01_graph_commands_has_no_local_handle_optional_exports_definition() -> None:
    """AC-01: graph_commands.py must not define _handle_optional_exports locally."""
    count = _count_defs(GRAPH_COMMANDS, FN_NAME)
    assert count == 0, (
        f"{GRAPH_COMMANDS.name} still defines `{FN_NAME}` locally "
        f"({count} definition(s) found). Remove and alias from graph_run_helpers."
    )


@pytest.mark.req("REQ-YG-033")
def test_ac02_graph_run_helpers_has_single_handle_optional_exports_definition() -> None:
    """AC-02: graph_run_helpers.py must contain exactly one canonical definition."""
    count = _count_defs(GRAPH_RUN_HELPERS, FN_NAME)
    assert count == 1, (
        f"{GRAPH_RUN_HELPERS.name} has {count} definition(s) of `{FN_NAME}`; "
        "expected exactly 1 canonical implementation."
    )


@pytest.mark.req("REQ-YG-033")
def test_ac03_graph_commands_aliases_handle_optional_exports_from_helpers() -> None:
    """AC-03: graph_commands.py must alias _handle_optional_exports from graph_run_helpers."""
    assert _has_alias(GRAPH_COMMANDS, FN_NAME), (
        f"{GRAPH_COMMANDS.name} does not alias `{FN_NAME}` from _graph_run_helpers. "
        "Add: `_handle_optional_exports = _graph_run_helpers._handle_optional_exports`"
    )


@pytest.mark.req("REQ-YG-033")
def test_ac04_cmd_graph_run_optional_exports_behavior_contract_preserved() -> None:
    """AC-04: cmd_graph_run must still call _handle_optional_exports (alias resolves)."""
    import argparse

    from yamlgraph.cli.graph_commands import _handle_optional_exports

    args = argparse.Namespace(
        export=False,
        export_state=None,
    )
    graph_path = Path("/fake/graph.yaml")
    result: dict = {}

    # Must not raise — if alias is broken this will fail with AttributeError/ImportError
    _handle_optional_exports(
        args,
        graph_path,
        result,
        json_mode=False,
        error_stream=None,
    )


@pytest.mark.req("REQ-YG-033")
def test_ac05_vulture_with_whitelist_is_clean_for_cli_refactor_scope() -> None:
    """AC-05: vulture must report no dead code after deduplication."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "vulture",
            "yamlgraph",
            "vulture_whitelist.py",
            "--min-confidence",
            "60",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert (
        result.returncode == 0
    ), f"vulture found dead code:\n{result.stdout}\n{result.stderr}"
