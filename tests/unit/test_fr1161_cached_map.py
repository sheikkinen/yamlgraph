"""FR-1161: `type: cached_map` warm-first map dispatch.

REQ-YG-728 witnesses. A cached_map freezes its population at dispatch,
runs item 0's worker alone, then fans out items 1..N-1 from the frozen
snapshot. Results, failures, accounting and verdict follow the FR-1073 map
contract. Graphs are built from real YAML via load_and_compile; workers
are Python tools that log their start/end to a per-test file.
"""

import asyncio
import re
import textwrap
from pathlib import Path

import pytest
from pydantic import BaseModel

from yamlgraph.compile.graph_loader import load_and_compile
from yamlgraph.models.state_builder import build_state_class

TOOLS_SRC = textwrap.dedent(
    '''
    """FR-1161 test tools."""

    import os
    import threading
    import time

    _LOCK = threading.Lock()
    _BARRIERS = {}
    _INFLIGHT = {}


    def _log(state, event):
        with _LOCK:
            with open(state["log"], "a", encoding="utf-8") as fh:
                fh.write(f"{event} {state['_map_index']}\\n")


    def _name(item):
        return item if isinstance(item, str) else item["name"]


    def record(state):
        _log(state, "start")
        time.sleep(0.05)
        _log(state, "end")
        return {"out": {"v": _name(state["item"])}}


    def overlap(state):
        _log(state, "start")
        if state["_map_index"] >= 1:
            with _LOCK:
                key = state["log"]
                if key not in _BARRIERS:
                    _BARRIERS[key] = threading.Barrier(len(state["items"]) - 1)
                barrier = _BARRIERS[key]
            barrier.wait(timeout=5)
        _log(state, "end")
        return {"out": {"v": _name(state["item"])}}


    def peak(state):
        key = state["log"]
        with _LOCK:
            now, top = _INFLIGHT.get(key, (0, 0))
            _INFLIGHT[key] = (now + 1, max(top, now + 1))
        time.sleep(0.15)
        with _LOCK:
            now, top = _INFLIGHT[key]
            _INFLIGHT[key] = (now - 1, top)
            with open(key + ".peak", "w", encoding="utf-8") as fh:
                fh.write(str(top))
        return {"out": {"v": _name(state["item"])}}


    def warm_outcome(state):
        _log(state, "start")
        if state["_map_index"] == 0:
            mode = state["mode"]
            if mode == "raise":
                raise ValueError("warm poison")
            if mode == "skip":
                return {"out": None, "_skipped": True, "errors": ["warm skip"]}
            if mode == "timeout":
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline:
                    if os.path.exists(state["log"] + ".release"):
                        break
                    time.sleep(0.02)
        _log(state, "end")
        return {"out": {"v": _name(state["item"])}}


    def count_results(state):
        _log(state, "start")
        return {"out": {"v": _name(state["item"]), "n": len(state.get("results") or [])}}


    def typed(state):
        item, cfg = state["item"], state["cfg"]
        if type(item).__name__ != "Item" or type(cfg).__name__ != "Cfg":
            raise TypeError(f"{type(item).__name__}/{type(cfg).__name__}")
        return {"out": {"v": item.name, "tag": cfg.tag}}


    def child_step(state):
        with _LOCK:
            with open(state["log"], "a", encoding="utf-8") as fh:
                fh.write(f"child-start {state['idx']}\\n")
        time.sleep(0.1)
        with _LOCK:
            with open(state["log"], "a", encoding="utf-8") as fh:
                fh.write(f"child-end {state['idx']}\\n")
        return {"done": state["item"]}


    def consume(state):
        return {"seen": [r["v"] for r in state.get("results") or [] if "v" in r]}
    '''
)

