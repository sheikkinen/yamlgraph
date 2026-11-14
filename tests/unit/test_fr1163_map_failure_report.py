"""FR-1163: a failed map join keeps its evidence; a failed run reports usage.

REQ-YG-692 witnesses. Graphs are compiled from real YAML so dispatch,
branch wrapper, reducers and join run as compiled. New symbols are imported
inside tests so RED fails on behaviour, not at collection.
"""

from __future__ import annotations

import asyncio
import json
import textwrap
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

import pytest

from yamlgraph.compile.graph_loader import load_and_compile
from yamlgraph.models.map_results import MapCompletenessError, MapFailure, MapVerdict

TOOLS_SRC = textwrap.dedent(
    """
    import os


    def sub(state):
        if state["item"] == "b":
            raise ValueError("poison b")
        return {"out": {"v": state["item"]}}


    def long_sub(state):
        if state["item"] == "b":
            raise ValueError("L" * 500)
        return {"out": {"v": state["item"]}}


    def ok(state):
        mark = os.environ.get("FR1163_MARK")
        if mark:
            open(mark, "w").close()
        return 1


    def boom(state):
        raise RuntimeError("plain boom")
    """
)

TOOLS = ("sub", "long_sub", "ok", "boom")

USAGE_LINE = (
    "\U0001f4ca Token usage: 100 in / 50 out (2 calls), 20 thinking, "
    "7 cache read, 3 cache write"
)
TIMING_LINE = "⏱ Timing: 1.5s total (2 calls, 0.75s mean)"
ZERO_USAGE_LINE = "\U0001f4ca Token usage: 0 in / 0 out (0 calls)"
ZERO_TIMING_LINE = "⏱ Timing: 0.0s total (0 calls, 0.0s mean)"


def _fan(kind: str = "map", fn: str = "sub", extra: str = "") -> str:
    return (
        f'type: {kind}\nover: "{{state.items}}"\nas: item\nnode:\n'
        f"  type: python\n  tool: {fn}\n  state_key: out\ncollect: results\n{extra}"
    )


NODES = {
    "fan": _fan(),
    "fan_cached": _fan("cached_map"),
    "fan_long": _fan(fn="long_sub"),
    "fan_strict3": _fan(extra="min_success: 3\n"),
    "py_ok": "type: python\ntool: ok\nstate_key: result",
    "py_fail": "type: python\ntool: boom\nstate_key: py_fail_out",
}


@pytest.fixture(autouse=True)
def _cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("YAMLGRAPH_ROUTE_LOG", raising=False)


def _graph(tmp_path: Path, nodes: list[str], extra: str = "") -> Path:
    (tmp_path / "tools_fr1163.py").write_text(TOOLS_SRC, encoding="utf-8")
    tools = "".join(
        f"  {t}:\n    type: python\n    path: tools_fr1163.py\n    function: {t}\n"
        for t in TOOLS
    )
    body = "".join(f"  {n}:\n{textwrap.indent(NODES[n], '    ')}\n" for n in nodes)
    chain = ["START", *nodes, "END"]
    edges = "".join(
        f"  - from: {a}\n    to: {b}\n" for a, b in zip(chain, chain[1:], strict=False)
    )
    text = (
        'version: "1.0"\nname: g\n'
        "state:\n  result: int\n  items: list\n  results: list\n"
        "variables:\n  items: [a, b, c]\n"
        f"{textwrap.dedent(extra)}tools:\n{tools}nodes:\n{body}edges:\n{edges}"
    )
    path = tmp_path / "g.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def _preset_trackers():
    """Trackers carrying known usage, as if earlier LLM calls had completed."""
    from yamlgraph.utils.timing_tracker import ExecutionTimingCallbackHandler
    from yamlgraph.utils.token_tracker import TokenUsageCallbackHandler

    tok = TokenUsageCallbackHandler()
    tok.total_input_tokens, tok.total_output_tokens, tok.total_calls = 100, 50, 2
    tok.total_reasoning_tokens = 20
    tok.total_cache_read_tokens, tok.total_cache_write_tokens = 7, 3
    tim = ExecutionTimingCallbackHandler()
    tim.total_duration, tim.total_calls, tim.call_durations = 1.5, 2, [0.5, 1.0]
    return tok, tim


