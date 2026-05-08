#!/usr/bin/env python3
"""YAMLGraph MCP Server — expose graphs as Copilot/MCP tools.

CAP-19: MCP Server Interface (REQ-YG-066, REQ-YG-067, REQ-YG-068)
CAP-136: Per-graph typed MCP tools (REQ-YG-310–314)

Usage (stdio transport):
    python yamlgraph/mcp_server.py

Configure in .mcp.json:
    {
      "mcpServers": {
        "yamlgraph": {
          "command": ".venv/bin/python3",
          "args": ["yamlgraph/mcp_server.py"]
        }
      }
    }
"""

from __future__ import annotations

import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

try:
    import mcp.server.stdio
    import mcp.types as types
    from mcp.server import Server
    from mcp.server.lowlevel.server import NotificationOptions
    from mcp.server.models import InitializationOptions
except ImportError as exc:
    raise ImportError(
        "MCP SDK not installed. Install with: pip install yamlgraph[mcp]"
    ) from exc

from yamlgraph.discovery import DEFAULT_GRAPH_PATTERNS, discover_graphs

logger = logging.getLogger(__name__)

# Default timeout for graph invocation (seconds)
INVOKE_TIMEOUT = 120

# Thread pool for blocking graph invocations
_executor = ThreadPoolExecutor(max_workers=1)


def _validate_input_schema(input_schema: dict[str, Any]) -> list[str]:
    """Validate minimal JSON Schema quality required by MCP typed tools."""
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
        return errors

    for required_key in required:
        if required_key not in properties:
            errors.append(f"required key '{required_key}' missing from properties")

    return errors