GRAPH = """
name: fr1161
description: cached_map witness.

state:
  items: list
  results: list
  seen: list
  log: str
  mode: str
  cfg: any

tools:
  sub:
    type: python
    path: tools_fr1161.py
    function: @FN@
  consume:
    type: python
    path: tools_fr1161.py
    function: consume

nodes:
  fan:
    type: @TYPE@
    over: "@OVER@"
    as: item
    node:
      type: python
      tool: sub
      state_key: out
    collect: results
@EXTRA@
  consume:
    type: python
    tool: consume
@NODES@
edges:
@EDGES@
"""

DEFAULT_EDGES = """  - from: START
    to: fan
  - from: fan
    to: consume
  - from: consume
    to: END
"""


class Item(BaseModel):
    name: str


class Cfg(BaseModel):
    tag: str


def _compile(
    tmp_path: Path,
    fn: str = "record",
    kind: str = "cached_map",
    extra: str = "",
    nodes: str = "",
    edges: str = DEFAULT_EDGES,
    over: str = "{state.items}",
):
    (tmp_path / "tools_fr1161.py").write_text(TOOLS_SRC, encoding="utf-8")
    text = (
        GRAPH.replace("@FN@", fn)
        .replace("@TYPE@", kind)
        .replace("@OVER@", over)
        .replace("@EXTRA@", textwrap.indent(textwrap.dedent(extra), "    "))
        .replace("@NODES@", nodes)
        .replace("@EDGES@", edges)
    )
    path = tmp_path / f"graph_{kind}.yaml"
    path.write_text(text, encoding="utf-8")
    return load_and_compile(str(path))


def _run(tmp_path: Path, items: list, config: dict | None = None, **kw) -> dict:
    state = {"items": items, "log": str(tmp_path / "events.log")}
    state.update(kw.pop("state", {}))
    return _compile(tmp_path, **kw).compile().invoke(state, config or {})


def _events(tmp_path: Path) -> list[tuple[str, int]]:
    lines = (tmp_path / "events.log").read_text(encoding="utf-8").splitlines()
    return [(e, int(i)) for e, i in (line.split() for line in lines)]


def _warm_first(events: list[tuple[str, int]]) -> bool:
    """Item 0 ended before any other item started."""
    end0 = events.index(("end", 0))
    return all(pos > end0 for pos, (e, i) in enumerate(events) if i != 0)


# --- 1, 2: order and kept parallelism --------------------------------------


@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.req("REQ-YG-728")
def test_item0_returns_before_any_other_starts(tmp_path, mode):
    app = _compile(tmp_path).compile()
    state = {"items": list("abcde"), "log": str(tmp_path / "events.log")}
    config = {"max_concurrency": 8}
    if mode == "sync":
        out = app.invoke(state, config)
    else:
        out = asyncio.run(app.ainvoke(state, config))
    assert _warm_first(_events(tmp_path))
    assert out["seen"] == list("abcde")


@pytest.mark.req("REQ-YG-728")
def test_release_wave_runs_in_parallel(tmp_path):
    out = _run(tmp_path, list("abcd"), fn="overlap", extra="min_success: 1.0")
    assert out["seen"] == list("abcd")
    assert _warm_first(_events(tmp_path))


@pytest.mark.req("REQ-YG-728")
def test_max_concurrency_caps_release_wave(tmp_path):
    _run(tmp_path, list("abcdef"), fn="peak", config={"max_concurrency": 2})
    assert (tmp_path / "events.log.peak").read_text() == "2"


# --- 3: parity with map -----------------------------------------------------


def _normalized(out: dict) -> dict:
    def strip(text: str) -> str:
        return re.sub(r"[0-9a-f]{32}", "<dispatch>", text)

    verdict = out["_map_verdict"]["fan"]
    return {
        "results": out["results"],
        "failures": [
            (f.index, f.error_type, strip(f.message), f.tolerated, f.node)
            for f in out["results_failures"]
        ],
        "verdict": (
            verdict.dispatched,
            verdict.succeeded,
            verdict.tolerated,
            verdict.failed,
            verdict.met,
        ),
    }


