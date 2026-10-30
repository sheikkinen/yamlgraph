"""FR-1153: a node's timeout must not drop the LangGraph runnable context.

Every graph here is compiled from YAML; the python tools below are the
nodes' callables and read the run's config through ``get_config()``.
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from langgraph.config import get_config

from yamlgraph.compile.graph_loader import compile_graph, load_graph_config
from yamlgraph.observability import otel

try:
    import opentelemetry.sdk as otel_sdk
except ImportError:
    otel_sdk = None

requires_otel_sdk = pytest.mark.skipif(
    otel_sdk is None, reason="requires the 'otel' extra (opentelemetry-sdk)"
)

_MODULE = "tests.unit.test_fr1153_timeout_runnable_context"
_barrier: threading.Barrier | None = None


def observe(_state: dict) -> dict:
    if _barrier is not None:
        _barrier.wait(timeout=3)
    return {"observed": get_config()["configurable"]["sentinel"]}


def observe_item(_state: dict) -> str:
    if _barrier is not None:
        _barrier.wait(timeout=3)
    return get_config()["configurable"]["sentinel"]


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    global _barrier
    _barrier = None
    monkeypatch.delenv(otel.ENV_VAR, raising=False)
    yield
    _barrier = None


def _python_graph(tmp_path, *, timeout: bool):
    path = tmp_path / "graph.yaml"
    path.write_text(
        'version: "1.0"\n'
        "name: fr1153-python\n"
        "state:\n"
        "  observed: str\n"
        "tools:\n"
        "  observe:\n"
        "    type: python\n"
        f"    module: {_MODULE}\n"
        "    function: observe\n"
        "nodes:\n"
        "  observe:\n"
        "    type: python\n"
        "    tool: observe\n"
        "    on_error: fail\n" + ("    timeout: 5\n" if timeout else "") + "edges:\n"
        "  - {from: START, to: observe}\n"
        "  - {from: observe, to: END}\n"
    )
    return compile_graph(load_graph_config(path)).compile()


def _map_graph(tmp_path):
    path = tmp_path / "map.yaml"
    path.write_text(
        'version: "1.0"\n'
        "name: fr1153-map\n"
        "state:\n"
        "  items: list\n"
        "  results: list\n"
        "tools:\n"
        "  observe_item:\n"
        "    type: python\n"
        f"    module: {_MODULE}\n"
        "    function: observe_item\n"
        "nodes:\n"
        "  fan:\n"
        "    type: map\n"
        '    over: "{state.items}"\n'
        "    as: item\n"
        "    max_items: 5\n"
        "    timeout: 5\n"
        "    min_success: 0.0\n"
        "    node:\n"
        "      type: python\n"
        "      tool: observe_item\n"
        "      state_key: observed\n"
        "      on_error: fail\n"
        "    collect: results\n"
        "edges:\n"
        "  - {from: START, to: fan}\n"
        "  - {from: fan, to: END}\n"
    )
    return compile_graph(load_graph_config(path)).compile()


def _invoke_python(app, sentinel: str) -> str:
    return app.invoke({}, {"configurable": {"sentinel": sentinel}})["observed"]


def _invoke_map(app, sentinel: str, items: list) -> list[str]:
    result = app.invoke({"items": items}, {"configurable": {"sentinel": sentinel}})
    assert result["results_failures"] == []
    return [r["value"] for r in result["results"]]


def _overlapped(fn, *args_per_call):
    global _barrier
    _barrier = threading.Barrier(len(args_per_call))
    with ThreadPoolExecutor(max_workers=len(args_per_call)) as pool:
        futures = [pool.submit(fn, *args) for args in args_per_call]
        return [f.result(timeout=10) for f in futures]


@pytest.mark.req("REQ-YG-078")
def test_python_node_without_timeout_sees_config(tmp_path):
    app = _python_graph(tmp_path, timeout=False)
    assert [_invoke_python(app, s) for s in ("a", "b")] == ["a", "b"]


@pytest.mark.req("REQ-YG-078")
def test_timed_python_node_sees_config(tmp_path):
    app = _python_graph(tmp_path, timeout=True)
    assert [_invoke_python(app, s) for s in ("a", "b")] == ["a", "b"]


@pytest.mark.req("REQ-YG-078")
def test_timed_map_node_sees_config(tmp_path):
    app = _map_graph(tmp_path)
    assert _invoke_map(app, "a", [1, 2]) == ["a", "a"]
    assert _invoke_map(app, "b", [1, 2]) == ["b", "b"]


@pytest.mark.req("REQ-YG-078")
def test_timed_python_node_overlapping_invocations_are_isolated(tmp_path):
    app = _python_graph(tmp_path, timeout=True)
    got = _overlapped(_invoke_python, (app, "a"), (app, "b"))
    assert got == ["a", "b"]


@pytest.mark.req("REQ-YG-078")
def test_timed_map_node_overlapping_invocations_are_isolated(tmp_path):
    app = _map_graph(tmp_path)
    got = _overlapped(_invoke_map, (app, "a", [1]), (app, "b", [1]))
    assert got == [["a"], ["b"]]


@requires_otel_sdk
@pytest.mark.req("REQ-YG-078", "REQ-YG-570")
def test_timed_python_node_sees_config_with_otel_enabled(tmp_path, in_memory_exporter):
    app = _python_graph(tmp_path, timeout=True)
    assert _invoke_python(app, "a") == "a"

    node_spans = [
        s
        for s in in_memory_exporter.get_finished_spans()
        if s.name == otel.NODE_EXECUTE_SPAN
        and s.attributes["yamlgraph.node.name"] == "observe"
    ]
    assert len(node_spans) == 1
    assert node_spans[0].end_time is not None
