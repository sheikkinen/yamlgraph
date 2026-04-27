"""Shared graph discovery for protocol servers (MCP, A2A).

Extracted from mcp_server.py (Phase 0 of FR-208) so both MCP and A2A
servers share the same discovery logic.

FR-291 / CAP-136: Per-graph typed MCP tools — adds input_vars, tool_name,
and input_schema derivation from graph YAML state block.
"""

from __future__ import annotations

import glob
import logging
import re
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# Default graph scan patterns (relative to project root)
DEFAULT_GRAPH_PATTERNS = [
    "examples/demos/*/*.yaml",
    "examples/*/*.yaml",
]

# REQ-YG-311: YAML type → JSON Schema type mapping
_TYPE_MAP: dict[str, str] = {
    "str": "string",
    "int": "integer",
    "float": "number",
    "bool": "boolean",
    "list": "array",
    "dict": "object",
}


def _yaml_type_to_json_schema(type_str: str) -> str:
    """Map a YAML state type annotation to a JSON Schema type.

    Parameterized types (e.g. ``list[str]``) map to the base type.
    Unknown types fall back to ``"string"``.

    Args:
        type_str: Type annotation string from graph YAML state block.

    Returns:
        JSON Schema type string.
    """
    # Strip parameterization: list[str] → list, dict[str, int] → dict
    base = re.split(r"\[", type_str, maxsplit=1)[0].strip()
    return _TYPE_MAP.get(base, "string")


def _extract_input_vars(
    state: dict[str, str],
    nodes: dict[str, Any],
) -> dict[str, str]:
    """Separate input vars from output vars in the state block.

    REQ-YG-310: Input vars are state keys NOT used as any node's
    ``state_key``. Output vars (state_key targets) are excluded.

    Args:
        state: State block from graph YAML (key → type string).
        nodes: Nodes block from graph YAML.

    Returns:
        Dict of input var name → JSON Schema type string.
    """
    state_keys_used_as_output = {
        node.get("state_key")
        for node in nodes.values()
        if isinstance(node, dict) and "state_key" in node
    }
    return {
        key: _yaml_type_to_json_schema(type_str)
        for key, type_str in state.items()
        if key not in state_keys_used_as_output
    }


def discover_graphs(patterns: list[str]) -> list[dict[str, Any]]:
    """Scan directories for graph YAML files and parse headers.

    A YAML file is considered a graph if it contains a ``nodes`` key.
    This allows discovery of non-standard filenames (e.g. ``pipeline.yaml``,
    ``drill-down.yaml``) while excluding prompt templates.

    Args:
        patterns: Glob patterns to scan for YAML files.

    Returns:
        List of dicts with keys: name, description, path, required_vars,
        input_vars, tool_name, input_schema.
    """
    graphs: list[dict[str, Any]] = []
    seen_paths: set[str] = set()

    for pattern in patterns:
        for path_str in sorted(glob.glob(pattern, recursive=True)):
            real = str(Path(path_str).resolve())
            if real in seen_paths:
                continue
            seen_paths.add(real)

            try:
                with open(path_str) as f:
                    config = yaml.safe_load(f)
                if not isinstance(config, dict):
                    continue

                # Only include files that look like graphs (have nodes)
                if "nodes" not in config:
                    continue

                name = config.get("name", Path(path_str).parent.name)
                description = config.get("description", "")
                state = config.get("state", {})
                nodes = config.get("nodes", {})
                required_vars = list(state.keys()) if isinstance(state, dict) else []

                # REQ-YG-310/311: Derive typed input vars
                input_vars = (
                    _extract_input_vars(state, nodes) if isinstance(state, dict) else {}
                )

                # REQ-YG-313: Normalize tool name
                tool_name = name.replace("-", "_")

                # REQ-YG-311: Build JSON Schema for MCP inputSchema
                input_schema: dict[str, Any] = {
                    "type": "object",
                    "properties": {k: {"type": v} for k, v in input_vars.items()},
                }
                if input_vars:
                    input_schema["required"] = list(input_vars.keys())

                graphs.append(
                    {
                        "name": name,
                        "description": description,
                        "path": str(Path(path_str).resolve()),
                        "required_vars": required_vars,
                        "input_vars": input_vars,
                        "tool_name": tool_name,
                        "input_schema": input_schema,
                    }
                )
            except Exception:
                logger.warning("Failed to parse %s", path_str, exc_info=True)

    return graphs