@pytest.mark.req("REQ-YG-728")
def test_parity_with_map(tmp_path):
    outs = {}
    for kind in ("map", "cached_map"):
        d = tmp_path / kind
        d.mkdir()
        outs[kind] = _run(
            d,
            list("abcd"),
            fn="warm_outcome",
            kind=kind,
            extra="min_success: 0.5",
            state={"mode": "raise"},
        )
    assert _normalized(outs["map"]) == _normalized(outs["cached_map"])


# --- 4: warm outcome truth table --------------------------------------------


@pytest.mark.parametrize(
    ("mode", "counts"),
    [
        ("raise", (3, 0, 1, 3)),
        ("timeout", (3, 0, 1, 3)),
        ("skip", (3, 1, 0, 4)),
    ],
)
@pytest.mark.parametrize("fraction", [1.0, 0.5])
@pytest.mark.req("REQ-YG-728")
def test_warm_outcome_releases_rest(tmp_path, mode, counts, fraction):
    extra = f"min_success: {fraction}\ntimeout: 0.3"
    met = counts[3] / 4 >= fraction
    try:
        app = _compile(tmp_path, fn="warm_outcome", extra=extra)
        from langgraph.checkpoint.memory import MemorySaver

        compiled = app.compile(checkpointer=MemorySaver())
        cfg = {"configurable": {"thread_id": f"{mode}-{fraction}"}}
        state = {"items": list("abcd"), "log": str(tmp_path / "events.log")}
        state["mode"] = mode
        if met:
            compiled.invoke(state, cfg)
        else:
            with pytest.raises(Exception) as exc_info:
                compiled.invoke(state, cfg)
            assert type(exc_info.value).__name__ == "MapCompletenessError"
        values = compiled.get_state(cfg).values
    finally:
        (tmp_path / "events.log.release").write_text("go")
    verdict = values["_map_verdict"]["fan"]
    assert (
        verdict.succeeded,
        verdict.tolerated,
        verdict.failed,
        verdict.accepted,
    ) == counts
    assert verdict.met is met
    rows = values["_map_accounting"]
    assert sorted(r.index for r in rows) == [0, 1, 2, 3]
    assert len({r.dispatch for r in rows}) == 1
    assert values["_cached_map_snapshot"].get("fan") is None
    started = {i for e, i in _events(tmp_path) if e == "start"}
    assert started == {0, 1, 2, 3}


# --- 5: empty and singleton populations -------------------------------------


@pytest.mark.parametrize("items", [[], ["a"]])
@pytest.mark.req("REQ-YG-728")
def test_empty_and_singleton(tmp_path, items):
    out = _run(tmp_path, items)
    verdict = out["_map_verdict"]["fan"]
    assert (verdict.dispatched, verdict.succeeded) == (len(items), len(items))
    assert out["seen"] == items


# --- 6: subgraph worker -----------------------------------------------------

CHILD = """
name: child
state:
  item: str
  log: str
  idx: int
  done: str
tools:
  step:
    type: python
    path: tools_fr1161.py
    function: child_step
nodes:
  step:
    type: python
    tool: step
edges:
  - {from: START, to: step}
  - {from: step, to: END}
"""


@pytest.mark.req("REQ-YG-728")
def test_subgraph_warm_finishes_before_release(tmp_path):
    (tmp_path / "tools_fr1161.py").write_text(TOOLS_SRC, encoding="utf-8")
    (tmp_path / "child.yaml").write_text(CHILD, encoding="utf-8")
    graph = (
        GRAPH.replace("@TYPE@", "cached_map")
        .replace("@FN@", "record")
        .replace("@OVER@", "{state.items}")
        .replace(
            "      type: python\n      tool: sub\n      state_key: out\n",
            "      type: subgraph\n      mode: invoke\n      graph: child.yaml\n"
            "      input_mapping:\n        item: item\n        log: log\n"
            "        _map_index: idx\n"
            "      output_mapping:\n        out: done\n      state_key: out\n",
        )
        .replace("@EXTRA@", "")
        .replace("@NODES@", "")
        .replace("@EDGES@", DEFAULT_EDGES)
    )
    path = tmp_path / "graph.yaml"
    path.write_text(graph, encoding="utf-8")
    app = load_and_compile(str(path)).compile()
    app.invoke({"items": list("abc"), "log": str(tmp_path / "events.log")})
    lines = (tmp_path / "events.log").read_text(encoding="utf-8").splitlines()
    end0 = lines.index("child-end 0")
    assert all(lines.index(f"child-start {i}") > end0 for i in (1, 2))


