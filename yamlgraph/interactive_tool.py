"""Interactive tool config-level expansion (FR-049).

Expands `type: interactive_tool` nodes into inline nodes + edges
BEFORE compile_nodes() runs. The expanded nodes use existing factories
(create_python_node, create_interrupt_node) — no new factory needed.

Constraint 8: expansion happens as a GraphConfig pre-processing step.
"""

from __future__ import annotations

import copy
import logging
from typing import Any

from yamlgraph.utils.conditions import negate_condition

logger = logging.getLogger(__name__)


def expand_interactive_tools(config: dict[str, Any]) -> dict[str, Any]:
    """Expand all interactive_tool nodes into inline nodes + edges.

    Transforms the config dict in-place (on a deep copy):
    - Replaces each interactive_tool node with 3-4 expanded entries
    - Rewrites incoming edges → {prefix}__start
    - Rewrites outgoing edges → {prefix}__end or {prefix}__step
    - Adds internal edges between expanded nodes

    Args:
        config: Raw graph configuration dict

    Returns:
        Modified copy of config with interactive_tool nodes expanded
    """
    nodes = config.get("nodes", {})

    # Find interactive_tool nodes
    interactive_nodes = {
        name: cfg
        for name, cfg in nodes.items()
        if cfg.get("type") == "interactive_tool"
    }

    if not interactive_nodes:
        return config

    result = copy.deepcopy(config)
    result_nodes = result["nodes"]
    result_edges = result["edges"]

    for node_name, node_config in interactive_nodes.items():
        _expand_single(node_name, node_config, result_nodes, result_edges)

    return result


def _expand_single(
    name: str,
    config: dict[str, Any],
    nodes: dict[str, Any],
    edges: list[dict[str, Any]],
) -> None:
    """Expand a single interactive_tool node into inline nodes + edges.

    Modifies nodes dict and edges list in place.

    Args:
        name: Original node name (becomes prefix)
        config: Interactive tool node configuration
        nodes: Mutable nodes dict
        edges: Mutable edges list
    """
    start_tool = config["start"]
    step_tool = config["step"]
    end_tool = config.get("end")
    resume_key = config["resume_key"]
    response_key = config["response_key"]
    loop_until = config["loop_until"]
    max_iterations = config.get("max_iterations", 10)
    on_error = config.get("on_error")

    # Remove original node
    del nodes[name]

    # 1. Start node — calls start tool (type: python)
    start_name = f"{name}__start"
    start_cfg: dict[str, Any] = {"type": "python", "tool": start_tool}
    if on_error:
        start_cfg["on_error"] = on_error
    nodes[start_name] = start_cfg

    # 2. Ask node — interrupt for user input (type: interrupt)
    ask_name = f"{name}__ask"
    nodes[ask_name] = {
        "type": "interrupt",
        "message": "{" + response_key + "}",
        "resume_key": resume_key,
        "idempotent": False,  # Constraint 10: regenerate each iteration
    }

    # 3. Step node — calls step tool (type: python)
    step_name = f"{name}__step"
    step_cfg: dict[str, Any] = {
        "type": "python",
        "tool": step_tool,
        "loop_limit": max_iterations,
    }
    if on_error:
        step_cfg["on_error"] = on_error
    nodes[step_name] = step_cfg

    # 4. End node — calls end tool if provided (type: python)
    end_name = f"{name}__end" if end_tool else None
    if end_tool:
        end_cfg: dict[str, Any] = {"type": "python", "tool": end_tool}
        if on_error:
            end_cfg["on_error"] = on_error
        nodes[end_name] = end_cfg

    # Exit target for outgoing edge rewriting
    exit_node = end_name or step_name  # Last node in expansion

    new_edges: list[dict[str, Any]] = []
    for edge in edges:
        if edge["to"] == name:
            # Incoming edge → redirect to __start
            new_edge = dict(edge)
            new_edge["to"] = start_name
            new_edges.append(new_edge)
        elif edge["from"] == name:
            # Outgoing edge → redirect from exit node
            new_edge = dict(edge)
            new_edge["from"] = exit_node
            if not end_tool:
                # No end tool: outgoing edge gets loop_until condition
                new_edge["condition"] = loop_until
            new_edges.append(new_edge)
        else:
            new_edges.append(edge)

    # Add internal edges
    # start → ask (Constraint 9: always, no error branching)
    new_edges.append({"from": start_name, "to": ask_name})

    # ask → step
    new_edges.append({"from": ask_name, "to": step_name})

    if end_tool:
        # step → ask (loop back, negated condition)
        new_edges.append(
            {
                "from": step_name,
                "to": ask_name,
                "condition": negate_condition(loop_until),
            }
        )
        # step → end (exit condition)
        new_edges.append(
            {
                "from": step_name,
                "to": end_name,
                "condition": loop_until,
            }
        )
    else:
        # step → ask (loop back, negated condition)
        new_edges.append(
            {
                "from": step_name,
                "to": ask_name,
                "condition": negate_condition(loop_until),
            }
        )
        # step → next (exit) is already handled by the rewritten outgoing edge above

    # Replace edges in place
    edges.clear()
    edges.extend(new_edges)

    logger.info(
        f"Expanded interactive_tool '{name}' into "
        f"{3 + (1 if end_tool else 0)} nodes"
    )
