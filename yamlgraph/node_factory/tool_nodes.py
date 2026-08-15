"""Tool call node factory.

Creates LangGraph nodes that dynamically invoke tools from state.
"""

import json
import logging
from collections.abc import Callable
from typing import Any

from yamlgraph.node_factory.base import GraphState
from yamlgraph.utils.expressions import resolve_node_variables, resolve_template

logger = logging.getLogger(__name__)


def _envelope(
    task_id: Any, tool_name: str, *, result: Any = None, error: str | None = None
) -> dict:
    """Tool response structure: error is nested here, not state-level."""
    return {
        "task_id": task_id,
        "tool": tool_name,
        "success": error is None,
        "result": result,
        "error": error,
    }


def _parse_output(result: Any, parsed_key: str) -> tuple[dict | None, str | None]:
    """FR-810: dict passes through; JSON-object string parses; else fail."""
    if isinstance(result, dict):
        return result, None
    if isinstance(result, str):
        try:
            parsed = json.loads(result)
        except (json.JSONDecodeError, ValueError):
            return None, f"parsed_key '{parsed_key}': output is not valid JSON"
        if isinstance(parsed, dict):
            return parsed, None
        return None, (
            f"parsed_key '{parsed_key}': JSON output is "
            f"{type(parsed).__name__}, expected object"
        )
    return None, (
        f"parsed_key '{parsed_key}': output is "
        f"{type(result).__name__}, expected dict or JSON-object string"
    )


def _resolve_tool_args(node_name: str, args_expr: Any, state: dict) -> dict:
    """Resolve tool args: inline mapping (FR-772) or whole-dict expression."""
    if isinstance(args_expr, dict):
        if not args_expr:
            return {}  # never fall back to whole-state passing
        resolved = resolve_node_variables(args_expr, state)
        for key, value in resolved.items():
            if isinstance(value, str) and "{state." in value:
                raise ValueError(
                    f"tool_call node '{node_name}': arg '{key}' did not "
                    f"fully resolve: {value!r}"
                )
        return resolved
    # Existing string form: whole dict from state
    args = resolve_template(args_expr, state)
    return args if isinstance(args, dict) else {}


def create_tool_call_node(
    node_name: str,
    node_config: dict[str, Any],
    tools_registry: dict[str, Callable],
    graph_tool_names: set[str] | None = None,
) -> Callable[[GraphState], dict]:
    """Create a node that dynamically calls a tool from state.

    This enables YAML-driven tool execution where tool name and args
    are resolved from state at runtime.

    Args:
        node_name: Name of the node
        node_config: Node configuration with 'tool', 'args', 'state_key'
            and optional 'parsed_key' (FR-810)
        tools_registry: Dict mapping tool names to callable functions
        graph_tool_names: Names of graph-runtime tools; 'parsed_key' is
            valid only for these (FR-810)

    Returns:
        Node function compatible with LangGraph
    """
    tool_expr = node_config["tool"]  # e.g., "{state.task.tool}"
    args_expr = node_config["args"]  # inline mapping OR "{state.task.args}"
    state_key = node_config.get("state_key", "result")
    # FR-810: expose parsed graph-tool output under a routable state key
    parsed_key = node_config.get("parsed_key")
    graph_tool_names = graph_tool_names or set()
    # FR-778: skip = failure envelope (default), fail = raise at the node
    on_error = node_config.get("on_error", "skip")

    def _fail(tool_name: str, error: str, cause: Exception | None = None) -> None:
        raise ValueError(
            f"tool_call node '{node_name}': tool '{tool_name}' failed: {error}"
        ) from cause

    def _failure_update(task_id: Any, tool_name: str, error: str) -> dict:
        if on_error == "fail":
            _fail(tool_name, error)
        return {
            state_key: _envelope(task_id, tool_name, error=error),
            "current_step": node_name,
        }

    def node_fn(state: dict) -> dict:
        # Resolve tool name and args from state
        tool_name = resolve_template(tool_expr, state)
        args = _resolve_tool_args(node_name, args_expr, state)

        # Extract task_id if available
        task = state.get("task", {})
        task_id = task.get("id") if isinstance(task, dict) else None

        # Look up tool in registry
        tool_func = tools_registry.get(tool_name)
        if tool_func is None:
            return _failure_update(task_id, tool_name, f"Unknown tool: {tool_name}")

        # FR-810: parsed_key is a graph-runtime tool contract — reject
        # dynamically resolved non-graph tools before execution
        if parsed_key and tool_name not in graph_tool_names:
            return _failure_update(
                task_id,
                tool_name,
                f"parsed_key '{parsed_key}' requires a graph-runtime tool; "
                f"'{tool_name}' is not one",
            )

        # Execute tool
        try:
            result = tool_func(**args)
        except Exception as e:
            if on_error == "fail":
                _fail(tool_name, str(e), cause=e)
            return {
                state_key: _envelope(task_id, tool_name, error=str(e)),
                "current_step": node_name,
            }

        update = {
            state_key: _envelope(task_id, tool_name, result=result),
            "current_step": node_name,
        }
        if parsed_key:
            parsed, parse_error = _parse_output(result, parsed_key)
            if parse_error:
                if on_error == "fail":
                    _fail(tool_name, parse_error)
                update[state_key]["success"] = False
                update[state_key]["error"] = parse_error
            else:
                update[parsed_key] = parsed
        return update

    node_fn.__name__ = f"{node_name}_tool_call"
    return node_fn
