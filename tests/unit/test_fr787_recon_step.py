"""Tests for FR-787 API discovery recon step (REQ-YG-592).

Tests cover:
- Graph/manifest/prompt existence and structure (AC-01, AC-02)
- Shared gh_code_search tool reference, no duplicate tool (AC-03)
- Search-variant guidance and bounded iteration budget (AC-04)
- ReconResult schema contract: four required list[str] fields (AC-05)
- Evidence source-identity and empty-result guidance (AC-06, AC-07)
- Orchestrator untouched (AC-10)
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

STEPS_DIR = Path(__file__).resolve().parents[2] / "examples" / "api-discovery" / "steps"
GRAPH_DIR = STEPS_DIR / "recon"

RECON_FIELDS = {"candidate_urls", "auth_hints", "schema_hints", "evidence"}


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


# ---------------------------------------------------------------------------
# File existence and structure (AC-01, AC-02)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-592")
def test_graph_file_exists():
    """AC-01: graph.yaml exists."""
    assert (GRAPH_DIR / "graph.yaml").exists()


@pytest.mark.req("REQ-YG-592")
def test_graph_is_agent_type_with_bounded_iterations():
    """AC-04: single agent node with a bounded iteration budget."""
    graph = _load(GRAPH_DIR / "graph.yaml")
    node = graph["nodes"]["recon_agent"]
    assert node["type"] == "agent"
    assert 1 <= node["max_iterations"] <= 50


@pytest.mark.req("REQ-YG-592")
def test_tool_manifest_exists_and_structured():
    """AC-02: recon.tool.yaml declares a graph runtime pointing to recon/graph.yaml."""
    manifest = _load(STEPS_DIR / "recon.tool.yaml")
    assert manifest["name"] == "recon"
    runtime = manifest["runtime"]
    assert runtime["type"] == "graph"
    assert runtime["path"] == "recon/graph.yaml"
    assert "hypothesis" in runtime["input_mapping"]
    assert runtime["output_key"] == "recon_result"


@pytest.mark.req("REQ-YG-592")
def test_prompt_file_exists():
    """AC-01: prompt YAML exists under prompts/."""
    assert (GRAPH_DIR / "prompts" / "recon.yaml").exists()


@pytest.mark.req("REQ-YG-592")
def test_graph_loads_and_compiles():
    """AC-01: the authored graph passes load_and_compile without raising."""
    from yamlgraph.compile.graph_loader import load_and_compile

    assert load_and_compile(str(GRAPH_DIR / "graph.yaml")) is not None


# ---------------------------------------------------------------------------
# Shared gh_code_search dependency (AC-03)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-592")
def test_graph_references_shared_gh_code_search_tool():
    """AC-03: graph references the shared FR-783 gh_code_search manifest by path."""
    graph = _load(GRAPH_DIR / "graph.yaml")
    tools = graph["tools"]
    assert "gh_code_search" in tools
    assert tools["gh_code_search"]["manifest"] == "../../tools/gh_code_search.tool.yaml"
    manifest_path = (GRAPH_DIR / tools["gh_code_search"]["manifest"]).resolve()
    assert manifest_path.exists()


@pytest.mark.req("REQ-YG-592")
def test_no_duplicate_tool_under_step():
    """AC-03: no local tool manifest duplicated under recon/."""
    assert list(GRAPH_DIR.glob("**/*.tool.yaml")) == []


# ---------------------------------------------------------------------------
# Search-variant guidance and iteration budget (AC-04)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-592")
def test_prompt_instructs_search_term_variants():
    """AC-04: prompt covers domain/service/country variant generation."""
    system = _load(GRAPH_DIR / "prompts" / "recon.yaml")["system"].lower()
    assert "domain" in system
    assert "service" in system
    assert "country" in system
    assert "variant" in system


@pytest.mark.req("REQ-YG-592")
def test_state_declares_hypothesis_and_bounded_budget():
    """AC-04: state declares hypothesis (str) and a defaulted max_iterations."""
    state = _load(GRAPH_DIR / "graph.yaml")["state"]
    assert state["hypothesis"]["type"] == "str"
    assert state["max_iterations"]["type"] == "int"
    assert 1 <= state["max_iterations"]["default"] <= 50


# ---------------------------------------------------------------------------
# ReconResult contract (AC-05)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-592")
def test_output_schema_has_exactly_four_required_string_arrays():
    """AC-05: output_schema requires the four ReconResult fields as list[str]."""
    prompt = _load(GRAPH_DIR / "prompts" / "recon.yaml")
    schema = prompt["output_schema"]
    assert schema["type"] == "object"
    props = schema["properties"]
    assert set(props.keys()) == RECON_FIELDS
    for field in RECON_FIELDS:
        assert props[field]["type"] == "array"
        assert props[field]["items"]["type"] == "string"
    assert set(schema["required"]) == RECON_FIELDS
    assert schema["additionalProperties"] is False


@pytest.mark.req("REQ-YG-592")
def test_recon_result_pydantic_model_builds_from_schema():
    """AC-05: the JSON-Schema dialect builds a model accepting list[str] fields."""
    from yamlgraph.schema_loader import build_pydantic_model_from_json_schema

    prompt = _load(GRAPH_DIR / "prompts" / "recon.yaml")
    model = build_pydantic_model_from_json_schema(
        prompt["output_schema"], "ReconResult"
    )
    instance = model.model_validate(
        {
            "candidate_urls": ["https://sotkanet.fi/rest/1.1/indicators"],
            "auth_hints": [],
            "schema_hints": ["JSON-stat"],
            "evidence": [
                "repo=owner/name; path=src/client.py; url=https://github.com/owner/name/blob/main/src/client.py; note=base URL"
            ],
        }
    )
    assert instance.candidate_urls[0].startswith("https://")


# ---------------------------------------------------------------------------
# Evidence identity and empty-result validity (AC-06, AC-07)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-592")
def test_prompt_requires_evidence_source_identity():
    """AC-06: prompt mandates repository, path, and URL in evidence strings."""
    system = _load(GRAPH_DIR / "prompts" / "recon.yaml")["system"].lower()
    assert "repository" in system
    assert "path" in system
    assert "url" in system


@pytest.mark.req("REQ-YG-592")
def test_prompt_declares_empty_result_valid():
    """AC-07: empty lists are documented as a legitimate outcome."""
    system = _load(GRAPH_DIR / "prompts" / "recon.yaml")["system"].lower()
    assert "empty" in system
    assert "valid" in system


@pytest.mark.req("REQ-YG-592")
def test_empty_recon_result_validates():
    """AC-07: an all-empty ReconResult validates, not errors."""
    from yamlgraph.schema_loader import build_pydantic_model_from_json_schema

    prompt = _load(GRAPH_DIR / "prompts" / "recon.yaml")
    model = build_pydantic_model_from_json_schema(
        prompt["output_schema"], "ReconResult"
    )
    instance = model.model_validate(
        {"candidate_urls": [], "auth_hints": [], "schema_hints": [], "evidence": []}
    )
    assert instance.evidence == []


# ---------------------------------------------------------------------------
# Orchestrator untouched (AC-10)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-592")
def test_no_orchestrator_graph_exists_or_references_recon():
    """AC-10: FR-787 ships no orchestrator; recon stays optional."""
    orchestrator = GRAPH_DIR.parents[1] / "graph.yaml"
    assert not orchestrator.exists()
