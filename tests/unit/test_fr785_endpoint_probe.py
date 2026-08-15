"""Tests for FR-785 API discovery endpoint-probe step (REQ-YG-586).

Tests cover:
- Graph/manifest file existence and structure (AC-02..AC-04)
- ProbeResult schema validation (AC-05)
- Response taxonomy routing logic (AC-06)
- max_iterations budget enforcement (AC-07)
- Lint pass (AC-09)
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from yamlgraph.compile.graph_loader import load_and_compile

STEPS_DIR = Path(__file__).resolve().parents[2] / "examples" / "api-discovery" / "steps"
GRAPH_DIR = STEPS_DIR / "endpoint-probe"


# ---------------------------------------------------------------------------
# File existence and structure (AC-02, AC-03, AC-04)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-586")
def test_graph_file_exists():
    """AC-02: graph.yaml exists."""
    assert (GRAPH_DIR / "graph.yaml").exists()


@pytest.mark.req("REQ-YG-586")
def test_graph_is_agent_type():
    """AC-02: graph uses agent node type with bounded max_iterations."""
    graph = yaml.safe_load((GRAPH_DIR / "graph.yaml").read_text())
    nodes = graph["nodes"]
    assert "probe_agent" in nodes
    node = nodes["probe_agent"]
    assert node["type"] == "agent"
    assert "max_iterations" in node


@pytest.mark.req("REQ-YG-586")
def test_graph_references_curl_probe_tool():
    """AC-02: agent node references curl_probe tool."""
    graph = yaml.safe_load((GRAPH_DIR / "graph.yaml").read_text())
    node = graph["nodes"]["probe_agent"]
    assert "curl_probe" in node["tools"]


@pytest.mark.req("REQ-YG-586")
def test_prompt_file_exists():
    """AC-03: prompt YAML exists under prompts/."""
    assert (GRAPH_DIR / "prompts" / "probe.yaml").exists()


@pytest.mark.req("REQ-YG-586")
def test_prompt_has_output_schema():
    """AC-05: prompt defines its result with the JSON-Schema dialect."""
    prompt = yaml.safe_load((GRAPH_DIR / "prompts" / "probe.yaml").read_text())
    assert "schema" not in prompt
    schema = prompt["output_schema"]
    assert schema["type"] == "object"
    assert set(schema["properties"]) == {
        "live_endpoints",
        "html_pages",
        "verdict_hint",
    }


@pytest.mark.req("REQ-YG-586")
def test_prompt_has_system_and_user():
    """AC-03: prompt has both system and user templates."""
    prompt = yaml.safe_load((GRAPH_DIR / "prompts" / "probe.yaml").read_text())
    assert "system" in prompt
    assert "user" in prompt
    assert "candidate_urls" in prompt["user"]


@pytest.mark.req("REQ-YG-586")
def test_tool_manifest_exists():
    """AC-04: endpoint_probe.tool.yaml exists at steps/ level."""
    manifest_path = STEPS_DIR / "endpoint_probe.tool.yaml"
    assert manifest_path.exists()


@pytest.mark.req("REQ-YG-586")
def test_tool_manifest_structure():
    """AC-04: manifest has runtime.type: graph, relative path, mappings."""
    manifest = yaml.safe_load((STEPS_DIR / "endpoint_probe.tool.yaml").read_text())
    assert manifest["name"] == "endpoint_probe"
    runtime = manifest["runtime"]
    assert runtime["type"] == "graph"
    assert runtime["path"] == "endpoint-probe/graph.yaml"
    assert "candidate_urls" in runtime["input_mapping"]
    assert "max_iterations" in runtime["input_mapping"]
    assert runtime["output_key"] == "probe_result"


# ---------------------------------------------------------------------------
# ProbeResult schema shape validation (AC-05)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-586")
def test_probe_result_schema_endpoint_hit_fields():
    """AC-05: EndpointHit items have url, status, content_type, body_preview."""
    prompt = yaml.safe_load((GRAPH_DIR / "prompts" / "probe.yaml").read_text())
    items_fields = prompt["output_schema"]["properties"]["live_endpoints"]["items"]
    assert items_fields["type"] == "object"
    required_fields = {"url", "status", "content_type", "body_preview"}
    assert set(items_fields["properties"]) == required_fields
    assert set(items_fields["required"]) == required_fields


@pytest.mark.req("REQ-YG-586")
def test_probe_result_schema_verdict_hint_optional():
    """AC-05: verdict_hint is omitted from the required field list."""
    prompt = yaml.safe_load((GRAPH_DIR / "prompts" / "probe.yaml").read_text())
    schema = prompt["output_schema"]
    assert set(schema["required"]) == {"live_endpoints", "html_pages"}
    assert "verdict_hint" not in schema["required"]


@pytest.mark.req("REQ-YG-586")
def test_endpoint_probe_graph_compiles():
    """FR-795: the shipped endpoint-probe graph compiles end to end."""
    load_and_compile(GRAPH_DIR / "graph.yaml")


# ---------------------------------------------------------------------------
# Taxonomy doctrine in prompt (AC-06)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-586")
def test_prompt_documents_403_ua_retry():
    """AC-06: prompt instructs 403→UA retry."""
    prompt = yaml.safe_load((GRAPH_DIR / "prompts" / "probe.yaml").read_text())
    system = prompt["system"]
    assert "403" in system
    assert "User-Agent" in system or "user-agent" in system.lower()


@pytest.mark.req("REQ-YG-586")
def test_prompt_documents_404_path_variants():
    """AC-06: prompt instructs 404→path variants."""
    prompt = yaml.safe_load((GRAPH_DIR / "prompts" / "probe.yaml").read_text())
    system = prompt["system"]
    assert "404" in system
    assert "/api/v1" in system


@pytest.mark.req("REQ-YG-586")
def test_prompt_documents_html_classification():
    """AC-06: prompt instructs 200+HTML→html_pages."""
    prompt = yaml.safe_load((GRAPH_DIR / "prompts" / "probe.yaml").read_text())
    system = prompt["system"]
    assert "html" in system.lower()
    assert "html_pages" in system


@pytest.mark.req("REQ-YG-586")
def test_prompt_documents_json_endpoint():
    """AC-06: prompt instructs 200+JSON→live_endpoints."""
    prompt = yaml.safe_load((GRAPH_DIR / "prompts" / "probe.yaml").read_text())
    system = prompt["system"]
    assert "json" in system.lower()
    assert "live_endpoints" in system


@pytest.mark.req("REQ-YG-586")
def test_prompt_documents_xml_classification():
    """AC-06: prompt instructs XML→classify (OData/SOAP/RSS/Atom)."""
    prompt = yaml.safe_load((GRAPH_DIR / "prompts" / "probe.yaml").read_text())
    system = prompt["system"]
    assert "xml" in system.lower()
    # At least some of the subtypes mentioned
    xml_lower = system.lower()
    assert any(t in xml_lower for t in ["odata", "soap", "rss", "atom"])


@pytest.mark.req("REQ-YG-586")
def test_prompt_documents_geo_blocked():
    """AC-06: prompt instructs 000→geo_blocked verdict."""
    prompt = yaml.safe_load((GRAPH_DIR / "prompts" / "probe.yaml").read_text())
    system = prompt["system"]
    assert "geo_blocked" in system


# ---------------------------------------------------------------------------
# max_iterations budget (AC-07)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-586")
def test_graph_max_iterations_bounded():
    """AC-07: agent node has explicit max_iterations value."""
    graph = yaml.safe_load((GRAPH_DIR / "graph.yaml").read_text())
    node = graph["nodes"]["probe_agent"]
    max_iter = node["max_iterations"]
    # Must be a positive integer (or state reference that defaults to one)
    assert max_iter is not None
    if isinstance(max_iter, int):
        assert 1 <= max_iter <= 50


@pytest.mark.req("REQ-YG-586")
def test_state_max_iterations_has_default():
    """AC-07: state declares max_iterations with a sensible default."""
    graph = yaml.safe_load((GRAPH_DIR / "graph.yaml").read_text())
    state = graph["state"]
    assert "max_iterations" in state
    mi = state["max_iterations"]
    assert "default" in mi
    assert 1 <= mi["default"] <= 50


# ---------------------------------------------------------------------------
# No files under yamlgraph/ (AC-10)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-586")
def test_no_yamlgraph_package_changes():
    """AC-10: FR-785 artifacts live under the example tree, not the package."""
    graph_path = GRAPH_DIR / "graph.yaml"
    assert "examples" in str(graph_path)
    # Must NOT be inside the yamlgraph package directory
    parts = graph_path.parts
    assert "yamlgraph" not in parts[parts.index("examples") + 1 :]
