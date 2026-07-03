"""Semantic & cross-reference linter checks (FR-025, FR-026, FR-172)."""

from __future__ import annotations

import re
from pathlib import Path

from yamlgraph.linter.checks import BUILTIN_STATE_FIELDS, LintIssue, load_graph
from yamlgraph.models.state_builder import COMMON_INPUT_FIELDS

# Sentinel node names that are always valid edge endpoints
_SENTINEL_NODES = {"START", "END"}

# Node types that do NOT support retry/fallback error handling
_NON_LLM_NODE_TYPES = {"tool", "python", "tool_call", "passthrough", "interactive_tool"}


def _err(code: str, message: str, fix: str) -> LintIssue:
    """Shorthand for error-severity LintIssue."""
    return LintIssue(severity="error", code=code, message=message, fix=fix)


def _node_fix(node_names: set[str]) -> str:
    """Build common fix suggestion listing valid node names."""
    return f"Check spelling; defined nodes: {', '.join(sorted(node_names))}"


def check_cross_references(graph_path: Path) -> list[LintIssue]:
    """Check edge from/to, loop_limits, and loop_exits reference existing nodes.

    E006 — edge endpoint references non-existent node
    E008 — loop_limits key references non-existent node
    E009 — loop_exits key not in loop_limits or target is invalid (FR-172)
    """
    issues: list[LintIssue] = []
    graph = load_graph(graph_path)

    node_names = set(graph.get("nodes", {}).keys())
    valid_targets = node_names | _SENTINEL_NODES
    fix = _node_fix(node_names)

    # E006: edge from/to validation
    for edge in graph.get("edges", []):
        from_node = edge.get("from")
        if from_node and from_node not in valid_targets:
            issues.append(
                _err(
                    "E006",
                    f"Edge 'from' references non-existent node '{from_node}'",
                    fix,
                )
            )
        to_value = edge.get("to")
        to_targets = (
            to_value if isinstance(to_value, list) else [to_value] if to_value else []
        )
        for target in to_targets:
            if target not in valid_targets:
                issues.append(
                    _err(
                        "E006",
                        f"Edge 'to' references non-existent node '{target}'",
                        fix,
                    )
                )

    # E008: loop_limits keys
    for key in graph.get("loop_limits", {}):
        if key not in node_names:
            issues.append(
                _err("E008", f"loop_limits references non-existent node '{key}'", fix)
            )

    # E009: loop_exits validation (FR-172)
    loop_limits = graph.get("loop_limits", {})
    for key, target in graph.get("loop_exits", {}).items():
        if key not in loop_limits:
            issues.append(
                _err(
                    "E009",
                    f"loop_exits key '{key}' is not in loop_limits",
                    f"Add '{key}: <limit>' to loop_limits or remove from loop_exits",
                )
            )
        if target != "END" and target not in node_names:
            issues.append(
                _err("E009", f"loop_exits target '{target}' is not a valid node", fix)
            )

    return issues


def check_passthrough_nodes(graph_path: Path) -> list[LintIssue]:
    """Check passthrough nodes have required output field.

    E601 — passthrough node missing output (silent no-op)
    """
    issues: list[LintIssue] = []
    graph = load_graph(graph_path)

    for node_name, node_config in graph.get("nodes", {}).items():
        if node_config.get("type") == "passthrough" and "output" not in node_config:
            issues.append(
                LintIssue(
                    severity="error",
                    code="E601",
                    message=f"Passthrough node '{node_name}' has no 'output' — it will be a silent no-op",
                    fix=f"Add 'output:' mapping to node '{node_name}'",
                )
            )

    return issues


def check_tool_call_nodes(graph_path: Path) -> list[LintIssue]:
    """Check tool_call nodes have required tool and args fields.

    E701 — tool_call node missing 'tool' field
    E702 — tool_call node missing 'args' field
    """
    issues: list[LintIssue] = []
    graph = load_graph(graph_path)

    for node_name, node_config in graph.get("nodes", {}).items():
        if node_config.get("type") != "tool_call":
            continue
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


def _build_known_state_fields(graph: dict) -> set[str]:
    """Build the complete set of known state field names from a parsed graph.

    Sources: state: section, node state_key values, BUILTIN_STATE_FIELDS,
    COMMON_INPUT_FIELDS, data_files keys, map collect keys.
    """
    fields: set[str] = set(graph.get("state", {}).keys())
    fields.update(BUILTIN_STATE_FIELDS)
    fields.update(COMMON_INPUT_FIELDS.keys())
    for key in graph.get("data_files", {}):
        fields.add(key)
    for node_config in graph.get("nodes", {}).values():
        if "state_key" in node_config:
            fields.add(node_config["state_key"])
        if collect := node_config.get("collect"):
            fields.add(collect)
    return fields


