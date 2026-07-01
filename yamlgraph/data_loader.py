"""Load external YAML data files into graph state.

This module provides the `data_files` directive functionality, loading
YAML files relative to the graph file at compile time. Supports both
single file paths and glob patterns (e.g. ``wiki/*.yaml``).
"""

from pathlib import Path
from typing import Any

import yaml


class DataFileError(Exception):
    """Error loading a data file."""

    pass


_GLOB_CHARS = {"*", "?", "["}


def _is_glob_pattern(value: str) -> bool:
    """Detect if a data_files value contains glob metacharacters."""
    return any(c in value for c in _GLOB_CHARS)


def _load_glob_pattern(key: str, pattern: str, graph_dir: Path) -> dict[str, Any]:
    """Load all files matching a glob pattern, returning dict keyed by stem.

    Args:
        key: The data_files key (for error messages)
        pattern: Glob pattern relative to graph_dir
        graph_dir: Resolved graph directory

    Returns:
        Dict mapping filename stems to parsed YAML content
    """
    # Reject recursive globs
    if "**" in pattern:
        raise DataFileError(
            f"data_files[{key}]: Recursive glob patterns ('**') are not supported.\n"
            f"  Pattern: {pattern}\n"
            f"  Hint: Use a flat pattern like 'wiki/*.yaml' instead"
        )

    # Security: verify the pattern's base directory is within graph_dir
    # Split pattern into directory part and glob part
    pattern_path = Path(pattern)
    # Find the first component with glob chars to determine the base
    parts = pattern_path.parts
    base_parts = []
    for part in parts:
        if any(c in part for c in _GLOB_CHARS):
            break
        base_parts.append(part)

    if base_parts:
        base_dir = (graph_dir / Path(*base_parts)).resolve()
        try:
            base_dir.relative_to(graph_dir)
        except ValueError:
            raise DataFileError(
                f"data_files[{key}]: Glob pattern '{pattern}' escapes graph directory.\n"
                f"  Resolved base: {base_dir}\n"
                f"  Must be within: {graph_dir}"
            ) from None

    # Expand glob
    matched: dict[str, Any] = {}
    for file_path in sorted(graph_dir.glob(pattern)):
        resolved = file_path.resolve()

        # Security: each resolved file must be within graph_dir
        try:
            resolved.relative_to(graph_dir)
        except ValueError:
            continue  # silently skip symlinks escaping boundary

        try:
            with open(resolved, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise DataFileError(
                f"data_files[{key}]: Invalid YAML in '{file_path.name}'\n  Error: {e}"
            ) from e

        matched[file_path.stem] = data if data is not None else {}

    return matched


def load_data_files(config: dict, graph_path: Path) -> dict[str, Any]:
    """Load external YAML files into initial state.

    Supports two modes:
    - Single file path: ``schema: schema.yaml`` → loads file content directly
    - Glob pattern: ``wiki: "wiki/*.yaml"`` → loads all matches as dict keyed by stem

    Args:
        config: Graph configuration dict containing optional `data_files` key
        graph_path: Path to the graph YAML file

    Returns:
        Dict mapping state keys to loaded data

    Raises:
        DataFileError: If file not found, path escapes graph directory,
                       or value is not a string path

    Example:
        >>> config = {"data_files": {"schema": "schema.yaml"}}
        >>> data = load_data_files(config, Path("graphs/main.yaml"))
        >>> data["schema"]  # Contents of graphs/schema.yaml
    """
    data_files = config.get("data_files", {})
    if not data_files:
        return {}

    graph_dir = graph_path.parent.resolve()
    loaded: dict[str, Any] = {}

    for key, value in data_files.items():
        if not isinstance(value, str):
            raise DataFileError(
                f"data_files[{key}]: Expected string path, got {type(value).__name__}"
            )

        if _is_glob_pattern(value):
            loaded[key] = _load_glob_pattern(key, value, graph_dir)
            continue

        # Single file mode (existing behavior)
        rel_path = value
        file_path = (graph_dir / rel_path).resolve()

        # Security: prevent path traversal
        try:
            file_path.relative_to(graph_dir)
        except ValueError:
            raise DataFileError(
                f"data_files[{key}]: Path '{rel_path}' escapes graph directory.\n"
                f"  Resolved: {file_path}\n"
                f"  Must be within: {graph_dir}"
            ) from None

        if not file_path.exists():
            raise DataFileError(
                f"data_files[{key}]: File not found\n"
                f"  Path: {file_path}\n"
                f"  Hint: Create the file or check the path in your graph YAML"
            )

        try:
            with open(file_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise DataFileError(
                f"data_files[{key}]: Invalid YAML in '{rel_path}'\n  Error: {e}"
            ) from e

        # Empty files return None from safe_load; normalize to empty dict
        loaded[key] = data if data is not None else {}

    return loaded
