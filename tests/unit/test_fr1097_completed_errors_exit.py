"""FR-1097: non-stream `graph run` exits 3 when this run recorded untolerated errors."""

from __future__ import annotations

import json
import textwrap
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

import pytest
from langchain_core.language_models import SimpleChatModel

TOOLS_SRC = textwrap.dedent(
    """
    import os


    def ok(state):
        mark = os.environ.get("FR1097_MARK")
        if mark:
            open(mark, "w").close()
        return 1


    def boom(state):
        raise ValueError("boom")


    def dict_error(state):
        return {"errors": [{"type": "state_error", "message": "dict err", "node": "emitter"}]}


    def missing_node(state):
        return {"errors": [{"type": "state_error", "message": "no node"}]}


    def unknown_type(state):
        return {"errors": [{"type": "nope", "message": "bad type", "node": "emitter"}]}


    def fan_sub(state):
        if state["item"] == "b":
            raise ValueError("poison b")
        return {"out": {"v": state["item"]}}
    """
)

TOOLS = ("ok", "boom", "dict_error", "missing_node", "unknown_type", "fan_sub")

NODES = {
    "p5": "type: llm\nprompt: echo\nrequires: [flag]\nstate_key: p5_out",
    "p1": "type: llm\nprompt: echo\nstate_key: p1_out",
    "llm_skip": "type: llm\nprompt: echo\non_error: skip\nstate_key: llm_skip_out",
    "llm_fail": "type: llm\nprompt: echo\non_error: fail\nstate_key: llm_fail_out",
    "py_ok": "type: python\ntool: ok\nstate_key: result",
    "py_skip": "type: python\ntool: boom\non_error: skip\nstate_key: py_skip_out",
    "py_fail": "type: python\ntool: boom\nstate_key: py_fail_out",
    "emit_dict": "type: python\ntool: dict_error",
    "emit_missing_node": "type: python\ntool: missing_node",
    "emit_unknown_type": "type: python\ntool: unknown_type",
    "guard_warn": (
        "type: llm\nprompt: echo\nstate_key: gw_out\nguards:\n  pre:\n"
        '    - check: "state.result >= 100"\n      on_fail: warn\n'
        "      message: guard warn fired"
    ),
    "guard_halt": (
        "type: llm\nprompt: echo\nstate_key: gh_out\nguards:\n  pre:\n"
        '    - check: "state.result >= 100"\n      on_fail: halt\n'
        "      message: guard halt fired"
    ),
    "ask": 'type: interrupt\nmessage: "continue?"\nresume_key: answer',
    "fan": (
        'type: map\nover: "{state.items}"\nas: item\nnode:\n  type: python\n'
        "  tool: fan_sub\n  state_key: out\ncollect: results"
    ),
}

LLM_PATCH_TARGETS = (
    "yamlgraph.utils.llm_factory.create_llm",
    "yamlgraph.executor.create_llm",
    "yamlgraph.executor_async.create_llm",
    "yamlgraph.utils.llm_factory_async.create_llm",
)


class _Model(SimpleChatModel):
    fail: bool = False

    def _call(self, messages, stop=None, run_manager=None, **kwargs) -> str:
        if self.fail:
            raise RuntimeError("llm down")
        return "echo"

    @property
    def _llm_type(self) -> str:
        return "fr1097"


def _patch_llm(fail: bool):
    stack = ExitStack()
    model = _Model(fail=fail)
    for target in LLM_PATCH_TARGETS:
        stack.enter_context(patch(target, return_value=model))
    return stack


@pytest.fixture
def echo_llm():
    with _patch_llm(fail=False):
        yield


@pytest.fixture
def boom_llm():
    with _patch_llm(fail=True):
        yield


@pytest.fixture(autouse=True)
def _cwd(tmp_path, monkeypatch):
    # configured exports write under ./outputs; keep them out of the repo tree
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("YAMLGRAPH_ROUTE_LOG", raising=False)


