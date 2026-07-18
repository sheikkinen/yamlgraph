"""RED acceptance tests for FR-445 python tool graph-root confinement."""

from __future__ import annotations

from pathlib import Path

import pytest

from yamlgraph.compile.graph_loader import load_and_compile


def _write_python_tool(path: Path, function_name: str = "run") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"def {function_name}(state):\n    return {{'ok': True}}\n", encoding="utf-8"
    )


def _write_graph(path: Path, tool_block: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        (
            "version: '1.0'\n"
            "name: fr445_python_tool_graph_root_confinement\n"
            "state:\n"
            "  result: dict\n"
            "tools:\n"
            f"{tool_block}\n"
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


@pytest.mark.req("REQ-YG-196")
def test_ac01_relative_in_root_path_loads_from_graph_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    graph_dir = tmp_path / "project" / "graphs"
    tool_path = graph_dir / "tools" / "helper.py"
    _write_python_tool(tool_path)

    graph_path = graph_dir / "graph.yaml"
    _write_graph(
        graph_path,
        "  test_tool:\n"
        "    type: python\n"
        "    path: tools/helper.py\n"
        "    function: run",
    )

    monkeypatch.chdir(tmp_path)
    load_and_compile(graph_path)


@pytest.mark.req("REQ-YG-196")
def test_ac02_relative_escape_path_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    graph_dir = tmp_path / "project" / "graphs"
    outside_tool = tmp_path / "project" / "outside.py"
    _write_python_tool(outside_tool)

    graph_path = graph_dir / "graph.yaml"
    _write_graph(
        graph_path,
        "  test_tool:\n"
        "    type: python\n"
        "    path: ../outside.py\n"
        "    function: run",
    )

    monkeypatch.chdir(graph_dir)
    with pytest.raises(ValueError, match="escape|outside|graph root|graph directory"):
        load_and_compile(graph_path)


@pytest.mark.req("REQ-YG-196")
def test_ac03_absolute_out_of_root_path_is_rejected(tmp_path: Path) -> None:
    graph_dir = tmp_path / "project" / "graphs"
    outside_tool = tmp_path / "outside.py"
    _write_python_tool(outside_tool)

    graph_path = graph_dir / "graph.yaml"
    _write_graph(
        graph_path,
        "  test_tool:\n"
        "    type: python\n"
        f"    path: {outside_tool}\n"
        "    function: run",
    )

    with pytest.raises(ValueError, match="escape|outside|graph root|graph directory"):
        load_and_compile(graph_path)


@pytest.mark.req("REQ-YG-196")
def test_ac04_absolute_in_root_path_is_allowed(tmp_path: Path) -> None:
    graph_dir = tmp_path / "project" / "graphs"
    in_root_tool = graph_dir / "tools" / "inside.py"
    _write_python_tool(in_root_tool)

    graph_path = graph_dir / "graph.yaml"
    _write_graph(
        graph_path,
        "  test_tool:\n"
        "    type: python\n"
        f"    path: {in_root_tool}\n"
        "    function: run",
    )

    load_and_compile(graph_path)


@pytest.mark.req("REQ-YG-196")
def test_ac05_module_loading_unchanged(tmp_path: Path) -> None:
    graph_path = tmp_path / "graph.yaml"
    _write_graph(
        graph_path,
        "  test_tool:\n"
        "    type: python\n"
        "    module: os.path\n"
        "    function: join",
    )

    load_and_compile(graph_path)
