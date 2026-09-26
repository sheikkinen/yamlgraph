"""FR-1085: one resolved ``max_concurrency`` at the six managed run boundaries.

Order: caller run value (or ``--max-concurrency``) → graph
``config.max_concurrency`` → ``YAMLGRAPH_MAX_CONCURRENCY`` → built-in 8.
Behavioural witnesses count in-flight map branches in a generated 40-item
graph; the host-width seam is the CPU source the running interpreter's
``ThreadPoolExecutor`` reads (Python 3.13: ``os.process_cpu_count``; 3.11
and 3.12: ``os.cpu_count``).
"""

from __future__ import annotations

import asyncio
import copy
import os
import sys
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

ENV = "YAMLGRAPH_MAX_CONCURRENCY"
ITEMS = 40
BOUNDARIES = (
    "cli_sync",
    "cli_async",
    "cli_stream",
    "invoke_graph",
    "run_graph_async",
    "run_graph_streaming_native",
)
RED_BOUNDARIES = ("cli_sync", "cli_async", "invoke_graph", "run_graph_async")

_LOCK = threading.Lock()
_ACTIVE = 0
_PEAK = 0
_CALLS = 0


def _reset() -> None:
    global _ACTIVE, _PEAK, _CALLS
    with _LOCK:
        _ACTIVE = _PEAK = _CALLS = 0


def counting_worker(state: dict) -> int:
    """Map sub-node: hold a slot for 50 ms and record peak occupancy."""
    global _ACTIVE, _PEAK, _CALLS
    with _LOCK:
        _CALLS += 1
        _ACTIVE += 1
        _PEAK = max(_PEAK, _ACTIVE)
    try:
        time.sleep(0.05)
    finally:
        with _LOCK:
            _ACTIVE -= 1
    return state["item"]


def _cpu_seam(count: int):
    name = "process_cpu_count" if sys.version_info >= (3, 13) else "cpu_count"
    return patch.object(os, name, return_value=count)


def _write_graph(tmp_path: Path, graph_width: int | None = None) -> Path:
    cfg: dict = {
        "name": "fr1085-fanout",
        "version": "1.0",
        "state": {
            "items": {"type": "list"},
            "results": {"type": "list", "reducer": "sorted_add"},
        },
        "tools": {
            "counter": {
                "type": "python",
                "module": __name__,
                "function": "counting_worker",
            }
        },
        "nodes": {
            "fan": {
                "type": "map",
                "over": "{state.items}",
                "as": "item",
                "node": {"type": "python", "tool": "counter", "state_key": "result"},
                "collect": "results",
            }
        },
        "edges": [{"from": "START", "to": "fan"}, {"from": "fan", "to": "END"}],
    }
    if graph_width is not None:
        cfg["config"] = {"max_concurrency": graph_width}
    path = tmp_path / f"graph-{graph_width}.yaml"
    path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return path


def _payload() -> dict:
    return {"items": list(range(ITEMS)), "results": []}


def _run_cli(tmp_path: Path, graph: Path, extra: list[str]) -> None:
    from yamlgraph.cli import create_parser
    from yamlgraph.cli.graph_commands import cmd_graph_run

    var_file = tmp_path / "vars.yaml"
    var_file.write_text(yaml.safe_dump({"items": list(range(ITEMS))}), "utf-8")
    args = create_parser().parse_args(
        ["graph", "run", str(graph), "--var-file", str(var_file), *extra]
    )
    with patch("yamlgraph.utils.tracing.create_tracer", return_value=None):
        try:
            cmd_graph_run(args)
        except SystemExit as exc:
            assert exc.code in (0, None), f"CLI exited {exc.code}"


async def _drain(graph: Path, config: dict | None) -> None:
    from yamlgraph.executor_async import run_graph_streaming_native

    async for _ in run_graph_streaming_native(
        str(graph), _payload(), config, yield_events=False
    ):
        pass