@dataclass
class Outcome:
    code: int
    out: str
    err: str


def _run(capsys, graph: Path, *argv: str, preset: bool = False, patches=()) -> Outcome:
    from yamlgraph.cli import create_parser
    from yamlgraph.cli.graph_commands import cmd_graph_run

    args = create_parser().parse_args(["graph", "run", str(graph), *argv])
    code = 0
    with ExitStack() as stack:
        if preset:
            tok, tim = _preset_trackers()
            stack.enter_context(
                patch(
                    "yamlgraph.utils.token_tracker.create_token_tracker",
                    return_value=tok,
                )
            )
            stack.enter_context(
                patch(
                    "yamlgraph.utils.timing_tracker.create_timing_tracker",
                    return_value=tim,
                )
            )
        for p in patches:
            stack.enter_context(p)
        try:
            cmd_graph_run(args)
        except SystemExit as exc:
            code = exc.code if isinstance(exc.code, int) else 1
    captured = capsys.readouterr()
    return Outcome(code, captured.out, captured.err)


# AC-01: the exception carries the evidence ----------------------------------


@pytest.mark.req("REQ-YG-692")
@pytest.mark.parametrize("node", ["fan", "fan_cached"])
@pytest.mark.parametrize("mode", ["invoke", "ainvoke"])
def test_ac01_completeness_error_carries_collect_and_failures(tmp_path, node, mode):
    app = load_and_compile(str(_graph(tmp_path, [node]))).compile()
    state = {"items": ["a", "b", "c"]}
    with pytest.raises(MapCompletenessError) as info:
        if mode == "invoke":
            app.invoke(state)
        else:
            asyncio.run(app.ainvoke(state))
    exc = info.value
    assert str(exc).startswith(f"Map node '{node}' incomplete: accepted 2/3")
    assert exc.collect_key == "results"
    assert list(exc.collected) == [{"v": "a"}, {"v": "c"}]
    assert [(f.index, f.error_type) for f in exc.failures] == [(1, "ValueError")]
    assert "poison b" in exc.failures[0].message


# AC-02: own dispatch only; whole channel snapshot --------------------------


def _verdict(dispatch: str, succeeded: int) -> MapVerdict:
    return MapVerdict(
        dispatch=dispatch,
        dispatched=3,
        succeeded=succeeded,
        tolerated=0,
        failed=3 - succeeded,
        accepted=succeeded,
        min_success=3,
        met=False,
    )


def _failure(map_name: str, dispatch: str, index: int) -> MapFailure:
    return MapFailure(
        map=map_name,
        dispatch=dispatch,
        index=index,
        error_type="ValueError",
        message=f"{map_name}/{dispatch}/{index}",
        node=f"_map_{map_name}_sub",
        tolerated=False,
    )


@pytest.mark.req("REQ-YG-692")
def test_ac02_join_selects_own_dispatch_and_snapshots_whole_channel():
    from yamlgraph.compile.map_contract import make_join_node

    channel = [{"v": "old"}, {"v": "x"}, {"v": "y"}]
    state = {
        "_map_verdict": {"fan": _verdict("d2", 1)},
        "results": channel,
        "results_failures": [
            _failure("fan", "d1", 0),
            _failure("other", "d2", 0),
            _failure("fan", "d2", 2),
            _failure("fan", "d2", 1),
        ],
    }
    with pytest.raises(MapCompletenessError) as info:
        make_join_node("fan", "results", "results_failures")(state)
    exc = info.value
    assert [(f.dispatch, f.index) for f in exc.failures] == [("d2", 1), ("d2", 2)]
    assert list(exc.collected) == channel
    assert exc.collected is not channel
    assert channel == [{"v": "old"}, {"v": "x"}, {"v": "y"}]

    from yamlgraph.cli.graph_run_failure import map_failure_lines

    text = "\n".join(map_failure_lines(exc, full=False))
    assert "3 collected results in 'results' (1 succeeded in failing dispatch)" in text


@pytest.mark.req("REQ-YG-692")
def test_ac02_two_argument_constructor_still_valid():
    exc = MapCompletenessError("fan", _verdict("d", 0))
    assert exc.collect_key == ""
    assert list(exc.collected) == []
    assert list(exc.failures) == []
    assert str(exc).startswith("Map node 'fan' incomplete: accepted 0/3")


