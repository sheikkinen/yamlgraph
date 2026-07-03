"""Loop detection utilities for graph compilation.

Detects nodes participating in cycles and auto-applies loop defaults.
Extracted from graph_loader.py to keep module under 450 lines.
"""

import copy
import logging
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)


def detect_loop_nodes(edges: list[dict]) -> set[str]:
    """Detect nodes that participate in cycles (loops).

    Uses DFS with path tracking to find back edges indicating cycles.

    Args:
        edges: List of edge dicts with 'from' and 'to' keys

    Returns:
        Set of node names that are part of at least one cycle
    """
    # Build adjacency list
    graph: dict[str, set[str]] = defaultdict(set)
    all_nodes: set[str] = set()

    for edge in edges:
        from_node = edge.get("from")
        to_nodes = edge.get("to")

        if from_node is None or to_nodes is None:
            continue

        if isinstance(to_nodes, str):
            to_nodes = [to_nodes]

        all_nodes.add(from_node)
        for to_node in to_nodes:
            graph[from_node].add(to_node)
            all_nodes.add(to_node)

    # Find nodes in cycles using DFS with path tracking
    loop_nodes: set[str] = set()
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = dict.fromkeys(all_nodes, WHITE)

    def dfs(node: str, path: list[str]) -> None:
        """DFS that tracks path to detect and extract cycle nodes."""
        color[node] = GRAY
        current_path = path + [node]

        for neighbor in graph.get(node, set()):
            if color[neighbor] == GRAY:
                # Back edge found - extract only the cycle portion
                # Find where neighbor appears in path to get cycle nodes
                try:
                    cycle_start = current_path.index(neighbor)
                    cycle_nodes = current_path[cycle_start:]
                    loop_nodes.update(cycle_nodes)
                except ValueError:
                    # neighbor not in path (shouldn't happen with GRAY check)
                    pass
            elif color[neighbor] == WHITE:
                dfs(neighbor, current_path)

        color[node] = BLACK

    for node in all_nodes:
        if color[node] == WHITE:
            dfs(node, [])

    return loop_nodes


def apply_loop_node_defaults(config: dict[str, Any]) -> dict[str, Any]:
    """Auto-apply skip_if_exists=false to nodes detected in loops.

    This eliminates the common footgun where loop nodes need explicit
    skip_if_exists: false to re-run on each iteration.

    Args:
        config: Raw graph configuration dict

    Returns:
        Modified copy of config with skip_if_exists applied to loop nodes
    """
    result = copy.deepcopy(config)
    edges = result.get("edges", [])
    nodes = result.get("nodes", {})

    loop_nodes = detect_loop_nodes(edges)

    if loop_nodes:
        logger.debug(f"Auto-detected loop nodes: {', '.join(sorted(loop_nodes))}")

    for node_name in loop_nodes:
        # Only set if node exists and not explicitly configured
        if node_name in nodes and "skip_if_exists" not in nodes[node_name]:
            nodes[node_name]["skip_if_exists"] = False

    return result
