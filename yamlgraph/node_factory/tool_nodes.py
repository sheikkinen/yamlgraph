"""Tool call node factory.

Creates LangGraph nodes that dynamically invoke tools from state.
"""

import logging
from collections.abc import Callable
from typing import Any

from yamlgraph.node_factory.base import GraphState
from yamlgraph.utils.expressions import resolve_template

logger = logging.getLogger(__name__)


def create_tool_call_node(
    node_name: str,
    node_config: dict[str, Any],
    tools_registry: dict[str, Callable],
) -> Callable[[GraphState], dict]:
    """Create a node that dynamically calls a tool from state.

    This enables YAML-driven tool execution where tool name and args
    are resolved from state at runtime.

    Args:
        node_name: Name of the node
        node_config: Node configuration with 'tool', 'args', 'state_key'
        tools_registry: Dict mapping tool names to callable functions

    Returns:
        Node function compatible with LangGraph
    """
    tool_expr = node_config["tool"]  # e.g., "{state.task.tool}"
    args_expr = node_config["args"]  # e.g., "{state.task.args}"
    state_key = node_config.get("state_key", "result")

    def node_fn(state: dict) -> dict:
        # Resolve tool name and args from state
        tool_name = resolve_template(tool_expr, state)
        args = resolve_template(args_expr, state)

        # Extract task_id if available
        task = state.get("task", {})
        task_id = task.get("id") if isinstance(task, dict) else None

        # Look up tool in registry
        tool_func = tools_registry.get(tool_name)
        if tool_func is None:
            return {
                state_key: {
                    "task_id": task_id,
                    "tool": tool_name,
                    "success": False,
                    "result": None,
                    "error": f"Unknown tool: {tool_name}",
                },
                "current_step": node_name,
            }

        # Execute tool
        try:
            # Ensure args is a dict
            if not isinstance(args, dict):
                args = {}
            result = tool_func(**args)
            return {
                state_key: {
                    "task_id": task_id,
                    "tool": tool_name,
                    "success": True,
                    "result": result,
                    "error": None,
                },
                "current_step": node_name,
            }
        except Exception as e:
            return {
                state_key: {
                    "task_id": task_id,
                    "tool": tool_name,
                    "success": False,
                    "result": None,
                    "error": str(e),
                },
                "current_step": node_name,
            }

    node_fn.__name__ = f"{node_name}_tool_call"
    return node_fn
