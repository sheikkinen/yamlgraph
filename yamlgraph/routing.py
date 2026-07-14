"""Routing utilities for LangGraph edge conditions.

Provides factory functions for creating router functions that determine
which node to route to based on state values and expressions.
"""

import logging
from collections.abc import Callable
from typing import Any

from langgraph.graph import END

from yamlgraph.utils.conditions import evaluate_condition
from yamlgraph.utils.route_log import emit_route

# Type alias for dynamic state
GraphState = dict[str, Any]

logger = logging.getLogger(__name__)


def make_router_fn(targets: list[str], source_node: str) -> Callable[[dict], str]:
    """Create a router function that reads _route from state.

    Used for type: router nodes with conditional edges to multiple targets.

    NOTE: Use `state: dict` not `state: GraphState` - type hints cause
    LangGraph to filter state fields. See docs/debug-router-type-hints.md

    Args:
        targets: List of valid target node names
        source_node: Name of the deciding node (route log attribution, FR-723)

    Returns:
        Router function that returns the target node name
    """

    def router_fn(state: dict) -> str:
        route = state.get("_route")
        logger.debug(f"Router: _route={route}, targets={targets}")
        if route and route in targets:
            logger.debug(f"Router: matched route {route}")
            emit_route(source_node, str(route), route)
            return route
        # Default to first target
        logger.debug(f"Router: defaulting to {targets[0]}")
        emit_route(source_node, "default", targets[0])
        return targets[0]

    return router_fn


def make_expr_router_fn(
    edges: list[tuple[str, str]],
    source_node: str,
    loop_exit_target: str | None = None,
    map_nodes: dict[str, tuple] | None = None,
) -> Callable[[GraphState], Any]:
    """Create router that evaluates expression conditions.

    Used for reflexion-style loops with expression-based conditions
    like "critique.score < 0.8".

    Args:
        edges: List of (condition, target) tuples
        source_node: Name of the source node (for logging)
        loop_exit_target: Target node when loop limit is reached (FR-172)
        map_nodes: Map node tracking dict; when a matched condition's target is a
            map node, the router returns that map's ``Send`` fan-out so per-item
            parallelism and the ``collect`` reducer are preserved (FR-467)

    Returns:
        Router function returning a target node name (str) or, when the matched
        target is a map node, a ``list[Send]`` fan-out.
    """
    map_nodes = map_nodes or {}

    def expr_router_fn(state: GraphState) -> Any:
        # Check loop limit first — a routing decision too (FR-723: the seam
        # the ninchat prototype could not see; loop exhaustion must be
        # visible in route logs).
        if state.get("_loop_limit_reached"):
            if loop_exit_target:
                # FR-630: Normalize "END" string to sentinel
                resolved = END if loop_exit_target == "END" else loop_exit_target
            else:
                resolved = END
            emit_route(source_node, "loop_exit", resolved)
            return resolved

        for condition, target in edges:
            try:
                if evaluate_condition(condition, state):
                    logger.debug(
                        f"Condition '{condition}' matched, routing to {target}"
                    )
                    # FR-467: a map-node target fans out via Send so item
                    # injection and the collect reducer are preserved.
                    if target in map_nodes:
                        map_edge_fn, _ = map_nodes[target]
                        sends = map_edge_fn(state)
                        # R-2: emit map-node name + count, never Send
                        # payloads (they carry state content).
                        fan_out = len(sends) if isinstance(sends, list) else 1
                        emit_route(source_node, condition, target, fan_out=fan_out)
                        return sends
                    emit_route(source_node, condition, target)
                    return target
            except ValueError as e:
                logger.warning(f"Failed to evaluate condition '{condition}': {e}")
        # No condition matched - this shouldn't happen with well-formed graphs
        logger.warning(f"No condition matched for {source_node}, defaulting to END")
        emit_route(source_node, "no_match", END)
        return END

    return expr_router_fn


__all__ = ["make_router_fn", "make_expr_router_fn"]
