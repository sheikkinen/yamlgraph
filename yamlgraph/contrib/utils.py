"""Core utilities for YAMLGraph pipelines (FR-044).

Functions extracted from common patterns across 10+ pipelines.
"""

from __future__ import annotations

from typing import Any


def get_map_result(item: dict | None) -> Any | None:
    """Extract result from map node output.

    Map nodes store results with keys like '_map_<node_name>_sub'.
    This function finds and returns that result without hardcoding the key.

    Args:
        item: A single item from a map node's collected output

    Returns:
        The nested result object (Pydantic model or dict), or None

    Example:
        >>> item = {"_map_generate_sub": {"title": "Hello"}}
        >>> get_map_result(item)
        {'title': 'Hello'}
    """
    if not isinstance(item, dict):
        return None

    for key, value in item.items():
        if key.startswith("_map_") and key.endswith("_sub"):
            return value

    return None


def to_serializable(obj: Any) -> Any:
    """Convert object to JSON-serializable form.

    Recursively converts Pydantic models to dicts. Handles nested structures
    including lists and dicts containing Pydantic models.

    Args:
        obj: Any object (Pydantic model, dict, list, or primitive)

    Returns:
        JSON-serializable version of the object

    Example:
        >>> from pydantic import BaseModel
        >>> class Item(BaseModel):
        ...     name: str
        >>> to_serializable(Item(name="test"))
        {'name': 'test'}
    """
    # Pydantic model -> dict
    if hasattr(obj, "model_dump"):
        return to_serializable(obj.model_dump())

    # Recursively handle lists
    if isinstance(obj, list):
        return [to_serializable(item) for item in obj]

    # Recursively handle dicts
    if isinstance(obj, dict):
        return {key: to_serializable(value) for key, value in obj.items()}

    # Primitives pass through unchanged
    return obj
