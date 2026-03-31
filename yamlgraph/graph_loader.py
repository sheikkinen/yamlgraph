"""YAML Graph Loader - Compile YAML to LangGraph.

This module provides functionality to load graph definitions from YAML files
and compile them into LangGraph StateGraph instances.
"""

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import StateGraph

from yamlgraph.data_loader import load_data_files
from yamlgraph.edge_compiler import _add_conditional_edges, _process_edge
from yamlgraph.models.state_builder import build_state_class
from yamlgraph.node_compiler import compile_nodes
from yamlgraph.storage.checkpointer_factory import get_checkpointer
from yamlgraph.tools.python_tool import load_python_function, parse_python_tools
from yamlgraph.tools.shell import parse_tools
from yamlgraph.utils.validators import validate_config

# Type alias for dynamic state
GraphState = dict[str, Any]

logger = logging.getLogger(__name__)


def detect_loop_nodes(edges: list[dict]) -> set[str]:
    """Detect nodes that participate in cycles (loops).

    Uses DFS with path tracking to find back edges indicating cycles.

    Args:
        edges: List of edge dicts with 'from' and 'to' keys

    Returns:
        Set of node names that are part of at least one cycle
    """
    from collections import defaultdict

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
    import copy

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


class GraphConfig:
    """Parsed graph configuration from YAML."""

    def __init__(self, config: dict, source_path: Path | None = None):
        """Initialize from parsed YAML dict.

        Args:
            config: Parsed YAML configuration dictionary
            source_path: Path to the source YAML file (for subgraph resolution)

        Raises:
            ValueError: If config is invalid
        """
        # Validate before storing
        validate_config(config)

        self.version = config.get("version", "1.0")
        self.name = config.get("name", "unnamed")
        self.description = config.get("description", "")
        self.defaults = config.get("defaults", {})
        self.nodes = config.get("nodes", {})
        self.edges = config.get("edges", [])
        self.tools = config.get("tools", {})
        self.loop_limits = config.get("loop_limits", {})
        self.loop_exits = config.get("loop_exits", {})
        self.checkpointer = config.get("checkpointer")
        # FR-027: Execution safety config
        graph_level_config = config.get("config", {})
        self.recursion_limit = graph_level_config.get("recursion_limit", 50)
        self.max_map_items = graph_level_config.get("max_map_items", 100)
        self.max_tokens = graph_level_config.get("max_tokens")
        self.timeout = graph_level_config.get("timeout")
        # Store raw config for dynamic state building
        self.raw_config = config
        # Store source path for subgraph resolution
        self.source_path = source_path
        # Prompt resolution options (FR-A: graph-relative prompts)
        # Check top-level first, then defaults
        self.prompts_relative = config.get(
            "prompts_relative", self.defaults.get("prompts_relative", False)
        )
        self.prompts_dir = config.get("prompts_dir", self.defaults.get("prompts_dir"))

        # FR-021: Load external data files into state
        if source_path:
            self.data = load_data_files(config, source_path)
        else:
            self.data = {}


def load_graph_config(path: str | Path) -> GraphConfig:
    """Load and parse a YAML graph definition.

    Args:
        path: Path to the YAML file

    Returns:
        GraphConfig instance

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the YAML is invalid or missing required fields
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Graph config not found: {path}")

    with open(path) as f:
        config = yaml.safe_load(f)

    # Guard against empty/null YAML files
    if config is None:
        raise ValueError(f"Empty or invalid YAML file: {path}")
    if not isinstance(config, dict):
        raise ValueError(
            f"Graph config must be a dict, got {type(config).__name__}: {path}"
        )

    # FR-010: Auto-apply skip_if_exists=false to loop nodes
    config = apply_loop_node_defaults(config)

    # FR-049: Expand interactive_tool nodes before compilation
    from yamlgraph.interactive_tool import expand_interactive_tools

    config = expand_interactive_tools(config)

    return GraphConfig(config, source_path=path.resolve())


def _resolve_state_class(config: GraphConfig) -> type:
    """Build state class dynamically from graph configuration.

    Args:
        config: Graph configuration

    Returns:
        TypedDict class for graph state
    """
    return build_state_class(config.raw_config)


def _parse_all_tools(
    config: GraphConfig,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Callable]]:
    """Parse shell and Python tools from config.

    Args:
        config: Graph configuration

    Returns:
        Tuple of (shell_tools, python_tools, callable_registry)
        callable_registry maps tool names to actual callable functions for tool_call nodes
    """
    tools = parse_tools(config.tools)
    python_tools = parse_python_tools(config.tools)

    # Build callable registry for tool_call nodes
    callable_registry: dict[str, Callable] = {}
    for name, tool_config in python_tools.items():
        try:
            callable_registry[name] = load_python_function(tool_config)
        except (ImportError, AttributeError) as e:
            logger.warning(f"Failed to load tool '{name}': {e}")

    if tools:
        logger.info(f"Parsed {len(tools)} shell tools: {', '.join(tools.keys())}")
    if python_tools:
        logger.info(
            f"Parsed {len(python_tools)} Python tools: {', '.join(python_tools.keys())}"
        )

    return tools, python_tools, callable_registry


def compile_graph(config: GraphConfig) -> StateGraph:
    """Compile a GraphConfig to a LangGraph StateGraph.

    Args:
        config: Parsed graph configuration

    Returns:
        StateGraph ready for compilation
    """
    # Build state class and create graph
    state_class = _resolve_state_class(config)
    graph = StateGraph(state_class)

    # Parse all tools
    tools, python_tools, callable_registry = _parse_all_tools(config)

    # Compile all nodes
    map_nodes, interrupt_nodes = compile_nodes(
        config, graph, tools, python_tools, callable_registry
    )

    # Process edges
    router_edges: dict[str, list] = {}
    expression_edges: dict[str, list[tuple[str, str]]] = {}

    for edge in config.edges:
        _process_edge(
            edge, graph, map_nodes, router_edges, expression_edges, interrupt_nodes
        )

    # Add conditional edges (FR-211: pass interrupt_nodes for route mapping redirect)
    _add_conditional_edges(
        graph,
        router_edges,
        expression_edges,
        config.loop_exits,
        interrupt_nodes=interrupt_nodes,
    )

    return graph


def load_and_compile(path: str | Path) -> StateGraph:
    """Load YAML and compile to StateGraph.

    Convenience function combining load_graph_config and compile_graph.

    Args:
        path: Path to YAML graph definition

    Returns:
        StateGraph ready for compilation
    """
    config = load_graph_config(path)
    logger.info(f"Loaded graph config: {config.name} v{config.version}")
    return compile_graph(config)


def get_checkpointer_for_graph(
    config: GraphConfig,
) -> BaseCheckpointSaver | None:
    """Get checkpointer from graph config.

    Args:
        config: Graph configuration

    Returns:
        Configured checkpointer or None if not specified

    Note:
        For async usage, use get_checkpointer_async() directly.
    """
    return get_checkpointer(config.checkpointer)
