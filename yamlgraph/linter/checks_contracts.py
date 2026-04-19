"""FR-061: Contract violation lint checks.

These checks detect misconfigurations that parse successfully but fail or
behave incorrectly at runtime — the gap between "valid YAML" and "correct graph".

E012: Hyphen in identifier position (state key, node name, tool name, state_key)
W021: skip_if_exists on list field with add reducer
W017: on_error: skip silently drops failures (FR-165)

Note: W020 (variables: on type: python) was removed by FR-252 — python nodes
now resolve variables: expressions, consistent with all other node types.
"""

from __future__ import annotations

from pathlib import Path

from yamlgraph.linter.checks import LintIssue, load_graph


def check_identifier_keys(graph_path: Path) -> list[LintIssue]:
    """E012: Keys used as Python identifiers must not contain hyphens.

    State keys, node names, and tool names become Python identifiers
    at runtime. Hyphens are valid in YAML but invalid in Python.
    """
    issues = []
    graph = load_graph(graph_path)

    # Check state keys
    for key in graph.get("state", {}):
        if "-" in key:
            issues.append(
                LintIssue(
                    severity="error",
                    code="E012",
                    message=f"State key '{key}' contains hyphen — invalid as Python identifier",
                    fix=f"Rename to '{key.replace('-', '_')}'",
                )
            )

    # Check node names (become Python function names)
    for node_name in graph.get("nodes", {}):
        if "-" in node_name:
            issues.append(
                LintIssue(
                    severity="error",
                    code="E012",
                    message=f"Node name '{node_name}' contains hyphen — invalid as Python identifier",
                    fix=f"Rename to '{node_name.replace('-', '_')}'",
                )
            )

    # Check node state_key values
    for node_name, node_config in graph.get("nodes", {}).items():
        state_key = node_config.get("state_key", "")
        if "-" in state_key:
            issues.append(
                LintIssue(
                    severity="error",
                    code="E012",
                    message=f"Node '{node_name}' state_key '{state_key}' contains hyphen",
                    fix=f"Rename to '{state_key.replace('-', '_')}'",
                )
            )

    # Check tool names (used as function names)
    for tool_name in graph.get("tools", {}):
        if "-" in tool_name:
            issues.append(
                LintIssue(
                    severity="error",
                    code="E012",
                    message=f"Tool name '{tool_name}' contains hyphen — invalid as function name",
                    fix=f"Rename to '{tool_name.replace('-', '_')}'",
                )
            )

    return issues


def check_skip_if_exists_add_reducer(graph_path: Path) -> list[LintIssue]:
    """W021: skip_if_exists on list fields with add reducer is likely wrong.

    Lists are truthy after the first element, so skip_if_exists triggers
    after turn 1 even when you want to keep generating. LLM nodes default
    to skip_if_exists=True.
    """
    issues = []
    graph = load_graph(graph_path)
    state_def = graph.get("state", {})

    for node_name, node_config in graph.get("nodes", {}).items():
        # skip_if_exists defaults to True for LLM nodes — check both explicit and implicit
        node_type = node_config.get("type", "llm")
        skip_if_exists = node_config.get("skip_if_exists")

        # Only LLM nodes have skip_if_exists default True
        if skip_if_exists is None and node_type == "llm":
            skip_if_exists = True
        elif skip_if_exists is None:
            continue

        if not skip_if_exists:
            continue

        state_key = node_config.get("state_key")
        if not state_key:
            continue

        field_type = state_def.get(state_key, "")
        is_list = (
            isinstance(field_type, str)
            and field_type.startswith("list")
            or (
                isinstance(field_type, dict)
                and field_type.get("type", "").startswith("list")
            )
        )

        if is_list:
            issues.append(
                LintIssue(
                    severity="warning",
                    code="W021",
                    message=f"Node '{node_name}': skip_if_exists on list field '{state_key}' "
                    "— list is truthy after first element, so skip triggers after turn 1",
                    fix="Set skip_if_exists: false or use a boolean control field instead",
                )
            )

    return issues


def check_top_level_provider_model(graph_path: Path) -> list[LintIssue]:
    """W016: provider/model at top level is silently ignored.

    These keys only take effect inside the defaults: block or per-node.
    Placing them at top level creates silent configuration drift.
    """
    issues = []
    graph = load_graph(graph_path)

    for key in ("provider", "model"):
        if key in graph and key not in graph.get("defaults", {}):
            issues.append(
                LintIssue(
                    severity="warning",
                    code="W016",
                    message=(
                        f"'{key}' at top level has no effect; move to 'defaults:' block"
                    ),
                    fix=f"defaults:\n  {key}: {graph[key]}",
                )
            )
        elif key in graph and key in graph.get("defaults", {}):
            issues.append(
                LintIssue(
                    severity="warning",
                    code="W016",
                    message=(
                        f"'{key}' at top level has no effect "
                        f"(defaults.{key} already set); remove top-level '{key}'"
                    ),
                    fix=f"Remove top-level '{key}:' line",
                )
            )

    return issues


def check_skip_without_verification(graph_path: Path) -> list[LintIssue]:
    """W022: on_error: skip without verification question (FR-164).

    Nodes using on_error: skip without a verification question risk
    silent failures — the skip executes without any stated expectation
    of what correct behavior looks like.
    """
    issues = []
    graph = load_graph(graph_path)

    for node_name, node_config in graph.get("nodes", {}).items():
        if node_config.get("on_error") == "skip" and not node_config.get(
            "verification"
        ):
            issues.append(
                LintIssue(
                    severity="warning",
                    code="W022",
                    message=(
                        f"Node '{node_name}' uses on_error: skip without "
                        f"verification question. Add verification.question to "
                        f"make skip behavior observable."
                    ),
                    fix='Add verification:\n  question: "Will return non-empty"',
                )
            )

    return issues


def check_silent_fallback(graph_path: Path) -> list[LintIssue]:
    """W017: on_error: skip silently drops failures.

    Nodes with on_error: skip swallow errors — the pipeline continues
    as if nothing happened, producing incomplete or wrong results without
    any trace of the failure. Use on_error: fail or on_error: fallback instead.
    """
    issues = []
    graph = load_graph(graph_path)

    for node_name, node_config in graph.get("nodes", {}).items():
        if node_config.get("on_error") == "skip":
            issues.append(
                LintIssue(
                    severity="warning",
                    code="W017",
                    message=(
                        f"Node '{node_name}' uses on_error: skip — "
                        f"failures are silently dropped"
                    ),
                    fix=(
                        "Use on_error: fail (crash loudly), "
                        "on_error: fallback (with explicit config), "
                        "or add error state accumulation in a downstream node"
                    ),
                )
            )
    return issues


__all__ = [
    "check_identifier_keys",
    "check_skip_if_exists_add_reducer",
    "check_top_level_provider_model",
    "check_skip_without_verification",
    "check_silent_fallback",
]
