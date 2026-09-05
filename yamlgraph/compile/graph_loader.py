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

from yamlgraph.compile.edge_compiler import _add_conditional_edges, _process_edge
from yamlgraph.compile.node_compiler import compile_nodes
from yamlgraph.data_loader import load_data_files
from yamlgraph.loop_detector import apply_loop_node_defaults
from yamlgraph.models.state_builder import build_state_class
from yamlgraph.storage.checkpointer_factory import get_checkpointer
from yamlgraph.tools.graph_tool import make_graph_tool_fn
from yamlgraph.tools.manifest import expand_tool_manifests
from yamlgraph.tools.python_tool import load_python_function, parse_python_tools
from yamlgraph.tools.schema_loader_tool import parse_schema_loader_tools
from yamlgraph.tools.shell import parse_tools
from yamlgraph.tools.tool_slots import resolve_tool_slots
from yamlgraph.tools.write_data_file_tool import parse_write_data_file_tools
from yamlgraph.utils.validators import validate_config, validate_max_concurrency

# Type alias for dynamic state
GraphState = dict[str, Any]

logger = logging.getLogger(__name__)

TOOL_LOAD_MODE_STRICT = "strict"
TOOL_LOAD_MODE_WARN = "warn"
VALID_TOOL_LOAD_MODES = {TOOL_LOAD_MODE_STRICT, TOOL_LOAD_MODE_WARN}


class GraphConfig:
    """Parsed graph configuration from YAML."""

    def __init__(
        self,
        config: dict,
        source_path: Path | None = None,
        tool_bindings: dict[str, str] | None = None,
    ):
        """Initialize from parsed YAML dict.

        Args:
            config: Parsed YAML configuration dictionary
            source_path: Path to the source YAML file (for subgraph resolution)
            tool_bindings: FR-892 slot name → manifest path bindings

        Raises:
            ValueError: If config is invalid
        """
        # Validate before storing
        validate_config(config)

        self.version = config.get("version", "1.0")
        self.name = config.get("name", "unnamed")
        self.description = config.get("description", "")
        self.defaults = config.get("defaults", {})
        self.provider = config.get("provider") or self.defaults.get("provider")
        self.nodes = config.get("nodes", {})
        self.edges = config.get("edges", [])
        # FR-892: resolve slot declarations against invocation bindings
        # BEFORE manifest expansion — slots become inline declarations.
        # Binding paths resolve relative to CWD (R-1 frozen contract):
        # the binding is the caller's input, not the graph author's.
        slotted = resolve_tool_slots(config.get("tools", {}), tool_bindings, Path.cwd())
        # FR-768: expand manifest-declared tools at the load boundary
        self.tools = expand_tool_manifests(slotted, source_path)
        self.loop_limits = config.get("loop_limits", {})
        self.loop_exits = config.get("loop_exits", {})
        self.checkpointer = config.get("checkpointer")
        # FR-677: Graph-level verification rules (read by the __verify__ node)
        self.verify = config.get("verify", [])
        # FR-027: Execution safety config
        graph_level_config = config.get("config", {})
        self.recursion_limit = graph_level_config.get("recursion_limit", 50)
        self.max_map_items = graph_level_config.get("max_map_items", 100)
        self.max_tokens = graph_level_config.get("max_tokens")
        self.timeout = graph_level_config.get("timeout")
        # FR-984: whole-invoke fan-out width, delegated to LangGraph
        self.max_concurrency = validate_max_concurrency(
            graph_level_config.get("max_concurrency")
        )
        self.tool_load_mode = graph_level_config.get(
            "tool_load_mode", TOOL_LOAD_MODE_STRICT
        )
        if self.tool_load_mode not in VALID_TOOL_LOAD_MODES:
            valid_modes = ", ".join(sorted(VALID_TOOL_LOAD_MODES))
            raise ValueError(
                f"Invalid config.tool_load_mode '{self.tool_load_mode}'. "
                f"Expected one of: {valid_modes}"
            )
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


def load_graph_config(
    path: str | Path, tool_bindings: dict[str, str] | None = None
) -> GraphConfig:
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

    with open(path, encoding="utf-8") as f:
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

    # FR-235: Expand pipeline template nodes before compilation
    from yamlgraph.compile.pipeline_template import expand_pipeline_templates

    config = expand_pipeline_templates(config)

    # FR-677: Insert terminal __verify__ node when a graph-level verify block
    # is present, redirecting explicit END destinations through it.
    from yamlgraph.compile.verify_insert import insert_verify_node

    config = insert_verify_node(config)

    return GraphConfig(config, source_path=path.resolve(), tool_bindings=tool_bindings)


def _resolve_state_class(config: GraphConfig) -> type:
    """Build state class dynamically from graph configuration.

    Args:
        config: Graph configuration

    Returns:
        TypedDict class for graph state
    """
    return build_state_class(config.raw_config, source_path=config.source_path)


