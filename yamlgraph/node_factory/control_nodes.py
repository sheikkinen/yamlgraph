"""Control flow node factories.

Creates interrupt and passthrough nodes for flow control.
"""

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from yamlgraph.executor_base import format_prompt
from yamlgraph.node_factory.base import GraphState

logger = logging.getLogger(__name__)


def create_interrupt_node(
    node_name: str,
    config: dict[str, Any],
    graph_path: Path | None = None,
    prompts_dir: Path | None = None,
    prompts_relative: bool = False,
) -> tuple[Callable[[GraphState], dict], Callable[[GraphState], dict]]:
    """Create an interrupt node split into prepare + interrupt functions.

    FR-060: The prepare function commits payload to state BEFORE
    interrupt() fires, so state_key holds the payload even when
    GraphInterrupt is raised.

    Args:
        node_name: Name of the node
        config: Node configuration with optional keys:
            - message: Static interrupt payload (string or dict)
            - prompt: Prompt name to generate dynamic payload
            - state_key: Where to store payload (default: "interrupt_message")
            - resume_key: Where to store resume value (default: "user_input")
        graph_path: Path to graph file for relative prompt resolution
        prompts_dir: Explicit prompts directory override
        prompts_relative: If True, resolve prompts relative to graph_path

    Returns:
        Tuple of (prepare_fn, interrupt_fn) — both compatible with LangGraph
    """
    from yamlgraph.executor import execute_prompt

    message = config.get("message")
    prompt_name = config.get("prompt")
    state_key = config.get("state_key", "interrupt_message")
    resume_key = config.get("resume_key", "user_input")
    idempotent = config.get("idempotent", True)

    def prepare_fn(state: dict) -> dict:
        """Compute and commit payload to state before interrupt fires."""
        existing_payload = state.get(state_key)

        if idempotent and existing_payload is not None:
            payload = existing_payload
        elif prompt_name:
            payload = execute_prompt(
                prompt_name,
                variables=state,
                graph_path=graph_path,
                prompts_dir=prompts_dir,
                prompts_relative=prompts_relative,
                state=state,
            )
        elif message is not None:
            has_template = (
                "{{" in message
                or "{%" in message
                or ("{" in message and "}" in message)
            )
            payload = format_prompt(message, state, state) if has_template else message
        else:
            payload = {"node": node_name}

        return {
            state_key: payload,
            "current_step": node_name,
        }

    def interrupt_fn(state: dict) -> dict:
        """Read committed payload from state and call interrupt()."""
        from langgraph.types import interrupt

        payload = state.get(state_key)
        response = interrupt(payload)
        return {
            resume_key: response,
            "current_step": node_name,
        }

    prepare_fn.__name__ = f"{node_name}_prepare"
    interrupt_fn.__name__ = f"{node_name}_interrupt"
    return (prepare_fn, interrupt_fn)


def create_passthrough_node(
    node_name: str,
    config: dict[str, Any],
) -> Callable[[GraphState], dict]:
    """Create a passthrough node that transforms state without external calls.

    Useful for:
    - Loop counters (increment values)
    - State accumulation (append to lists)
    - Simple data transformations
    - Clean transition points in graphs

    Args:
        node_name: Name of the node
        config: Node configuration with:
            - output: Dict of state_key -> expression mappings
                      Expressions use {state.field} syntax
                      Supports arithmetic: {state.count + 1}
                      Supports list append: {state.history + [state.current]}

    Returns:
        Node function compatible with LangGraph

    Example:
        ```yaml
        next_turn:
          type: passthrough
          output:
            turn_number: "{state.turn_number + 1}"
            history: "{state.history + [state.narration]}"
        ```
    """
    from yamlgraph.utils.expressions import resolve_template

    output_templates = config.get("output", {})
    loop_limit = config.get("loop_limit")

    def passthrough_fn(state: dict) -> dict:
        # FR-027: Check loop limit (same pattern as LLM nodes)
        from yamlgraph.error_handlers import check_loop_limit

        loop_counts = dict(state.get("_loop_counts") or {})
        current_count = loop_counts.get(node_name, 0)

        if check_loop_limit(node_name, loop_limit, current_count):
            return {"_loop_limit_reached": True, "current_step": node_name}

        loop_counts[node_name] = current_count + 1

        result = {"current_step": node_name, "_loop_counts": loop_counts}

        for key, template in output_templates.items():
            try:
                resolved = resolve_template(template, state)
                # If resolution failed (None) and key exists in state, keep original
                if resolved is None and key in state:
                    result[key] = state[key]
                else:
                    result[key] = resolved
            except Exception as e:
                logger.warning(
                    f"Passthrough node {node_name}: failed to resolve {key}: {e}"
                )
                # Keep original value on error
                if key in state:
                    result[key] = state[key]

        logger.info(f"Node {node_name} completed successfully")
        return result

    passthrough_fn.__name__ = f"{node_name}_passthrough"
    return passthrough_fn
