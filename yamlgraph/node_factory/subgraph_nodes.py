"""Subgraph node factory.

Creates LangGraph nodes that invoke compiled subgraphs.
"""

import logging
from collections.abc import Callable
from contextvars import ContextVar
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Thread-safe loading stack to detect circular subgraph references
# Note: Do NOT use default=[] as it shares the same list across contexts
_loading_stack: ContextVar[list[Path]] = ContextVar("loading_stack")


def _map_input_state(
    parent_state: dict[str, Any],
    input_mapping: dict[str, str] | str,
) -> dict[str, Any]:
    """Map parent state to child input based on mapping config.

    Args:
        parent_state: Current state from parent graph
        input_mapping: Mapping configuration:
            - dict: explicit {parent_key: child_key} mapping
            - "auto": copy all fields
            - "*": pass state reference directly

    Returns:
        Input state for child graph
    """
    if input_mapping == "auto":
        return parent_state.copy()
    elif input_mapping == "*":
        return parent_state
    else:
        return {
            child_key: parent_state.get(parent_key)
            for parent_key, child_key in input_mapping.items()
        }


def _map_output_state(
    child_output: dict[str, Any],
    output_mapping: dict[str, str] | str,
) -> dict[str, Any]:
    """Map child output to parent state updates based on mapping config.

    Args:
        child_output: Output state from child graph
        output_mapping: Mapping configuration:
            - dict: explicit {parent_key: child_key} mapping
            - "auto": pass all fields
            - "*": pass output directly

    Returns:
        Updates to apply to parent state
    """
    if output_mapping in ("auto", "*"):
        return child_output
    else:
        return {
            parent_key: child_output.get(child_key)
            for parent_key, child_key in output_mapping.items()
        }


def _build_child_config(
    parent_config: dict[str, Any],
    node_name: str,
) -> dict[str, Any]:
    """Build child graph config with propagated thread ID.

    Args:
        parent_config: RunnableConfig from parent graph
        node_name: Name of the subgraph node

    Returns:
        Config for child graph with thread_id: parent_thread:node_name
    """
    configurable = parent_config.get("configurable", {})
    parent_thread_id = configurable.get("thread_id")

    child_thread_id = (
        f"{parent_thread_id}:{node_name}" if parent_thread_id else node_name
    )

    return {
        **parent_config,
        "configurable": {
            **configurable,
            "thread_id": child_thread_id,
        },
    }


def create_subgraph_node(
    node_name: str,
    node_config: dict[str, Any],
    parent_graph_path: Path,
    parent_checkpointer: Any | None = None,
) -> Callable[[dict, dict], dict] | Any:
    """Create a node that invokes a compiled subgraph.

    Args:
        node_name: Name of this node in parent graph
        node_config: Subgraph configuration from YAML
        parent_graph_path: Path to parent graph (for relative resolution)
        parent_checkpointer: Checkpointer to inherit (if any)

    Returns:
        Node function that invokes subgraph (or CompiledGraph for mode=direct)

    Raises:
        FileNotFoundError: If subgraph YAML doesn't exist
        ValueError: If circular reference detected
    """
    from yamlgraph.graph_loader import compile_graph, load_graph_config

    # Resolve path relative to parent graph file
    graph_rel_path = node_config["graph"]
    graph_path = (parent_graph_path.parent / graph_rel_path).resolve()

    mode = node_config.get("mode", "invoke")
    input_mapping = node_config.get("input_mapping", {})
    output_mapping = node_config.get("output_mapping", {})
    interrupt_output_mapping = node_config.get("interrupt_output_mapping", {})

    # Validate graph exists
    if not graph_path.exists():
        raise FileNotFoundError(f"Subgraph not found: {graph_path}")

    # Circular reference detection (thread-safe)
    # Use .get([]) to provide default without sharing mutable state
    stack = _loading_stack.get([])
    if graph_path in stack:
        cycle = " -> ".join(str(p) for p in [*stack, graph_path])
        raise ValueError(f"Circular subgraph reference: {cycle}")

    # Push onto loading stack for this context
    token = _loading_stack.set([*stack, graph_path])
    try:
        subgraph_config = load_graph_config(graph_path)
        state_graph = compile_graph(subgraph_config)
        # Compile with checkpointer (if provided)
        compiled = state_graph.compile(checkpointer=parent_checkpointer)
    finally:
        _loading_stack.reset(token)

    if mode == "direct":
        # Mode: Direct - shared schema, LangGraph handles state mapping
        # Return compiled graph directly - LangGraph's add_node() accepts
        # CompiledStateGraph objects and handles them natively
        return compiled

    # Mode: Invoke - explicit state mapping
    from langchain_core.runnables import RunnableConfig

    def subgraph_node(state: dict, config: RunnableConfig | None = None) -> dict:
        """Execute the subgraph with mapped state."""
        from langgraph.errors import GraphInterrupt

        config = config or {}

        # Build child input from parent state
        child_input = _map_input_state(state, input_mapping)

        # Build child config with propagated thread ID
        child_config = _build_child_config(config, node_name)

        # Invoke subgraph - may raise GraphInterrupt
        try:
            child_output = compiled.invoke(child_input, child_config)
            is_interrupted = "__interrupt__" in child_output
        except GraphInterrupt:
            # FR-006: Child hit an interrupt
            if interrupt_output_mapping:
                # Get child state from checkpointer
                child_state = compiled.get_state(child_config)
                child_output = dict(child_state.values) if child_state else {}

                # Apply interrupt_output_mapping
                parent_updates = _map_output_state(
                    child_output, interrupt_output_mapping
                )
                parent_updates["current_step"] = node_name

                # Use __pregel_send to update parent state before re-raising
                # This allows the mapped state to be included in the result
                send = config.get("configurable", {}).get("__pregel_send")
                if send:
                    # Convert dict to list of (key, value) tuples
                    updates = [(k, v) for k, v in parent_updates.items()]
                    send(updates)
                    logger.info(
                        f"FR-006: Subgraph {node_name} mapped state: "
                        f"{list(parent_updates.keys())}"
                    )

            # Re-raise to pause the graph
            raise

        # Normal completion path
        if is_interrupted and interrupt_output_mapping:
            parent_updates = _map_output_state(child_output, interrupt_output_mapping)
            parent_updates["__interrupt__"] = child_output["__interrupt__"]
        else:
            parent_updates = _map_output_state(child_output, output_mapping)

        parent_updates["current_step"] = node_name

        return parent_updates

    subgraph_node.__name__ = f"{node_name}_subgraph"
    return subgraph_node
