"""Tests for per-graph typed MCP tools — FR-291 / CAP-136.

TDD red phase: tests for discovery schema derivation, per-graph MCP tools,
name normalization, and collision detection.

REQ-YG-310: Input/output var separation in discovery
REQ-YG-311: JSON Schema derivation from state types
REQ-YG-312: Per-graph MCP tool registration
REQ-YG-313: Tool name normalization (hyphens → underscores)
REQ-YG-314: Name collision detection at startup
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

# Guard: mcp is an optional dependency
mcp = pytest.importorskip("mcp")
from mcp import types  # noqa: E402 (CONF-037)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

GRAPH_WITH_IO = """\
version: "1.0"
name: test-graph
description: A test graph with inputs and outputs
state:
  name: str
  style: str
  greeting: str
nodes:
  greet:
    type: llm
    prompt: greet
    variables:
      name: "{state.name}"
      style: "{state.style}"
    state_key: greeting
edges:
  - from: START
    to: greet
  - from: greet
    to: END
"""

GRAPH_MULTI_TYPE = """\
version: "1.0"
name: multi-type
description: Graph with multiple state types
state:
  topic: str
  depth: int
  temperature: float
  verbose: bool
  tags: list
  options: dict
  result: str
nodes:
  analyze:
    type: llm
    prompt: analyze
    state_key: result
edges:
  - from: START
    to: analyze
  - from: analyze
    to: END
"""

GRAPH_NO_STATE = """\
version: "1.0"
name: stateless
description: Graph with no state block
nodes:
  process:
    type: llm
    prompt: process
    state_key: output
edges:
  - from: START
    to: process
  - from: process
    to: END
"""

GRAPH_PARAMETERIZED = """\
version: "1.0"
name: parameterized
description: Graph with parameterized types
state:
  items: list[str]
  config: dict[str, int]
  output: str
nodes:
  process:
    type: llm
    prompt: process
    state_key: output
edges:
  - from: START
    to: process
  - from: process
    to: END
"""


def _write_graph(tmp_path: Path, name: str, content: str) -> Path:
    """Write a graph YAML to a subdirectory and return the path."""
    graph_dir = tmp_path / name
    graph_dir.mkdir(parents=True, exist_ok=True)
    path = graph_dir / "graph.yaml"
    path.write_text(content)
    return path


async def _call_list_tools(server):
    """Invoke the registered list_tools handler."""
    handler = server.request_handlers[types.ListToolsRequest]
    req = types.ListToolsRequest(method="tools/list")
    result = await handler(req)
    return result.root.tools


async def _call_tool(server, name: str, arguments: dict):
    """Invoke the registered call_tool handler."""
    handler = server.request_handlers[types.CallToolRequest]
    req = types.CallToolRequest(
        method="tools/call",
        params=types.CallToolRequestParams(name=name, arguments=arguments),
    )
    result = await handler(req)
    return result.root.content


# ---------------------------------------------------------------------------
# REQ-YG-310: Input/output var separation in discovery
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-310")
def test_discover_separates_input_from_output(tmp_path: Path):
    """discover_graphs excludes state_key targets from input_vars."""
    from yamlgraph.discovery import discover_graphs

    _write_graph(tmp_path, "demo", GRAPH_WITH_IO)
    graphs = discover_graphs([str(tmp_path / "*/graph.yaml")])

    assert len(graphs) == 1
    g = graphs[0]
    # 'name' and 'style' are inputs (not used as state_key)
    # 'greeting' is output (used as state_key by greet node)
    assert "input_vars" in g
    assert "name" in g["input_vars"]
    assert "style" in g["input_vars"]
    assert "greeting" not in g["input_vars"]


@pytest.mark.req("REQ-YG-310")
def test_discover_no_state_block(tmp_path: Path):
    """Graph without state block has empty input_vars."""
    from yamlgraph.discovery import discover_graphs

    _write_graph(tmp_path, "demo", GRAPH_NO_STATE)
    graphs = discover_graphs([str(tmp_path / "*/graph.yaml")])

    assert len(graphs) == 1
    assert graphs[0]["input_vars"] == {}


@pytest.mark.req("REQ-YG-310")
def test_discover_all_outputs(tmp_path: Path):
    """Graph where every state field is a state_key has empty input_vars."""
    from yamlgraph.discovery import discover_graphs

    yaml_content = """\
version: "1.0"
name: all-outputs
description: Every state field is an output
state:
  result_a: str
  result_b: str
nodes:
  a:
    type: llm
    prompt: a
    state_key: result_a
  b:
    type: llm
    prompt: b
    state_key: result_b
edges:
  - from: START
    to: a
  - from: a
    to: b
  - from: b
    to: END
