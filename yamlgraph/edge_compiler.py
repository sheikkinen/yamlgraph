"""Edge compilation for StateGraph construction.

Handles START edges, map node edges, conditional/router edges,
parallel fan-out edges, and expression-based routing.
Extracted from graph_loader.py (FR-067).
"""

import logging
from typing import Any

from langgraph.graph import END, StateGraph

from yamlgraph.routing import make_expr_router_fn, make_router_fn

logger = logging.getLogger(__name__)


def _handle_start_edge(
    graph: StateGraph,
    to_node: str | list[str],
    map_nodes: dict[str, tuple],
) -> None:
    """Handle START -> node edge (single or fan-out)."""
    if isinstance(to_node, list):
        # FR-234: START -> [a, b, c] parallel fan-out
        _handle_start_fanout(graph, to_node, map_nodes)
        return
    if to_node in map_nodes:
        map_edge_fn, sub_node_name = map_nodes[to_node]
        graph.set_conditional_entry_point(map_edge_fn, [sub_node_name])
    else:
        graph.set_entry_point(to_node)


def _handle_start_fanout(
    graph: StateGraph, targets: list[str], map_nodes: dict[str, tuple]
) -> None:
    """Handle START -> [a, b, c] parallel fan-out.

    LangGraph requires exactly one entry point, so we use a conditional
    entry point that returns all targets via a routing function.
    """
    resolved: list[str] = []
    for target in targets:
        if target in map_nodes:
            _, sub_node_name = map_nodes[target]
            resolved.append(sub_node_name)
        else:
            resolved.append(target)

    def _fanout_entry(state: dict) -> list[str]:
        return resolved

    graph.set_conditional_entry_point(_fanout_entry, resolved)


def _handle_map_to_map_edge(
    graph: StateGraph, from_node: str, to_node: str, map_nodes: dict[str, tuple]
) -> bool:
    """Handle map_node -> map_node edge. Returns True if handled."""
    if from_node in map_nodes and to_node in map_nodes:
        _, from_sub = map_nodes[from_node]
        to_map_edge_fn, to_sub = map_nodes[to_node]
        graph.add_conditional_edges(from_sub, to_map_edge_fn, [to_sub])
        return True
    return False


def _handle_to_map_edge(
    graph: StateGraph, from_node: str, to_node: str, map_nodes: dict[str, tuple]
) -> bool:
    """Handle regular -> map_node edge. Returns True if handled."""
    if isinstance(to_node, str) and to_node in map_nodes:
        map_edge_fn, sub_node_name = map_nodes[to_node]
        graph.add_conditional_edges(from_node, map_edge_fn, [sub_node_name])
        return True
    return False


def _handle_from_map_edge(
    graph: StateGraph, from_node: str, to_node: str, map_nodes: dict[str, tuple]
) -> bool:
    """Handle map_node -> regular edge (fan-in). Returns True if handled."""
    if from_node in map_nodes:
        _, sub_node_name = map_nodes[from_node]
        target = END if to_node == "END" else to_node
        graph.add_edge(sub_node_name, target)
        return True
    return False


