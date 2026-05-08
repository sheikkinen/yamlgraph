"""Shared graph discovery for protocol servers (MCP, A2A).

Extracted from mcp_server.py (Phase 0 of FR-208) so both MCP and A2A
servers share the same discovery logic.

FR-291 / CAP-136: Per-graph typed MCP tools — adds input_vars, tool_name,
and input_schema derivation from graph YAML state block.
"""

from __future__ import annotations

import glob
import logging
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


def _split_top_level_args(text: str) -> list[str]:
    """Split comma-separated generic args while respecting nested brackets."""
    parts: list[str] = []
    current: list[str] = []
    depth = 0

    for ch in text:
        if ch == "[":
            depth += 1
        elif ch == "]" and depth > 0:
            depth -= 1

        if ch == "," and depth == 0:
            part = "".join(current).strip()
            if part:
                parts.append(part)
            current = []
            continue

        current.append(ch)

    tail = "".join(current).strip()
    if tail:
        parts.append(tail)
    return parts


def _parse_yaml_type(type_str: str) -> tuple[str, list[str]]:
    """Parse a YAML type into base type and optional generic args."""
    text = type_str.strip()
    if "[" not in text or not text.endswith("]"):
        return text, []
    base, arg_text = text.split("[", maxsplit=1)
    return base.strip(), _split_top_level_args(arg_text[:-1])


def _state_type_string(type_val: str | dict | Any) -> str:
    """Normalize state value into a type annotation string."""
    if isinstance(type_val, dict):
        type_str = type_val.get("type", "str")
        return type_str if isinstance(type_str, str) else "str"
    if isinstance(type_val, str):
        return type_val
    return "str"


def _yaml_type_to_json_schema(type_str: str) -> str:
    """Map a YAML state type annotation to a JSON Schema type.

    Parameterized types (e.g. ``list[str]``) map to the base type.
    Unknown types fall back to ``"string"``.

    Args:
        type_str: Type annotation string from graph YAML state block.

    Returns:
        JSON Schema type string.
    """
    base, _ = _parse_yaml_type(type_str)
    return _TYPE_MAP.get(base, "string")


def _build_property_schema(type_str: str) -> dict[str, Any]:
    """Build a JSON Schema property from a YAML state type annotation."""
    json_type = _yaml_type_to_json_schema(type_str)
    schema: dict[str, Any] = {"type": json_type}
    _, params = _parse_yaml_type(type_str)

    if json_type == "array":
        item_type = params[0] if params else "str"
        schema["items"] = {"type": _yaml_type_to_json_schema(item_type)}
    elif json_type == "object":
        value_type = params[1] if len(params) >= 2 else "str"
        schema["additionalProperties"] = {"type": _yaml_type_to_json_schema(value_type)}

    return schema


def _extract_output_state_keys(nodes: dict[str, Any]) -> set[str]:
    """Extract state keys that are outputs from node config."""
    output_keys: set[str] = set()

    for node in nodes.values():
        if not isinstance(node, dict):
            continue

        state_key = node.get("state_key")
        if isinstance(state_key, str):
            output_keys.add(state_key)

        collect = node.get("collect")
        if isinstance(collect, str):
            output_keys.add(collect)
        elif isinstance(collect, list):
            output_keys.update(item for item in collect if isinstance(item, str))

    return output_keys


def _extract_input_vars(
    state: dict[str, str | dict], nodes: dict[str, Any]
) -> dict[str, str]:
    """Separate input vars from output vars in the state block.

    REQ-YG-310: Input vars are state keys NOT used as any node's
    ``state_key`` or map-node ``collect`` output.

    Args:
        state: State block from graph YAML (key → type string or dict).
        nodes: Nodes block from graph YAML.

    Returns:
        Dict of input var name → JSON Schema type string.
    """
    state_keys_used_as_output = _extract_output_state_keys(nodes)
    result: dict[str, str] = {}
    for key, type_val in state.items():
        if key in state_keys_used_as_output:
            continue
        type_str = _state_type_string(type_val)
        result[key] = _yaml_type_to_json_schema(type_str)
    return result


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

                # REQ-YG-313: Normalize tool name (hyphens/spaces → underscores)
                tool_name = name.replace("-", "_").replace(" ", "_")

                # REQ-YG-311: Build JSON Schema for MCP inputSchema
                input_schema: dict[str, Any] = {"type": "object", "properties": {}}
                for key in input_vars:
                    type_str = _state_type_string(state.get(key))
                    input_schema["properties"][key] = _build_property_schema(type_str)
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