def _graph(tmp_path: Path, nodes: list[str], extra: str = "", name="g") -> Path:
    (tmp_path / "prompts").mkdir(exist_ok=True)
    (tmp_path / "prompts" / "echo.yaml").write_text(
        'system: echo\nuser: "hello"\n', encoding="utf-8"
    )
    (tmp_path / "tools_fr1097.py").write_text(TOOLS_SRC, encoding="utf-8")
    tools = "".join(
        f"  {t}:\n    type: python\n    path: tools_fr1097.py\n    function: {t}\n"
        for t in TOOLS
    )
    body = "".join(f"  {n}:\n{textwrap.indent(NODES[n], '    ')}\n" for n in nodes)
    chain = ["START", *nodes, "END"]
    edges = "".join(
        f"  - from: {a}\n    to: {b}\n" for a, b in zip(chain, chain[1:], strict=False)
    )
    text = (
        f'version: "1.0"\nname: {name}\nprompts_relative: true\nprompts_dir: prompts\n'
        f"state:\n  flag: str\n  result: int\n  items: list\n  results: list\n"
        f"{textwrap.dedent(extra)}\ntools:\n{tools}nodes:\n{body}edges:\n{edges}"
    )
    path = tmp_path / f"{name}.yaml"
    path.write_text(text, encoding="utf-8")
    return path


@dataclass
class Outcome:
    code: int
    out: str
    err: str

    @property
    def json(self) -> dict:
        line = next(ln for ln in reversed(self.out.splitlines()) if ln.startswith("{"))
        return json.loads(line)


def _run(capsys, graph: Path, *argv: str, stdin: str | None = None) -> Outcome:
    from yamlgraph.cli import create_parser
    from yamlgraph.cli.graph_commands import cmd_graph_run

    args = create_parser().parse_args(["graph", "run", str(graph), *argv])
    code = 0
    with ExitStack() as stack:
        if stdin is not None:
            stack.enter_context(patch("builtins.input", return_value=stdin))
        try:
            cmd_graph_run(args)
        except SystemExit as exc:
            code = (
                exc.code
                if isinstance(exc.code, int)
                else (0 if exc.code is None else 1)
            )
    captured = capsys.readouterr()
    return Outcome(code, captured.out, captured.err)


def _counts(o: Outcome) -> tuple[int, int]:
    return o.json["_error_count"], o.json["_tolerated_error_count"]


# AC-01 -----------------------------------------------------------------------


@pytest.mark.req("REQ-YG-700")
def test_ac01_map_partial_failure_exits_3(tmp_path, capsys):
    g = _graph(tmp_path, ["fan"], "variables:\n  items: [a, b]\n")
    g.write_text(
        g.read_text().replace(
            "collect: results", "collect: results\n    min_success: 1"
        )
    )
    o = _run(capsys, g, "--json")
    assert o.code == 3, o.err
    assert _counts(o) == (1, 0)
    assert [e["node"] for e in o.json["errors"]] == ["_map_fan_sub"]


@pytest.mark.req("REQ-YG-700")
def test_ac01_map_without_min_success_exits_1_no_tally(tmp_path, capsys):
    g = _graph(tmp_path, ["fan"], "variables:\n  items: [a, b]\n")
    o = _run(capsys, g)
    assert o.code == 1
    assert "completed with" not in o.err


# AC-02 -----------------------------------------------------------------------


@pytest.mark.req("REQ-YG-700")
@pytest.mark.parametrize("mode", ["text", "json"])
def test_ac02_p5_exits_3_and_names_node(tmp_path, capsys, echo_llm, mode):
    argv = ["--json"] if mode == "json" else []
    o = _run(capsys, _graph(tmp_path, ["p5"]), *argv)
    assert o.code == 3, o.err
    assert "p5: Missing required state: flag" in o.err
    if mode == "json":
        assert _counts(o) == (1, 0)