# --- 7: topology and diagnostic names ---------------------------------------


@pytest.mark.req("REQ-YG-728")
def test_topology_and_join_owns_outgoing(tmp_path):
    drawable = _compile(tmp_path).compile().get_graph()
    expected = {
        "fan",
        "_map_fan_warm",
        "_map_fan_sub",
        "_map_fan_account",
        "_map_fan_join",
    }
    assert expected <= set(drawable.nodes)
    into_consume = {e.source for e in drawable.edges if e.target == "consume"}
    assert into_consume == {"_map_fan_join"}


@pytest.mark.req("REQ-YG-728")
def test_warm_failure_names_map_sub(tmp_path):
    out = _run(
        tmp_path,
        list("ab"),
        fn="warm_outcome",
        extra="min_success: 0",
        state={"mode": "raise"},
    )
    (failure,) = out["results_failures"]
    assert (failure.index, failure.node) == (0, "_map_fan_sub")


# --- 8, 9, 10: dispatch-time snapshot ---------------------------------------


@pytest.mark.req("REQ-YG-728")
def test_collect_as_over_runs_original_population(tmp_path):
    out = _run(
        tmp_path,
        [],
        over="{state.results}",
        state={"results": [{"name": n} for n in "abc"]},
    )
    starts = sorted(i for e, i in _events(tmp_path) if e == "start")
    assert starts == [0, 1, 2]
    verdict = out["_map_verdict"]["fan"]
    assert (verdict.dispatched, verdict.succeeded) == (3, 3)
    assert len({r.dispatch for r in out["_map_accounting"]}) == 1


@pytest.mark.req("REQ-YG-728")
def test_release_sees_dispatch_time_inputs(tmp_path):
    out = _run(tmp_path, list("abcd"), fn="count_results")
    assert [r["n"] for r in out["results"]] == [0, 0, 0, 0]


@pytest.mark.req("REQ-YG-728")
def test_reentry_uses_fresh_snapshot(tmp_path):
    edges = """  - from: START
    to: fan
  - from: fan
    to: consume
  - from: consume
    to: fan
    condition: _loop_counts.consume < 2
  - from: consume
    to: END
    condition: _loop_counts.consume >= 2
"""
    out = _run(tmp_path, list("ab"), edges=edges)
    tokens = [row.dispatch for row in out["_map_accounting"]]
    assert len(set(tokens)) == 2
    assert sorted(row.index for row in out["_map_accounting"]) == [0, 0, 1, 1]
    assert out["_cached_map_snapshot"].get("fan") is None
    assert out["_map_open"].get("fan") is None


# --- 11: cap and overflow before warm ---------------------------------------


@pytest.mark.req("REQ-YG-728")
def test_overflow_error_raises_before_any_worker(tmp_path):
    with pytest.raises(ValueError, match="exceed"):
        _run(tmp_path, list("abc"), extra="max_items: 2")
    assert not (tmp_path / "events.log").exists()


@pytest.mark.req("REQ-YG-728")
def test_truncate_caps_population(tmp_path):
    out = _run(tmp_path, list("abc"), extra="max_items: 2\non_overflow: truncate")
    assert out["seen"] == ["a", "b"]


# --- 12: schema, load, state, codegen, published schema ---------------------


@pytest.mark.parametrize("missing", ["over", "as", "node", "collect"])
@pytest.mark.req("REQ-YG-728")
def test_missing_field_fails_like_map(tmp_path, missing):
    config = {
        "type": "cached_map",
        "over": "{state.items}",
        "as": "item",
        "node": {"type": "python", "tool": "sub"},
        "collect": "results",
    }
    del config[missing]
    from yamlgraph.utils.validators import validate_map_node

    with pytest.raises(ValueError, match=f"missing required '{missing}'"):
        validate_map_node("fan", config)