def _check_w801_condition_braces(graph: dict) -> list[LintIssue]:
    """W801: condition uses {braces} or state. prefix (should be bare names)."""
    issues: list[LintIssue] = []
    for edge in graph.get("edges", []):
        condition = edge.get("condition")
        if not condition or not isinstance(condition, str):
            continue
        if re.search(r"\{state\.", condition) or re.search(r"\{[a-zA-Z_]", condition):
            issues.append(
                LintIssue(
                    severity="warning",
                    code="W801",
                    message=f"Condition '{condition}' uses braces — conditions use bare variable names",
                    fix="Remove {{ }} braces and 'state.' prefix from condition expression",
                )
            )
    return issues


def _check_w007_bare_refs(
    node_name: str, value: str, known_fields: set[str]
) -> list[LintIssue]:
    """W007: variable {name} without state. prefix where name is known state field."""
    issues: list[LintIssue] = []
    protected = value.replace("{{", "\x00").replace("}}", "\x01")
    for ref in re.findall(r"\{(\w+)\}", protected):
        if ref in known_fields:
            issues.append(
                LintIssue(
                    severity="warning",
                    code="W007",
                    message=(
                        f"Variable '{{{{ {ref} }}}}' in node '{node_name}' "
                        f"appears to reference state field '{ref}' "
                        f"without 'state.' prefix"
                    ),
                    fix=f"Use '{{{{state.{ref}}}}}' instead of '{{{{{ref}}}}}'",
                )
            )
    return issues


def _check_e007_unknown_state_refs(
    node_name: str, value: str, known_fields: set[str]
) -> list[LintIssue]:
    """E007: {state.X} where X is not in known fields."""
    issues: list[LintIssue] = []
    protected = value.replace("{{", "\x00").replace("}}", "\x01")
    for ref in re.findall(r"\{state\.(\w+)", protected):
        if ref not in known_fields:
            issues.append(
                LintIssue(
                    severity="error",
                    code="E007",
                    message=(
                        f"'{{{{state.{ref}}}}}' in node '{node_name}' "
                        f"references undeclared state field '{ref}'"
                    ),
                    fix=f"Add '{ref}: str' to the state section or check for typos",
                )
            )
    return issues


def _extract_expression_values(node_config: dict) -> list[str]:
    """Extract all string values from expression-bearing sections."""
    values: list[str] = []
    for section in ("variables", "output", "args", "input_mapping"):
        mapping = node_config.get(section) or {}
        if isinstance(mapping, dict):
            values.extend(v for v in mapping.values() if isinstance(v, str))
    if isinstance(node_config.get("over"), str):
        values.append(node_config["over"])
    return values


def check_expression_syntax(graph_path: Path) -> list[LintIssue]:
    """Check condition and variable expression syntax.

    W801 — condition uses {braces} or state. prefix (should be bare names)
    W007 — variable expression uses {name} without state. prefix
    E007 — {state.X} references field not in known state
    """
    graph = load_graph(graph_path)
    issues = _check_w801_condition_braces(graph)
    known_fields = _build_known_state_fields(graph)

    for node_name, node_config in graph.get("nodes", {}).items():
        for value in _extract_expression_values(node_config):
            issues.extend(_check_w007_bare_refs(node_name, value, known_fields))
            issues.extend(
                _check_e007_unknown_state_refs(node_name, value, known_fields)
            )

    return issues


def check_error_handling(graph_path: Path) -> list[LintIssue]:
    """Check error handling configuration.

    E010 — on_error: fallback without fallback configuration
    E011 — on_error: retry/fallback on tool/python node (unsupported)
    """
    issues: list[LintIssue] = []
    graph = load_graph(graph_path)

    for node_name, node_config in graph.get("nodes", {}).items():
        on_error = node_config.get("on_error")
        node_type = node_config.get("type", "llm")

        # E010: fallback without config
        if on_error == "fallback" and "fallback" not in node_config:
            issues.append(
                LintIssue(
                    severity="error",
                    code="E010",
                    message=f"Node '{node_name}' has on_error: fallback but no fallback config",
                    fix=f"Add 'fallback:' config to node '{node_name}' (e.g., fallback: {{provider: openai}})",
                )
            )

        # E011: retry/fallback on non-LLM nodes (unsupported)
        if on_error in ("retry", "fallback") and node_type in _NON_LLM_NODE_TYPES:
            issues.append(
                LintIssue(
                    severity="error",
                    code="E011",
                    message=(
                        f"Node '{node_name}' (type: {node_type}) has on_error: {on_error} "
                        f"but only LLM nodes support retry/fallback"
                    ),
                    fix=f"Change on_error to 'skip' or 'fail' for node '{node_name}'",
                )
            )

    return issues


