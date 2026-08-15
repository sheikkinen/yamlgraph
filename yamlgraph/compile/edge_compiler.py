"""Edge compilation for StateGraph construction.

Classify-then-dispatch (FR-718): `classify_edge` names every edge form
as an explicit EdgeShape; per-shape compilers are registered in
_EDGE_COMPILERS. An unnameable shape raises naming the edge — PLAIN is
a member, never a fall-through claim (Commandment 6).
Extracted from graph_loader.py (FR-067).
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from langgraph.graph import END, StateGraph

from yamlgraph.routing import make_expr_router_fn, make_router_fn

logger = logging.getLogger(__name__)


class EdgeShape(Enum):
    """Every edge form the compiler can name (FR-718)."""

    START = "start"
    PARALLEL_FANOUT = "parallel_fanout"
    MAP_TO_MAP = "map_to_map"
    TO_MAP = "to_map"
    FROM_MAP = "from_map"
    ROUTER_CONDITIONAL = "router_conditional"
    EXPRESSION = "expression"
    PLAIN = "plain"


def _classify_fanout(from_node: str, to_node: list, condition: str | None) -> EdgeShape:
    """Fan-out list without type: conditional (FR-234)."""
    if condition:
        raise ValueError(
            f"Edge '{from_node}' -> {to_node} has a condition on a "
            "parallel fan-out list without type: conditional — the "
            "condition cannot apply to a fan-out. Use type: "
            "conditional with routes, or split into conditional edges."
        )
    return EdgeShape.START if from_node == "START" else EdgeShape.PARALLEL_FANOUT


def _classify_scalar(
    from_node: str,
    to_node: str | list[str],
    condition: str | None,
    edge_type: str | None,
    map_node_names: set[str],
) -> EdgeShape:
    """Non-fan-out forms, in retired-probe-chain order (rules table)."""
    is_to_map = isinstance(to_node, str) and to_node in map_node_names
    rules: list[tuple[bool, EdgeShape]] = [
        (from_node == "START", EdgeShape.START),
        (from_node in map_node_names and is_to_map, EdgeShape.MAP_TO_MAP),
        (condition is None and is_to_map, EdgeShape.TO_MAP),
        (from_node in map_node_names, EdgeShape.FROM_MAP),
        (
            edge_type == "conditional" and isinstance(to_node, list),
            EdgeShape.ROUTER_CONDITIONAL,
        ),
        (bool(condition), EdgeShape.EXPRESSION),
    ]
    for matches, shape in rules:
        if matches:
            return shape
    return EdgeShape.PLAIN


def classify_edge(
    from_node: str,
    to_node: str | list[str],
    condition: str | None,
    edge_type: str | None,
    map_node_names: set[str],
) -> EdgeShape:
    """Name the shape of an edge — pure, exhaustive, order-faithful.

    Order mirrors the retired probe chain exactly: fan-out before START,
    map memberships next (map-to-map is condition-blind, to-map is not —
    FR-467), router before expression, PLAIN last and explicit.

    Raises:
        ValueError: for the one unnameable form — a fan-out list with a
        condition but no ``type: conditional``; the old chain compiled
        it with the condition SILENTLY DROPPED.
    """
    if isinstance(to_node, list) and edge_type != "conditional":
        return _classify_fanout(from_node, to_node, condition)
    return _classify_scalar(from_node, to_node, condition, edge_type, map_node_names)


@dataclass
class _EdgeContext:
    """Everything a per-shape compiler may touch."""

    graph: StateGraph
    from_node: str
    to_node: Any
    condition: str | None
    map_nodes: dict[str, tuple]
    router_edges: dict[str, list]
    expression_edges: dict[str, list[tuple[str, str]]]
    interrupt_nodes: set[str] | None = None
    subgraph_interrupt_nodes: set[str] | None = None
    map_fanout_sources: set[str] | None = field(default=None)


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


def build_router_route_mapping(
    target_nodes: list[str],
    interrupt_nodes: set[str] | None = None,
    subgraph_interrupt_nodes: set[str] | None = None,
) -> dict[str, str]:
    """Pure route mapping for router edges (FR-718 extraction).

    FR-211: interrupt targets redirect to *_prepare, subgraph interrupts
    to *__run; original names stay as route labels for make_router_fn.
    """
    route_mapping: dict[str, str] = {}
    for target in target_nodes:
        if interrupt_nodes and target in interrupt_nodes:
            route_mapping[target] = f"{target}_prepare"
        elif subgraph_interrupt_nodes and target in subgraph_interrupt_nodes:
            route_mapping[target] = f"{target}__run"
        else:
            route_mapping[target] = target
    return route_mapping


def build_expression_route_mapping(
    expr_edges: list[tuple[str, str]],
    loop_exit_target: Any,
    map_nodes: dict[str, tuple],
) -> dict[Any, Any]:
    """Pure route mapping for expression edges (FR-718 extraction).

    END is always reachable; a map-node target routes to its sub-node
    (Send fan-out, FR-467), so the path_map lists the sub-node.
    """
    targets = {target for _, target in expr_edges}
    targets.add(END)
    if loop_exit_target:
        targets.add(loop_exit_target)
    route_mapping: dict[Any, Any] = {}
    for t in targets:
        if t in map_nodes:
            _, sub_node_name = map_nodes[t]
            route_mapping[sub_node_name] = sub_node_name
        else:
            route_mapping[t] = t
    return route_mapping


def _compile_start(ctx: _EdgeContext) -> None:
    to = ctx.to_node
    if isinstance(to, list):
        # Redirect interrupt targets before passing to start handler
        to = [
            f"{t}_prepare" if ctx.interrupt_nodes and t in ctx.interrupt_nodes else t
            for t in to
        ]
        # FR-797: relay-capable subgraph targets enter at their run node
        sgi = ctx.subgraph_interrupt_nodes
        to = [f"{t}__run" if sgi and t in sgi else t for t in to]
    _handle_start_edge(ctx.graph, to, ctx.map_nodes)


def _compile_parallel_fanout(ctx: _EdgeContext) -> None:
    _add_parallel_fanout_edges(
        ctx.graph,
        ctx.from_node,
        ctx.to_node,
        ctx.map_nodes,
        ctx.interrupt_nodes,
        ctx.subgraph_interrupt_nodes,
    )


def _compile_map_to_map(ctx: _EdgeContext) -> None:
    _, from_sub = ctx.map_nodes[ctx.from_node]
    to_map_edge_fn, to_sub = ctx.map_nodes[ctx.to_node]
    ctx.graph.add_conditional_edges(from_sub, to_map_edge_fn, [to_sub])


def _compile_to_map(ctx: _EdgeContext) -> None:
    map_edge_fn, sub_node_name = ctx.map_nodes[ctx.to_node]
    ctx.graph.add_conditional_edges(ctx.from_node, map_edge_fn, [sub_node_name])
    if ctx.map_fanout_sources is not None:
        ctx.map_fanout_sources.add(ctx.from_node)


def _compile_from_map(ctx: _EdgeContext) -> None:
    _, sub_node_name = ctx.map_nodes[ctx.from_node]
    target = END if ctx.to_node == "END" else ctx.to_node
    ctx.graph.add_edge(sub_node_name, target)


def _compile_router_conditional(ctx: _EdgeContext) -> None:
    ctx.router_edges[ctx.from_node] = ctx.to_node


def _compile_expression(ctx: _EdgeContext) -> None:
    # FR-467: keep the map node *name* as the target; it is resolved to the
    # map sub-node (and Send fan-out) inside the single expression router.
    ctx.expression_edges.setdefault(ctx.from_node, []).append(
        (ctx.condition, END if ctx.to_node == "END" else ctx.to_node)
    )


def _compile_plain(ctx: _EdgeContext) -> None:
    ctx.graph.add_edge(ctx.from_node, END if ctx.to_node == "END" else ctx.to_node)


_EDGE_COMPILERS = {
    EdgeShape.START: _compile_start,
    EdgeShape.PARALLEL_FANOUT: _compile_parallel_fanout,
    EdgeShape.MAP_TO_MAP: _compile_map_to_map,
    EdgeShape.TO_MAP: _compile_to_map,
    EdgeShape.FROM_MAP: _compile_from_map,
    EdgeShape.ROUTER_CONDITIONAL: _compile_router_conditional,
    EdgeShape.EXPRESSION: _compile_expression,
    EdgeShape.PLAIN: _compile_plain,
}


def _process_edge(
    edge: dict[str, Any],
    graph: StateGraph,
    map_nodes: dict[str, tuple],
    router_edges: dict[str, list],
    expression_edges: dict[str, list[tuple[str, str]]],
    interrupt_nodes: set[str] | None = None,
    map_fanout_sources: set[str] | None = None,
    subgraph_interrupt_nodes: set[str] | None = None,
) -> None:
    """Classify one edge, then dispatch to its shape compiler (FR-718)."""
    from_node = edge["from"]
    to_node = edge["to"]
    condition = edge.get("condition")
    edge_type = edge.get("type")

    # FR-797: relay-capable subgraph rewrite happens BEFORE all edge-shape
    # dispatch (J-15); outgoing edges may be fully handled there.
    if subgraph_interrupt_nodes:
        from yamlgraph.compile.subgraph_relay import relay_rewrite

        handled, to_node = relay_rewrite(
            graph, from_node, to_node, condition, edge_type, subgraph_interrupt_nodes
        )
        if handled:
            return

    # FR-060: Redirect incoming edges to interrupt prepare node (before
    # membership classification — a *_prepare name is never a map node).
    if interrupt_nodes and isinstance(to_node, str) and to_node in interrupt_nodes:
        to_node = f"{to_node}_prepare"

    shape = classify_edge(
        from_node, to_node, condition, edge_type, set(map_nodes.keys())
    )
    _EDGE_COMPILERS[shape](
        _EdgeContext(
            graph=graph,
            from_node=from_node,
            to_node=to_node,
            condition=condition,
            map_nodes=map_nodes,
            router_edges=router_edges,
            expression_edges=expression_edges,
            interrupt_nodes=interrupt_nodes,
            subgraph_interrupt_nodes=subgraph_interrupt_nodes,
            map_fanout_sources=map_fanout_sources,
        )
    )


def _add_parallel_fanout_edges(
    graph: StateGraph,
    from_node: str,
    targets: list[str],
    map_nodes: dict[str, tuple],
    interrupt_nodes: set[str] | None = None,
    subgraph_interrupt_nodes: set[str] | None = None,
) -> None:
    """Add parallel fan-out edges from one source to multiple targets (FR-234).

    Each target gets its own edge. LangGraph executes them concurrently.
    Handles interrupt node redirects and map node targets.
    """
    for target in targets:
        # FR-060: Redirect interrupt targets to prepare node
        if interrupt_nodes and target in interrupt_nodes:
            target = f"{target}_prepare"

        # FR-797: Redirect relay-capable subgraph targets to run node
        if subgraph_interrupt_nodes and target in subgraph_interrupt_nodes:
            target = f"{target}__run"

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
    map_nodes: dict[str, tuple] | None = None,
    map_fanout_sources: set[str] | None = None,
) -> None:
    """Add router and expression conditional edges to graph.

    Args:
        graph: StateGraph to add edges to
        router_edges: Router-style conditional edges
        expression_edges: Expression-based conditional edges
        loop_exits: Map of node name to exit target when loop limit reached (FR-172)
        interrupt_nodes: Interrupt node names needing *_prepare redirect (FR-211)
        subgraph_interrupt_nodes: Subgraph interrupt names needing *__run redirect
        map_nodes: Map node tracking dict; conditional edges whose target is a map
            node route through the map's Send fan-out (FR-467)
        map_fanout_sources: Sources that registered an unconditional map fan-out
            router; used to reject dual-router nodes (FR-467 guard)
    """
    map_nodes = map_nodes or {}

    # FR-467 guard: a source must not carry both an unconditional map fan-out
    # router and an expression router — LangGraph would fan out to both every
    # superstep, making conditions ineffective (silent infinite loop).
    if map_fanout_sources:
        clash = map_fanout_sources & set(expression_edges)
        if clash:
            node = sorted(clash)[0]
            raise ValueError(
                f"Node '{node}' has both an unconditional edge to a map node and "
                "conditional edge(s). LangGraph would run both routers every "
                "superstep, so the condition would never take effect. Make all "
                f"edges out of '{node}' conditional, or remove the conditional "
                "edges."
            )

    # Add router conditional edges
    for source_node, target_nodes in router_edges.items():
        graph.add_conditional_edges(
            source_node,
            make_router_fn(target_nodes, source_node),
            build_router_route_mapping(
                target_nodes, interrupt_nodes, subgraph_interrupt_nodes
            ),
        )

    # Add expression-based conditional edges
    for source_node, expr_edges in expression_edges.items():
        loop_exit_target = (loop_exits or {}).get(source_node)
        # FR-630: Normalize YAML string "END" to LangGraph sentinel
        if loop_exit_target == "END":
            loop_exit_target = END
        graph.add_conditional_edges(
            source_node,
            make_expr_router_fn(
                expr_edges, source_node, loop_exit_target, map_nodes=map_nodes
            ),
            build_expression_route_mapping(expr_edges, loop_exit_target, map_nodes),
        )


__all__ = [
    "EdgeShape",
    "classify_edge",
    "build_router_route_mapping",
    "build_expression_route_mapping",
    "_process_edge",
    "_add_conditional_edges",
]