def _process_edge(
    edge: dict[str, Any],
    graph: StateGraph,
    map_nodes: dict[str, tuple],
    router_edges: dict[str, list],
    expression_edges: dict[str, list[tuple[str, str]]],
    interrupt_nodes: set[str] | None = None,
) -> None:
    """Process a single edge and add to graph or edge tracking dicts.

    Args:
        edge: Edge configuration dict
        graph: StateGraph to add edges to
        map_nodes: Map node tracking dict
        router_edges: Dict to collect router edges
        expression_edges: Dict to collect expression-based edges
        interrupt_nodes: Set of interrupt node names with prepare split
    """
    from_node = edge["from"]
    to_node = edge["to"]
    condition = edge.get("condition")
    edge_type = edge.get("type")

    # FR-234: Parallel fan-out — to: [a, b, c] without type: conditional
    if isinstance(to_node, list) and edge_type != "conditional":
        if from_node == "START":
            # Redirect interrupt targets before passing to start handler
            resolved = [
                f"{t}_prepare" if interrupt_nodes and t in interrupt_nodes else t
                for t in to_node
            ]
            _handle_start_edge(graph, resolved, map_nodes)
        else:
            _add_parallel_fanout_edges(
                graph, from_node, to_node, map_nodes, interrupt_nodes
            )
        return

    # FR-060: Redirect incoming edges to interrupt prepare node
    if interrupt_nodes and isinstance(to_node, str) and to_node in interrupt_nodes:
        to_node = f"{to_node}_prepare"

    # Handle START edge
    if from_node == "START":
        _handle_start_edge(graph, to_node, map_nodes)
        return

    # Handle map node edges (delegate to handlers that return True if handled)
    if _handle_map_to_map_edge(graph, from_node, to_node, map_nodes):
        return
    if _handle_to_map_edge(graph, from_node, to_node, map_nodes):
        return
    if _handle_from_map_edge(graph, from_node, to_node, map_nodes):
        return

    # Handle conditional/expression edges (collect for later processing)
    if edge_type == "conditional" and isinstance(to_node, list):
        router_edges[from_node] = to_node
        return

    if condition:
        expression_edges.setdefault(from_node, []).append(
            (condition, END if to_node == "END" else to_node)
        )
        return

    # Simple edge
    graph.add_edge(from_node, END if to_node == "END" else to_node)


def _add_parallel_fanout_edges(
    graph: StateGraph,
    from_node: str,
    targets: list[str],
    map_nodes: dict[str, tuple],
    interrupt_nodes: set[str] | None = None,
) -> None:
    """Add parallel fan-out edges from one source to multiple targets (FR-234).

    Each target gets its own edge. LangGraph executes them concurrently.
    Handles interrupt node redirects and map node targets.
    """
    for target in targets:
        # FR-060: Redirect interrupt targets to prepare node
        if interrupt_nodes and target in interrupt_nodes:
            target = f"{target}_prepare"

        # Map node targets use conditional edge with map function
        if target in map_nodes:
            map_edge_fn, sub_node_name = map_nodes[target]
            graph.add_conditional_edges(from_node, map_edge_fn, [sub_node_name])
            continue

        resolved = END if target == "END" else target
        graph.add_edge(from_node, resolved)


def _add_conditional_edges(
    graph: StateGraph,
    router_edges: dict[str, list],
    expression_edges: dict[str, list[tuple[str, str]]],
    loop_exits: dict[str, str] | None = None,
    interrupt_nodes: set[str] | None = None,
    subgraph_interrupt_nodes: set[str] | None = None,
) -> None:
    """Add router and expression conditional edges to graph.

    Args:
        graph: StateGraph to add edges to
        router_edges: Router-style conditional edges
        expression_edges: Expression-based conditional edges
        loop_exits: Map of node name to exit target when loop limit reached (FR-172)
        interrupt_nodes: Interrupt node names needing *_prepare redirect (FR-211)
        subgraph_interrupt_nodes: Subgraph interrupt names needing *__run redirect
    """
    # Add router conditional edges
    for source_node, target_nodes in router_edges.items():
        # FR-211: Redirect interrupt targets in route mapping while keeping
        # original names as route labels for make_router_fn matching
        route_mapping = {}
        for target in target_nodes:
            if interrupt_nodes and target in interrupt_nodes:
                route_mapping[target] = f"{target}_prepare"
            elif subgraph_interrupt_nodes and target in subgraph_interrupt_nodes:
                route_mapping[target] = f"{target}__run"
            else:
                route_mapping[target] = target
        graph.add_conditional_edges(
            source_node,
            make_router_fn(target_nodes),
            route_mapping,
        )

    # Add expression-based conditional edges
    for source_node, expr_edges in expression_edges.items():
        loop_exit_target = (loop_exits or {}).get(source_node)
        targets = {target for _, target in expr_edges}
        targets.add(END)  # Always include END as fallback
        if loop_exit_target:
            targets.add(loop_exit_target)
        route_mapping = {t: (END if t == END else t) for t in targets}
        graph.add_conditional_edges(
            source_node,
            make_expr_router_fn(expr_edges, source_node, loop_exit_target),
            route_mapping,
        )


__all__ = ["_process_edge", "_add_conditional_edges"]
