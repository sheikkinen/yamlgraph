"""RED acceptance tests for FR-355 MCP startup schema validation gate."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

# Guard: mcp is an optional dependency
mcp = pytest.importorskip("mcp")
from mcp import types  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]


def _validate_input_schema(input_schema: dict) -> list[str]:
    """Return schema validation errors for MCP input schema."""
    errors: list[str] = []

    properties = input_schema.get("properties", {})
    if not isinstance(properties, dict):
        return ["input_schema.properties must be an object"]

    for key, prop in properties.items():
        if not isinstance(prop, dict):
            errors.append(f"{key}: property schema must be an object")
            continue

        schema_type = prop.get("type")
        if schema_type == "array" and "items" not in prop:
            errors.append(f"{key}: array type must include items")
        if schema_type == "object" and not (
            "properties" in prop or "additionalProperties" in prop
        ):
            errors.append(
                f"{key}: object type should include properties or additionalProperties"
            )

    required = input_schema.get("required", [])
    if not isinstance(required, list):
        errors.append("input_schema.required must be a list when present")
    else:
        for req_key in required:
            if req_key not in properties:
                errors.append(f"required key '{req_key}' missing from properties")

    return errors


async def _call_list_tools(server):
    """Invoke list_tools MCP handler and return tool list."""
    handler = server.request_handlers[types.ListToolsRequest]
    req = types.ListToolsRequest(method="tools/list")
    result = await handler(req)
    return result.root.tools


@pytest.mark.req("REQ-YG-311")
def test_all_discovered_schemas_valid() -> None:
    """All discovered default-pattern graphs should have valid input schema."""
    from yamlgraph.discovery import DEFAULT_GRAPH_PATTERNS, discover_graphs

    patterns = [str(REPO_ROOT / p) for p in DEFAULT_GRAPH_PATTERNS]
    graphs = discover_graphs(patterns)

    invalid: dict[str, list[str]] = {}
    for graph in graphs:
        errs = _validate_input_schema(graph["input_schema"])
        if errs:
            invalid[graph["name"]] = errs

    assert not invalid, f"Discovered invalid input_schema values: {invalid}"


@pytest.mark.req("REQ-YG-312")
@pytest.mark.asyncio
async def test_array_without_items_excluded(tmp_path: Path) -> None:
    """Graph with bare array property should be excluded from MCP tool list."""
    from yamlgraph.export.mcp import create_server

    invalid_graph = {
        "name": "invalid-array-tool",
        "description": "Graph with array input missing items",
        "path": str(tmp_path / "invalid-array" / "graph.yaml"),
        "required_vars": ["topic", "tags"],
        "input_vars": {"topic": "string", "tags": "array"},
        "tool_name": "invalid_array_tool",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "tags": {"type": "array"},
            },
            "required": ["topic", "tags"],
        },
    }
    with patch("yamlgraph.export.mcp.discover_graphs", return_value=[invalid_graph]):
        server = create_server(graph_patterns=[])

    tools = await _call_list_tools(server)
    tool_names = {tool.name for tool in tools}

    assert "invalid_array_tool" not in tool_names


@pytest.mark.req("REQ-YG-312")
def test_invalid_schema_exclusion_logs_warning(tmp_path: Path) -> None:
    """Startup logs one warning with graph name and validation reason."""
    from yamlgraph.export.mcp import create_server

    invalid_graph = {
        "name": "invalid-array-warning-tool",
        "description": "Graph with array input missing items",
        "path": str(tmp_path / "invalid-array-warning" / "graph.yaml"),
        "required_vars": ["topic", "tags"],
        "input_vars": {"topic": "string", "tags": "array"},
        "tool_name": "invalid_array_warning_tool",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "tags": {"type": "array"},
            },
            "required": ["topic", "tags"],
        },
    }
    with (
        patch("yamlgraph.export.mcp.discover_graphs", return_value=[invalid_graph]),
        patch("yamlgraph.export.mcp.logger.warning") as warning_mock,
    ):
        create_server(graph_patterns=[])

    warning_mock.assert_called_once()
    warning_args = warning_mock.call_args.args
    assert warning_args[1] == "invalid-array-warning-tool"
    assert "array type must include items" in warning_args[2]


@pytest.mark.req("REQ-YG-310")
def test_collect_keys_excluded_from_inputs(tmp_path: Path) -> None:
    """Map collect targets should be treated as outputs, not required inputs."""
    from yamlgraph.discovery import discover_graphs

    graph_dir = tmp_path / "collect-output"
    graph_dir.mkdir()
    graph_path = graph_dir / "graph.yaml"
    graph_path.write_text(
        'version: "1.0"\n'
        "name: collect-output-graph\n"
        "description: Graph with map collect output\n"
        "state:\n"
        "  topic: str\n"
        "  collected: list\n"
        "nodes:\n"
        "  expand:\n"
        "    type: map\n"
        '    over: "{state.topic}"\n'
        "    as: item\n"
        "    node:\n"
        "      type: llm\n"
        "      prompt: expand\n"
        "      state_key: expanded\n"
        "    collect: collected\n"
        "edges:\n"
        "  - from: START\n"
        "    to: expand\n"
        "  - from: expand\n"
        "    to: END\n"
    )

    graphs = discover_graphs([str(graph_path)])
    assert len(graphs) == 1

    graph = graphs[0]
    assert "collected" not in graph["input_vars"]
    assert "collected" not in graph["input_schema"]["properties"]
    assert "collected" not in graph["input_schema"].get("required", [])