def _parse_graph_tools(
    config: GraphConfig,
) -> tuple[dict[str, dict[str, Any]], dict[str, Callable]]:
    """Parse ``type: graph`` tools — compile child graphs and create callables.

    FR-658: Lives in Layer 2 (graph_loader) because it needs
    ``load_graph_config`` and ``compile_graph``.

    Args:
        config: Parent graph configuration.

    Returns:
        Tuple of (graph_tool_configs, graph_tool_callables).
    """
    from yamlgraph.node_factory.subgraph_nodes import _loading_stack

    parent_path = config.source_path or Path.cwd() / "graph.yaml"
    configs: dict[str, dict[str, Any]] = {}
    callables: dict[str, Callable] = {}

    for name, raw in config.tools.items():
        if not isinstance(raw, dict) or raw.get("type") != "graph":
            continue

        raw_path = raw["path"]
        graph_path = Path(raw_path)
        if not graph_path.is_absolute():
            graph_path = (parent_path.parent / graph_path).resolve()
        else:
            graph_path = graph_path.resolve()

        input_mapping: dict[str, str] = raw.get("input_mapping", {})
        output_key: str = raw.get("output_key", "result")

        # AC-8: compile once at parse time
        child_config = load_graph_config(graph_path)
        sg = compile_graph(child_config)
        compiled = sg.compile()

        description: str = raw.get("description") or child_config.description or name

        fn = make_graph_tool_fn(
            compiled,
            input_mapping,
            output_key,
            graph_path,
            _loading_stack,
            default_variables=child_config.raw_config.get("variables") or None,
        )
        configs[name] = {
            "description": description,
            "input_mapping": input_mapping,
            "output_key": output_key,
        }
        callables[name] = fn

    return configs, callables


def _parse_all_tools(
    config: GraphConfig,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Callable], dict[str, Any]]:
    """Parse shell, Python, and graph tools from config.

    Args:
        config: Graph configuration

    Returns:
        Tuple of (shell_tools, python_tools, callable_registry, graph_tool_configs)
        callable_registry maps tool names to actual callable functions for tool_call nodes
    """
    tools = parse_tools(config.tools)
    python_tools = parse_python_tools(config.tools)
    schema_loader_tools = parse_schema_loader_tools(config.tools)
    write_data_file_tools = parse_write_data_file_tools(config.tools)
    python_tools.update(schema_loader_tools)
    python_tools.update(write_data_file_tools)

    # FR-658: Parse type: graph tools (AC-1, AC-2, AC-8)
    graph_tool_configs, graph_tool_callables = _parse_graph_tools(config)

    graph_root = (
        config.source_path.parent.resolve()
        if config.source_path
        else Path.cwd().resolve()
    )

    # Resolve prompts_dir for write_data_file self-modification guard
    prompts_dir: Path | None = None
    if config.prompts_dir and config.source_path:
        prompts_dir = (config.source_path.parent / config.prompts_dir).resolve()

    # Build callable registry for tool_call nodes
    callable_registry: dict[str, Callable] = {}
    load_failures: list[tuple[str, Exception]] = []
    for name, tool_config in python_tools.items():
        try:
            callable_registry[name] = load_python_function(
                tool_config,
                graph_root=graph_root,
                tool_name=name,
                graph_path=config.source_path,
                prompts_dir=prompts_dir,
            )
        except (ImportError, AttributeError, ValueError, TypeError) as e:
            if config.tool_load_mode == TOOL_LOAD_MODE_WARN:
                logger.warning(f"Failed to load tool '{name}': {e}")
            else:
                load_failures.append((name, e))

    if load_failures:
        failures = "; ".join(f"{name}: {error}" for name, error in load_failures)
        raise ValueError(
            "Python tool load failed in strict mode "
            f"(config.tool_load_mode={TOOL_LOAD_MODE_STRICT}): {failures}"
        )

    # FR-658: Merge graph-tool callables into callable_registry
    callable_registry.update(graph_tool_callables)

    if tools:
        logger.info(f"Parsed {len(tools)} shell tools: {', '.join(tools.keys())}")
    if python_tools:
        logger.info(
            f"Parsed {len(python_tools)} Python tools: {', '.join(python_tools.keys())}"
        )
    if graph_tool_configs:
        logger.info(
            f"Parsed {len(graph_tool_configs)} graph tools: {', '.join(graph_tool_configs.keys())}"
        )

    return tools, python_tools, callable_registry, graph_tool_configs


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

    # FR-723: graph-YAML opt-in for the route decision log (process-wide).
    observability = config.raw_config.get("observability") or {}
    if observability.get("route_log") or observability.get("profile") == "regulated":
        from yamlgraph.utils.route_log import enable_route_log

        enable_route_log(True)

    # Parse all tools
    tools, python_tools, callable_registry, graph_tool_configs = _parse_all_tools(
        config
    )

    # Compile all nodes
    map_nodes, interrupt_nodes, subgraph_interrupt_nodes = compile_nodes(
        config, graph, tools, python_tools, callable_registry, graph_tool_configs
    )

    # Process edges
    router_edges: dict[str, list] = {}
    expression_edges: dict[str, list[tuple[str, str]]] = {}
    map_fanout_sources: set[str] = set()

    for edge in config.edges:
        _process_edge(
            edge,
            graph,
            map_nodes,
            router_edges,
            expression_edges,
            interrupt_nodes,
            map_fanout_sources,
            subgraph_interrupt_nodes=subgraph_interrupt_nodes,
        )

    # Add conditional edges (FR-211: pass interrupt_nodes for route mapping redirect)
    _add_conditional_edges(
        graph,
        router_edges,
        expression_edges,
        config.loop_exits,
        interrupt_nodes=interrupt_nodes,
        subgraph_interrupt_nodes=subgraph_interrupt_nodes,
        map_nodes=map_nodes,
        map_fanout_sources=map_fanout_sources,
    )

    return graph


def invoke_graph(
    path: str | Path,
    variables: dict[str, Any],
    *,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Load, compile, and invoke a graph synchronously.

    Convenience function combining load_graph_config, compile_graph,
    and compiled graph invocation.

    Args:
        path: Path to graph YAML file.
        variables: Input variables / initial state.
        config: Optional LangGraph run config (thread_id, etc.).

    Returns:
        Result dict from graph invocation.
    """
    graph_config = load_graph_config(path)
    sg = compile_graph(graph_config)
    compiled = sg.compile()
    return compiled.invoke(variables, config=config or {})


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