def _run(boundary: str, tmp_path: Path, graph: Path, caller: int | None) -> None:
    """Run the fixture through one managed boundary."""
    flag = ["--max-concurrency", str(caller)] if caller is not None else []
    config = {"max_concurrency": caller} if caller is not None else None
    if boundary == "cli_sync":
        _run_cli(tmp_path, graph, flag)
    elif boundary == "cli_async":
        _run_cli(tmp_path, graph, ["--async", *flag])
    elif boundary == "cli_stream":
        _run_cli(tmp_path, graph, ["--stream", *flag])
    elif boundary == "invoke_graph":
        from yamlgraph.compile.graph_loader import invoke_graph

        invoke_graph(graph, _payload(), config=config)
    elif boundary == "run_graph_async":
        from yamlgraph.executor_async import load_and_compile_async
        from yamlgraph.observability.otel import run_graph_async

        async def go() -> None:
            app = await load_and_compile_async(graph, cache=None)
            await run_graph_async(app, _payload(), config)

        asyncio.run(go())
    elif boundary == "run_graph_streaming_native":
        asyncio.run(_drain(graph, config))
    else:  # pragma: no cover - parametrisation guard
        raise AssertionError(boundary)


def _peak(boundary: str, tmp_path: Path, graph: Path, caller=None) -> int:
    _reset()
    _run(boundary, tmp_path, graph, caller)
    assert _CALLS == ITEMS, f"{boundary}: {_CALLS} of {ITEMS} branches ran"
    return _PEAK


@pytest.fixture(autouse=True)
def _no_env(monkeypatch):
    monkeypatch.delenv(ENV, raising=False)


# ---------------------------------------------------------------------------
# AC-01 (RED on main) / AC-02 — default width at every managed boundary
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-698")
@pytest.mark.parametrize("boundary", RED_BOUNDARIES)
def test_ac01_host_width_64_is_capped_at_8(boundary, tmp_path):
    graph = _write_graph(tmp_path)
    with _cpu_seam(64):
        peak = _peak(boundary, tmp_path, graph)
    assert peak <= 8, f"{boundary}: measured peak {peak} with 64 CPUs, no width"


@pytest.mark.req("REQ-YG-698")
@pytest.mark.parametrize("cpus", [2, 64])
@pytest.mark.parametrize("boundary", BOUNDARIES)
def test_ac02_default_width_is_8_at_every_boundary(boundary, cpus, tmp_path):
    graph = _write_graph(tmp_path)
    with _cpu_seam(cpus):
        peak = _peak(boundary, tmp_path, graph)
    assert 1 <= peak <= 8, f"{boundary} @ {cpus} CPUs: peak {peak}"


@pytest.mark.req("REQ-YG-698")
def test_ac02_resolver_default_is_exactly_8():
    from yamlgraph.utils.concurrency import resolve_max_concurrency

    assert resolve_max_concurrency(None, None) == 8


# ---------------------------------------------------------------------------
# AC-03 — precedence, exact resolution and behavioural cap
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-698")
@pytest.mark.parametrize(
    ("caller", "graph", "env", "expected"),
    [
        (2, 3, "5", 2),
        (None, 3, "5", 3),
        (None, None, "5", 5),
        (None, None, None, 8),
    ],
    ids=["caller", "graph", "env", "default"],
)
def test_ac03_precedence_is_exact(caller, graph, env, expected, monkeypatch):
    from yamlgraph.utils.concurrency import resolve_max_concurrency

    if env is not None:
        monkeypatch.setenv(ENV, env)
    assert resolve_max_concurrency(caller, graph) == expected


@pytest.mark.req("REQ-YG-698")
@pytest.mark.parametrize(
    ("caller", "graph_width", "env", "expected"),
    [(2, 3, "5", 2), (None, 3, "5", 3), (None, None, "5", 5)],
    ids=["caller", "graph", "env"],
)
@pytest.mark.parametrize("boundary", BOUNDARIES)
def test_ac03_selected_width_caps_the_peak(
    boundary, caller, graph_width, env, expected, tmp_path, monkeypatch
):
    monkeypatch.setenv(ENV, env)
    graph = _write_graph(tmp_path, graph_width)
    with _cpu_seam(64):
        peak = _peak(boundary, tmp_path, graph, caller)
    assert 1 <= peak <= expected, f"{boundary}: peak {peak} > {expected}"


