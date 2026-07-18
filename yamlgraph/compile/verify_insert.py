"""Compile-time graph-level verify block insertion (FR-677).

Rewrites a graph config carrying a top-level ``verify:`` list so a terminal
``__verify__`` node runs once before END. Every explicit ``END`` destination
(scalar edges, list fan-out/router edges, loop_exits) is redirected through the
verify node, then a single ``__verify__ -> END`` edge is appended.

Follows the expand_pipeline_templates() rewrite pattern from FR-235.
"""

from __future__ import annotations

import copy
from typing import Any

VERIFY_NODE_NAME = "__verify__"


def _redirect(value: Any) -> Any:
    """Redirect an edge destination away from END to the verify node."""
    if value == "END":
        return VERIFY_NODE_NAME
    if isinstance(value, list):
        return [VERIFY_NODE_NAME if v == "END" else v for v in value]
    return value


def insert_verify_node(config: dict[str, Any]) -> dict[str, Any]:
    """Insert a terminal ``__verify__`` node when ``verify:`` rules are present.

    Args:
        config: Parsed graph configuration dict.

    Returns:
        The config, rewritten in place when ``verify:`` is non-empty; otherwise
        returned unchanged.
    """
    rules = config.get("verify")
    if not rules:
        return config

    config = copy.deepcopy(config)

    nodes = config.setdefault("nodes", {})
    if VERIFY_NODE_NAME in nodes:
        raise ValueError(
            f"Node name '{VERIFY_NODE_NAME}' is reserved for graph-level verify"
        )
    nodes[VERIFY_NODE_NAME] = {"type": "verify"}

    # Redirect explicit END destinations in edges through the verify node.
    for edge in config.get("edges", []):
        if "to" in edge:
            edge["to"] = _redirect(edge["to"])

    # Redirect router destinations (routes map + default_route) that name END,
    # since the router stores the resolved target node in state._route.
    for node in nodes.values():
        if not isinstance(node, dict):
            continue
        routes = node.get("routes")
        if isinstance(routes, dict):
            for key, target in list(routes.items()):
                routes[key] = _redirect(target)
        if node.get("default_route") == "END":
            node["default_route"] = VERIFY_NODE_NAME

    # Redirect loop_exits that terminate at END.
    loop_exits = config.get("loop_exits")
    if isinstance(loop_exits, dict):
        for key, target in list(loop_exits.items()):
            loop_exits[key] = _redirect(target)

    # Terminate the verify node at END.
    config.setdefault("edges", []).append({"from": VERIFY_NODE_NAME, "to": "END"})

    return config
