"""CLI helper utilities.

Shared functions for CLI commands to reduce boilerplate.
"""

from pathlib import Path
from typing import Any

import yaml


class GraphLoadError(Exception):
    """Error loading or parsing graph YAML file."""

    pass


def load_graph_config(path: str | Path) -> dict[str, Any] | None:
    """Load and parse a graph YAML file.

    Centralizes the common CLI pattern of:
    - Checking if file exists
    - Loading YAML content
    - Standardized error handling

    Args:
        path: Path to the graph YAML file (string or Path)

    Returns:
        Parsed YAML dict, or None if file is empty

    Raises:
        GraphLoadError: If file not found or invalid YAML
    """
    path = Path(path)

    if not path.exists():
        raise GraphLoadError(f"Graph file not found: {path}")

    try:
        with open(path) as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise GraphLoadError(f"Invalid YAML in {path}: {e}") from e


__all__ = ["load_graph_config", "GraphLoadError"]