"""
    _write_graph(tmp_path, "demo", yaml_content)
    graphs = discover_graphs([str(tmp_path / "*/graph.yaml")])

    assert len(graphs) == 1
    assert graphs[0]["input_vars"] == {}


# ---------------------------------------------------------------------------
# REQ-YG-311: JSON Schema derivation from state types
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-311")
def test_discover_input_schema_types(tmp_path: Path):
    """input_vars includes JSON Schema property dicts derived from state type annotations."""
    from yamlgraph.discovery import discover_graphs

    _write_graph(tmp_path, "demo", GRAPH_MULTI_TYPE)
    graphs = discover_graphs([str(tmp_path / "*/graph.yaml")])

    assert len(graphs) == 1
    iv = graphs[0]["input_vars"]
    assert iv["topic"] == {"type": "string"}
    assert iv["depth"] == {"type": "integer"}
    assert iv["temperature"] == {"type": "number"}
    assert iv["verbose"] == {"type": "boolean"}
    assert iv["tags"] == {"type": "array", "items": {"type": "string"}}
    assert iv["options"] == {"type": "object", "additionalProperties": True}
    # 'result' is a state_key output — excluded
    assert "result" not in iv


@pytest.mark.req("REQ-YG-311")
def test_discover_parameterized_types(tmp_path: Path):
    """Parameterized types like list[str] extract element type for items."""
    from yamlgraph.discovery import discover_graphs

    _write_graph(tmp_path, "demo", GRAPH_PARAMETERIZED)
    graphs = discover_graphs([str(tmp_path / "*/graph.yaml")])

    assert len(graphs) == 1
    iv = graphs[0]["input_vars"]
    assert iv["items"] == {"type": "array", "items": {"type": "string"}}
    assert iv["config"] == {
        "type": "object",
        "additionalProperties": {"type": "integer"},
    }
    assert "output" not in iv  # state_key target


@pytest.mark.req("REQ-YG-311")
def test_discover_unknown_type_fallback(tmp_path: Path):
    """Unknown type annotation falls back to 'string'."""
    from yamlgraph.discovery import discover_graphs

    yaml_content = """\
version: "1.0"
name: unknown-types
description: Has unknown type annotations
state:
  custom: MyCustomType
  output: str
nodes:
  n:
    type: llm
    prompt: p
    state_key: output
edges:
  - from: START
    to: n
  - from: n
    to: END
"""
    _write_graph(tmp_path, "demo", yaml_content)
    graphs = discover_graphs([str(tmp_path / "*/graph.yaml")])

    assert len(graphs) == 1
    assert graphs[0]["input_vars"]["custom"] == {"type": "string"}


@pytest.mark.req("REQ-YG-311")
def test_array_schema_includes_items(tmp_path: Path):
    """Array-typed input vars produce JSON Schema with required 'items' field.

    Regression test: GitHub Copilot rejects MCP tools whose array parameters
    lack ``items`` (JSON Schema §6.4.1). Without ``items``, the entire MCP
    server fails to load.
    """
    from yamlgraph.discovery import discover_graphs

    yaml_content = """\
version: "1.0"
name: array-test
description: Graph with list inputs
state:
  plain_list: list
  typed_list: list[int]
  output: str
nodes:
  n:
    type: llm
    prompt: p
    state_key: output
edges:
  - from: START
    to: n
  - from: n
    to: END
"""
    _write_graph(tmp_path, "demo", yaml_content)
    graphs = discover_graphs([str(tmp_path / "*/graph.yaml")])

    g = graphs[0]
    schema = g["input_schema"]
    props = schema["properties"]

    # Plain list → array with default string items
    assert props["plain_list"]["type"] == "array"
    assert "items" in props["plain_list"], "array type must include 'items'"
    assert props["plain_list"]["items"] == {"type": "string"}

    # Typed list[int] → array with integer items
    assert props["typed_list"]["type"] == "array"
    assert "items" in props["typed_list"], "array type must include 'items'"
    assert props["typed_list"]["items"] == {"type": "integer"}

    # Output excluded
    assert "output" not in props


@pytest.mark.req("REQ-YG-311")
@pytest.mark.asyncio
async def test_mcp_tool_array_param_valid_schema(tmp_path: Path):
    """MCP tool with array parameter produces schema Copilot can validate."""
    from yamlgraph.mcp_server import create_server

    yaml_content = """\
version: "1.0"
name: array-tool
description: Tool with array params
state:
  tags: list
  items: list[str]
  result: str
nodes:
  n:
    type: llm
    prompt: p
    state_key: result
edges:
  - from: START
    to: n
  - from: n
    to: END
