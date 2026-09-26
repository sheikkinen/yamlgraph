"""FR-1084: graph run refuses --var/--var-file keys the state schema cannot hold."""

from __future__ import annotations

import asyncio
import json
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

import pytest
from langchain_core.language_models import SimpleChatModel
from langchain_core.messages import AIMessageChunk
from langchain_core.outputs import ChatGenerationChunk

GRAPH_YAML = """\
version: "1.0"
name: fr1084-fixture
prompts_relative: true
prompts_dir: prompts
state:
  declared: str
  gv_declared: str
  _hidden: str
variables:
  gv_declared: default-gv
  gv_only: from-graph
nodes:
  echo:
    type: llm
    prompt: echo
    variables:
      declared: "{state.declared}"
      inferred_sk: "{state.inferred_sk}"
      gv_declared: "{state.gv_declared}"
    state_key: inferred_sk
  witness:
    type: llm
    prompt: echo
    variables:
      declared: "{state.declared}"
      inferred_sk: "{state.inferred_sk}"
      gv_declared: "{state.gv_declared}"
    state_key: witness_out
edges:
  - from: START
    to: echo
  - from: echo
    to: witness
  - from: witness
    to: END
"""

PROMPT_YAML = """\
system: echo
user: "declared={declared} inferred_sk={inferred_sk} gv_declared={gv_declared}"
"""

VISIBLE_ACCEPTED = (
    "completed_at, current_step, declared, errors, gv_declared, inferred_sk, "
    "input, message, messages, started_at, style, thread_id, topic, witness_out, "
    "word_count"
)

LLM_PATCH_TARGETS = (
    "yamlgraph.utils.llm_factory.create_llm",
    "yamlgraph.executor.create_llm",
    "yamlgraph.executor_async.create_llm",
    "yamlgraph.utils.llm_factory_async.create_llm",
)


class _EchoModel(SimpleChatModel):
    """Returns its rendered prompt, so the output witnesses what reached state."""

    calls: list[str] = []

    def _call(self, messages, stop=None, run_manager=None, **kwargs) -> str:
        text = " | ".join(str(m.content) for m in messages)
        self.calls.append(text)
        return text

    def _stream(self, messages, stop=None, run_manager=None, **kwargs):
        text = self._call(messages)
        chunk = ChatGenerationChunk(message=AIMessageChunk(content=text))
        if run_manager:
            run_manager.on_llm_new_token(text, chunk=chunk)
        yield chunk

    @property
    def _llm_type(self) -> str:
        return "fr1084-echo"


@pytest.fixture
def graph_file(tmp_path: Path) -> Path:
    (tmp_path / "prompts").mkdir()
    (tmp_path / "prompts" / "echo.yaml").write_text(PROMPT_YAML, encoding="utf-8")
    path = tmp_path / "graph.yaml"
    path.write_text(GRAPH_YAML, encoding="utf-8")
    return path


@pytest.fixture
def echo_llm():
    model = _EchoModel(calls=[])
    with ExitStack() as stack:
        for target in LLM_PATCH_TARGETS:
            stack.enter_context(patch(target, return_value=model))
        yield model


def _run(graph_file: Path, *argv: str) -> None:
    from yamlgraph.cli import create_parser
    from yamlgraph.cli.graph_commands import cmd_graph_run

    args = create_parser().parse_args(["graph", "run", str(graph_file), *argv])
    cmd_graph_run(args)


def _diagnostic(unknown: str) -> str:
    return (
        f"❌ Unknown --var/--var-file state key(s) for graph.yaml: {unknown}; "
        f"accepted keys: {VISIBLE_ACCEPTED}"
    )


@pytest.mark.req("REQ-YG-697")
def test_ac01_unknown_var_exits_1_before_any_llm_call(graph_file, echo_llm, capsys):
    with (
        patch("yamlgraph.cli.graph_commands._build_run_config") as build,
        pytest.raises(SystemExit) as exc,
    ):
        _run(graph_file, "--var", "unknown=x")

    assert exc.value.code == 1
    assert _diagnostic("unknown") in capsys.readouterr().out.splitlines()
    assert echo_llm.calls == []
    build.assert_not_called()