# ---------------------------------------------------------------------------
# AC-04 — graph width on the programmatic boundaries
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-698")
@pytest.mark.parametrize(("caller", "expected"), [(None, 3), (2, 2)])
@pytest.mark.parametrize("boundary", ["run_graph_async", "invoke_graph"])
def test_ac04_graph_width_3_reaches_the_api(boundary, caller, expected, tmp_path):
    graph = _write_graph(tmp_path, 3)
    with _cpu_seam(64):
        peak = _peak(boundary, tmp_path, graph, caller)
    assert 1 <= peak <= expected, f"{boundary}: peak {peak} > {expected}"


# ---------------------------------------------------------------------------
# AC-05 — validation at the boundary, before any node runs
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-698")
@pytest.mark.parametrize("raw", ["", "abc", "0", "-1", "2.5", "true"])
def test_ac05_bad_env_raises_naming_variable_and_value(raw, monkeypatch):
    from yamlgraph.utils.concurrency import resolve_max_concurrency

    monkeypatch.setenv(ENV, raw)
    with pytest.raises(ValueError, match=ENV) as exc:
        resolve_max_concurrency(None, None)
    assert repr(raw) in str(exc.value)


@pytest.mark.req("REQ-YG-698")
@pytest.mark.parametrize("bad", [True, False, "4", 2.5, 0, -1])
def test_ac05_bad_caller_value_raises_naming_source_and_value(bad):
    from yamlgraph.utils.concurrency import resolve_max_concurrency

    with pytest.raises(ValueError, match="max_concurrency") as exc:
        resolve_max_concurrency(bad, 4)
    assert repr(bad) in str(exc.value)


@pytest.mark.req("REQ-YG-698")
def test_ac05_positive_integers_accepted(monkeypatch):
    from yamlgraph.utils.concurrency import resolve_max_concurrency

    assert resolve_max_concurrency(1, None) == 1
    monkeypatch.setenv(ENV, "12")
    assert resolve_max_concurrency(None, None) == 12


@pytest.mark.req("REQ-YG-698")
@pytest.mark.parametrize("boundary", BOUNDARIES)
def test_ac05_bad_env_raises_before_any_node_runs(boundary, tmp_path, monkeypatch):
    monkeypatch.setenv(ENV, "abc")
    graph = _write_graph(tmp_path)
    _reset()
    with pytest.raises((ValueError, SystemExit)):
        _run(boundary, tmp_path, graph, None)
    assert _CALLS == 0


@pytest.mark.req("REQ-YG-698")
@pytest.mark.parametrize("boundary", ["invoke_graph", "run_graph_async"])
def test_ac05_bad_caller_raises_before_any_node_runs(boundary, tmp_path):
    graph = _write_graph(tmp_path)
    _reset()
    with pytest.raises(ValueError, match="max_concurrency"):
        _run(boundary, tmp_path, graph, 0)
    assert _CALLS == 0


# ---------------------------------------------------------------------------
# AC-07 — caller config preserved and unmutated
# ---------------------------------------------------------------------------


def _caller_config() -> dict:
    return {
        "configurable": {"thread_id": "t-1085"},
        "callbacks": [object()],
        "tags": ["fr1085"],
        "metadata": {"trace": "keep"},
        "recursion_limit": 17,
    }


class _SpyApp:
    """Compiled-app stand-in recording the config each boundary passes on."""

    def __init__(self) -> None:
        self.seen: list[dict] = []

    def invoke(self, state, config=None):
        self.seen.append(config)
        return {}

    async def ainvoke(self, state, config=None):
        self.seen.append(config)
        return {}

    async def astream(self, state, config=None, **_):
        self.seen.append(config)
        if False:  # pragma: no cover - makes this an async generator
            yield None

    async def aget_state(self, config):
        return MagicMock(tasks=())


