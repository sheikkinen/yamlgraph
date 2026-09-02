"""Tests for FR-809 API discovery orchestrator v2 (REQ-YG-599).

Static structural witnesses for the recon and browser-sniff extension:
- recon/browser-sniff tool_call composition on committed manifests (AC-01)
- use_recon flag defaulting true; recon gated on it (AC-02, AC-04)
- parsed_key exposure for probe/page/sniff outputs (AC-03)
- browser-sniff entry edge exactly on parsed page_findings SPA-without-API
  (AC-03, judgement R-1)
- deterministic sniff_url selection, no LLM choice (R-2)
- manual_reason terminal schema field (AC-06, R-3)
- steps_tried copy-only discipline extended to the new wrappers (AC-07)

Live fixture/regression smokes (AC-05/AC-06/AC-08) run through the
authoring route validation and are recorded in the FR, not here.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.process  # references examples/ (FR-756)

EXAMPLE_DIR = Path(__file__).resolve().parents[2] / "examples" / "api-discovery"

V2_STEP_TOOLS = {
    "recon": "steps/recon.tool.yaml",
    "browser_sniff": "steps/browser_sniff.tool.yaml",
}

PARSED_KEYS = {
    "endpoint_probe": "probe_findings",
    "page_analysis": "page_findings",
    "browser_sniff": "sniff_findings",
}


def _graph() -> dict:
    return yaml.safe_load((EXAMPLE_DIR / "graph.yaml").read_text(encoding="utf-8"))


def _synth_prompt() -> dict:
    return yaml.safe_load((EXAMPLE_DIR / "prompts" / "synthesize.yaml").read_text(encoding="utf-8"))


def _edges_from(graph: dict, source: str) -> list[dict]:
    return [e for e in graph["edges"] if e["from"] == source]


def _edges_to(graph: dict, target: str) -> list[dict]:
    return [e for e in graph["edges"] if e["to"] == target]


# ---------------------------------------------------------------------------
# Composition (AC-01)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-599")
def test_v2_step_manifests_referenced_as_tool_calls():
    """AC-01: recon and browser_sniff are tool_call nodes on committed manifests."""
    graph = _graph()
    for tool_name, manifest_path in V2_STEP_TOOLS.items():
        assert graph["tools"][tool_name]["manifest"] == manifest_path
        assert (EXAMPLE_DIR / manifest_path).exists()
        node = graph["nodes"][tool_name]
        assert node["type"] == "tool_call"
        assert node["tool"] == tool_name


@pytest.mark.req("REQ-YG-599")
def test_no_subgraph_nodes():
    """AC-01: composition stays tool_call-only — no subgraph nodes."""
    node_types = {node["type"] for node in _graph()["nodes"].values()}
    assert "subgraph" not in node_types


@pytest.mark.req("REQ-YG-599")
def test_graph_compiles():
    """AC-01: load_and_compile succeeds with the v2 nodes present."""
    from yamlgraph.compile.graph_loader import load_and_compile

    assert load_and_compile(str(EXAMPLE_DIR / "graph.yaml")) is not None


# ---------------------------------------------------------------------------
# Recon gating (AC-02, AC-04)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-599")
def test_use_recon_defaults_true():
    """AC-02: use_recon input flag exists and defaults true."""
    state = _graph()["state"]
    assert state["use_recon"]["type"] == "bool"
    assert state["use_recon"]["default"] is True


@pytest.mark.req("REQ-YG-599")
def test_recon_gated_on_use_recon_and_feeds_candidates():
    """AC-04: recon runs only when use_recon is true; exits to generate_candidates."""
    graph = _graph()
    recon_entries = _edges_to(graph, "recon")
    assert len(recon_entries) == 1
    assert "use_recon == true" in recon_entries[0]["condition"]
    assert {e["to"] for e in _edges_from(graph, "recon")} == {"generate_candidates"}
    # the recon-disabled path reaches generate_candidates without recon
    bypass = [
        e
        for e in _edges_to(graph, "generate_candidates")
        if e["from"] != "recon" and "use_recon != true" in e.get("condition", "")
    ]
    assert bypass, "expected a use_recon != true bypass edge to generate_candidates"


@pytest.mark.req("REQ-YG-599")
def test_generate_candidates_consumes_recon_result():
    """AC-04: candidate generation receives recon_result as evidence."""
    node = _graph()["nodes"]["generate_candidates"]
    assert any(
        "recon_result" in str(expr) for expr in node.get("variables", {}).values()
    )


# ---------------------------------------------------------------------------
# Parsed outputs and browser-sniff entry (AC-03, R-1)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-599")
def test_parsed_keys_exposed():
    """AC-03: probe/page/sniff tool_calls expose parsed state keys (FR-810)."""
    nodes = _graph()["nodes"]
    for node_name, parsed_key in PARSED_KEYS.items():
        assert nodes[node_name].get("parsed_key") == parsed_key, node_name


@pytest.mark.req("REQ-YG-599")
def test_browser_sniff_entered_only_on_parsed_spa_without_api():
    """R-1: entry condition is exactly the parsed page_findings SPA clause."""
    graph = _graph()
    entries = _edges_to(graph, "browser_sniff")
    assert len(entries) == 1
    condition = entries[0]["condition"]
    assert "page_findings.is_spa == true" in condition
    assert "page_findings.api_found != true" in condition
    # never from candidate hints
    assert "candidate_urls" not in condition


@pytest.mark.req("REQ-YG-599")
def test_sniff_url_selection_is_deterministic():
    """R-2: sniff_url is produced without LLM choice and feeds browser_sniff args."""
    graph = _graph()
    nodes = graph["nodes"]
    # the producer is the pure python selector (dict-merge return), never an llm
    selector = nodes["select_sniff_url"]
    assert selector["type"] == "python"
    assert graph["tools"][selector["tool"]]["type"] == "python"
    assert (EXAMPLE_DIR / graph["tools"][selector["tool"]]["path"]).exists()
    for name, node in nodes.items():
        if node["type"] == "llm":
            assert node.get("state_key") != "sniff_url", name
    assert nodes["browser_sniff"]["args"]["url"] == "{state.sniff_url}"


# ---------------------------------------------------------------------------
# Terminal schema and evidence section (AC-06, AC-07, R-3)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-599")
def test_manual_reason_in_terminal_schema():
    """R-3: synthesize schema carries manual_reason; closed shape preserved."""
    schema = _synth_prompt()["output_schema"]
    assert "manual_reason" in schema["properties"]
    assert schema["properties"]["manual_reason"]["type"] == "string"
    assert schema["additionalProperties"] is False
    assert schema["properties"]["verdict"]["enum"] == [
        "found",
        "not_found",
        "needs_manual",
    ]


@pytest.mark.req("REQ-YG-599")
def test_steps_tried_evidence_covers_new_wrappers():
    """AC-07: actual-steps section gates recon and browser-sniff on wrapper content."""
    user = _synth_prompt()["user"]
    assert "- recon" in user
    assert "- browser-sniff" in user
    # copy-only discipline: each new label sits inside a wrapper-gated block
    for wrapper in ("recon_result", "sniff_result"):
        assert f"{{% if {wrapper}" in user, wrapper


@pytest.mark.req("REQ-YG-599")
def test_fetch_page_output_is_byte_capped():
    """Boundary: unbounded page HTML overflowed the LLM context (smoke pos5,
    213k tokens > 200k anthropic limit). fetch_page must cap its output."""
    raw = yaml.safe_load((EXAMPLE_DIR / "tools" / "fetch_page.tool.yaml").read_text(encoding="utf-8"))
    cmd = raw["runtime"]["command"]
    assert "head -c" in cmd, "fetch_page command must byte-cap its output"
    cap = int(cmd.split("head -c")[1].split()[0])
    assert 4_000 <= cap <= 40_000, cap
