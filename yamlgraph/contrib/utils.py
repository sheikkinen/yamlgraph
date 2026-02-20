"""Core utilities for YAMLGraph pipelines (FR-044).

Functions extracted from common patterns across 10+ pipelines.
"""

from __future__ import annotations

from typing import Any


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
