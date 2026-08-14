"""Tests for FR-786 API discovery page-analysis step (REQ-YG-587).

Tests cover:
- Graph/manifest file existence and structure (AC-01, AC-02)
- Shared fetch_page tool reference, no duplicate tool (AC-03)
- Platform catalog data file and data_files wiring (AC-04)
- PageAnalysis schema shape (AC-05)
- Deterministic fixtures exist (AC-06, AC-07 preconditions)
- Scope boundary: no sibling-step artifacts introduced (AC-09)
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

STEPS_DIR = Path(__file__).resolve().parents[2] / "examples" / "api-discovery" / "steps"
GRAPH_DIR = STEPS_DIR / "page-analysis"


# ---------------------------------------------------------------------------
# File existence and structure (AC-01, AC-02)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-587")
def test_graph_file_exists():
    """AC-01: graph.yaml exists."""
    assert (GRAPH_DIR / "graph.yaml").exists()


@pytest.mark.req("REQ-YG-587")
def test_graph_is_agent_type():
    """AC-01: graph uses agent node type with bounded max_iterations."""
    graph = yaml.safe_load((GRAPH_DIR / "graph.yaml").read_text())
    node = graph["nodes"]["analyze"]
    assert node["type"] == "agent"
    assert "max_iterations" in node
    assert 1 <= node["max_iterations"] <= 50


@pytest.mark.req("REQ-YG-587")
def test_tool_manifest_exists():
    """AC-02: page_analysis.tool.yaml exists at steps/ level."""
    assert (STEPS_DIR / "page_analysis.tool.yaml").exists()


@pytest.mark.req("REQ-YG-587")
def test_tool_manifest_structure():
    """AC-02: manifest has runtime.type: graph, relative path, mappings."""
    manifest = yaml.safe_load((STEPS_DIR / "page_analysis.tool.yaml").read_text())
    assert manifest["name"] == "page_analysis"
    runtime = manifest["runtime"]
    assert runtime["type"] == "graph"
    assert runtime["path"] == "page-analysis/graph.yaml"
    assert "html_pages" in runtime["input_mapping"]
    assert runtime["output_key"] == "page_analysis"


@pytest.mark.req("REQ-YG-587")
def test_prompt_file_exists():
    """AC-01: prompt YAML exists under prompts/."""
    assert (GRAPH_DIR / "prompts" / "analyze.yaml").exists()


# ---------------------------------------------------------------------------
# Shared fetch_page dependency, no duplicate tool (AC-03)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-587")
def test_graph_references_shared_fetch_page_tool():
    """AC-03: graph references the shared FR-783 fetch_page manifest by path."""
    graph = yaml.safe_load((GRAPH_DIR / "graph.yaml").read_text())
    tools = graph["tools"]
    assert "fetch_page" in tools
    assert tools["fetch_page"]["manifest"] == "../../tools/fetch_page.tool.yaml"
    manifest_path = (GRAPH_DIR / tools["fetch_page"]["manifest"]).resolve()
    assert manifest_path.exists()


@pytest.mark.req("REQ-YG-587")
def test_no_duplicate_fetch_tool_under_step():
    """AC-03: no local fetch/curl tool manifest duplicated under page-analysis/."""
    duplicates = list(GRAPH_DIR.glob("**/*.tool.yaml"))
    assert duplicates == []


# ---------------------------------------------------------------------------
# Platform catalog (AC-04)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-587")
def test_graph_loads_platform_catalog_via_data_files():
    """AC-04: platform catalog is loaded through data_files, not hardcoded."""
    graph = yaml.safe_load((GRAPH_DIR / "graph.yaml").read_text())
    assert graph["data_files"]["platform_catalog"] == "data/platform_catalog.yaml"


@pytest.mark.req("REQ-YG-587")
def test_platform_catalog_contains_required_families():
    """AC-04: catalog covers CKAN, PxWeb, SwaggerUI, OData, Liferay, JSF, WordPress REST, EntryScape."""
    catalog = yaml.safe_load((GRAPH_DIR / "data" / "platform_catalog.yaml").read_text())
    names = {p["name"] for p in catalog["platforms"]}
    required = {
        "CKAN",
        "PxWeb",
        "SwaggerUI",
        "OData",
        "Liferay",
        "JSF",
        "WordPress REST",
        "EntryScape",
    }
    assert required.issubset(names)
    for platform in catalog["platforms"]:
        assert platform["markers"], f"{platform['name']} has no markers"


@pytest.mark.req("REQ-YG-587")
def test_prompt_renders_platform_catalog_not_hardcoded():
    """AC-04: prompt references platform_catalog via Jinja, not a hardcoded list."""
    prompt_text = (GRAPH_DIR / "prompts" / "analyze.yaml").read_text()
    assert "platform_catalog" in prompt_text
    assert "{% for platform in platform_catalog.platforms %}" in prompt_text


# ---------------------------------------------------------------------------
# PageAnalysis schema shape (AC-05)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-587")
def test_page_analysis_schema_exact_fields():
    """AC-05: PageAnalysis schema has exactly the four required fields."""
    prompt = yaml.safe_load((GRAPH_DIR / "prompts" / "analyze.yaml").read_text())
    schema = prompt["schema"]
    assert schema["name"] == "PageAnalysis"
    fields = set(schema["fields"].keys())
    assert fields == {"api_found", "is_spa", "platform_candidates", "api_urls"}


@pytest.mark.req("REQ-YG-587")
def test_page_analysis_schema_field_types():
    """AC-05: field types match bool/list[str] contract."""
    prompt = yaml.safe_load((GRAPH_DIR / "prompts" / "analyze.yaml").read_text())
    fields = prompt["schema"]["fields"]
    assert fields["api_found"]["type"] == "bool"
    assert fields["is_spa"]["type"] == "bool"
    assert fields["platform_candidates"]["type"] == "list[str]"
    assert fields["api_urls"]["type"] == "list[str]"


# ---------------------------------------------------------------------------
# Deterministic fixtures (AC-06, AC-07 preconditions)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-587")
def test_fixtures_exist():
    """AC-06/AC-07: portal and SPA fixtures are committed under fixtures/."""
    fixtures = GRAPH_DIR / "fixtures"
    assert (fixtures / "portal_with_api.html").exists()
    assert (fixtures / "spa_no_api.html").exists()


@pytest.mark.req("REQ-YG-587")
def test_portal_fixture_carries_expected_markers():
    """AC-06: portal fixture embeds CKAN/PxWeb/SwaggerUI/OData markers and API URLs."""
    html = (GRAPH_DIR / "fixtures" / "portal_with_api.html").read_text()
    assert "/api/3/action/" in html
    assert "/PXWeb/api/" in html
    assert "swagger-ui" in html
    assert "$metadata" in html
    assert "fetch(" in html


@pytest.mark.req("REQ-YG-587")
def test_spa_fixture_has_no_static_api_references():
    """AC-07: SPA fixture has no inline fetch/data-api-url/platform markers."""
    html = (GRAPH_DIR / "fixtures" / "spa_no_api.html").read_text()
    assert "fetch(" not in html
    assert "data-api" not in html
    catalog = yaml.safe_load((GRAPH_DIR / "data" / "platform_catalog.yaml").read_text())
    for platform in catalog["platforms"]:
        for marker in platform["markers"]:
            assert marker not in html


# ---------------------------------------------------------------------------
# Scope boundary (AC-09)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-587")
def test_no_sibling_step_dependency_introduced():
    """AC-09: page-analysis's own graph doesn't reference sibling steps.

    Directory existence for browser-sniff/orchestrator/platform-confirm/
    schema-extract is NOT asserted here: those are separate FRs (e.g.
    FR-788) that legitimately create their own directories over time.
    The FR-786 boundary is that ITS graph doesn't depend on them.
    """
    graph_text = (GRAPH_DIR / "graph.yaml").read_text()
    for forbidden in (
        "browser-sniff",
        "orchestrator",
        "platform-confirm",
        "schema-extract",
    ):
        assert forbidden not in graph_text


@pytest.mark.req("REQ-YG-587")
def test_no_yamlgraph_package_changes():
    """AC-09: FR-786 artifacts live under the example tree, not the package."""
    graph_path = GRAPH_DIR / "graph.yaml"
    assert "examples" in str(graph_path)
    assert "yamlgraph" + "/yamlgraph" not in str(graph_path)
