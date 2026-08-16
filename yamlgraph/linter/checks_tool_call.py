"""tool_call node linter checks (FR-025, FR-810).

Split from checks_semantic.py at the 450-line module cap.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from yamlgraph.linter.checks import LintIssue, load_graph

__all__ = ["check_tool_call_nodes"]


def _is_statically_non_graph(tool_decl: dict, graph_dir: Path) -> bool:
    """True only when the declaration provably resolves to a non-graph tool.

    Inline declarations carry their type directly. Manifest-backed tools
    are resolved by reading the manifest's runtime.type; an unreadable or
    malformed manifest is unknown, not non-graph (fail open — W703 is
    advisory and a false warning misdirects authors).
    """
    manifest_ref = tool_decl.get("manifest")
    if not manifest_ref:
        return tool_decl.get("type") != "graph"
    try:
        manifest = yaml.safe_load((graph_dir / manifest_ref).read_text())
        runtime_type = manifest["runtime"]["type"]
    except (OSError, yaml.YAMLError, KeyError, TypeError):
        return False
    return runtime_type != "graph"


def check_tool_call_nodes(graph_path: Path) -> list[LintIssue]:
    """Check tool_call nodes have required tool and args fields.

    E701 — tool_call node missing 'tool' field
    E702 — tool_call node missing 'args' field
    W703 — parsed_key on a statically known non-graph tool (FR-810)
    """
    issues: list[LintIssue] = []
    graph = load_graph(graph_path)
    tools = graph.get("tools", {}) or {}

    for node_name, node_config in graph.get("nodes", {}).items():
        if node_config.get("type") != "tool_call":
            continue
        if node_config.get("parsed_key"):
            tool_ref = node_config.get("tool")
            tool_decl = tools.get(tool_ref) if isinstance(tool_ref, str) else None
            if isinstance(tool_decl, dict) and _is_statically_non_graph(
                tool_decl, graph_path.parent
            ):
                issues.append(
                    LintIssue(
                        severity="warning",
                        code="W703",
                        message=(
                            f"tool_call node '{node_name}' uses parsed_key with "
                            f"non-graph tool '{tool_ref}' — parsed_key requires "
                            f"a graph-runtime tool (FR-810)"
                        ),
                        fix=f"Remove parsed_key or make '{tool_ref}' a graph tool",
                    )
                )
        if "tool" not in node_config:
            issues.append(
                LintIssue(
                    severity="error",
                    code="E701",
                    message=f"tool_call node '{node_name}' missing required 'tool' field",
                    fix=f"Add 'tool: <tool_name>' to node '{node_name}'",
                )
            )
        if "args" not in node_config:
            issues.append(
                LintIssue(
                    severity="error",
                    code="E702",
                    message=f"tool_call node '{node_name}' missing required 'args' field",
                    fix=f"Add 'args:' mapping to node '{node_name}'",
                )
            )

    return issues