def _assert_preserved(original: dict, caller: dict, seen: dict, width: int) -> None:
    assert caller == original, "caller-owned mapping was mutated"
    assert seen is not caller
    assert seen["max_concurrency"] == width
    for key in ("configurable", "tags", "metadata", "recursion_limit"):
        assert seen[key] == original[key]
    assert seen["callbacks"][0] is caller["callbacks"][0]


@pytest.mark.req("REQ-YG-698")
def test_ac07_invoke_graph_preserves_config(tmp_path):
    from yamlgraph.compile import graph_loader

    spy = _SpyApp()
    caller = _caller_config()
    original = copy.copy(caller)
    loaded = MagicMock(max_concurrency=3)
    with (
        patch.object(graph_loader, "load_graph_config", return_value=loaded),
        patch.object(graph_loader, "compile_graph") as compile_graph,
    ):
        compile_graph.return_value.compile.return_value = spy
        graph_loader.invoke_graph(tmp_path / "g.yaml", {}, config=caller)
    _assert_preserved(original, caller, spy.seen[0], 3)


@pytest.mark.req("REQ-YG-698")
def test_ac07_run_graph_async_without_metadata_uses_env_then_default(monkeypatch):
    from yamlgraph.observability.otel import run_graph_async

    spy = _SpyApp()
    caller = _caller_config()
    original = copy.copy(caller)
    asyncio.run(run_graph_async(spy, {}, caller))
    _assert_preserved(original, caller, spy.seen[0], 8)

    monkeypatch.setenv(ENV, "5")
    asyncio.run(run_graph_async(spy, {}, caller))
    assert spy.seen[1]["max_concurrency"] == 5

    asyncio.run(run_graph_async(spy, {}, {**caller, "max_concurrency": 2}))
    assert spy.seen[2]["max_concurrency"] == 2


@pytest.mark.req("REQ-YG-698")
def test_ac07_run_graph_async_reads_graph_width_metadata():
    from yamlgraph.utils.concurrency import GRAPH_WIDTH_ATTR

    from yamlgraph.observability.otel import run_graph_async

    spy = _SpyApp()
    setattr(spy, GRAPH_WIDTH_ATTR, 3)
    caller = _caller_config()
    original = copy.copy(caller)
    asyncio.run(run_graph_async(spy, {}, caller))
    _assert_preserved(original, caller, spy.seen[0], 3)


@pytest.mark.req("REQ-YG-698")
def test_ac07_streaming_native_preserves_config():
    from yamlgraph.utils.concurrency import GRAPH_WIDTH_ATTR

    import yamlgraph.executor_async as executor_async

    spy = _SpyApp()
    setattr(spy, GRAPH_WIDTH_ATTR, 3)
    caller = _caller_config()
    original = copy.copy(caller)

    async def fake_load(_path):
        return spy

    async def go() -> None:
        async for _ in executor_async.run_graph_streaming_native(
            "g.yaml", {}, caller, yield_events=False
        ):
            pass

    with patch.object(executor_async, "load_and_compile_async", fake_load):
        asyncio.run(go())
    _assert_preserved(original, caller, spy.seen[0], 3)


@pytest.mark.req("REQ-YG-698")
def test_ac07_load_and_compile_async_records_graph_width(tmp_path):
    from yamlgraph.utils.concurrency import GRAPH_WIDTH_ATTR

    from yamlgraph.executor_async import load_and_compile_async

    app = asyncio.run(load_and_compile_async(_write_graph(tmp_path, 3), cache=None))
    assert getattr(app, GRAPH_WIDTH_ATTR) == 3
    app = asyncio.run(load_and_compile_async(_write_graph(tmp_path), cache=None))
    assert getattr(app, GRAPH_WIDTH_ATTR) is None
