"""CLI helper utilities.

Shared functions for CLI commands to reduce boilerplate.
"""

import json
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


def require_graph_config(path: str | Path) -> dict[str, Any]:
    """Load graph config, raising if empty or missing.

    Like load_graph_config but guarantees a non-None return.
    Use this when an empty YAML file is an error condition.

    Args:
        path: Path to the graph YAML file

    Returns:
        Parsed YAML dict (never None)

    Raises:
        GraphLoadError: If file not found, invalid YAML, or empty
    """
    config = load_graph_config(path)
    if config is None:
        raise GraphLoadError(f"Empty YAML file: {path}")
    return config


def parse_vars(var_list: list[str] | None) -> dict[str, Any]:
    """Parse --var key=value arguments into a dict.

    Supports @file syntax: --var content=@file.txt reads file content.
    Only treats value as file path if it starts with @.

    Args:
        var_list: List of "key=value" strings

    Returns:
        Dict mapping keys to values

    Raises:
        ValueError: If a var doesn't contain '='
        FileNotFoundError: If @file path doesn't exist
    """
    if not var_list:
        return {}

    result: dict[str, Any] = {}
    for item in var_list:
        if "=" not in item:
            raise ValueError(f"Invalid var format: '{item}' (expected key=value)")
        key, value = item.split("=", 1)

        # @file syntax: read from file
        if value.startswith("@"):
            file_path = value[1:]
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            result[key] = path.read_text()
        else:
            result[key] = value

    return result


def load_var_file(path: str | None) -> dict[str, Any]:
    """Load variables from YAML or JSON file.

    Args:
        path: Path to var file, or None

    Returns:
        Dict of variables from file, or empty dict if path is None

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not path:
        return {}

    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Var file not found: {path}")

    with open(file_path) as f:
        if path.endswith(".json"):
            return json.load(f)
        return yaml.safe_load(f) or {}


__all__ = [
    "load_graph_config",
    "require_graph_config",
    "GraphLoadError",
    "parse_vars",
    "load_var_file",
]