# AC-03: text output ----------------------------------------------------------


@pytest.mark.req("REQ-YG-692")
def test_ac03_text_report_names_failures_and_count(tmp_path, capsys):
    o = _run(capsys, _graph(tmp_path, ["fan"]))
    assert o.code == 1
    assert "❌ Error: Map node 'fan' incomplete" in o.out
    assert "#1 ValueError: poison b" in o.out
    assert "2 collected results in 'results' (2 succeeded in failing dispatch)" in o.out
    assert "{'v': 'a'}" not in o.out


@pytest.mark.req("REQ-YG-692")
def test_ac03_full_prints_collected_snapshot(tmp_path, capsys):
    o = _run(capsys, _graph(tmp_path, ["fan"]), "--full")
    assert o.code == 1
    assert "{'v': 'a'}" in o.out and "{'v': 'c'}" in o.out


@pytest.mark.req("REQ-YG-692")
def test_ac03_long_message_cut_in_text_full_in_json(tmp_path, capsys):
    g = _graph(tmp_path, ["fan_long"])
    text = _run(capsys, g)
    assert "L" * 200 in text.out
    assert "L" * 201 not in text.out
    js = _run(capsys, g, "--json")
    assert json.loads(js.out)["map"]["failures"][0]["message"].count("L") == 500


@pytest.mark.req("REQ-YG-692")
def test_ac03_explicit_threshold_failure_reports_same_evidence(tmp_path, capsys):
    o = _run(capsys, _graph(tmp_path, ["fan_strict3"]))
    assert o.code == 1
    assert "#1 ValueError: poison b" in o.out
    assert "2 collected results in 'results'" in o.out


# AC-04 / AC-06: usage on failure ---------------------------------------------


@pytest.mark.req("REQ-YG-692")
def test_ac04_map_failure_reports_usage_once(tmp_path, capsys):
    o = _run(
        capsys, _graph(tmp_path, ["fan"]), "--token-usage", "--timing", preset=True
    )
    assert o.code == 1
    assert o.out.count(USAGE_LINE) == 1
    assert o.out.count(TIMING_LINE) == 1
    assert o.out.count("❌ Error:") == 1


@pytest.mark.req("REQ-YG-692")
def test_ac04_flags_off_print_no_usage(tmp_path, capsys):
    o = _run(capsys, _graph(tmp_path, ["fan"]), preset=True)
    assert "Token usage" not in o.out + o.err
    assert "Timing" not in o.out + o.err


@pytest.mark.req("REQ-YG-692")
def test_ac06_zero_call_failure_prints_zero_usage(tmp_path, capsys):
    o = _run(capsys, _graph(tmp_path, ["py_fail"]), "--token-usage", "--timing")
    assert o.code == 1
    assert ZERO_USAGE_LINE in o.out
    assert ZERO_TIMING_LINE in o.out


@pytest.mark.req("REQ-YG-692")
def test_ac06_non_map_failure_reports_recorded_usage(tmp_path, capsys):
    o = _run(
        capsys,
        _graph(tmp_path, ["py_fail"]),
        "--token-usage",
        "--timing",
        preset=True,
    )
    assert o.code == 1
    assert o.out.count(USAGE_LINE) == 1
    assert o.out.count(TIMING_LINE) == 1
    assert "collected results" not in o.out


# AC-05: JSON -------------------------------------------------------------------


@pytest.mark.req("REQ-YG-692")
def test_ac05_json_failure_object(tmp_path, capsys):
    o = _run(
        capsys,
        _graph(tmp_path, ["fan"]),
        "--json",
        "--token-usage",
        "--timing",
        preset=True,
    )
    assert o.code == 1
    payload = json.loads(o.out)
    assert payload["status"] == "failed"
    assert payload["error"].startswith("Map node 'fan' incomplete")
    m = payload["map"]
    assert (m["name"], m["collect_key"]) == ("fan", "results")
    assert m["verdict"]["met"] is False and m["verdict"]["succeeded"] == 2
    assert m["collected"] == [{"v": "a"}, {"v": "c"}]
    assert [(f["index"], f["error_type"]) for f in m["failures"]] == [(1, "ValueError")]
    tok, tim = _preset_trackers()
    assert payload["token_usage"] == tok.summary()
    assert payload["timing"] == tim.summary()
    assert "Token usage" not in o.err


