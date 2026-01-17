"""Expression resolution utilities for YAML graphs."""

from typing import Any


def resolve_state_expression(expr: str | Any, state: dict[str, Any]) -> Any:
    """Resolve {state.path.to.value} expressions.

    Supports expressions like:
        - "{name}" -> state["name"]
        - "{state.story.panels}" -> state["story"]["panels"]
        - "{story.title}" -> state["story"]["title"]

    Non-expression values (no braces) pass through unchanged.

    Args:
        expr: Expression string like "{state.story.panels}" or any value
        state: Current graph state dict

    Returns:
        Resolved value from state, or original value if not an expression

    Raises:
        KeyError: If path cannot be resolved in state
    """
    if not isinstance(expr, str):
        return expr

    if not (expr.startswith("{") and expr.endswith("}")):
        return expr

    path = expr[1:-1]  # Remove braces

    # Handle "state." prefix (optional)
    if path.startswith("state."):
        path = path[6:]  # Remove "state."

    # Navigate nested path
    value = state
    for key in path.split("."):
        if isinstance(value, dict) and key in value:
            value = value[key]
        elif hasattr(value, key):
            # Support object attribute access (Pydantic models, etc.)
            value = getattr(value, key)
        else:
            raise KeyError(f"Cannot resolve '{key}' in path '{expr}'")

    return value
