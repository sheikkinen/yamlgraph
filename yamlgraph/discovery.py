"""Shared graph discovery for graph-listing consumers.

Extracted from the former protocol server (Phase 0 of FR-208) so every
consumer shares the same discovery logic.

FR-291: adds input_vars, tool_name, and input_schema derivation from the
graph YAML state block, consumed by the skill exporter.
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


def _yaml_type_to_json_schema(type_str: str) -> dict[str, Any]:
    """Map a YAML state type annotation to a JSON Schema property dict.

    Parameterized types (e.g. ``list[str]``) extract element types.
    Array types always include ``items``; defaults to ``{"type": "string"}``.
    Unknown types fall back to ``"string"``.

    Args:
        type_str: Type annotation string from graph YAML state block.

    Returns:
        JSON Schema property dict (e.g. ``{"type": "array", "items": {"type": "string"}}``).
    """
    # Split parameterization: list[str] → ("list", "str]")
    parts = re.split(r"\[", type_str, maxsplit=1)
    base = parts[0].strip()
    params_str = parts[1].rstrip("]") if len(parts) > 1 else ""
    params = (
        [p.strip() for p in params_str.split(",") if p.strip()] if params_str else []
    )
    json_type = _TYPE_MAP.get(base, "string")

    schema: dict[str, Any] = {"type": json_type}

    if json_type == "array":
        item_type = params[0] if params else "str"
        schema["items"] = _yaml_type_to_json_schema(item_type)
    elif json_type == "object":
        if len(params) >= 2:
            value_type = params[1]
            schema["additionalProperties"] = _yaml_type_to_json_schema(value_type)
        else:
            schema["additionalProperties"] = True

    return schema


def _extract_output_state_keys(nodes: dict[str, Any]) -> set[str | None]:
    """Extract state keys used as node outputs (state_key or collect targets)."""
    state_keys_used_as_output: set[str | None] = set()
    for node in nodes.values():
        if not isinstance(node, dict):
            continue
        if "state_key" in node:
            state_keys_used_as_output.add(node["state_key"])
        # Map nodes write to their ``collect`` target, not ``state_key``
        if "collect" in node:
            state_keys_used_as_output.add(node["collect"])
    return state_keys_used_as_output


def _state_type_string(type_val: str | dict | Any) -> str:
    """Extract the type string from a state value (string or dict with 'type' key)."""
    if isinstance(type_val, dict):
        return type_val.get("type", "str")
    if isinstance(type_val, str):
        return type_val
    return "str"


def _build_property_schema(type_str: str) -> dict[str, Any]:
    """Build a JSON Schema property dict from a YAML type string."""
    return _yaml_type_to_json_schema(type_str)


def _extract_input_vars(
    state: dict[str, str | dict], nodes: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    """Separate input vars from output vars in the state block.

    REQ-YG-310: Input vars are state keys NOT used as any node's
    ``state_key``. Output vars (state_key targets) are excluded.

    Args:
        state: State block from graph YAML (key → type string or dict).
        nodes: Nodes block from graph YAML.

    Returns:
        Dict of input var name → JSON Schema property dict.
    """
    state_keys_used_as_output = _extract_output_state_keys(nodes)
    result: dict[str, dict[str, Any]] = {}
    for key, type_val in state.items():
        if key in state_keys_used_as_output:
            continue
        type_str = _state_type_string(type_val)
        result[key] = _build_property_schema(type_str)
    return result


def _validate_json_schema(schema: dict[str, Any], tool_name: str) -> None:
    """Validate a JSON Schema has ``items`` for every array type.

    MCP clients (VS Code Copilot) reject tool schemas where an array
    property lacks ``items``.  This guard prevents broken schemas from
    reaching the wire.

    Args:
        schema: JSON Schema dict to validate.
        tool_name: Tool name for error reporting.

    Raises:
        ValueError: If any array property is missing ``items``.
    """

    def _check(obj: Any, path: str) -> None:
        if isinstance(obj, dict):
            if obj.get("type") == "array" and "items" not in obj:
                raise ValueError(
                    f"Tool '{tool_name}': array at '{path}' missing 'items'. "
                    f"MCP clients require items for array types."
                )
            for k, v in obj.items():
                _check(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                _check(v, f"{path}[{i}]")

    _check(schema, "inputSchema")


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
                input_schema: dict[str, Any] = {
                    "type": "object",
                    "properties": dict(input_vars),
                }
                if input_vars:
                    input_schema["required"] = list(input_vars.keys())

                # Guard: validate schema before serving to MCP clients
                _validate_json_schema(input_schema, tool_name)

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
