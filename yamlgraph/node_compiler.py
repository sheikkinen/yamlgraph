"""Node Compiler - Compile YAML node configs to LangGraph nodes.

Extracted from graph_loader.py to keep modules under 400 lines.
Uses a registry pattern (FR-220) to dispatch node types to handlers.
"""

import concurrent.futures
import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from langgraph.graph import StateGraph
from langgraph.types import CachePolicy

from yamlgraph.constants import NodeType
from yamlgraph.map_compiler import compile_map_node
from yamlgraph.models.graph_schema import CacheConfig
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
    cache_policy: CachePolicy | None = field(default=None)


# ---------------------------------------------------------------------------
# Cache policy resolution (FR-032)
# ---------------------------------------------------------------------------


def resolve_cache_policy(cache_config: CacheConfig | None) -> CachePolicy | None:
    """Convert CacheConfig → LangGraph CachePolicy.

    Args:
        cache_config: Parsed cache configuration from YAML, or None.

    Returns:
        CachePolicy instance, or None if caching not configured.
    """
    if cache_config is None:
        return None
    return CachePolicy(ttl=cache_config.ttl)


def _parse_cache_field(raw: Any) -> CacheConfig | None:
    """Parse raw cache field value from YAML node config.

    Handles: True → CacheConfig(), False/None → None, dict → CacheConfig(**dict).
    """
    if raw is True:
        return CacheConfig()
    if raw is False or raw is None:
        return None
    if isinstance(raw, dict):
        return CacheConfig(**raw)
    if isinstance(raw, CacheConfig):
        return raw
    return None


# ---------------------------------------------------------------------------
# Timeout wrapper (FR-069)
# ---------------------------------------------------------------------------


def _maybe_wrap_timeout(
    node_fn: Callable,
    node_config: dict[str, Any],
    node_name: str,
) -> Callable:
    """Wrap node function with ThreadPoolExecutor timeout if configured.

    FR-069: Per-node timeout bounding. When timeout is set, the node
    function is executed in a one-shot ThreadPoolExecutor. On
    concurrent.futures.TimeoutError, a PipelineError with
    error_type=TIMEOUT_ERROR is returned.

    Args:
        node_fn: The original node function
        node_config: Node configuration dict (checked for 'timeout')
        node_name: Name of the node (for error messages)

    Returns:
        Wrapped function if timeout is set, original function otherwise
    """
    timeout = node_config.get("timeout")
    if timeout is None:
        return node_fn

    state_key = node_config.get("state_key", node_name)

    def timed_fn(state: dict) -> dict:
        pool = ThreadPoolExecutor(max_workers=1)
        try:
            return pool.submit(node_fn, state).result(timeout=timeout)
        except concurrent.futures.TimeoutError as e:
            from yamlgraph.models import PipelineError
            from yamlgraph.models.schemas import ErrorType

            pe = PipelineError.from_exception(
                e, node=node_name, error_type=ErrorType.TIMEOUT_ERROR
            )
            return {
                state_key: None,
                "current_step": node_name,
                "errors": [pe],
            }
        finally:
            pool.shutdown(wait=False, cancel_futures=True)

    timed_fn.__name__ = getattr(node_fn, "__name__", f"{node_name}_node")
    return timed_fn


# ---------------------------------------------------------------------------
# Node type handlers — one per node type
# ---------------------------------------------------------------------------

NodeTypeHandler = Callable[[NodeCompileContext], tuple[str, Any] | None]


def _compile_tool_node(ctx: NodeCompileContext) -> None:
    node_fn = create_tool_node(ctx.node_name, ctx.node_config, ctx.tools)
    node_fn = _maybe_wrap_timeout(node_fn, ctx.node_config, ctx.node_name)
    ctx.graph.add_node(ctx.node_name, node_fn, cache_policy=ctx.cache_policy)
    return None


def _compile_python_node(ctx: NodeCompileContext) -> None:
    node_fn = create_python_node(ctx.node_name, ctx.node_config, ctx.python_tools)
    node_fn = _maybe_wrap_timeout(node_fn, ctx.node_config, ctx.node_name)
    ctx.graph.add_node(ctx.node_name, node_fn, cache_policy=ctx.cache_policy)
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
    node_fn = _maybe_wrap_timeout(node_fn, ctx.node_config, ctx.node_name)
    ctx.graph.add_node(ctx.node_name, node_fn, cache_policy=ctx.cache_policy)
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
    node_fn = _maybe_wrap_timeout(node_fn, ctx.node_config, ctx.node_name)
    ctx.graph.add_node(ctx.node_name, node_fn, cache_policy=ctx.cache_policy)
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
    ctx.graph.add_node(prepare_name, prepare_fn, cache_policy=ctx.cache_policy)
    ctx.graph.add_node(ctx.node_name, interrupt_fn)
    ctx.graph.add_edge(prepare_name, ctx.node_name)
    return (ctx.node_name, "interrupt_prepare")


def _compile_passthrough_node(ctx: NodeCompileContext) -> None:
    node_fn = create_passthrough_node(ctx.node_name, ctx.node_config)
    ctx.graph.add_node(ctx.node_name, node_fn, cache_policy=ctx.cache_policy)
    return None


def _compile_copilot_node(ctx: NodeCompileContext) -> None:
    node_fn = create_copilot_node(
        ctx.node_name,
        ctx.node_config,
        defaults=ctx.effective_defaults,
        graph_path=ctx.config.source_path,
        prompts_dir=ctx.prompts_dir,
        prompts_relative=ctx.prompts_relative,
    )
    ctx.graph.add_node(ctx.node_name, node_fn, cache_policy=ctx.cache_policy)
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
    ctx.graph.add_node(ctx.node_name, node_fn, cache_policy=ctx.cache_policy)
    return None


def _compile_llm_node(ctx: NodeCompileContext) -> None:
    node_fn = create_node_function(
        ctx.node_name,
        ctx.node_config,
        ctx.effective_defaults,
        graph_path=ctx.config.source_path,
    )
    node_fn = _maybe_wrap_timeout(node_fn, ctx.node_config, ctx.node_name)
    ctx.graph.add_node(ctx.node_name, node_fn, cache_policy=ctx.cache_policy)
    return None


def _compile_race_node(ctx: NodeCompileContext) -> None:
    node_fn = create_race_node(
        ctx.node_name,
        ctx.node_config,
        ctx.effective_defaults,
        graph_path=ctx.config.source_path,
    )
    # Race owns `timeout` natively via as_completed(timeout=...);
    # do NOT wrap in _maybe_wrap_timeout (nested pools drop return value — FR-267).
    ctx.graph.add_node(ctx.node_name, node_fn, cache_policy=ctx.cache_policy)
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

    # Resolve cache policy (FR-032)
    raw_cache = node_config.get("cache")
    cache_config = _parse_cache_field(raw_cache)
    node_cache_policy = resolve_cache_policy(cache_config)

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
        cache_policy=node_cache_policy,
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


__all__ = [
    "NodeCompileContext",
    "NODE_TYPE_HANDLERS",
    "_maybe_wrap_timeout",
    "compile_node",
    "compile_nodes",
    "compile_node",
    "compile_nodes",
    "resolve_cache_policy",
]
