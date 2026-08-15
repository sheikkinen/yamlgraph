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


def _guard_unrelayed_interrupt(
    child_output: Any, node_name: str, graph_path: Path
) -> None:
    """FR-797 fail-loud: a child interrupt reached a non-relay subgraph node.

    Raises:
        ValueError: naming the child graph and the missing relay config.
    """
    if isinstance(child_output, dict) and "__interrupt__" in child_output:
        raise ValueError(
            f"Subgraph node {node_name!r} received an interrupt from child "
            f"graph {graph_path} but is not relay-capable: the child declares "
            "no 'type: interrupt' node and the parent node has no "
            "'interrupt_output_mapping'. Declare the interrupt in the child "
            "graph (with a resumable 'checkpointer:') so the parent can "
            "relay the pause."
        )


def create_subgraph_node(
    node_name: str,
    node_config: dict[str, Any],
    parent_graph_path: Path,
    parent_checkpointer: Any | None = None,
) -> Callable[[dict, dict], dict] | tuple[Callable, Callable] | Any:
    """Create node function(s) that invoke a compiled subgraph.

    Args:
        node_name: Name of this node in parent graph
        node_config: Subgraph configuration from YAML
        parent_graph_path: Path to parent graph (for relative resolution)
        parent_checkpointer: Checkpointer to inherit (if any)

    Returns:
        - CompiledGraph for mode=direct
        - (run_fn, pause_fn) tuple for relay-capable nodes (FR-797
          two-node split: run commits, pause interrupts)
        - single node function otherwise

    Raises:
        FileNotFoundError: If subgraph YAML doesn't exist
        ValueError: If circular reference detected
    """
    from yamlgraph.compile.graph_loader import (
        compile_graph,
        get_checkpointer_for_graph,
        load_graph_config,
    )
    from yamlgraph.models.relay_fields import subgraph_relay_capable

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

    relay = mode == "invoke" and subgraph_relay_capable(node_config, parent_graph_path)

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
        # FR-797 checkpointer precedence: parent-provided → child-declared →
        # (relay only) in-process MemorySaver default so pause/resume works
        # without durable claims. get_checkpointer(None) returns None.
        checkpointer = parent_checkpointer or get_checkpointer_for_graph(
            subgraph_config
        )
        if relay and checkpointer is None:
            from langgraph.checkpoint.memory import MemorySaver

            checkpointer = MemorySaver()
        compiled = state_graph.compile(checkpointer=checkpointer)
    finally:
        _loading_stack.reset(token)

    if mode == "direct":
        # Mode: Direct - shared schema, LangGraph handles state mapping
        # Return compiled graph directly - LangGraph's add_node() accepts
        # CompiledStateGraph objects and handles them natively
        return compiled

    if relay:
        return _create_relay_pair(
            node_name,
            compiled,
            graph_path,
            input_mapping,
            output_mapping,
            interrupt_output_mapping,
        )

    # Mode: Invoke, child cannot interrupt - single node, unchanged behavior
    from langchain_core.runnables import RunnableConfig

    def subgraph_node(state: dict, config: RunnableConfig | None = None) -> dict:
        """Execute the subgraph with mapped state."""
        config = config or {}
        child_input = _map_input_state(state, input_mapping)
        child_config = _build_child_config(config, node_name)

        child_output = compiled.invoke(child_input, child_config)
        # langgraph 1.x returns __interrupt__ instead of raising (FR-797);
        # a non-relay child has no resumable pause path — fail loud.
        _guard_unrelayed_interrupt(child_output, node_name, graph_path)

        parent_updates = _map_output_state(child_output, output_mapping)
        parent_updates["current_step"] = node_name
        return parent_updates

    subgraph_node.__name__ = f"{node_name}_subgraph"
    return subgraph_node


def _create_relay_pair(
    node_name: str,
    compiled: Any,
    graph_path: Path,
    input_mapping: dict[str, str] | str,
    output_mapping: dict[str, str] | str,
    interrupt_output_mapping: dict[str, str] | str,
) -> tuple[Callable, Callable]:
    """FR-797 two-node split: run commits state, pause interrupts.

    ``{name}__run`` invokes (or resumes) the child and RETURNS normally,
    committing mapped interrupt state plus relay internals to the parent
    checkpoint. ``{name}__pause`` then performs the parent-native
    ``interrupt(payload)``. Commit-before-pause — the FR-060 model.
    """
    from langchain_core.runnables import RunnableConfig
    from langgraph.types import Command

    paused_key = f"__{node_name}_paused__"
    payload_key = f"__{node_name}_payload__"
    resume_key = f"__{node_name}_resume__"

    def run_fn(state: dict, config: RunnableConfig | None = None) -> dict:
        """Invoke or resume the child; commit outcome, never pause here."""
        config = config or {}
        child_config = _build_child_config(config, node_name)

        # J-1 replay guard: a paused child gets ONLY the resume command,
        # never a re-send of its original input.
        child_paused = False
        try:
            snapshot = compiled.get_state(child_config)
            child_paused = bool(snapshot and snapshot.next)
        except (AttributeError, NotImplementedError, ValueError):
            child_paused = False

        if child_paused:
            child_output = compiled.invoke(
                Command(resume=state.get(resume_key)), child_config
            )
        else:
            child_input = _map_input_state(state, input_mapping)
            child_output = compiled.invoke(child_input, child_config)

        if isinstance(child_output, dict) and "__interrupt__" in child_output:
            payload = _interrupt_payload(child_output["__interrupt__"])
            updates = (
                _map_output_state(child_output, interrupt_output_mapping)
                if interrupt_output_mapping
                else {}
            )
            updates[paused_key] = True
            updates[payload_key] = payload
        else:
            updates = _map_output_state(child_output, output_mapping)
            updates[paused_key] = False

        updates["current_step"] = node_name
        return updates

    def pause_fn(state: dict) -> dict:
        """Perform the parent-native pause; relay the resume value."""
        from langgraph.types import interrupt

        resume_value = interrupt(state.get(f"__{node_name}_payload__"))
        return {resume_key: resume_value, "current_step": node_name}

    run_fn.__name__ = f"{node_name}__run"
    pause_fn.__name__ = f"{node_name}__pause"
    return run_fn, pause_fn


def _interrupt_payload(interrupts: Any) -> Any:
    """Extract the human-facing payload from a child __interrupt__ value."""
    if isinstance(interrupts, list | tuple) and interrupts:
        first = interrupts[0]
        return getattr(first, "value", first)
    return interrupts
