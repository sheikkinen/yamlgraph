"""Tests for FR-788 API discovery platform-confirm step (REQ-YG-589).

Tests cover:
- Graph/manifest file existence and structure (AC-01, AC-02)
- Shared curl_probe tool reference, no duplicate tool (AC-03)
- Frozen input/output cardinality (AC-04, AC-05)
- Family confirmation matrix content (AC-06)
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

STEPS_DIR = Path(__file__).resolve().parents[2] / "examples" / "api-discovery" / "steps"
GRAPH_DIR = STEPS_DIR / "platform-confirm"


# ---------------------------------------------------------------------------
# File existence and structure (AC-01, AC-02)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-589")
def test_graph_file_exists():
    """AC-01: graph.yaml exists."""
    assert (GRAPH_DIR / "graph.yaml").exists()


@pytest.mark.req("REQ-YG-589")
def test_graph_is_agent_type_with_bounded_iterations():
    """AC-01: graph uses agent node type with bounded max_iterations."""
    graph = yaml.safe_load((GRAPH_DIR / "graph.yaml").read_text(encoding="utf-8"))
    node = graph["nodes"]["confirm"]
    assert node["type"] == "agent"
    assert 1 <= node["max_iterations"] <= 50


@pytest.mark.req("REQ-YG-589")
def test_tool_manifest_exists_and_structured():
    """AC-02: platform_confirm.tool.yaml exists with runtime.type: graph."""
    manifest = yaml.safe_load((STEPS_DIR / "platform_confirm.tool.yaml").read_text(encoding="utf-8"))
    assert manifest["name"] == "platform_confirm"
    runtime = manifest["runtime"]
    assert runtime["type"] == "graph"
    assert runtime["path"] == "platform-confirm/graph.yaml"
    assert "platform_candidates" in runtime["input_mapping"]
    assert "base_urls" in runtime["input_mapping"]
    assert runtime["output_key"] == "platform_confirmation"


@pytest.mark.req("REQ-YG-589")
def test_prompt_file_exists():
    """AC-01: prompt YAML exists under prompts/."""
    assert (GRAPH_DIR / "prompts" / "confirm.yaml").exists()


# ---------------------------------------------------------------------------
# Shared curl_probe dependency, no duplicate tool (AC-03)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-589")
def test_graph_references_shared_curl_probe_tool():
    """AC-03: graph references the shared FR-783 curl_probe manifest by path."""
    graph = yaml.safe_load((GRAPH_DIR / "graph.yaml").read_text(encoding="utf-8"))
    tools = graph["tools"]
    assert "curl_probe" in tools
    assert tools["curl_probe"]["manifest"] == "../../tools/curl_probe.tool.yaml"
    manifest_path = (GRAPH_DIR / tools["curl_probe"]["manifest"]).resolve()
    assert manifest_path.exists()


@pytest.mark.req("REQ-YG-589")
def test_no_duplicate_curl_tool_under_step():
    """AC-03: no local curl tool manifest duplicated under platform-confirm/."""
    assert list(GRAPH_DIR.glob("**/*.tool.yaml")) == []


# ---------------------------------------------------------------------------
# Frozen cardinality (AC-04, AC-05)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-589")
def test_state_declares_frozen_input_cardinality():
    """AC-04: state declares platform_candidates and base_urls as list[str]."""
    graph = yaml.safe_load((GRAPH_DIR / "graph.yaml").read_text(encoding="utf-8"))
    state = graph["state"]
    assert state["platform_candidates"]["type"] == "list[str]"
    assert state["base_urls"]["type"] == "list[str]"


@pytest.mark.req("REQ-YG-589")
def test_platform_confirmation_schema_exact_fields():
    """AC-05: PlatformConfirmation schema has exactly the four required fields."""
    prompt = yaml.safe_load((GRAPH_DIR / "prompts" / "confirm.yaml").read_text(encoding="utf-8"))
    schema = prompt["schema"]
    assert schema["name"] == "PlatformConfirmation"
    fields = set(schema["fields"].keys())
    assert fields == {"family", "base_url", "confirmed", "sample_response"}


@pytest.mark.req("REQ-YG-589")
def test_platform_confirmation_schema_field_types():
    """AC-05: field types match str/bool contract."""
    prompt = yaml.safe_load((GRAPH_DIR / "prompts" / "confirm.yaml").read_text(encoding="utf-8"))
    fields = prompt["schema"]["fields"]
    assert fields["family"]["type"] == "str"
    assert fields["base_url"]["type"] == "str"
    assert fields["confirmed"]["type"] == "bool"
    assert fields["sample_response"]["type"] == "str"


@pytest.mark.req("REQ-YG-589")
def test_prompt_documents_stop_at_first_confirmed_pair():
    """AC-04: prompt instructs stopping at the first satisfied predicate."""
    system = yaml.safe_load((GRAPH_DIR / "prompts" / "confirm.yaml").read_text(encoding="utf-8"))[
        "system"
    ]
    assert "first" in system.lower()
    assert (
        "confirmed: false" in system.lower()
        or "confirmed:false" in system.lower().replace(" ", "")
    )


# ---------------------------------------------------------------------------
# Family confirmation matrix (AC-06)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-589")
def test_prompt_documents_family_confirmation_matrix():
    """AC-06: prompt embeds predicates for all six required families."""
    system = yaml.safe_load((GRAPH_DIR / "prompts" / "confirm.yaml").read_text(encoding="utf-8"))[
        "system"
    ]
    for family in ("CKAN", "PxWeb", "OData", "OpenAPI", "WordPress", "JSON-stat"):
        assert family in system


@pytest.mark.req("REQ-YG-589")
def test_prompt_documents_ckan_substance_predicate():
    """AC-06: CKAN predicate requires success + non-zero count, not just 200."""
    system = yaml.safe_load((GRAPH_DIR / "prompts" / "confirm.yaml").read_text(encoding="utf-8"))[
        "system"
    ]
    assert "success" in system.lower()
    assert "count > 0" in system


# ---------------------------------------------------------------------------
# Scope boundary
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-589")
def test_no_sibling_step_dependency_introduced():
    """FR-788 does not depend on browser-sniff/orchestrator/schema-extract/page-analysis internals."""
    graph_text = (GRAPH_DIR / "graph.yaml").read_text(encoding="utf-8")
    for forbidden in (
        "browser-sniff",
        "orchestrator",
        "schema-extract",
        "page-analysis",
    ):
        assert forbidden not in graph_text


@pytest.mark.req("REQ-YG-589")
def test_no_yamlgraph_package_changes():
    """FR-788 artifacts live under the example tree, not the package."""
    graph_path = GRAPH_DIR / "graph.yaml"
    parts = graph_path.parts
    assert "examples" in parts
    assert "yamlgraph" not in parts[parts.index("examples") + 1 :]
