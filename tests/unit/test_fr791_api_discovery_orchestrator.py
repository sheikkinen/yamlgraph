"""Tests for FR-791 API discovery orchestrator (REQ-YG-595).

Tests cover:
- Orchestrator graph existence, compile, and input contract (AC-01, AC-02)
- tool_call composition on the four committed step manifests, no subgraph
  nodes, no recon/browser-sniff references (AC-03, AC-04)
- Conditional skip routing for platform-confirm and schema-extract (AC-05)
- Terminal result schema: exactly one verdict, profile constraints (AC-06)
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

EXAMPLE_DIR = Path(__file__).resolve().parents[2] / "examples" / "api-discovery"

STEP_TOOLS = {
    "endpoint_probe": "steps/endpoint_probe.tool.yaml",
    "page_analysis": "steps/page_analysis.tool.yaml",
    "platform_confirm": "steps/platform_confirm.tool.yaml",
    "schema_extract": "steps/schema_extract.tool.yaml",
}


def _graph() -> dict:
    return yaml.safe_load((EXAMPLE_DIR / "graph.yaml").read_text())


def _synth_schema() -> dict:
    prompt = yaml.safe_load((EXAMPLE_DIR / "prompts" / "synthesize.yaml").read_text())
    return prompt["output_schema"]


# ---------------------------------------------------------------------------
# Existence, compile, input contract (AC-01, AC-02)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-595")
def test_orchestrator_and_prompts_exist():
    """AC-01: orchestrator graph and its two prompts exist."""
    assert (EXAMPLE_DIR / "graph.yaml").exists()
    assert (EXAMPLE_DIR / "prompts" / "generate_candidates.yaml").exists()
    assert (EXAMPLE_DIR / "prompts" / "synthesize.yaml").exists()


@pytest.mark.req("REQ-YG-595")
def test_orchestrator_loads_and_compiles():
    """AC-01: load_and_compile succeeds — step manifest absence would fail here."""
    from yamlgraph.compile.graph_loader import load_and_compile

    assert load_and_compile(str(EXAMPLE_DIR / "graph.yaml")) is not None


@pytest.mark.req("REQ-YG-595")
def test_input_contract_documented_in_state():
    """AC-02: required hypothesis/purpose/country; optional domain_hint; result key."""
    state = _graph()["state"]
    for required in ("hypothesis", "purpose", "country"):
        assert state[required]["type"] == "str"
        assert "default" not in state[required]
    assert state["domain_hint"]["type"] == "str"
    assert state["domain_hint"]["default"] == ""
    assert state["result"]["type"] == "dict"


# ---------------------------------------------------------------------------
# Composition boundaries (AC-03, AC-04)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-595")
def test_tool_call_composition_on_committed_step_manifests():
    """AC-03: four tool_call nodes consume exactly the committed manifests."""
    graph = _graph()
    for tool_name, manifest_path in STEP_TOOLS.items():
        assert graph["tools"][tool_name]["manifest"] == manifest_path
        assert (EXAMPLE_DIR / manifest_path).exists()
        node = graph["nodes"][tool_name]
        assert node["type"] == "tool_call"
        assert node["tool"] == tool_name
        assert node["on_error"] == "fail"


@pytest.mark.req("REQ-YG-595")
def test_no_subgraph_nodes_and_no_v2_step_references():
    """AC-03/AC-04: no subgraph node type.

    The original v1 exclusion of recon/browser-sniff references is
    superseded by FR-809 (orchestrator v2) — the FR-791 judgement froze
    them out of v1 as sequencing, not architecture. Route-preservation
    with recon disabled is witnessed in test_fr809_orchestrator_v2.py.
    """
    graph = _graph()
    node_types = {node["type"] for node in graph["nodes"].values()}
    assert "subgraph" not in node_types


@pytest.mark.req("REQ-YG-595")
def test_llm_nodes_fail_loudly():
    """AC-06 support: candidate generation and synthesize fail on invalid output."""
    graph = _graph()
    for name in ("generate_candidates", "synthesize"):
        node = graph["nodes"][name]
        assert node["type"] == "llm"
        assert node["on_error"] == "fail"


# ---------------------------------------------------------------------------
# Skip routing (AC-04, AC-05)
# ---------------------------------------------------------------------------


def _edges_from(graph: dict, source: str) -> list[dict]:
    return [e for e in graph["edges"] if e["from"] == source]


@pytest.mark.req("REQ-YG-595")
def test_absent_candidates_route_to_terminal_synthesize():
    """AC-04: no candidates → synthesize terminal, not a run failure."""
    edges = _edges_from(_graph(), "generate_candidates")
    targets = {e["to"] for e in edges}
    assert targets == {"endpoint_probe", "synthesize"}


@pytest.mark.req("REQ-YG-595")
def test_platform_confirm_skipped_without_candidates():
    """AC-05: page-analysis preserves confirm/synthesize exits under v2 sniffing."""
    edges = _edges_from(_graph(), "page_analysis")
    by_target = {e["to"]: e.get("condition", "") for e in edges}
    assert set(by_target) == {"browser_sniff", "platform_confirm", "synthesize"}
    assert "has_platform_hint" in by_target["platform_confirm"]
    assert "page_findings.is_spa == true" in by_target["browser_sniff"]


@pytest.mark.req("REQ-YG-595")
def test_schema_extract_only_after_confirmation_success():
    """AC-05: schema-extract entered only when platform confirmation succeeded."""
    edges = _edges_from(_graph(), "platform_confirm")
    by_target = {e["to"]: e.get("condition", "") for e in edges}
    assert set(by_target) == {"schema_extract", "synthesize"}
    assert "platform_confirmation.success == true" in by_target["schema_extract"]


@pytest.mark.req("REQ-YG-595")
def test_synthesize_is_the_single_terminal():
    """AC-06: every path ends at synthesize → END."""
    graph = _graph()
    ends = [e for e in graph["edges"] if e["to"] == "END"]
    assert len(ends) == 1
    assert ends[0]["from"] == "synthesize"


# ---------------------------------------------------------------------------
# Terminal result schema (AC-06)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-595")
def test_result_schema_is_single_terminal_contract():
    """AC-06: verdict enum, required reason/steps_tried/alternatives, closed shape."""
    schema = _synth_schema()
    assert schema["properties"]["verdict"]["enum"] == [
        "found",
        "not_found",
        "needs_manual",
    ]
    assert set(schema["required"]) == {
        "verdict",
        "reason",
        "steps_tried",
        "alternatives",
    }
    assert schema["additionalProperties"] is False
    assert schema["properties"]["steps_tried"]["minItems"] == 1
    profile = schema["properties"]["profile"]
    assert set(profile["required"]) == {"url", "platform_family", "endpoints"}
    assert profile["properties"]["endpoints"]["minItems"] == 1
    assert profile["additionalProperties"] is False


@pytest.mark.req("REQ-YG-595")
def test_result_model_validates_found_and_not_found_shapes():
    """AC-06: both terminal shapes validate; missing steps_tried fails."""
    from pydantic import ValidationError

    from yamlgraph.schema_loader import build_pydantic_model_from_json_schema

    model = build_pydantic_model_from_json_schema(_synth_schema(), "DiscoveryResult")
    found = model.model_validate(
        {
            "verdict": "found",
            "profile": {
                "url": "https://statfin.stat.fi/PXWeb/api/v1/fi/StatFin/",
                "platform_family": "PXWeb",
                "endpoints": ["https://statfin.stat.fi/PXWeb/api/v1/fi/StatFin/"],
            },
            "reason": "",
            "steps_tried": ["candidate generation", "endpoint-probe"],
            "alternatives": [],
        }
    )
    assert found.verdict == "found"
    not_found = model.model_validate(
        {
            "verdict": "not_found",
            "reason": "candidates exhausted",
            "steps_tried": ["candidate generation", "endpoint-probe"],
            "alternatives": [],
        }
    )
    assert not_found.profile is None
    with pytest.raises(ValidationError):
        model.model_validate({"verdict": "found", "reason": "", "alternatives": []})