def _partition_graphs_by_schema(
    graphs: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split discovered graphs into valid/invalid typed-tool candidates."""
    valid_graphs: list[dict[str, Any]] = []
    invalid_graphs: list[dict[str, Any]] = []

    for graph in graphs:
        errors = _validate_input_schema(graph["input_schema"])
        if errors:
            logger.warning(
                "Excluding graph '%s' from MCP typed tools: %s",
                graph["name"],
                "; ".join(errors),
            )
            invalid_graphs.append(graph)
            continue
        valid_graphs.append(graph)

    return valid_graphs, invalid_graphs


# ---------------------------------------------------------------------------
# REQ-YG-068: Graph invocation
# ---------------------------------------------------------------------------


def _invoke_graph(graph_path: str, variables: dict[str, Any]) -> dict[str, Any]:
    """Load, compile, and invoke a graph synchronously.

    Delegates to graph_loader.invoke_graph (FR-255).

    Args:
        graph_path: Absolute path to graph.yaml.
        variables: Input variables for the graph.

    Returns:
        Result dict from graph invocation.
    """
    from yamlgraph.graph_loader import invoke_graph

    return invoke_graph(graph_path, variables)


# ---------------------------------------------------------------------------
# REQ-YG-066: MCP server with stdio transport
# ---------------------------------------------------------------------------


def create_server(
    graph_patterns: list[str] | None = None,
) -> Server:
    """Create and configure the MCP server.

    Args:
        graph_patterns: Glob patterns for graph discovery.
            Defaults to DEFAULT_GRAPH_PATTERNS.

    Returns:
        Configured MCP Server instance.
    """
    if graph_patterns is None:
        graph_patterns = DEFAULT_GRAPH_PATTERNS

    graphs = discover_graphs(graph_patterns)
    valid_typed_graphs, _ = _partition_graphs_by_schema(graphs)
    graph_lookup: dict[str, dict[str, Any]] = {g["name"]: g for g in graphs}

    # REQ-YG-314: Collision detection — tool_name must be unique
    tool_name_to_graph: dict[str, str] = {}
    for g in valid_typed_graphs:
        tool_name = g["tool_name"]
        if tool_name in tool_name_to_graph:
            raise ValueError(
                f"Tool name collision: '{tool_name}' used by both "
                f"'{tool_name_to_graph[tool_name]}' and '{g['name']}'"
            )
        tool_name_to_graph[tool_name] = g["name"]

    # REQ-YG-312: Build per-graph tool lookup (tool_name → graph info)
    typed_tool_lookup: dict[str, dict[str, Any]] = {
        g["tool_name"]: g for g in valid_typed_graphs
    }

    server = Server("yamlgraph")

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """List generic tools and per-graph typed tools."""
        tools = [
            types.Tool(
                name="yamlgraph_list_graphs",
                description=(
                    "List available YAMLGraph graphs with descriptions "
                    "and required variables."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            types.Tool(
                name="yamlgraph_run_graph",
                description=(
                    "Run a YAMLGraph pipeline by name. Pass variables "
                    "required by the graph."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "graph": {
                            "type": "string",
                            "description": ("Graph name (from yamlgraph_list_graphs)"),
                        },
                        "vars": {
                            "type": "object",
                            "description": "Input variables for the graph",
                            "additionalProperties": {"type": "string"},
                        },
                    },
                    "required": ["graph"],
                },
            ),
        ]

        # REQ-YG-312: Per-graph typed tools
        for g in valid_typed_graphs:
            tools.append(
                types.Tool(
                    name=g["tool_name"],
                    description=g["description"],
                    inputSchema=g["input_schema"],
                )
            )

        return tools

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict[str, Any]
    ) -> list[types.TextContent]:
        """Route tool calls to handlers."""
        try:
            if name == "yamlgraph_list_graphs":
                return _handle_list_graphs(graphs)
            elif name == "yamlgraph_run_graph":
                return await _handle_run_graph(arguments, graph_lookup, server)
            elif name in typed_tool_lookup:
                # REQ-YG-312: Per-graph typed tool → delegate to run_graph
                graph_info = typed_tool_lookup[name]
                run_args = {"graph": graph_info["name"], "vars": arguments}
                return await _handle_run_graph(run_args, graph_lookup, server)
            else:
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps({"error": f"Unknown tool: {name}"}),
                    )
                ]
        except Exception as e:
            logger.error("Tool %s failed: %s", name, e, exc_info=True)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps({"error": str(e)}),
                )
            ]

    return server


def _handle_list_graphs(
    graphs: list[dict[str, Any]],
) -> list[types.TextContent]:
    """Return graph list as JSON."""
    summary = [
        {
            "name": g["name"],
            "description": g["description"],
            "required_vars": g["required_vars"],
        }
        for g in graphs
    ]
    return [types.TextContent(type="text", text=json.dumps(summary, indent=2))]


async def _handle_run_graph(
    arguments: dict[str, Any],
    graph_lookup: dict[str, dict[str, Any]],
    server: Server | None = None,
) -> list[types.TextContent]:
    """Invoke a graph and return result as JSON."""
    graph_name = arguments.get("graph", "")
    variables = arguments.get("vars", {})

    if graph_name not in graph_lookup:
        available = list(graph_lookup.keys())
        return [
            types.TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": f"Graph '{graph_name}' not found",
                        "available": available,
                    }
                ),
            )
        ]

    graph_info = graph_lookup[graph_name]
    graph_path = graph_info["path"]

    loop = asyncio.get_event_loop()

    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(_executor, _invoke_graph, graph_path, variables),
            timeout=INVOKE_TIMEOUT,
        )
    except TimeoutError:
        return [
            types.TextContent(
                type="text",
                text=json.dumps(
                    {"error": f"Graph '{graph_name}' timed out after {INVOKE_TIMEOUT}s"}
                ),
            )
        ]
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=json.dumps({"error": f"Graph execution failed: {e}"}),
            )
        ]

    # Serialize result — filter non-serializable values
    serializable = {}
    for k, v in result.items():
        try:
            json.dumps(v)
            serializable[k] = v
        except (TypeError, ValueError):
            serializable[k] = str(v)

    return [types.TextContent(type="text", text=json.dumps(serializable, indent=2))]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


async def main() -> None:
    """Run the MCP server with stdio transport."""
    import sys

    # Accept --patterns arg or fall back to defaults
    if "--patterns" in sys.argv:
        idx = sys.argv.index("--patterns")
        patterns = sys.argv[idx + 1 :]
    else:
        project_root = Path(__file__).resolve().parent.parent
        patterns = [str(project_root / p) for p in DEFAULT_GRAPH_PATTERNS]

    server = create_server(graph_patterns=patterns)

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="yamlgraph",
                server_version="0.4.39",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