@pytest.mark.req("REQ-YG-697")
def test_ac02_file_and_cli_unknowns_are_unioned_sorted_once(
    graph_file, tmp_path, echo_llm, capsys
):
    var_file = tmp_path / "vars.yaml"
    var_file.write_text("zeta: 1\nalpha: 2\ndeclared: ok\n", encoding="utf-8")

    with (
        patch("yamlgraph.cli.graph_commands._build_run_config") as build,
        patch("yamlgraph.cli.graph_commands._run_graph_until_complete") as invoke,
        pytest.raises(SystemExit) as exc,
    ):
        _run(
            graph_file,
            "--var-file",
            str(var_file),
            "--var",
            "alpha=3",
            "--var",
            "mid=4",
        )

    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert out.count("❌ Unknown --var/--var-file") == 1
    assert _diagnostic("alpha, mid, zeta") in out.splitlines()
    build.assert_not_called()
    invoke.assert_not_called()
    assert echo_llm.calls == []


@pytest.mark.req("REQ-YG-697")
def test_ac03_json_mode_keeps_stdout_empty(graph_file, echo_llm, capsys):
    with pytest.raises(SystemExit) as exc:
        _run(graph_file, "--json", "--var", "unknown=x")

    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == _diagnostic("unknown") + "\n"


ACCEPTED_ARGV = (
    "--var",
    "declared=a",
    "--var",
    "inferred_sk=b",
    "--var",
    "gv_declared=c",
)


@pytest.mark.req("REQ-YG-697")
@pytest.mark.parametrize("mode_flag", [[], ["--async"]])
def test_ac04_accepted_keys_reach_state_sync_and_async(
    graph_file, echo_llm, capsys, mode_flag
):
    _run(graph_file, "--json", *mode_flag, *ACCEPTED_ARGV)

    state = json.loads(capsys.readouterr().out)
    assert (state["declared"], state["inferred_sk"], state["gv_declared"]) == (
        "a",
        "b",
        "c",
    )
    assert "declared=a inferred_sk=b gv_declared=c" in state["witness_out"]


@pytest.mark.req("REQ-YG-697")
def test_ac04_accepted_keys_reach_state_stream(graph_file, echo_llm, capsys):
    _run(graph_file, "--stream", *ACCEPTED_ARGV)

    assert "declared=a inferred_sk=b gv_declared=c" in capsys.readouterr().out


def _compiled_app(graph_file: Path):
    from yamlgraph.compile.graph_loader import compile_graph, load_graph_config

    return compile_graph(load_graph_config(str(graph_file))).compile()


def _full_input(app) -> dict:
    values = {}
    for key in app.get_input_jsonschema()["properties"]:
        try:
            values[key] = app.channels[key].typ()
        except (AttributeError, TypeError):
            values[key] = f"v-{key}"
    values["not_in_schema"] = "dropped"
    return values


@pytest.mark.req("REQ-YG-697")
def test_ac05_input_schema_equals_retained_keys_in_every_mode(graph_file, echo_llm):
    app = _compiled_app(graph_file)
    schema_keys = set(app.get_input_jsonschema()["properties"])
    payload = _full_input(app)

    async def _astream_last():
        last = None
        async for chunk in app.astream(payload, stream_mode="values"):
            last = chunk
        return last

    for result in (
        app.invoke(payload),
        asyncio.run(app.ainvoke(payload)),
        asyncio.run(_astream_last()),
    ):
        assert set(result) == schema_keys
        assert "not_in_schema" not in result


@pytest.mark.req("REQ-YG-697")
def test_ac06_import_state_is_not_validated(graph_file, tmp_path, echo_llm, capsys):
    imported = tmp_path / "prior.json"
    imported.write_text(
        json.dumps({"declared": "from-prior", "other_graph_key": "foreign"}),
        encoding="utf-8",
    )

    _run(graph_file, "--json", "--import-state", str(imported))

    state = json.loads(capsys.readouterr().out)
    assert state["declared"] == "from-prior"
    assert "other_graph_key" not in state


@pytest.mark.req("REQ-YG-697")
def test_ac07_graph_variable_only_key_is_unknown(graph_file, echo_llm, capsys):
    with pytest.raises(SystemExit) as exc:
        _run(graph_file, "--var", "gv_only=x")

    assert exc.value.code == 1
    assert _diagnostic("gv_only") in capsys.readouterr().out.splitlines()


@pytest.mark.req("REQ-YG-697")
def test_ac07_underscore_key_accepted_but_hidden(graph_file, echo_llm, capsys):
    _run(graph_file, "--json", "--var", "_hidden=h")

    state = json.loads(capsys.readouterr().out)
    assert state["_hidden"] == "h"
    assert "_hidden" not in VISIBLE_ACCEPTED