@pytest.mark.req("REQ-YG-692")
def test_ac05_json_non_map_failure_has_no_map_or_usage_keys(tmp_path, capsys):
    o = _run(capsys, _graph(tmp_path, ["py_fail"]), "--json")
    assert o.code == 1
    payload = json.loads(o.out)
    assert payload["status"] == "failed"
    assert "plain boom" in payload["error"]
    assert "map" not in payload
    assert "token_usage" not in payload and "timing" not in payload


# AC-07: timeout and streaming --------------------------------------------------


@pytest.mark.req("REQ-YG-692")
def test_ac07_timeout_reports_usage_once(tmp_path, capsys):
    o = _run(
        capsys,
        _graph(tmp_path, ["py_ok"]),
        "--token-usage",
        preset=True,
        patches=(
            patch(
                "yamlgraph.cli.graph_commands._run_graph_until_complete",
                side_effect=TimeoutError("Graph execution timed out after 5s"),
            ),
        ),
    )
    assert o.code == 1
    assert o.out.count(USAGE_LINE) == 1
    assert o.out.count("❌ Error:") == 1


@pytest.mark.req("REQ-YG-692")
def test_ac07_streaming_error_reports_usage_to_stderr(tmp_path, capsys):
    o = _run(
        capsys,
        _graph(tmp_path, ["py_ok"]),
        "--stream",
        "--token-usage",
        preset=True,
        patches=(
            patch("yamlgraph.cli.graph_commands._run_streaming", return_value=True),
        ),
    )
    assert o.code == 1
    assert o.err.count(USAGE_LINE) == 1


# AC-08: nothing downstream, nothing exported ----------------------------------


@pytest.mark.req("REQ-YG-692")
def test_ac08_no_downstream_node_and_no_exports(tmp_path, capsys, monkeypatch):
    mark = tmp_path / "ran"
    monkeypatch.setenv("FR1163_MARK", str(mark))
    exports = "exports:\n  result:\n    format: json\n    filename: r.json\n"
    g = _graph(tmp_path, ["fan", "py_ok"], exports)
    state_file = tmp_path / "state.json"
    o = _run(capsys, g, "--export", "--export-state", str(state_file))
    assert o.code == 1
    assert not mark.exists()
    assert not state_file.exists()
    assert not (tmp_path / "outputs").exists()


# AC-09: success and non-execution paths unchanged ----------------------------


@pytest.mark.req("REQ-YG-692")
def test_ac09_success_prints_usage_once_and_no_failure_report(tmp_path, capsys):
    o = _run(
        capsys,
        _graph(tmp_path, ["py_ok"]),
        "--token-usage",
        "--timing",
        preset=True,
    )
    assert o.code == 0
    assert o.out.count(USAGE_LINE) == 1
    assert o.out.count(TIMING_LINE) == 1
    assert "❌" not in o.out


@pytest.mark.req("REQ-YG-692")
def test_ac09_success_with_zero_calls_prints_no_usage(tmp_path, capsys):
    o = _run(capsys, _graph(tmp_path, ["py_ok"]), "--token-usage", "--timing")
    assert o.code == 0
    assert "Token usage" not in o.out
    assert "Timing" not in o.out


@pytest.mark.req("REQ-YG-692")
def test_ac09_post_success_export_failure_unchanged(tmp_path, capsys):
    o = _run(
        capsys,
        _graph(tmp_path, ["py_ok"]),
        "--token-usage",
        preset=True,
        patches=(
            patch(
                "yamlgraph.cli.graph_commands._handle_optional_exports",
                side_effect=OSError("disk full"),
            ),
        ),
    )
    assert o.code == 1
    assert o.out.count(USAGE_LINE) == 1
    assert o.out.count("❌ Error:") == 1


@pytest.mark.req("REQ-YG-692")
def test_ac09_pre_execution_refusal_prints_no_usage(tmp_path, capsys):
    g = _graph(tmp_path, ["py_ok"])
    g.write_text(g.read_text().replace("tool: ok", "tool: missing_tool"))
    o = _run(capsys, g, "--token-usage", "--timing", preset=True)
    assert o.code == 1
    assert "Token usage" not in o.out + o.err
    assert "Timing" not in o.out + o.err
