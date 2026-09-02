"""FR-807 route evidence record hardening witnesses (REQ-YG-552)."""

from __future__ import annotations

import json
from argparse import Namespace

import pytest

from yamlgraph.cli.export_commands import cmd_graph_export
from yamlgraph.utils import route_log


@pytest.fixture(autouse=True)
def _reset_route_log(monkeypatch):
    monkeypatch.delenv("YAMLGRAPH_ROUTE_LOG", raising=False)
    route_log.reset_route_log()
    yield
    route_log.reset_route_log()


@pytest.mark.req("REQ-YG-552")
def test_route_run_context_emits_bound_header_route_and_end(tmp_path, monkeypatch):
    graph = tmp_path / "graph.yaml"
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    graph.write_text(
        "name: evidence\nprompts_relative: true\nprompts_dir: prompts\n"
        "nodes:\n  classify:\n    type: llm\n    prompt: classify\n"
        "    state_key: result\nedges:\n  - from: START\n    to: classify\n"
        "  - from: classify\n    to: END\n",
        encoding="utf-8",
    )
    (prompts / "classify.yaml").write_text(
        "system: classify\nuser: '{input}'\n", encoding="utf-8"
    )
    sink = tmp_path / "route.jsonl"
    monkeypatch.setenv("YAMLGRAPH_ROUTE_LOG", str(sink))

    with route_log.route_run_context(graph, thread_id="thread-7") as run:
        route_log.emit_route("classify", "default", "END")

    lines = [json.loads(line) for line in sink.read_text(encoding="utf-8").splitlines()]
    assert [line["event"] for line in lines] == ["run", "route", "run_end"]
    assert lines[0]["run_id"] == run.run_id == lines[2]["run_id"]
    assert lines[0]["artifact_hash"].startswith("sha256:")
    assert lines[0]["thread_id"] == "thread-7"
    assert lines[1]["thread_id"] == "thread-7"
    assert lines[1]["ts"].endswith("Z")
    assert lines[2]["dropped_events"] == 0


@pytest.mark.req("REQ-YG-552")
def test_artifact_hash_is_prompt_sensitive_and_fails_missing_prompt(tmp_path):
    graph = tmp_path / "graph.yaml"
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    graph.write_text(
        "name: evidence\nprompts_relative: true\nprompts_dir: prompts\n"
        "nodes:\n  step:\n    type: llm\n    prompt: p\n    state_key: out\n"
        "edges:\n  - from: START\n    to: step\n  - from: step\n    to: END\n",
        encoding="utf-8",
    )
    prompt = prompts / "p.yaml"
    prompt.write_text("system: one\nuser: hi\n", encoding="utf-8")

    first = route_log.compute_artifact_hash(graph)
    assert first == route_log.compute_artifact_hash(graph)
    prompt.write_text("system: two\nuser: hi\n", encoding="utf-8")
    assert route_log.compute_artifact_hash(graph) != first
    prompt.unlink()
    with pytest.raises(ValueError, match="prompt|artifact"):
        route_log.compute_artifact_hash(graph)


@pytest.mark.req("REQ-YG-552")
def test_artifact_hash_includes_subgraph_transitively(tmp_path):
    child = tmp_path / "child.yaml"
    child.write_text(
        "name: child\nnodes:\n  c:\n    type: passthrough\n"
        "edges:\n  - from: START\n    to: c\n  - from: c\n    to: END\n",
        encoding="utf-8",
    )
    parent = tmp_path / "graph.yaml"
    parent.write_text(
        "name: parent\nnodes:\n  child:\n    type: subgraph\n"
        "    graph: child.yaml\nedges:\n  - from: START\n    to: child\n"
        "  - from: child\n    to: END\n",
        encoding="utf-8",
    )

    first = route_log.compute_artifact_hash(parent)
    child.write_text(child.read_text(encoding="utf-8") + "description: changed\n", encoding="utf-8")
    assert route_log.compute_artifact_hash(parent) != first


@pytest.mark.req("REQ-YG-552")
def test_artifact_hash_includes_graph_tool_transitively(tmp_path):
    child = tmp_path / "child.yaml"
    child.write_text(
        "name: child\nnodes:\n  c:\n    type: passthrough\n"
        "edges:\n  - from: START\n    to: c\n  - from: c\n    to: END\n",
        encoding="utf-8",
    )
    manifest = tmp_path / "child.tool.yaml"
    manifest.write_text(
        "name: child\ndescription: child graph\nruntime:\n  type: graph\n"
        "  path: child.yaml\n",
        encoding="utf-8",
    )
    parent = tmp_path / "graph.yaml"
    parent.write_text(
        "name: parent\ntools:\n  child:\n    manifest: child.tool.yaml\n"
        "nodes:\n  step:\n    type: passthrough\n"
        "edges:\n  - from: START\n    to: step\n  - from: step\n    to: END\n",
        encoding="utf-8",
    )

    first = route_log.compute_artifact_hash(parent)
    child.write_text(child.read_text(encoding="utf-8") + "description: changed\n", encoding="utf-8")
    assert route_log.compute_artifact_hash(parent) != first


@pytest.mark.asyncio
@pytest.mark.req("REQ-YG-552")
async def test_async_entrypoint_emits_run_envelope(tmp_path, monkeypatch):
    from yamlgraph.executor_async import run_graph_async

    graph = tmp_path / "graph.yaml"
    graph.write_text(
        "name: async-evidence\nnodes:\n  step:\n    type: passthrough\n"
        "edges:\n  - from: START\n    to: step\n  - from: step\n    to: END\n",
        encoding="utf-8",
    )
    sink = tmp_path / "route.jsonl"
    monkeypatch.setenv("YAMLGRAPH_ROUTE_LOG", str(sink))

    class App:
        _yamlgraph_source_path = str(graph)

        async def ainvoke(self, state, config):
            route_log.emit_route("step", "default", "END")
            return state

    await run_graph_async(App(), {}, {"configurable": {"thread_id": "async"}})
    records = [json.loads(line) for line in sink.read_text(encoding="utf-8").splitlines()]
    assert [record["event"] for record in records] == ["run", "route", "run_end"]


@pytest.mark.req("REQ-YG-552")
def test_overlay_rejects_headerless_and_mismatched_route_logs(tmp_path):
    graph = tmp_path / "graph.yaml"
    graph.write_text(
        "name: evidence\nnodes:\n  step:\n    type: passthrough\n"
        "edges:\n  - from: START\n    to: step\n  - from: step\n    to: END\n",
        encoding="utf-8",
    )
    overlay = tmp_path / "route.jsonl"
    args = Namespace(
        graph_path=str(graph), mermaid=True, overlay=str(overlay), output=None
    )

    overlay.write_text(
        json.dumps(
            {
                "event": "route",
                "node": "step",
                "value": "default",
                "target": "END",
                "thread_id": None,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(SystemExit) as missing:
        cmd_graph_export(args)
    assert missing.value.code == 1

    overlay.write_text(
        json.dumps({"event": "run", "artifact_hash": "sha256:wrong"}) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(SystemExit) as mismatch:
        cmd_graph_export(args)
    assert mismatch.value.code == 1


@pytest.mark.req("REQ-YG-552")
def test_failed_record_increments_counter_once_without_raising(monkeypatch):
    monkeypatch.setenv("YAMLGRAPH_ROUTE_LOG", "1")
    monkeypatch.setattr(
        route_log, "_deliver_record", lambda record: (_ for _ in ()).throw(OSError())
    )

    route_log.emit_route("step", "default", "END")

    assert route_log.route_log_dropped_count() == 1
