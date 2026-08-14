"""RED/GREEN tests for FR-794 shared Python tool manifest root confinement fix.

FR-445 confines `type: python` file-tool paths to the *consuming graph's*
root. FR-768 manifest sharing resolves a manifest-declared `path:` relative
to the *manifest's own* directory instead. The two checks disagree whenever
a manifest lives outside the consuming graph's directory tree (the "one
tool, many consumers" pattern) — this file proves the bug and the fix.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from yamlgraph.compile.graph_loader import load_and_compile
from yamlgraph.tools.manifest import expand_tool_manifests
from yamlgraph.tools.python_tool import load_python_function, parse_python_tools


def _write_tool_py(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "def run(state):\n    return {'result': {'ok': True}}\n", encoding="utf-8"
    )


def _write_manifest(path: Path, tool_py_relative: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        (
            "name: shared_tool\n"
            "description: shared python tool\n"
            "runtime:\n"
            "  type: python\n"
            f"  path: {tool_py_relative}\n"
            "  function: run\n"
        ),
        encoding="utf-8",
    )


def _write_consumer_graph(path: Path, manifest_relative: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        (
            "version: '1.0'\n"
            "name: fr794_manifest_root_fix\n"
            "state:\n"
            "  result: dict\n"
            "tools:\n"
            "  shared_tool:\n"
            f"    manifest: {manifest_relative}\n"
            "nodes:\n"
            "  run_tool:\n"
            "    type: python\n"
            "    tool: shared_tool\n"
            "    state_key: result\n"
            "edges:\n"
            "  - from: START\n"
            "    to: run_tool\n"
            "  - from: run_tool\n"
            "    to: END\n"
        ),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# AC-01/AC-02: cross-directory manifest-shared python tool loads and executes
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-588")
def test_manifest_python_tool_loads_and_executes_across_directories(
    tmp_path: Path,
) -> None:
    """A type: python manifest in a sibling directory tree must be usable."""
    tool_py = tmp_path / "shared" / "tools" / "shared_tool.py"
    _write_tool_py(tool_py)
    manifest_path = tmp_path / "shared" / "tools" / "shared_tool.tool.yaml"
    _write_manifest(manifest_path, "shared_tool.py")

    graph_path = tmp_path / "steps" / "consumer" / "graph.yaml"
    _write_consumer_graph(graph_path, "../../shared/tools/shared_tool.tool.yaml")

    graph = load_and_compile(graph_path)
    result = graph.compile().invoke({})
    assert result["result"] == {"ok": True}


@pytest.mark.req("REQ-YG-588")
def test_manifest_path_escaping_manifest_dir_is_rejected(tmp_path: Path) -> None:
    """A manifest whose own path escapes ITS OWN directory must be rejected,
    even when the escape target still lives inside the consuming graph's
    root (the gap FR-445's graph-root-only check could not see)."""
    # Escape target lives under the graph root but OUTSIDE the manifest's
    # own directory (manifest is nested one level deeper than the tool).
    tool_py = tmp_path / "steps" / "consumer" / "outside_manifest.py"
    _write_tool_py(tool_py)
    manifest_path = tmp_path / "steps" / "consumer" / "nested" / "shared_tool.tool.yaml"
    _write_manifest(manifest_path, "../outside_manifest.py")

    graph_path = tmp_path / "steps" / "consumer" / "graph.yaml"
    _write_consumer_graph(graph_path, "nested/shared_tool.tool.yaml")

    with pytest.raises(ValueError, match="escape|manifest"):
        load_and_compile(graph_path)


# ---------------------------------------------------------------------------
# AC-04: FR-445 inline-tool graph-root confinement is unaffected (regression)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-588")
def test_inline_tool_escape_still_rejected(tmp_path: Path) -> None:
    """Inline (non-manifest) type: python tools keep graph-root confinement."""
    outside_tool = tmp_path / "outside.py"
    _write_tool_py(outside_tool)

    graph_dir = tmp_path / "project" / "graph"
    graph_path = graph_dir / "graph.yaml"
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    graph_path.write_text(
        (
            "version: '1.0'\n"
            "name: fr794_inline_regression\n"
            "state:\n"
            "  result: dict\n"
            "tools:\n"
            "  test_tool:\n"
            "    type: python\n"
            "    path: ../../outside.py\n"
            "    function: run\n"
            "nodes:\n"
            "  run_tool:\n"
            "    type: python\n"
            "    tool: test_tool\n"
            "    state_key: result\n"
            "edges:\n"
            "  - from: START\n"
            "    to: run_tool\n"
            "  - from: run_tool\n"
            "    to: END\n"
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="escape|graph root"):
        load_and_compile(graph_path)


# ---------------------------------------------------------------------------
# AC-05: the already-merged FR-785 endpoint-probe graph's tool loading is
# repaired (full graph compile stays blocked on the separate FR-795
# prompt-schema repair, per the judge's SPLIT verdict; not asserted here).
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-588")
def test_endpoint_probe_curl_probe_tool_loads_without_escape_error() -> None:
    """FR-785's shared curl_probe manifest must load at the tool seam."""
    repo_root = Path(__file__).resolve().parents[2]
    graph_path = (
        repo_root
        / "examples"
        / "api-discovery"
        / "steps"
        / "endpoint-probe"
        / "graph.yaml"
    )
    graph_config = {"curl_probe": {"manifest": "../../tools/curl_probe.tool.yaml"}}
    expanded = expand_tool_manifests(graph_config, graph_path)
    python_tools = parse_python_tools(expanded)

    func = load_python_function(
        python_tools["curl_probe"],
        graph_root=graph_path.parent,
        tool_name="curl_probe",
    )
    assert callable(func)