"""
    _write_graph(tmp_path, "demo", yaml_content)
    server = create_server(graph_patterns=[str(tmp_path / "*/graph.yaml")])

    tools = await _call_list_tools(server)
    tool = next(t for t in tools if t.name == "array_tool")

    props = tool.inputSchema["properties"]
    # Both array params must have items
    for key in ("tags", "items"):
        assert props[key]["type"] == "array", f"{key} should be array"
        assert "items" in props[key], f"{key} array must have 'items'"


# ---------------------------------------------------------------------------
# REQ-YG-313: Tool name normalization
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-313")
def test_discover_tool_name_normalization(tmp_path: Path):
    """Graph name with hyphens normalized to underscores for tool_name."""
    from yamlgraph.discovery import discover_graphs

    _write_graph(tmp_path, "demo", GRAPH_WITH_IO)
    graphs = discover_graphs([str(tmp_path / "*/graph.yaml")])

    assert len(graphs) == 1
    assert graphs[0]["tool_name"] == "test_graph"


@pytest.mark.req("REQ-YG-313")
def test_discover_tool_name_already_valid(tmp_path: Path):
    """Graph name without hyphens keeps same tool_name."""
    from yamlgraph.discovery import discover_graphs

    yaml_content = """\
version: "1.0"
name: simplename
description: No hyphens
nodes:
  n:
    type: llm
    prompt: p
    state_key: out
edges:
  - from: START
    to: n
  - from: n
    to: END
"""
    _write_graph(tmp_path, "demo", yaml_content)
    graphs = discover_graphs([str(tmp_path / "*/graph.yaml")])

    assert graphs[0]["tool_name"] == "simplename"


# ---------------------------------------------------------------------------
# REQ-YG-312: Per-graph MCP tool registration
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-312")
@pytest.mark.asyncio
async def test_per_graph_tools_registered(tmp_path: Path):
    """Each discovered graph appears as its own named MCP tool."""
    from yamlgraph.mcp_server import create_server

    _write_graph(tmp_path, "demo", GRAPH_WITH_IO)
    server = create_server(graph_patterns=[str(tmp_path / "*/graph.yaml")])

    tools = await _call_list_tools(server)
    tool_names = {t.name for t in tools}

    # Generic tools retained
    assert "yamlgraph_list_graphs" in tool_names
    assert "yamlgraph_run_graph" in tool_names

    # Per-graph typed tool added
    assert "test_graph" in tool_names


@pytest.mark.req("REQ-YG-312")
@pytest.mark.asyncio
async def test_per_graph_tool_has_typed_schema(tmp_path: Path):
    """Per-graph tool has JSON Schema derived from input vars."""
    from yamlgraph.mcp_server import create_server

    _write_graph(tmp_path, "demo", GRAPH_WITH_IO)
    server = create_server(graph_patterns=[str(tmp_path / "*/graph.yaml")])

    tools = await _call_list_tools(server)
    tool = next(t for t in tools if t.name == "test_graph")

    props = tool.inputSchema["properties"]
    assert "name" in props
    assert props["name"]["type"] == "string"
    assert "style" in props
    assert props["style"]["type"] == "string"
    # Output field not exposed as parameter
    assert "greeting" not in props


@pytest.mark.req("REQ-YG-312")
@pytest.mark.asyncio
async def test_per_graph_tool_has_description(tmp_path: Path):
    """Per-graph tool description comes from graph description."""
    from yamlgraph.mcp_server import create_server

    _write_graph(tmp_path, "demo", GRAPH_WITH_IO)
    server = create_server(graph_patterns=[str(tmp_path / "*/graph.yaml")])

    tools = await _call_list_tools(server)
    tool = next(t for t in tools if t.name == "test_graph")

    assert "A test graph with inputs and outputs" in tool.description


@pytest.mark.req("REQ-YG-312")
@pytest.mark.asyncio
async def test_per_graph_tool_invocation(tmp_path: Path):
    """Calling a per-graph typed tool invokes the correct graph."""
    from yamlgraph.mcp_server import create_server

    _write_graph(tmp_path, "demo", GRAPH_WITH_IO)
    server = create_server(graph_patterns=[str(tmp_path / "*/graph.yaml")])

    captured = {}

    def fake_invoke(graph_path: str, variables: dict) -> dict:
        captured["path"] = graph_path
        captured["vars"] = variables
        return {"greeting": "Hello!"}

    with patch("yamlgraph.mcp_server._invoke_graph", side_effect=fake_invoke):
        result = await _call_tool(
            server,
            "test_graph",
            {"name": "World", "style": "casual"},
        )

    assert len(result) == 1
    parsed = json.loads(result[0].text)
    assert "greeting" in parsed
    assert captured["vars"]["name"] == "World"
    assert captured["vars"]["style"] == "casual"


@pytest.mark.req("REQ-YG-312")
@pytest.mark.asyncio
async def test_per_graph_tool_no_state(tmp_path: Path):
    """Graph with no state block registers as tool with empty schema."""
    from yamlgraph.mcp_server import create_server

    _write_graph(tmp_path, "demo", GRAPH_NO_STATE)
    server = create_server(graph_patterns=[str(tmp_path / "*/graph.yaml")])

    tools = await _call_list_tools(server)
    tool = next(t for t in tools if t.name == "stateless")

    assert tool.inputSchema["properties"] == {}


@pytest.mark.req("REQ-YG-312")
@pytest.mark.asyncio
async def test_per_graph_tool_multi_type_schema(tmp_path: Path):
    """Per-graph tool with multiple types has correct JSON Schema."""
    from yamlgraph.mcp_server import create_server

    _write_graph(tmp_path, "demo", GRAPH_MULTI_TYPE)
    server = create_server(graph_patterns=[str(tmp_path / "*/graph.yaml")])

    tools = await _call_list_tools(server)
    tool = next(t for t in tools if t.name == "multi_type")

    props = tool.inputSchema["properties"]
    assert props["topic"]["type"] == "string"
    assert props["depth"]["type"] == "integer"
    assert props["temperature"]["type"] == "number"
    assert props["verbose"]["type"] == "boolean"
    assert props["tags"]["type"] == "array"
    assert props["options"]["type"] == "object"
    assert "result" not in props


# ---------------------------------------------------------------------------
# REQ-YG-314: Name collision detection
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-314")
def test_name_collision_raises(tmp_path: Path):
    """Two graphs with the same tool_name raise ValueError at startup."""
    from yamlgraph.mcp_server import create_server

    # Two different directories, same graph name
    _write_graph(tmp_path, "dir_a", GRAPH_WITH_IO)
    _write_graph(tmp_path, "dir_b", GRAPH_WITH_IO)

    with pytest.raises(ValueError, match="collision"):
        create_server(graph_patterns=[str(tmp_path / "*/graph.yaml")])


@pytest.mark.req("REQ-YG-314")
def test_no_collision_different_names(tmp_path: Path):
    """Graphs with different names don't trigger collision."""
    from yamlgraph.mcp_server import create_server

    _write_graph(tmp_path, "dir_a", GRAPH_WITH_IO)
    _write_graph(tmp_path, "dir_b", GRAPH_NO_STATE)

    # Should not raise — names are different (test-graph vs stateless)
    server = create_server(graph_patterns=[str(tmp_path / "*/graph.yaml")])
    assert server is not None