def _state_config(kind: str) -> dict:
    return {
        "state": {"items": "list"},
        "nodes": {
            "fan": {
                "type": kind,
                "over": "{state.items}",
                "as": "item",
                "node": {"type": "python", "tool": "sub"},
                "collect": "results",
            }
        },
        "edges": [],
    }


@pytest.mark.req("REQ-YG-728")
def test_state_declares_map_and_snapshot_channels():
    fields = build_state_class(_state_config("cached_map")).__annotations__
    for key in (
        "results",
        "results_failures",
        "_map_accounting",
        "_map_open",
        "_map_verdict",
        "_cached_map_snapshot",
    ):
        assert key in fields, key


@pytest.mark.req("REQ-YG-728")
def test_state_codegen_declares_snapshot():
    from yamlgraph.models.state_codegen import generate_typeddict_code

    code = generate_typeddict_code(_state_config("cached_map"))
    assert "_cached_map_snapshot" in code
    assert "results_failures" in code
    compile(code, "<state>", "exec")


@pytest.mark.req("REQ-YG-728")
def test_published_schema_accepts_cached_map():
    import json

    import jsonschema

    import yamlgraph

    schema_path = Path(yamlgraph.__file__).parent / "schemas" / "graph-v1.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    graph = _state_config("cached_map")
    graph.update({"version": "1.0", "name": "g"})
    graph["edges"] = [{"from": "START", "to": "fan"}, {"from": "fan", "to": "END"}]
    jsonschema.validate(graph, schema)


# --- 13: composition --------------------------------------------------------


@pytest.mark.parametrize("first", ["map", "cached_map"])
@pytest.mark.req("REQ-YG-728")
def test_composition_with_map(tmp_path, first):
    second = "cached_map" if first == "map" else "map"
    nodes = f"""
  fan2:
    type: {second}
    over: "{{state.items}}"
    as: item
    node:
      type: python
      tool: sub
      state_key: out
    collect: results
"""
    edges = """  - from: START
    to: fan
  - from: fan
    to: fan2
  - from: fan2
    to: consume
  - from: consume
    to: END
"""
    out = _run(tmp_path, list("ab"), kind=first, nodes=nodes, edges=edges)
    verdicts = out["_map_verdict"]
    assert verdicts["fan"].dispatched == verdicts["fan2"].dispatched == 2
    assert verdicts["fan"].dispatch != verdicts["fan2"].dispatch


# --- 14: lint ---------------------------------------------------------------


@pytest.mark.req("REQ-YG-728")
def test_lint_accepts_and_reports_missing_fields(tmp_path):
    from yamlgraph.linter.patterns.map import check_map_patterns

    _compile(tmp_path)
    good = check_map_patterns(tmp_path / "graph_cached_map.yaml")
    assert not [i for i in good if i.severity == "error"]
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "name: bad\nnodes:\n  fan:\n    type: cached_map\n    as: item\n"
        "edges:\n  - {from: START, to: fan}\n  - {from: fan, to: END}\n",
        encoding="utf-8",
    )
    codes = {i.code for i in check_map_patterns(bad)}
    assert {"E201", "E203", "E204"} <= codes


# --- 15: type preservation --------------------------------------------------


@pytest.mark.req("REQ-YG-728")
def test_pydantic_items_and_inputs_keep_their_types(tmp_path):
    outs = {}
    for kind in ("map", "cached_map"):
        d = tmp_path / kind
        d.mkdir()
        outs[kind] = _run(
            d,
            [Item(name=n) for n in "abc"],
            fn="typed",
            kind=kind,
            state={"cfg": Cfg(tag="t")},
        )
    assert outs["cached_map"]["results"] == outs["map"]["results"]
    assert [r["v"] for r in outs["cached_map"]["results"]] == ["a", "b", "c"]
    assert not outs["cached_map"].get("results_failures")