@pytest.mark.req("REQ-YG-700")
@pytest.mark.parametrize("mode", ["text", "json"])
def test_ac02_p1_llm_failure_exits_3(tmp_path, capsys, boom_llm, mode):
    argv = ["--json"] if mode == "json" else []
    o = _run(capsys, _graph(tmp_path, ["p1"]), *argv)
    assert o.code == 3, o.err
    assert "p1: " in o.err and "llm down" in o.err
    if mode == "json":
        assert _counts(o) == (1, 0)


# AC-03 -----------------------------------------------------------------------


@pytest.mark.req("REQ-YG-700")
def test_ac03_skips_are_tolerated(tmp_path, capsys, boom_llm):
    g = _graph(tmp_path, ["llm_skip", "py_skip"])
    o = _run(capsys, g, "--json")
    assert o.code == 0, o.err
    assert _counts(o) == (0, 2)
    assert len(o.json["errors"]) == 2
    text = _run(capsys, g)
    assert text.code == 0
    assert "completed with 0 errors (2 tolerated)" in text.err


@pytest.mark.req("REQ-YG-700")
def test_ac03_guard_warn_is_tolerated(tmp_path, capsys, echo_llm):
    o = _run(capsys, _graph(tmp_path, ["py_ok", "guard_warn"]), "--json")
    assert o.code == 0, o.err
    assert _counts(o) == (0, 1)


@pytest.mark.req("REQ-YG-700")
def test_ac03_verify_warn_is_tolerated(tmp_path, capsys):
    verify = 'verify:\n  - check: "state.result >= 100"\n    on_fail: warn\n    message: verify warn\n'
    o = _run(capsys, _graph(tmp_path, ["py_ok"], verify), "--json")
    assert o.code == 0, o.err
    assert _counts(o) == (0, 1)


# AC-04 / AC-09 ---------------------------------------------------------------


@pytest.mark.req("REQ-YG-700")
def test_ac04_mixed_lists_only_untolerated(tmp_path, capsys, echo_llm):
    g = _graph(tmp_path, ["p5", "py_skip"])
    o = _run(capsys, g, "--json")
    assert o.code == 3
    assert _counts(o) == (1, 1)
    assert "p5: Missing required state" in o.err
    assert "py_skip:" not in o.err


@pytest.mark.req("REQ-YG-700")
def test_ac09_skip_update_is_delta_only(tmp_path, capsys, echo_llm):
    o = _run(capsys, _graph(tmp_path, ["p5", "py_skip"]), "--json")
    assert [e["node"] for e in o.json["errors"]] == ["p5", "py_skip"]


# AC-05 -----------------------------------------------------------------------


@pytest.mark.req("REQ-YG-700")
def test_ac05_python_default_fail_exits_1(tmp_path, capsys):
    o = _run(capsys, _graph(tmp_path, ["py_fail"]))
    assert o.code == 1
    assert "completed with" not in o.err


@pytest.mark.req("REQ-YG-700")
def test_ac05_llm_on_error_fail_exits_1(tmp_path, capsys, boom_llm):
    o = _run(capsys, _graph(tmp_path, ["llm_fail"]))
    assert o.code == 1
    assert "completed with" not in o.err


@pytest.mark.req("REQ-YG-700")
def test_ac05_export_failure_exits_1(tmp_path, capsys):
    g = _graph(
        tmp_path,
        ["py_ok"],
        "exports:\n  result:\n    format: json\n    filename: r.json\n",
    )
    with patch(
        "yamlgraph.storage.export.export_result", side_effect=OSError("disk full")
    ):
        o = _run(capsys, g, "--export")
    assert o.code == 1


# AC-06 -----------------------------------------------------------------------

CHECKPOINT = "checkpointer:\n  type: memory\n"


@pytest.mark.req("REQ-YG-700")
def test_ac06_json_interrupt_exits_1(tmp_path, capsys, echo_llm):
    o = _run(
        capsys, _graph(tmp_path, ["ask", "p5"], CHECKPOINT), "--json", "--thread", "t"
    )
    assert o.code == 1


