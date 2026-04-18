"""Node Compiler - Compile YAML node configs to LangGraph nodes.

Extracted from graph_loader.py to keep modules under 400 lines.
Uses a registry pattern (FR-220) to dispatch node types to handlers.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from langgraph.graph import StateGraph

from yamlgraph.constants import NodeType
from yamlgraph.map_compiler import compile_map_node
from yamlgraph.node_factory import (
    create_copilot_node,
    create_interrupt_node,
    create_node_function,
    create_passthrough_node,
    create_race_node,
    create_subgraph_node,
    create_tool_call_node,
)
from yamlgraph.tools.agent import create_agent_node
from yamlgraph.tools.nodes import create_tool_node
from yamlgraph.tools.python_tool import create_python_node

if TYPE_CHECKING:
    from yamlgraph.graph_loader import GraphConfig

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Context passed to node type handlers (FR-220)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NodeCompileContext:
    """All context needed to compile a single node."""

    node_name: str
    node_config: dict[str, Any]
    graph: StateGraph
    config: "GraphConfig"
    tools: dict[str, Any]
    python_tools: dict[str, Any]
    callable_registry: dict[str, Callable]
    effective_defaults: dict[str, Any]
    prompts_dir: Path | None
    prompts_relative: bool


# ---------------------------------------------------------------------------
# Node type handlers — one per node type
# ---------------------------------------------------------------------------

NodeTypeHandler = Callable[[NodeCompileContext], tuple[str, Any] | None]


def _compile_tool_node(ctx: NodeCompileContext) -> None:
    node_fn = create_tool_node(ctx.node_name, ctx.node_config, ctx.tools)
    ctx.graph.add_node(ctx.node_name, node_fn)
    return None


def _compile_python_node(ctx: NodeCompileContext) -> None:
    node_fn = create_python_node(ctx.node_name, ctx.node_config, ctx.python_tools)
    ctx.graph.add_node(ctx.node_name, node_fn)
    return None


def _compile_agent_node(ctx: NodeCompileContext) -> None:
    node_fn = create_agent_node(
        ctx.node_name,
        ctx.node_config,
        ctx.tools,
        ctx.python_tools,
        defaults=ctx.effective_defaults,
        graph_path=ctx.config.source_path,
    )
    ctx.graph.add_node(ctx.node_name, node_fn)
    return None


def _compile_map_node(ctx: NodeCompileContext) -> tuple[str, Any]:
    map_edge_fn, sub_node_name = compile_map_node(
        ctx.node_name,
        ctx.node_config,
        ctx.graph,
        ctx.effective_defaults,
        ctx.callable_registry,
        graph_path=ctx.config.source_path,
        python_tools=ctx.python_tools,
        tools=ctx.tools,
    )
    return (ctx.node_name, (map_edge_fn, sub_node_name))


def _compile_tool_call_node(ctx: NodeCompileContext) -> None:
    node_fn = create_tool_call_node(
        ctx.node_name, ctx.node_config, ctx.callable_registry
    )
    ctx.graph.add_node(ctx.node_name, node_fn)
    return None


def _compile_interrupt_node(ctx: NodeCompileContext) -> tuple[str, Any]:
    """FR-060: Two-node split — prepare commits state, interrupt pauses."""
    prepare_fn, interrupt_fn = create_interrupt_node(
        ctx.node_name,
        ctx.node_config,
        graph_path=ctx.config.source_path,
        prompts_dir=ctx.prompts_dir,
        prompts_relative=ctx.prompts_relative,
    )
    prepare_name = f"{ctx.node_name}_prepare"
    ctx.graph.add_node(prepare_name, prepare_fn)
    ctx.graph.add_node(ctx.node_name, interrupt_fn)
    ctx.graph.add_edge(prepare_name, ctx.node_name)
    return (ctx.node_name, "interrupt_prepare")


def _compile_passthrough_node(ctx: NodeCompileContext) -> None:
    node_fn = create_passthrough_node(ctx.node_name, ctx.node_config)
    ctx.graph.add_node(ctx.node_name, node_fn)
    return None


def _compile_copilot_node(ctx: NodeCompileContext) -> None:
    node_fn = create_copilot_node(
        ctx.node_name,
        ctx.node_config,
        graph_path=ctx.config.source_path,
        prompts_dir=ctx.prompts_dir,
        prompts_relative=ctx.prompts_relative,
    )
    ctx.graph.add_node(ctx.node_name, node_fn)
    return None


def _compile_subgraph_node(ctx: NodeCompileContext) -> None:
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
    ctx.graph.add_node(ctx.node_name, node_fn)
    return None


def _compile_llm_node(ctx: NodeCompileContext) -> None:
    node_fn = create_node_function(
        ctx.node_name,
        ctx.node_config,
        ctx.effective_defaults,
        graph_path=ctx.config.source_path,
    )
    ctx.graph.add_node(ctx.node_name, node_fn)
    return None


def _compile_race_node(ctx: NodeCompileContext) -> None:
    node_fn = create_race_node(
        ctx.node_name,
        ctx.node_config,
        ctx.effective_defaults,
        graph_path=ctx.config.source_path,
    )
    ctx.graph.add_node(ctx.node_name, node_fn)
    return None


# ---------------------------------------------------------------------------
# Registry: NodeType → handler (FR-220)
# ---------------------------------------------------------------------------

NODE_TYPE_HANDLERS: dict[str, NodeTypeHandler] = {
    NodeType.TOOL: _compile_tool_node,
    NodeType.PYTHON: _compile_python_node,
    NodeType.AGENT: _compile_agent_node,
    NodeType.MAP: _compile_map_node,
    NodeType.TOOL_CALL: _compile_tool_call_node,
    NodeType.INTERRUPT: _compile_interrupt_node,
    NodeType.PASSTHROUGH: _compile_passthrough_node,
    NodeType.COPILOT: _compile_copilot_node,
    NodeType.SUBGRAPH: _compile_subgraph_node,
    NodeType.LLM: _compile_llm_node,
    NodeType.ROUTER: _compile_llm_node,
    NodeType.RACE: _compile_race_node,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compile_node(
    node_name: str,
    node_config: dict[str, Any],
    graph: StateGraph,
    config: "GraphConfig",
    tools: dict[str, Any],
    python_tools: dict[str, Any],
    callable_registry: dict[str, Callable],
) -> tuple[str, Any] | None:
    """Compile a single node and add to graph.

    Args:
        node_name: Name of the node
        node_config: Node configuration dict
        graph: StateGraph to add node to
        config: Full graph config for defaults
        tools: Shell tools registry
        python_tools: Python tools registry
        callable_registry: Loaded callable functions for tool_call nodes

    Returns:
        Tuple of (node_name, metadata) for map/interrupt nodes, None otherwise.

    Raises:
        ValueError: If node type is not registered in NODE_TYPE_HANDLERS.
    """
    # Enrich config with loop_limit if specified
    enriched_config = dict(node_config)
    if node_name in config.loop_limits:
        enriched_config["loop_limit"] = config.loop_limits[node_name]

    # Build prompts path config
    prompts_relative = config.prompts_relative
    prompts_dir = config.prompts_dir
    if prompts_dir:
        prompts_dir = Path(prompts_dir)

    # Build effective defaults with prompts settings merged
    effective_defaults = dict(config.defaults)
    effective_defaults["prompts_relative"] = prompts_relative
    if prompts_dir:
        effective_defaults["prompts_dir"] = str(prompts_dir)

    # Dispatch via registry (FR-220)
    node_type = node_config.get("type", NodeType.LLM)
    handler = NODE_TYPE_HANDLERS.get(node_type)
    if handler is None:
        raise ValueError(
            f"Unknown node type: {node_type!r}. "
            f"Registered types: {sorted(NODE_TYPE_HANDLERS.keys())}"
        )

    ctx = NodeCompileContext(
        node_name=node_name,
        node_config=enriched_config,
        graph=graph,
        config=config,
        tools=tools,
        python_tools=python_tools,
        callable_registry=callable_registry,
        effective_defaults=effective_defaults,
        prompts_dir=prompts_dir,
        prompts_relative=prompts_relative,
    )
    result = handler(ctx)

    logger.info(f"Added node: {node_name} (type={node_type})")
    return result


def compile_nodes(
    config: "GraphConfig",
    graph: StateGraph,
    tools: dict[str, Any],
    python_tools: dict[str, Any],
    callable_registry: dict[str, Callable],
) -> tuple[dict[str, tuple], set[str]]:
    """Compile all nodes and add to graph.

    Args:
        config: Graph configuration
        graph: StateGraph to add nodes to
        tools: Shell tools registry
        python_tools: Python tools registry
        callable_registry: Loaded callable functions for tool_call nodes

    Returns:
        Tuple of:
        - map_nodes: name -> (map_edge_fn, sub_node_name)
        - interrupt_nodes: set of node names with prepare split
    """
    map_nodes: dict[str, tuple] = {}
    interrupt_nodes: set[str] = set()

    for node_name, node_config in config.nodes.items():
        result = compile_node(
            node_name,
            node_config,
            graph,
            config,
            tools,
            python_tools,
            callable_registry,
        )
        if result:
            name, info = result
            if info == "interrupt_prepare":
                interrupt_nodes.add(name)
            else:
                map_nodes[name] = info

    return map_nodes, interrupt_nodes


__all__ = ["NodeCompileContext", "NODE_TYPE_HANDLERS", "compile_node", "compile_nodes"]
