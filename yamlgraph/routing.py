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
) -> Callable[[GraphState], Any]:
    """Create router that evaluates expression conditions.

    Used for reflexion-style loops with expression-based conditions
    like "critique.score < 0.8".

    Args:
        edges: List of (condition, target) tuples
        source_node: Name of the source node (for logging)
        loop_exit_target: Target node when loop limit is reached (FR-172)

    Returns:
        Router function returning a target node name. A map target is its
        dispatch node (FR-1073), which fans out itself.
    """

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
