"""Tests for FR-790 API discovery schema-extract step (REQ-YG-594).

Tests cover:
- Graph/manifest/prompt/fixture existence and structure (AC-01, AC-02)
- Family routing and deterministic parse_openapi boundary (AC-05, AC-07)
- CapabilityReport schema contract incl. EndpointInfo shape (AC-03)
- Input mapping from PlatformConfirmation (AC-04)
- Fixture substance for OpenAPI and CKAN smokes (AC-05, AC-06)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

STEPS_DIR = Path(__file__).resolve().parents[2] / "examples" / "api-discovery" / "steps"
GRAPH_DIR = STEPS_DIR / "schema-extract"

REPORT_FIELDS = {
    "family",
    "base_url",
    "endpoints",
    "auth_model",
    "rate_limits",
    "freshness",
    "languages",
    "sample_response",
    "limitations",
}
ENDPOINT_FIELDS = {"method", "path", "description", "parameters"}
PROMPT_NAMES = ("openapi", "ckan", "unsupported")


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# File existence and structure (AC-01, AC-02)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-594")
def test_graph_and_prompts_and_fixtures_exist():
    """AC-01: graph, three family prompts, and both smoke fixtures exist."""
    assert (GRAPH_DIR / "graph.yaml").exists()
    for name in PROMPT_NAMES:
        assert (GRAPH_DIR / "prompts" / f"{name}.yaml").exists()
    assert (GRAPH_DIR / "fixtures" / "openapi_petstore.json").exists()
    assert (GRAPH_DIR / "fixtures" / "ckan_sample.json").exists()


@pytest.mark.req("REQ-YG-594")
def test_tool_manifest_exists_and_structured():
    """AC-02: schema_extract.tool.yaml declares a graph runtime pointing to the step."""
    manifest = _load(STEPS_DIR / "schema_extract.tool.yaml")
    assert manifest["name"] == "schema_extract"
    runtime = manifest["runtime"]
    assert runtime["type"] == "graph"
    assert runtime["path"] == "schema-extract/graph.yaml"
    assert runtime["output_key"] == "capability_report"


@pytest.mark.req("REQ-YG-594")
def test_graph_loads_and_compiles():
    """AC-01: the authored graph passes load_and_compile without raising."""
    from yamlgraph.compile.graph_loader import load_and_compile

    assert load_and_compile(str(GRAPH_DIR / "graph.yaml")) is not None


# ---------------------------------------------------------------------------
# Routing and deterministic OpenAPI boundary (AC-05, AC-07)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-594")
def test_no_agent_node_and_family_routing():
    """AC-07/C-5: no agent node; conditional edges cover openapi, ckan, other."""
    graph = _load(GRAPH_DIR / "graph.yaml")
    node_types = {node["type"] for node in graph["nodes"].values()}
    assert "agent" not in node_types
    conditions = [edge.get("condition", "") for edge in graph["edges"]]
    assert any("== 'openapi'" in c for c in conditions)
    assert any("== 'ckan'" in c for c in conditions)
    assert any("!=" in c for c in conditions)


@pytest.mark.req("REQ-YG-594")
def test_openapi_path_uses_shared_parse_openapi_tool_call():
    """AC-05: OpenAPI path is a deterministic tool_call on the FR-783 manifest."""
    graph = _load(GRAPH_DIR / "graph.yaml")
    assert (
        graph["tools"]["parse_openapi"]["manifest"]
        == "../../tools/parse_openapi.tool.yaml"
    )
    node = graph["nodes"]["parse_openapi_spec"]
    assert node["type"] == "tool_call"
    assert node["tool"] == "parse_openapi"
    assert node["on_error"] == "fail"


@pytest.mark.req("REQ-YG-594")
def test_llm_nodes_fail_loudly():
    """AC-03: invalid output fails validation — every llm node has on_error: fail."""
    graph = _load(GRAPH_DIR / "graph.yaml")
    for node in graph["nodes"].values():
        if node["type"] == "llm":
            assert node["on_error"] == "fail"


# ---------------------------------------------------------------------------
# CapabilityReport schema contract (AC-03)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-594")
@pytest.mark.parametrize("prompt_name", PROMPT_NAMES)
def test_capability_report_schema_pinned(prompt_name: str):
    """AC-03: all nine fields required; EndpointInfo shape enforced per prompt."""
    schema = _load(GRAPH_DIR / "prompts" / f"{prompt_name}.yaml")["output_schema"]
    assert schema["type"] == "object"
    assert set(schema["properties"].keys()) == REPORT_FIELDS
    assert set(schema["required"]) == REPORT_FIELDS
    assert schema["additionalProperties"] is False
    items = schema["properties"]["endpoints"]["items"]
    assert set(items["properties"].keys()) == ENDPOINT_FIELDS
    assert set(items["required"]) == {"path", "parameters"}
    assert items["properties"]["parameters"]["items"]["type"] == "string"


@pytest.mark.req("REQ-YG-594")
def test_capability_report_model_rejects_invalid_output():
    """AC-03: a report missing required fields fails validation, not silently accepted."""
    from pydantic import ValidationError

    from yamlgraph.schema_loader import build_pydantic_model_from_json_schema

    schema = _load(GRAPH_DIR / "prompts" / "ckan.yaml")["output_schema"]
    model = build_pydantic_model_from_json_schema(schema, "CapabilityReport")
    with pytest.raises(ValidationError):
        model.model_validate({"family": "ckan", "base_url": "https://data.gov.fi"})


# ---------------------------------------------------------------------------
# Input mapping from PlatformConfirmation (AC-04)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-594")
def test_input_mapping_matches_platform_confirmation_contract():
    """AC-04: state and manifest consume family/base_url/sample_response + spec input."""
    graph = _load(GRAPH_DIR / "graph.yaml")
    state = graph["state"]
    assert state["family"]["type"] == "str"
    assert state["base_url"]["type"] == "str"
    assert state["sample_response"]["type"] == "str"
    assert state["openapi_spec_json"]["type"] == "str"
    manifest = _load(STEPS_DIR / "schema_extract.tool.yaml")
    mapping = manifest["runtime"]["input_mapping"]
    assert set(mapping.keys()) == {
        "family",
        "base_url",
        "sample_response",
        "openapi_spec_json",
    }


# ---------------------------------------------------------------------------
# Fixture substance (AC-05, AC-06)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-594")
def test_openapi_fixture_parses_deterministically_with_known_path_and_param():
    """AC-05: parse_openapi on the fixture yields /pets with parameter limit."""
    import sys

    tools_dir = GRAPH_DIR.parents[1] / "tools"
    sys.path.insert(0, str(tools_dir))
    try:
        from parse_openapi import parse_openapi
    finally:
        sys.path.remove(str(tools_dir))
    inventory = parse_openapi(
        (GRAPH_DIR / "fixtures" / "openapi_petstore.json").read_text(encoding="utf-8")
    )
    endpoints = {e["path"]: e for e in inventory["endpoints"]}
    assert "/pets" in endpoints
    assert "limit" in endpoints["/pets"]["parameters"]


@pytest.mark.req("REQ-YG-594")
def test_ckan_fixture_carries_required_signals():
    """AC-06: CKAN fixture has dataset count, organizations, freshness, languages."""
    fixture = json.loads((GRAPH_DIR / "fixtures" / "ckan_sample.json").read_text(encoding="utf-8"))
    text = json.dumps(fixture)
    assert '"count"' in text
    assert "organization" in text
    assert "metadata_modified" in text
    assert '"fi"' in text
