"""Graph validation and linting commands.

Provides validation helpers and CLI commands for checking graph YAML files.
"""

import sys
from argparse import Namespace
from pathlib import Path
from typing import TextIO

from yamlgraph.cli.helpers import GraphLoadError, require_graph_config
from yamlgraph.config import WORKING_DIR
from yamlgraph.linter import lint_graph
from yamlgraph.linter.checks import LintIssue


def _validate_required_fields(config: dict) -> tuple[list[str], list[str]]:
    """Validate required fields in graph config.

    Args:
        config: Parsed YAML configuration

    Returns:
        Tuple of (errors, warnings) lists
    """
    errors = []
    warnings = []

    if not config.get("name"):
        errors.append("Missing required field: name")

    if not config.get("nodes"):
        errors.append("Missing required field: nodes")

    if not config.get("edges"):
        warnings.append("No edges defined")

    return errors, warnings


def _validate_edges(edges: list[dict], node_names: set[str]) -> list[str]:
    """Validate edge references in graph config.

    Args:
        edges: List of edge configurations
        node_names: Set of valid node names (including START/END)

    Returns:
        List of error messages
    """
    errors = []

    for i, edge in enumerate(edges):
        from_node = edge.get("from", "")
        to_node = edge.get("to", "")

        if from_node not in node_names:
            errors.append(f"Edge {i + 1}: unknown 'from' node '{from_node}'")

        # Handle conditional edges where 'to' is a list
        if isinstance(to_node, list):
            for t in to_node:
                if t not in node_names:
                    errors.append(f"Edge {i + 1}: unknown 'to' node '{t}'")
        elif to_node not in node_names:
            errors.append(f"Edge {i + 1}: unknown 'to' node '{to_node}'")

    return errors


def _validate_nodes(nodes: dict) -> list[str]:
    """Validate node configurations.

    Args:
        nodes: Dict of node_name -> node_config

    Returns:
        List of warning messages
    """
    warnings = []

    for node_name, node_config in nodes.items():
        node_type = node_config.get("type", "llm")
        if node_type == "agent" and not node_config.get("tools"):
            warnings.append(f"Node '{node_name}': agent has no tools")

    return warnings


def _report_validation_result(
    graph_path: Path,
    config: dict,
    errors: list[str],
    warnings: list[str],
) -> None:
    """Report validation results and exit appropriately.

    Args:
        graph_path: Path to the graph file
        config: Parsed graph configuration
        errors: List of error messages
        warnings: List of warning messages
    """
    name = config.get("name", graph_path.stem)
    nodes = config.get("nodes", {})
    edges = config.get("edges", [])

    if errors:
        print(f"\n❌ {graph_path.name} ({name}) - INVALID\n")
        for err in errors:
            print(f"   ✗ {err}")
        for warn in warnings:
            print(f"   ⚠ {warn}")
        print()
        sys.exit(1)
    elif warnings:
        print(f"\n⚠️  {graph_path.name} ({name}) - VALID with warnings\n")
        for warn in warnings:
            print(f"   ⚠ {warn}")
        print()
    else:
        print(f"\n✅ {graph_path.name} ({name}) - VALID\n")
        print(f"   Nodes: {len(nodes)}")
        print(f"   Edges: {len(edges)}")
        print()


def cmd_graph_validate(args: Namespace) -> None:
    """Validate a graph YAML file.

    Checks:
    - File exists and is valid YAML
    - Required fields present (name, nodes, edges)
    - Node references are valid
    - Edge references match existing nodes
    """
    graph_path = Path(args.graph_path)

    try:
        config = require_graph_config(graph_path)

        # Run validations
        errors, warnings = _validate_required_fields(config)

        nodes = config.get("nodes", {})
        edges = config.get("edges", [])
        node_names = set(nodes.keys()) | {"START", "END"}

        errors.extend(_validate_edges(edges, node_names))
        warnings.extend(_validate_nodes(nodes))

        # Report results
        _report_validation_result(graph_path, config, errors, warnings)

    except GraphLoadError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error validating graph: {e}")
        sys.exit(1)


def _report_human_lint_result(
    graph_path: Path,
    errors: list[LintIssue],
    warnings: list[LintIssue],
    issues: list[LintIssue],
) -> None:
    """Print human-readable lint output for a single graph file."""
    if not errors and not warnings:
        print(f"✅ {graph_path.name} - No issues found")
        return

    status = "❌" if errors else "⚠️"
    print(f"{status} {graph_path.name}")
    for issue in issues:
        icon = "❌" if issue.severity == "error" else "⚠"
        print(f"   {icon} [{issue.code}] {issue.message}")
        if issue.fix:
            print(f"      Fix: {issue.fix}")


def _lint_single_graph(
    graph_path: Path,
    *,
    json_mode: bool,
    error_stream: TextIO,
) -> tuple[int, int]:
    """Lint one graph file and emit output in human or JSON mode."""
    try:
        result = lint_graph(graph_path, WORKING_DIR)
    except Exception as e:
        print(f"❌ Error linting {graph_path}: {e}", file=error_stream)
        return 1, 0

    errors = [issue for issue in result.issues if issue.severity == "error"]
    warnings = [issue for issue in result.issues if issue.severity == "warning"]

    if json_mode:
        print(result.model_dump_json())
    else:
        _report_human_lint_result(graph_path, errors, warnings, result.issues)

    return len(errors), len(warnings)


def cmd_graph_lint(args: Namespace) -> None:
    """Lint graph YAML files for issues.

    Checks:
    - Missing state declarations for variables
    - Undefined tool references
    - Missing prompt files
    - Unreachable nodes
    - Invalid node types
    """
    total_errors = 0
    total_warnings = 0
    json_mode = getattr(args, "json", False)
    error_stream = sys.stderr if json_mode else sys.stdout

    for graph_path_str in args.graph_path:
        graph_path = Path(graph_path_str)

        if not graph_path.exists():
            print(f"❌ Graph file not found: {graph_path}", file=error_stream)
            total_errors += 1
            continue

        errors, warnings = _lint_single_graph(
            graph_path,
            json_mode=json_mode,
            error_stream=error_stream,
        )
        total_errors += errors
        total_warnings += warnings

    # Summary
    if json_mode:
        if total_errors > 0:
            sys.exit(1)
        return

    print()
    if total_errors == 0 and total_warnings == 0:
        print("✅ All graphs passed linting")
    else:
        print(f"Found {total_errors} error(s) and {total_warnings} warning(s)")
        if total_errors > 0:
            sys.exit(1)


__all__ = [
    "cmd_graph_validate",
    "cmd_graph_lint",
    "_validate_required_fields",
    "_validate_edges",
    "_validate_nodes",
    "_report_validation_result",
]