@pytest.mark.req("REQ-YG-700")
def test_ac06_text_interrupt_resumed_to_p5_exits_3(tmp_path, capsys, echo_llm):
    g = _graph(tmp_path, ["ask", "p5"], CHECKPOINT)
    o = _run(capsys, g, "--thread", "t", stdin="yes")
    assert o.code == 3, o.err


@pytest.mark.req("REQ-YG-700")
def test_ac06_text_interrupt_empty_input_exits_0(tmp_path, capsys, echo_llm):
    g = _graph(tmp_path, ["ask", "p5"], CHECKPOINT)
    assert _run(capsys, g, "--thread", "t", stdin="").code == 0


# AC-07 -----------------------------------------------------------------------


@pytest.mark.req("REQ-YG-700")
def test_ac07_output_and_exports_exist_before_exit_3(tmp_path, capsys, echo_llm):
    exports = "exports:\n  result:\n    format: json\n    filename: r.json\n"
    g = _graph(tmp_path, ["py_ok", "p5"], exports)
    state_file = tmp_path / "state.json"
    o = _run(capsys, g, "--json", "--export", "--export-state", str(state_file))
    assert o.code == 3
    assert _counts(o) == (1, 0)
    configured = tmp_path / "outputs" / "unknown" / "r.json"
    assert configured.exists() and state_file.exists()
    for f in (configured, state_file):
        text = f.read_text(encoding="utf-8")
        assert "_error_count" not in text and "_tolerated_error_count" not in text


# AC-08 -----------------------------------------------------------------------


@pytest.mark.req("REQ-YG-700")
@pytest.mark.parametrize(
    ("nodes", "expected"),
    [
        (["p5"], (1, 0)),
        (["py_skip"], (0, 1)),
        (["p5", "py_skip"], (1, 1)),
        (["py_ok"], (0, 0)),
    ],
)
def test_ac08_run_end_carries_counts(
    tmp_path, capsys, monkeypatch, echo_llm, nodes, expected
):
    sink = tmp_path / "route.jsonl"
    monkeypatch.setenv("YAMLGRAPH_ROUTE_LOG", str(sink))
    o = _run(capsys, _graph(tmp_path, nodes), "--json")
    assert _counts(o) == expected
    run_end = [
        r
        for r in map(json.loads, sink.read_text().splitlines())
        if r["event"] == "run_end"
    ][-1]
    assert (run_end["error_count"], run_end["tolerated_error_count"]) == expected


# AC-10 -----------------------------------------------------------------------


def _import_file(tmp_path: Path, entry: dict) -> Path:
    path = tmp_path / "import.json"
    path.write_text(json.dumps({"errors": [entry]}), encoding="utf-8")
    return path


OLD_ERROR = {"type": "state_error", "message": "old loss", "node": "prev"}


@pytest.mark.req("REQ-YG-700")
def test_ac10_imported_error_does_not_count(tmp_path, capsys):
    imp = _import_file(tmp_path, OLD_ERROR)
    o = _run(capsys, _graph(tmp_path, ["py_ok"]), "--json", "--import-state", str(imp))
    assert o.code == 0, o.err
    assert _counts(o) == (0, 0)
    assert len(o.json["errors"]) == 1


@pytest.mark.req("REQ-YG-700")
def test_ac10_real_export_state_chain_does_not_count(tmp_path, capsys, echo_llm):
    state_file = tmp_path / "state.json"
    first = _run(
        capsys, _graph(tmp_path, ["p5"]), "--json", "--export-state", str(state_file)
    )
    assert first.code == 3
    o = _run(
        capsys,
        _graph(tmp_path, ["py_ok"], name="g2"),
        "--json",
        "--import-state",
        str(state_file),
    )
    assert o.code == 0, o.out + o.err
    assert _counts(o) == (0, 0)
    assert o.json["errors"][0]["node"] == "p5"


