"""Map node compiler - Handles type: map node compilation.

This module provides functionality to compile map nodes that fan out
to sub-nodes for parallel processing using LangGraph's Send mechanism.
"""

import concurrent.futures
import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from langgraph.graph import StateGraph

from yamlgraph.compile.map_contract import (
    branch_failure,
    classify_result,
    make_dispatch_node,
    make_dispatch_router,
    make_join_node,
    success_accounting,
)
from yamlgraph.config import DEFAULT_MAX_MAP_ITEMS
from yamlgraph.constants import NodeType
from yamlgraph.models.schemas import ErrorType, PipelineError
from yamlgraph.node_factory import (
    create_node_function,
    create_subgraph_node,
    create_tool_call_node,
)
from yamlgraph.tools.agent import create_agent_node
from yamlgraph.tools.python_tool import load_python_function
from yamlgraph.utils.expressions import resolve_state_expression

logger = logging.getLogger(__name__)


def flatten_map_results(items: list[dict]) -> list[dict]:
    """Flatten map node results by merging _map_xxx_sub contents into items.

    FR-052: When flatten_output: true, this function merges the nested
    _map_xxx_sub dict into each item at the top level, removing the
    wrapper key.

    Args:
        items: List of map node results with _map_xxx_sub keys

    Returns:
        List with flattened items (sub-key contents merged into item)

    Example:
        >>> items = [{"_map_index": 0, "_map_analyze_sub": {"score": 0.8}}]
        >>> flatten_map_results(items)
        [{"_map_index": 0, "score": 0.8}]
    """
    if not items:
        return []

    result = []
    for item in items:
        if not isinstance(item, dict):
            result.append(item)
            continue

        # Find _map_xxx_sub key
        sub_key = None
        for key in item:
            if key.startswith("_map_") and key.endswith("_sub"):
                sub_key = key
                break

        if sub_key is None:
            # No sub key - pass through unchanged
            result.append(item)
            continue

        sub_value = item[sub_key]

        # Handle Pydantic models
        if hasattr(sub_value, "model_dump"):
            sub_value = sub_value.model_dump()

        # Scalars can't be flattened - keep wrapper
        if not isinstance(sub_value, dict):
            result.append(item)
            continue

        # Build flattened item: start with non-sub-key fields, then merge sub_value
        flattened = {}
        for key, value in item.items():
            if key != sub_key:
                flattened[key] = value

        # Merge sub_value (overwrites any conflicts)
        flattened.update(sub_value)
        result.append(flattened)

    return result


def _execute_node_fn(
    node_fn: Callable[[dict], dict],
    state: dict,
    timeout: float | None,
) -> dict:
    """Execute a node function with optional timeout.

    FR-069: When timeout is set, runs in a one-shot ThreadPoolExecutor.
    Raises concurrent.futures.TimeoutError on timeout.

    Note: Uses cancel_futures=True on shutdown so the timed-out thread
    does not block the caller (ThreadPoolExecutor.__exit__ calls
    shutdown(wait=True) which would wait for the thread to finish).
    """
    if timeout is not None:
        pool = ThreadPoolExecutor(max_workers=1)
        try:
            return pool.submit(node_fn, state).result(timeout=timeout)
        finally:
            pool.shutdown(wait=False, cancel_futures=True)
    return node_fn(state)


def wrap_for_reducer(
    node_fn: Callable[[dict], dict],
    collect_key: str,
    state_key: str,
    flatten_output: bool = False,
    timeout: float | None = None,
    *,
    map_name: str,
    failures_key: str,
) -> Callable[[dict], dict]:
    """Wrap sub-node output for Annotated reducer aggregation.

    FR-1073: successes go to `collect_key`; failures go to `failures_key`
    as typed `MapFailure` records and never enter `collect_key`. Every
    branch appends one `MapAccounting` row for the join.

    Args:
        node_fn: The original node function
        collect_key: State key where results are collected
        state_key: Key to extract from node result
        flatten_output: If True, merge _map_xxx_sub contents into items (FR-052)
        timeout: Optional per-branch timeout in seconds (FR-069)
        map_name: Owning map node name
        failures_key: State key where failures are collected

    Returns:
        Wrapped function that outputs in reducer-compatible format
    """
    sub_node_name = f"_map_{map_name}_sub"

    def wrapped(state: dict) -> dict:
        try:
            result = _execute_node_fn(node_fn, state, timeout)
        except concurrent.futures.TimeoutError as e:
            # A wrapper timeout is never tolerated: on_error never saw it.
            return branch_failure(
                map_name,
                state,
                failures_key,
                "TimeoutError",
                f"Branch timed out after {timeout}s",
                False,
                PipelineError.from_exception(
                    e, node=sub_node_name, error_type=ErrorType.TIMEOUT_ERROR
                ),
            )
        except Exception as e:
            return branch_failure(
                map_name,
                state,
                failures_key,
                type(e).__name__,
                str(e),
                False,
                PipelineError.from_exception(e, node=sub_node_name),
            )

        failure = classify_result(map_name, state, failures_key, result)
        if failure is not None:
            return failure

        extracted = (
            result.get(state_key, result) if isinstance(result, dict) else result
        )

        # Convert Pydantic models to dicts
        if hasattr(extracted, "model_dump"):
            extracted = extracted.model_dump()

        # Include _map_index if present for ordering
        if "_map_index" in state:
            if isinstance(extracted, dict):
                extracted = {"_map_index": state["_map_index"], **extracted}
            else:
                extracted = {"_map_index": state["_map_index"], "value": extracted}

        # FR-052: Flatten if requested
        if flatten_output and isinstance(extracted, dict):
            flattened = flatten_map_results([extracted])
            if flattened:
                extracted = flattened[0]

        return {
            collect_key: [extracted],
            "_map_accounting": success_accounting(map_name, state),
        }

    return wrapped