def check_edge_types(graph_path: Path) -> list[LintIssue]:
    """Check conditional edges have list 'to' target.

    E802 — conditional edge with string 'to' (silently becomes normal edge)
    """
    issues: list[LintIssue] = []
    graph = load_graph(graph_path)

    for edge in graph.get("edges", []):
        edge_type = edge.get("type")
        if edge_type == "conditional" and not isinstance(edge.get("to"), list):
            from_node = edge.get("from", "?")
            issues.append(
                LintIssue(
                    severity="error",
                    code="E802",
                    message=(
                        f"Conditional edge from '{from_node}' has string 'to' — "
                        f"conditional edges require a list of targets"
                    ),
                    fix="Change 'to: node' to 'to: [node_a, node_b]'",
                )
            )

    return issues


def check_unguarded_cycles(graph_path: Path) -> list[LintIssue]:
    """Warn when cycle nodes lack loop_limits entries.

    W012 — node in cycle without loop_limits
    """
    from yamlgraph.loop_detector import detect_loop_nodes

    issues: list[LintIssue] = []
    graph = load_graph(graph_path)

    edges = graph.get("edges", [])
    loop_nodes = detect_loop_nodes(edges)
    loop_limits = graph.get("loop_limits", {})

    for node in sorted(loop_nodes):
        if node not in loop_limits:
            issues.append(
                LintIssue(
                    severity="warning",
                    code="W012",
                    message=f"Node '{node}' is in a cycle but has no loop_limits entry",
                    fix=f"Add '{node}: <limit>' to loop_limits section",
                )
            )

    return issues


def check_skip_if_exists_in_cycle(graph_path: Path) -> list[LintIssue]:
    """Warn when cycle node has explicit skip_if_exists: true.

    W015 — skip_if_exists: true on a node in a cycle.

    When a node participates in a cycle and has skip_if_exists explicitly
    set to true, it will cache its first output and return stale results
    on every subsequent iteration — the graph loops but produces no new work.

    Only fires on EXPLICIT `skip_if_exists: true`. Does not warn on nodes
    that inherit the default, because apply_loop_node_defaults() in
    graph_loader.py already corrects the default at runtime.
    """
    from yamlgraph.loop_detector import detect_loop_nodes

    issues: list[LintIssue] = []
    graph = load_graph(graph_path)

    edges = graph.get("edges", [])
    loop_nodes = detect_loop_nodes(edges)
    nodes = graph.get("nodes", {})

    for node_name in sorted(loop_nodes):
        node_config = nodes.get(node_name, {})
        # Only warn on EXPLICIT skip_if_exists: true (not default)
        if node_config.get("skip_if_exists") is True:
            issues.append(
                LintIssue(
                    severity="warning",
                    code="W015",
                    message=(
                        f"Node '{node_name}' is in a cycle with "
                        f"skip_if_exists: true — it will return "
                        f"cached output on every iteration"
                    ),
                    fix=(
                        f"Set 'skip_if_exists: false' on node "
                        f"'{node_name}' or remove the explicit setting"
                    ),
                )
            )

    return issues


def check_dynamic_map_without_max_items(
    node_name: str, node_config: dict, graph_config: dict
) -> list[LintIssue]:
    """W013: dynamic fan-out without explicit cap."""
    over = node_config.get("over")
    if not isinstance(over, str) or "{" not in over:
        return []
    if "max_items" in node_config or graph_config.get("max_map_items") is not None:
        return []
    return [
        LintIssue(
            severity="warning",
            code="W013",
            message=f"Map node '{node_name}' fans out over dynamic expression '{over}' without max_items",
            fix=f"Add 'max_items: <limit>' to node '{node_name}' or 'max_map_items' to config",
        )
    ]


__all__ = [
    "check_cross_references",
    "check_passthrough_nodes",
    "check_tool_call_nodes",
    "check_expression_syntax",
    "check_error_handling",
    "check_edge_types",
    "check_unguarded_cycles",
    "check_skip_if_exists_in_cycle",
    "check_dynamic_map_without_max_items",
]