# ---------------------------------------------------------------------------
# Map node collect key exclusion
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-310")
def test_discover_excludes_collect_key_from_inputs(tmp_path: Path):
    """Map node ``collect`` target is an output, not an input var.

    Regression: animated-character-storyboard's ``animated_panels``
    was exposed as a required input because ``collect`` was not treated
    as an output key — only ``state_key`` was checked.
    """
    from yamlgraph.discovery import discover_graphs

    yaml_content = """\
version: "1.0"
name: map-collect-test
description: Graph with map node using collect
state:
  concept: str
  panels: list
  result: str
nodes:
  generate:
    type: map
    over: "{state.concept}"
    as: item
    node:
      type: llm
      prompt: gen
      state_key: panel
    collect: panels
  finalize:
    type: llm
    prompt: final
    state_key: result
edges:
  - from: START
    to: generate
  - from: generate
    to: finalize
  - from: finalize
    to: END
"""
    _write_graph(tmp_path, "demo", yaml_content)
    graphs = discover_graphs([str(tmp_path / "*/graph.yaml")])

    assert len(graphs) == 1
    iv = graphs[0]["input_vars"]
    # 'concept' is input (not state_key or collect target)
    assert "concept" in iv
    # 'panels' is a collect target — should be excluded
    assert "panels" not in iv
    # 'result' is a state_key — should be excluded
    assert "result" not in iv


# ---------------------------------------------------------------------------
# Schema validation guard
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-311")
def test_validate_json_schema_rejects_array_without_items():
    """_validate_json_schema raises on array missing items."""
    from yamlgraph.discovery import _validate_json_schema

    bad_schema = {
        "type": "object",
        "properties": {
            "tags": {"type": "array"},  # missing items
        },
    }
    with pytest.raises(ValueError, match="missing 'items'"):
        _validate_json_schema(bad_schema, "broken_tool")


@pytest.mark.req("REQ-YG-311")
def test_validate_json_schema_accepts_valid_array():
    """_validate_json_schema passes for arrays with items."""
    from yamlgraph.discovery import _validate_json_schema

    good_schema = {
        "type": "object",
        "properties": {
            "tags": {"type": "array", "items": {"type": "string"}},
        },
    }
    # Should not raise
    _validate_json_schema(good_schema, "good_tool")
