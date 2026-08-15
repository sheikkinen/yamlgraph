"""Tests for FR-789 API discovery browser-sniff step (REQ-YG-593).

Tests cover:
- Graph/manifest/prompt existence and structure (AC-01, AC-02)
- FR-784 network_sniff dependency referenced, not reimplemented (AC-03, AC-04)
- SniffResult schema contract incl. typed needs_manual path (AC-05)
- Telemetry-exclusion and needs-manual prompt doctrine (AC-06, AC-07)
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

STEPS_DIR = Path(__file__).resolve().parents[2] / "examples" / "api-discovery" / "steps"
GRAPH_DIR = STEPS_DIR / "browser-sniff"

CAPTURED_REQUEST_FIELDS = {"url", "method", "status", "content_type", "body_preview"}


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


# ---------------------------------------------------------------------------
# File existence and structure (AC-01, AC-02)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-593")
def test_graph_file_exists():
    """AC-01: graph.yaml exists."""
    assert (GRAPH_DIR / "graph.yaml").exists()


@pytest.mark.req("REQ-YG-593")
def test_graph_is_agent_type_with_bounded_iterations():
    """AC-01: single agent node with a bounded iteration budget."""
    graph = _load(GRAPH_DIR / "graph.yaml")
    node = graph["nodes"]["sniff_agent"]
    assert node["type"] == "agent"
    assert 1 <= node["max_iterations"] <= 50


@pytest.mark.req("REQ-YG-593")
def test_tool_manifest_exists_and_structured():
    """AC-02: browser_sniff.tool.yaml declares a graph runtime pointing to the step."""
    manifest = _load(STEPS_DIR / "browser_sniff.tool.yaml")
    assert manifest["name"] == "browser_sniff"
    runtime = manifest["runtime"]
    assert runtime["type"] == "graph"
    assert runtime["path"] == "browser-sniff/graph.yaml"
    assert "url" in runtime["input_mapping"]
    assert runtime["output_key"] == "sniff_result"


@pytest.mark.req("REQ-YG-593")
def test_prompt_file_exists():
    """AC-01: prompt YAML exists under prompts/."""
    assert (GRAPH_DIR / "prompts" / "sniff.yaml").exists()


@pytest.mark.req("REQ-YG-593")
def test_graph_loads_and_compiles():
    """AC-01: the authored graph passes load_and_compile without raising."""
    from yamlgraph.compile.graph_loader import load_and_compile

    assert load_and_compile(str(GRAPH_DIR / "graph.yaml")) is not None


# ---------------------------------------------------------------------------
# FR-784 dependency referenced, not reimplemented (AC-03, AC-04)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-593")
def test_graph_references_shared_network_sniff_tool():
    """AC-03/AC-04: graph references the FR-784 network_sniff manifest by path."""
    graph = _load(GRAPH_DIR / "graph.yaml")
    tools = graph["tools"]
    assert "network_sniff" in tools
    assert tools["network_sniff"]["manifest"] == "../../tools/network_sniff.tool.yaml"
    manifest_path = (GRAPH_DIR / tools["network_sniff"]["manifest"]).resolve()
    assert manifest_path.exists()


@pytest.mark.req("REQ-YG-593")
def test_no_duplicate_tool_or_sniffer_under_step():
    """AC-03: no local manifest or JS sniffer duplicated under browser-sniff/."""
    assert list(GRAPH_DIR.glob("**/*.tool.yaml")) == []
    assert list(GRAPH_DIR.glob("**/*.js")) == []


@pytest.mark.req("REQ-YG-593")
def test_agent_node_uses_network_sniff():
    """AC-04: the agent node's tool list is exactly network_sniff."""
    graph = _load(GRAPH_DIR / "graph.yaml")
    assert graph["nodes"]["sniff_agent"]["tools"] == ["network_sniff"]


# ---------------------------------------------------------------------------
# SniffResult contract (AC-05)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-593")
def test_output_schema_declares_sniff_result_contract():
    """AC-05: schema has api_calls, auth_required required; typed needs_manual path."""
    schema = _load(GRAPH_DIR / "prompts" / "sniff.yaml")["output_schema"]
    assert schema["type"] == "object"
    props = schema["properties"]
    assert set(props.keys()) == {
        "api_calls",
        "auth_required",
        "verdict_hint",
        "manual_reason",
    }
    assert props["api_calls"]["type"] == "array"
    assert props["auth_required"]["type"] == "boolean"
    assert props["verdict_hint"]["enum"] == ["needs_manual"]
    assert set(schema["required"]) == {"api_calls", "auth_required"}
    assert schema["additionalProperties"] is False


@pytest.mark.req("REQ-YG-593")
def test_captured_request_item_contract():
    """AC-05: api_calls items require the five CapturedRequest fields."""
    schema = _load(GRAPH_DIR / "prompts" / "sniff.yaml")["output_schema"]
    items = schema["properties"]["api_calls"]["items"]
    assert set(items["properties"].keys()) == CAPTURED_REQUEST_FIELDS
    assert set(items["required"]) == CAPTURED_REQUEST_FIELDS
    assert items["properties"]["status"]["type"] == "integer"


@pytest.mark.req("REQ-YG-593")
def test_sniff_result_model_accepts_needs_manual_and_healthy_shapes():
    """AC-05: the JSON-Schema dialect builds a model accepting both result shapes."""
    from yamlgraph.schema_loader import build_pydantic_model_from_json_schema

    schema = _load(GRAPH_DIR / "prompts" / "sniff.yaml")["output_schema"]
    model = build_pydantic_model_from_json_schema(schema, "SniffResult")
    healthy = model.model_validate(
        {
            "api_calls": [
                {
                    "url": "http://127.0.0.1:8931/api/data",
                    "method": "GET",
                    "status": 200,
                    "content_type": "application/json",
                    "body_preview": '{"items": []}',
                }
            ],
            "auth_required": False,
        }
    )
    assert healthy.auth_required is False
    manual = model.model_validate(
        {
            "api_calls": [],
            "auth_required": True,
            "verdict_hint": "needs_manual",
            "manual_reason": "captcha",
        }
    )
    assert manual.verdict_hint == "needs_manual"


# ---------------------------------------------------------------------------
# Filtering and needs-manual doctrine (AC-06, AC-07)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-593")
def test_prompt_mandates_data_retention_and_telemetry_exclusion():
    """AC-06: prompt keeps classification == data and excludes telemetry noise."""
    system = _load(GRAPH_DIR / "prompts" / "sniff.yaml")["system"].lower()
    assert "classification is exactly data" in system
    assert "telemetry" in system
    assert "exclude" in system


@pytest.mark.req("REQ-YG-593")
def test_prompt_treats_needs_manual_as_result_not_error():
    """AC-07: auth/CAPTCHA maps to needs_manual, never an error."""
    system = _load(GRAPH_DIR / "prompts" / "sniff.yaml")["system"].lower()
    assert "needs_manual" in system
    assert "captcha" in system
    assert "not an error" in system