@pytest.mark.req("REQ-YG-700")
def test_ac10_import_plus_new_error_counts_one(tmp_path, capsys, echo_llm):
    imp = _import_file(tmp_path, OLD_ERROR)
    o = _run(capsys, _graph(tmp_path, ["p5"]), "--json", "--import-state", str(imp))
    assert o.code == 3
    assert _counts(o) == (1, 0)


@pytest.mark.req("REQ-YG-700")
def test_ac10_checkpoint_history_does_not_count(tmp_path, capsys, echo_llm):
    cp = f"checkpointer:\n  type: sqlite\n  path: {tmp_path / 'cp.db'}\n"
    g = _graph(tmp_path, ["p5"], cp)
    assert _run(capsys, g, "--json", "--thread", "a").code == 3
    clean = _run(capsys, g, "--json", "--thread", "a", "--var", "flag=x")
    assert clean.code == 0, clean.err
    assert _counts(clean) == (0, 0)
    assert _run(capsys, g, "--json", "--thread", "b").code == 3
    again = _run(capsys, g, "--json", "--thread", "b")
    assert again.code == 3
    assert _counts(again) == (1, 0)
    assert len(again.json["errors"]) == 2


@pytest.mark.req("REQ-YG-700")
@pytest.mark.parametrize(
    "entry",
    [
        {"type": "state_error", "message": "m"},
        {"type": "nope", "message": "m", "node": "n"},
    ],
)
def test_ac10_malformed_initial_error_exits_1_before_nodes(
    tmp_path, capsys, monkeypatch, entry
):
    mark = tmp_path / "ran"
    monkeypatch.setenv("FR1097_MARK", str(mark))
    imp = _import_file(tmp_path, entry)
    o = _run(capsys, _graph(tmp_path, ["py_ok"]), "--import-state", str(imp))
    assert o.code == 1
    assert "invalid initial state errors[0]" in o.out + o.err
    assert not mark.exists()


# AC-11 -----------------------------------------------------------------------


@pytest.mark.req("REQ-YG-700")
def test_ac11_serialized_dict_error_is_tallied(tmp_path, capsys):
    o = _run(capsys, _graph(tmp_path, ["emit_dict"]), "--json")
    assert o.code == 3, o.err
    assert _counts(o) == (1, 0)
    assert "emitter: dict err" in o.err


@pytest.mark.req("REQ-YG-700")
@pytest.mark.parametrize(
    ("node", "index"), [("emit_missing_node", 0), ("emit_unknown_type", 1)]
)
def test_ac11_malformed_result_error_exits_1(tmp_path, capsys, echo_llm, node, index):
    nodes = [node] if index == 0 else ["p5", node]
    exports = "exports:\n  result:\n    format: json\n    filename: r.json\n"
    g = _graph(tmp_path, ["py_ok", *nodes], exports)
    o = _run(capsys, g, "--json", "--export")
    assert o.code == 1
    assert f"invalid result errors[{index}]" in o.err
    assert not any(ln.startswith("{") for ln in o.out.splitlines())
    assert not (tmp_path / "outputs").exists()
    assert "completed with" not in o.err


# AC-12 -----------------------------------------------------------------------


@pytest.mark.req("REQ-YG-700")
@pytest.mark.parametrize("mode", ["text", "json"])
def test_ac12_returned_guard_halt_exits_3(tmp_path, capsys, echo_llm, mode):
    argv = ["--json"] if mode == "json" else []
    o = _run(capsys, _graph(tmp_path, ["py_ok", "guard_halt"]), *argv)
    assert o.code == 3, o.err
    assert "guard_halt: guard halt fired" in o.err
    if mode == "json":
        assert _counts(o) == (1, 0)
    else:
        assert "RESULT" in o.out


@pytest.mark.req("REQ-YG-700")
def test_ac12_raised_verify_halt_exits_1(tmp_path, capsys):
    verify = 'verify:\n  - check: "state.result >= 100"\n    on_fail: halt\n    message: verify halt\n'
    o = _run(capsys, _graph(tmp_path, ["py_ok"], verify))
    assert o.code == 1
    assert "completed with" not in o.err