def compile_map_node(
    name: str,
    config: dict[str, Any],
    builder: StateGraph,
    defaults: dict[str, Any],
    tools_registry: dict[str, Any] | None = None,
    graph_path: Any | None = None,
    python_tools: dict[str, Callable] | None = None,
    tools: dict[str, Any] | None = None,
) -> tuple[Callable[[dict], Any], str]:
    """Compile type: map node using LangGraph Send.

    FR-1073: adds three nodes to the builder: `<name>` (dispatch),
    `_map_<name>_sub` and `_map_<name>_join`, wired dispatch -> sub ->
    join. Callers route INTO `<name>` and OUT OF the join.

    Args:
        name: Name of the map node
        config: Map node configuration with 'over', 'as', 'node', 'collect'
        builder: StateGraph builder to add sub-node to
        defaults: Default configuration for nodes
        tools_registry: Optional tools registry for tool_call sub-nodes
        graph_path: Path to graph YAML file (for relative prompt resolution)
        python_tools: Optional python tools registry for python sub-nodes

    Returns:
        Tuple of (dispatch_router, join_node_name)
    """
    over_expr = config["over"]
    item_var = config["as"]
    sub_node_name = f"_map_{name}_sub"
    collect_key = config["collect"]
    flatten_output = config.get("flatten_output", False)
    sub_node_config = dict(config["node"])  # Copy to avoid mutating original
    state_key = sub_node_config.get("state_key", "result")
    sub_node_type = sub_node_config.get("type", "llm")

    # Auto-inject the 'as' variable into sub-node's variables
    # So the prompt can access it as {item_var}
    sub_variables = dict(sub_node_config.get("variables", {}))
    sub_variables[item_var] = f"{{state.{item_var}}}"
    sub_node_config["variables"] = sub_variables

    # Create sub-node based on type
    if sub_node_type == NodeType.TOOL_CALL:
        if tools_registry is None:
            raise ValueError(
                f"Map node '{name}' has tool_call sub-node but no tools_registry"
            )
        sub_node = create_tool_call_node(sub_node_name, sub_node_config, tools_registry)
    elif sub_node_type == NodeType.PYTHON:
        if python_tools is None:
            raise ValueError(
                f"Map node '{name}' has python sub-node but no python_tools registry"
            )
        tool_name = sub_node_config.get("tool")
        if tool_name not in python_tools:
            raise ValueError(f"Unknown python tool '{tool_name}' in map node '{name}'")
        # Load the actual function from the tool config
        tool_config = python_tools[tool_name]
        graph_root = graph_path.parent.resolve() if graph_path else None
        sub_node = load_python_function(
            tool_config,
            graph_root=graph_root,
            tool_name=tool_name,
        )
    elif sub_node_type == NodeType.AGENT:
        if tools is None:
            raise ValueError(
                f"Map node '{name}' has agent sub-node but no tools registry"
            )
        from yamlgraph.node_factory.base import get_output_model_for_node

        agent_output_model = get_output_model_for_node(
            sub_node_config,
            prompts_dir=defaults.get("prompts_dir") if defaults else None,
            graph_path=graph_path,
            prompts_relative=defaults.get("prompts_relative", False)
            if defaults
            else False,
        )
        sub_node = create_agent_node(
            sub_node_name,
            sub_node_config,
            tools=tools,
            python_tools=python_tools or {},
            defaults=defaults,
            graph_path=graph_path,
            output_model=agent_output_model,
        )
    elif sub_node_type == NodeType.SUBGRAPH:
        # FR-202: Map over subgraphs for nested pipelines
        sub_node = create_subgraph_node(
            sub_node_name,
            sub_node_config,
            parent_graph_path=graph_path,
        )
    else:
        sub_node = create_node_function(
            sub_node_name, sub_node_config, defaults, graph_path=graph_path
        )

    failures_key = config.get("failures") or f"{collect_key}_failures"
    wrapped_node = wrap_for_reducer(
        sub_node,
        collect_key,
        state_key,
        flatten_output,
        timeout=config.get("timeout"),
        map_name=name,
        failures_key=failures_key,
    )
    join_name = f"_map_{name}_join"
    max_items = config.get(
        "max_items", defaults.get("max_map_items", DEFAULT_MAX_MAP_ITEMS)
    )

    def resolve_items(state: dict, warn: bool) -> list:
        try:
            items = resolve_state_expression(over_expr, state)
        except KeyError as e:
            available_keys = list(state.keys())
            raise KeyError(
                f"Map node '{name}' failed: expression '{over_expr}' could not be resolved. "
                f"Missing key: {e}. Available state keys: {available_keys}"
            ) from e

        if not isinstance(items, list):
            raise TypeError(
                f"Map 'over' must resolve to list, got {type(items).__name__}"
            )

        # FR-027: Cap fan-out to prevent unbounded Send() calls
        if len(items) > max_items:
            if warn:
                logger.warning(
                    "Map node '%s': truncating %d items to %d",
                    name,
                    len(items),
                    max_items,
                )
            items = items[:max_items]
        return items

    # FR-1073: dispatch -> sub -> join
    builder.add_node(name, make_dispatch_node(name, resolve_items))
    builder.add_node(sub_node_name, wrapped_node)
    builder.add_node(join_name, make_join_node(name, config.get("min_success")))
    map_edge = make_dispatch_router(
        name, sub_node_name, join_name, item_var, resolve_items
    )
    builder.add_conditional_edges(name, map_edge, [sub_node_name, join_name])
    builder.add_edge(sub_node_name, join_name)

    return map_edge, join_name
