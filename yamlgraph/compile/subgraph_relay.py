"""FR-797 relay-capable subgraph compilation: the two-node interrupt split.

``{name}__run`` invokes/resumes the child and RETURNS normally, committing
mapped interrupt state plus relay internals to the parent checkpoint;
``{name}__pause`` then performs the parent-native ``interrupt(payload)``.
Commit-before-pause — the FR-060 model applied to subgraph nodes.
"""

import logging
from typing import TYPE_CHECKING, Any

from langgraph.graph import END, StateGraph

from yamlgraph.compile.node_otel import _maybe_wrap_otel
from yamlgraph.models.graph_schema import NodeType
from yamlgraph.node_factory import create_subgraph_node

if TYPE_CHECKING:
    from yamlgraph.compile.node_compiler import NodeCompileContext

logger = logging.getLogger(__name__)


def compile_subgraph_node(ctx: "NodeCompileContext") -> tuple[str, Any] | None:
    """Compile handler for subgraph nodes (single node or relay pair)."""
    if not ctx.config.source_path:
        raise ValueError(
            f"Cannot resolve subgraph path for node '{ctx.node_name}': "
            "parent graph has no source_path"
        )
    node_fn = create_subgraph_node(
        ctx.node_name,
        ctx.node_config,
        parent_graph_path=ctx.config.source_path,
    )
    if isinstance(node_fn, tuple):
        return _register_relay_pair(ctx, *node_fn)
    node_fn = _maybe_wrap_otel(node_fn, ctx.node_name, NodeType.SUBGRAPH)
    ctx.graph.add_node(ctx.node_name, node_fn, cache_policy=ctx.cache_policy)
    return None


def _register_relay_pair(
    ctx: "NodeCompileContext", run_fn: Any, pause_fn: Any
) -> tuple[str, str]:
    """Register {name}__run + {name}__pause with the loop-back edge."""
    run_name = f"{ctx.node_name}__run"
    pause_name = f"{ctx.node_name}__pause"
    run_fn = _maybe_wrap_otel(run_fn, run_name, NodeType.SUBGRAPH)
    ctx.graph.add_node(run_name, run_fn, cache_policy=ctx.cache_policy)
    ctx.graph.add_node(pause_name, pause_fn)
    # Loop-back: after the pause resumes, re-enter the run node.
    ctx.graph.add_edge(pause_name, run_name)
    return (ctx.node_name, "subgraph_interrupt")


def relay_rewrite(
    graph: StateGraph,
    from_node: str,
    to_node: Any,
    condition: str | None,
    edge_type: str | None,
    sgi: set[str],
) -> tuple[bool, Any]:
    """FR-797 relay edge rewrite: (handled, possibly-redirected to_node).

    Outgoing edges from relay nodes are compiled here in full (Phase-1:
    simple scalar targets only); incoming edges are redirected to the
    ``{name}__run`` entry node.
    """
    if from_node in sgi:
        if condition or edge_type == "conditional" or isinstance(to_node, list):
            raise ValueError(
                f"Edge from relay-capable subgraph node {from_node!r} must be "
                "a simple edge to one target: conditional edges and fan-out "
                "lists from interrupt-relaying subgraph nodes are not "
                "supported (FR-797 Phase-1). Route conditions from a "
                "downstream node instead."
            )
        _add_relay_outgoing_edges(graph, from_node, to_node)
        return True, to_node
    if isinstance(to_node, str) and to_node in sgi:
        return False, f"{to_node}__run"
    return False, to_node


def _add_relay_outgoing_edges(graph: StateGraph, node_name: str, to_node: str) -> None:
    """FR-797: route {name}__run → {name}__pause when paused, else onward."""
    run_name = f"{node_name}__run"
    pause_name = f"{node_name}__pause"
    target = END if to_node == "END" else to_node
    paused_key = f"__{node_name}_paused__"

    def _relay_router(state: dict) -> str:
        return pause_name if state.get(paused_key) else to_node

    _relay_router.__name__ = f"{node_name}__relay_route"
    graph.add_conditional_edges(
        run_name, _relay_router, {pause_name: pause_name, to_node: target}
    )
