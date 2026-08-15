"""Tests for FR-792 multi-step investigation scaffold (REQ-YG-596).

Tests cover:
- Full directory generation for 3-step and 6-step skeletons (AC-03, AC-07)
- Orchestrator tool_call composition, no subgraph nodes (AC-04)
- Step manifest graph-runtime path resolution (AC-05)
- Step graph placeholder shape and typed output schema (AC-06)
- Lint on every generated graph (AC-07)
- Deterministic --stub end-to-end smoke asserting final state shape (AC-08)
- Generated README contract (AC-09)

All generation happens in pytest tmp_path directories — never governed
paths (AC-10).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "scaffold_investigation.py"

THREE_STEPS = ["registry", "financials", "news"]
SIX_STEPS = ["recon", "probe", "pages", "sniff", "confirm", "extract"]


def _load_scaffold_module():
    spec = importlib.util.spec_from_file_location("scaffold_investigation", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["scaffold_investigation"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def scaffold():
    return _load_scaffold_module()


def _generate(scaffold, home: Path, steps: list[str], *, stub: bool = False) -> Path:
    scaffold.scaffold_investigation(name=home.name, steps=steps, home=home, stub=stub)
    return home


def _lint_clean(graph_path: Path) -> bool:
    from yamlgraph.linter import lint_graph

    result = lint_graph(graph_path, graph_path.parent)
    return not [i for i in result.issues if i.severity == "error"]


# ---------------------------------------------------------------------------
# Directory structure (AC-03, AC-07)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-596")
@pytest.mark.parametrize("steps", [THREE_STEPS, SIX_STEPS], ids=["3-step", "6-step"])
def test_generates_full_directory_structure(scaffold, tmp_path: Path, steps: list[str]):
    """AC-03/AC-07: exact file paths exist for every requested step."""
    home = _generate(scaffold, tmp_path / "invest", steps)
    assert (home / "graph.yaml").exists()
    assert (home / "tools" / "README.md").exists()
    for step in steps:
        assert (home / "steps" / f"{step}.tool.yaml").exists()
        assert (home / "steps" / step / "graph.yaml").exists()
        assert (home / "steps" / step / "prompts" / "investigate.yaml").exists()


# ---------------------------------------------------------------------------
# Orchestrator composition (AC-04)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-596")
def test_orchestrator_uses_tool_call_not_subgraph(scaffold, tmp_path: Path):
    """AC-04: one tool_call node per step referencing its manifest; no subgraph."""
    home = _generate(scaffold, tmp_path / "invest", THREE_STEPS)
    graph = yaml.safe_load((home / "graph.yaml").read_text())
    node_types = {n["type"] for n in graph["nodes"].values()}
    assert "subgraph" not in node_types
    for step in THREE_STEPS:
        assert graph["tools"][step]["manifest"] == f"steps/{step}.tool.yaml"
        node = graph["nodes"][step]
        assert node["type"] == "tool_call"
        assert node["tool"] == step
    assert graph["nodes"]["synthesize"]["type"] in {"llm", "passthrough"}


# ---------------------------------------------------------------------------
# Step manifests (AC-05)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-596")
def test_step_manifests_resolve_from_manifest_location(scaffold, tmp_path: Path):
    """AC-05: runtime.type graph with a path that resolves relative to the manifest."""
    home = _generate(scaffold, tmp_path / "invest", THREE_STEPS)
    for step in THREE_STEPS:
        manifest_path = home / "steps" / f"{step}.tool.yaml"
        manifest = yaml.safe_load(manifest_path.read_text())
        assert manifest["name"] == step
        assert manifest["runtime"]["type"] == "graph"
        child = (manifest_path.parent / manifest["runtime"]["path"]).resolve()
        assert child.exists()


# ---------------------------------------------------------------------------
# Step graph shape (AC-06)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-596")
def test_step_graphs_have_placeholder_agent_and_typed_schema(scaffold, tmp_path: Path):
    """AC-06: default skeleton step = agent node + typed output schema stub."""
    home = _generate(scaffold, tmp_path / "invest", THREE_STEPS)
    for step in THREE_STEPS:
        graph = yaml.safe_load((home / "steps" / step / "graph.yaml").read_text())
        agent_nodes = [n for n in graph["nodes"].values() if n["type"] == "agent"]
        assert len(agent_nodes) == 1
        prompt = yaml.safe_load(
            (home / "steps" / step / "prompts" / "investigate.yaml").read_text()
        )
        schema = prompt["output_schema"]
        assert schema["properties"]["findings"]["items"]["type"] == "string"
        assert schema["properties"]["confidence"]["type"] == "string"
        assert set(schema["required"]) == {"findings", "confidence"}


# ---------------------------------------------------------------------------
# Lint every generated graph (AC-07)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-596")
@pytest.mark.parametrize("stub", [False, True], ids=["default", "stub"])
@pytest.mark.parametrize("steps", [THREE_STEPS, SIX_STEPS], ids=["3-step", "6-step"])
def test_all_generated_graphs_lint_clean(
    scaffold, tmp_path: Path, steps: list[str], stub: bool
):
    """AC-07: orchestrator and every step graph pass lint with zero errors."""
    home = _generate(scaffold, tmp_path / "invest", steps, stub=stub)
    assert _lint_clean(home / "graph.yaml")
    for step in steps:
        assert _lint_clean(home / "steps" / step / "graph.yaml")


@pytest.mark.req("REQ-YG-596")
def test_generated_orchestrator_compiles(scaffold, tmp_path: Path):
    """AC-07 support: load_and_compile resolves manifests end-to-end."""
    from yamlgraph.compile.graph_loader import load_and_compile

    home = _generate(scaffold, tmp_path / "invest", THREE_STEPS, stub=True)
    assert load_and_compile(str(home / "graph.yaml")) is not None


# ---------------------------------------------------------------------------
# Deterministic --stub end-to-end smoke (AC-08)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-596")
def test_stub_skeleton_runs_end_to_end_without_providers(scaffold, tmp_path: Path):
    """AC-08: --stub orchestrator runs deterministically; final state shape asserted."""
    home = _generate(scaffold, tmp_path / "invest", THREE_STEPS, stub=True)
    from yamlgraph.compile.graph_loader import load_and_compile

    compiled = load_and_compile(str(home / "graph.yaml"))
    final = compiled.invoke({"objective": "smoke objective"})
    result = final["result"]
    assert result["verdict"] == "stub"
    for step in THREE_STEPS:
        wrapper = final[f"{step}_result"]
        assert wrapper["success"] is True
        assert step in str(wrapper["result"])


# ---------------------------------------------------------------------------
# Generated README (AC-09)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-596")
def test_readme_documents_tools_edges_and_prompts(scaffold, tmp_path: Path):
    """AC-09: README explains leaf manifests, conditional edges, TODO prompts."""
    home = _generate(scaffold, tmp_path / "invest", THREE_STEPS)
    readme = (home / "tools" / "README.md").read_text().lower()
    assert "tool.yaml" in readme
    assert "manifest" in readme
    assert "condition" in readme
    assert "prompt" in readme
