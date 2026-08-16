"""Route decision log tests (FR-723, AC-01).

One JSON line per routing decision at the single seam where all decisions
happen (routing.py). The zero-overhead-when-off guard is the load-bearing
criterion (judgement blast-radius ruling) — it is tested first.
"""

import json
import logging
import os
from unittest.mock import MagicMock

import pytest
from langgraph.graph import END
from langgraph.types import Send

from yamlgraph.routing import make_expr_router_fn, make_router_fn
from yamlgraph.utils import route_log
from yamlgraph.utils.route_log import (
    current_route_thread_id,
    emit_route,
    reset_route_log,
    route_log_enabled,
    route_thread_id,
)


@pytest.fixture(autouse=True)
def _isolated_route_log(monkeypatch):
    """Reset flag, env, and file sinks around every test."""
    monkeypatch.delenv("YAMLGRAPH_ROUTE_LOG", raising=False)
    reset_route_log()
    yield
    reset_route_log()


@pytest.fixture
def route_records():
    """Collect raw records emitted on the public yamlgraph.route logger."""
    records: list[logging.LogRecord] = []

    class _Collector(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    handler = _Collector(level=logging.INFO)
    logger = logging.getLogger("yamlgraph.route")
    logger.addHandler(handler)
    yield records
    logger.removeHandler(handler)


def _lines(records: list[logging.LogRecord]) -> list[dict]:
    return [json.loads(r.getMessage()) for r in records]


class TestZeroOverheadWhenOff:
    """AC-01 load-bearing: disabled ⇒ zero lines AND no serialization cost."""

    @pytest.mark.req("REQ-YG-552")
    def test_disabled_emits_nothing_and_never_serializes(
        self, monkeypatch, route_records
    ):
        dumps_spy = MagicMock(side_effect=AssertionError("must not serialize"))
        monkeypatch.setattr(route_log.json, "dumps", dumps_spy)

        router = make_router_fn(["a", "b"], "chooser")
        assert router({"_route": "b"}) == "b"

        expr = make_expr_router_fn([("score < 0.5", "refine")], "critique")
        assert expr({"score": 0.3}) == "refine"
        assert expr({"_loop_limit_reached": True}) == END

        assert route_records == []
        dumps_spy.assert_not_called()

    @pytest.mark.req("REQ-YG-552")
    def test_env_flag_off_values(self, monkeypatch):
        for value in ("", "0", "false"):
            monkeypatch.setenv("YAMLGRAPH_ROUTE_LOG", value)
            assert route_log_enabled() is False


class TestSimpleRouterEmission:
    """make_router_fn decides too (judgement advisory: not expr-only)."""

    @pytest.mark.req("REQ-YG-552")
    def test_matched_route_emits_line(self, monkeypatch, route_records):
        monkeypatch.setenv("YAMLGRAPH_ROUTE_LOG", "1")
        router = make_router_fn(["positive", "negative"], "classify")
        assert router({"_route": "negative"}) == "negative"

        (line,) = _lines(route_records)
        assert line == {
            "event": "route",
            "node": "classify",
            "value": "negative",
            "target": "negative",
            "thread_id": None,
            "ts": line["ts"],
        }
        assert line["ts"].endswith("Z")

    @pytest.mark.req("REQ-YG-552")
    def test_default_route_emits_default_value(self, monkeypatch, route_records):
        monkeypatch.setenv("YAMLGRAPH_ROUTE_LOG", "1")
        router = make_router_fn(["a", "b"], "classify")
        assert router({}) == "a"

        (line,) = _lines(route_records)
        assert line["value"] == "default"
        assert line["target"] == "a"


class TestExprRouterEmission:
    @pytest.mark.req("REQ-YG-552")
    def test_condition_match_emits_condition_and_target(
        self, monkeypatch, route_records
    ):
        monkeypatch.setenv("YAMLGRAPH_ROUTE_LOG", "1")
        router = make_expr_router_fn(
            [("critique.score < 0.8", "refine"), ("critique.score >= 0.8", "END")],
            "critique",
        )
        assert router({"critique": {"score": 0.5}}) == "refine"

        (line,) = _lines(route_records)
        assert line["node"] == "critique"
        assert line["value"] == "critique.score < 0.8"
        assert line["target"] == "refine"

    @pytest.mark.req("REQ-YG-552")
    def test_loop_exit_with_target_emits(self, monkeypatch, route_records):
        """The sixth seam — loop exhaustion routes must be visible (FR-723)."""
        monkeypatch.setenv("YAMLGRAPH_ROUTE_LOG", "1")
        router = make_expr_router_fn(
            [("score < 0.8", "refine")], "critique", loop_exit_target="recap"
        )
        assert router({"_loop_limit_reached": True}) == "recap"

        (line,) = _lines(route_records)
        assert line["value"] == "loop_exit"
        assert line["target"] == "recap"

    @pytest.mark.req("REQ-YG-552")
    def test_loop_exit_without_target_emits_end(self, monkeypatch, route_records):
        monkeypatch.setenv("YAMLGRAPH_ROUTE_LOG", "1")
        router = make_expr_router_fn([("score < 0.8", "refine")], "critique")
        assert router({"_loop_limit_reached": True}) == END

        (line,) = _lines(route_records)
        assert line["value"] == "loop_exit"
        assert line["target"] == "END"

    @pytest.mark.req("REQ-YG-552")
    def test_no_match_fallthrough_emits(self, monkeypatch, route_records):
        monkeypatch.setenv("YAMLGRAPH_ROUTE_LOG", "1")
        router = make_expr_router_fn([("score > 0.9", "a")], "critique")
        assert router({"score": 0.1}) == END

        (line,) = _lines(route_records)
        assert line["value"] == "no_match"
        assert line["target"] == "END"


class TestMapFanOutEmission:
    """R-2: map fan-out emits name + count, never Send payloads (privacy)."""

    @pytest.mark.req("REQ-YG-552")
    def test_map_fanout_emits_name_count_no_state(self, monkeypatch, route_records):
        monkeypatch.setenv("YAMLGRAPH_ROUTE_LOG", "1")

        def map_edge_fn(state):
            return [
                Send("process_items_sub", {"item": "SECRET-PAYLOAD-1"}),
                Send("process_items_sub", {"item": "SECRET-PAYLOAD-2"}),
            ]

        router = make_expr_router_fn(
            [("ready == True", "process_items")],
            "generate",
            map_nodes={"process_items": (map_edge_fn, "process_items_sub")},
        )
        result = router({"ready": True})
        assert isinstance(result, list) and len(result) == 2

        (line,) = _lines(route_records)
        assert line["target"] == "process_items"
        assert line["fan_out"] == 2
        raw = route_records[0].getMessage()
        assert "SECRET" not in raw
        assert "Send(" not in raw


class TestThreadId:
    """R-1: contextvar set around invocation; null never fabricated."""

    @pytest.mark.req("REQ-YG-552")
    def test_contextvar_carried_into_route_line(self, monkeypatch, route_records):
        monkeypatch.setenv("YAMLGRAPH_ROUTE_LOG", "1")
        router = make_router_fn(["a"], "classify")
        with route_thread_id("call-123"):
            router({"_route": "a"})
        router({"_route": "a"})

        first, second = _lines(route_records)
        assert first["thread_id"] == "call-123"
        assert second["thread_id"] is None

    @pytest.mark.req("REQ-YG-552")
    def test_cli_invoke_graph_sets_contextvar(self):
        from yamlgraph.cli.graph_run_helpers import _invoke_graph

        seen: dict = {}

        class FakeApp:
            def invoke(self, input_data, config=None):
                seen["tid"] = current_route_thread_id()
                return {}

        _invoke_graph(
            FakeApp(), {}, {"configurable": {"thread_id": "t-9"}}, use_async=False
        )
        assert seen["tid"] == "t-9"
        assert current_route_thread_id() is None

    @pytest.mark.req("REQ-YG-552")
    def test_run_graph_async_sets_contextvar(self):
        import asyncio

        from yamlgraph.executor_async import run_graph_async

        seen: dict = {}

        class FakeApp:
            async def ainvoke(self, state, config=None):
                seen["tid"] = current_route_thread_id()
                return {}

        asyncio.run(
            run_graph_async(FakeApp(), {}, {"configurable": {"thread_id": "async-7"}})
        )
        assert seen["tid"] == "async-7"


class TestForensicDiscipline:
    @pytest.mark.req("REQ-YG-552")
    def test_emission_never_raises(self, monkeypatch):
        monkeypatch.setenv("YAMLGRAPH_ROUTE_LOG", "1")
        monkeypatch.setattr(
            route_log.json, "dumps", MagicMock(side_effect=RuntimeError("boom"))
        )
        emit_route("critique", "loop_exit", "recap")  # must not raise


class TestOptInSurfaces:
    @pytest.mark.req("REQ-YG-552")
    def test_graph_yaml_observability_flag_enables(self, tmp_path):
        from yamlgraph.compile.graph_loader import compile_graph, load_graph_config

        graph_yaml = tmp_path / "graph.yaml"
        graph_yaml.write_text(
            """
name: flag-demo
observability:
  route_log: true
nodes:
  step:
    type: passthrough
edges:
  - from: START
    to: step
  - from: step
    to: END
"""
        )
        assert route_log_enabled() is False
        compile_graph(load_graph_config(graph_yaml))
        assert route_log_enabled() is True

    @pytest.mark.req("REQ-YG-552")
    def test_env_path_value_appends_jsonl_file(
        self, monkeypatch, tmp_path, route_records
    ):
        sink = tmp_path / "route.jsonl"
        monkeypatch.setenv("YAMLGRAPH_ROUTE_LOG", str(sink))
        router = make_router_fn(["a"], "classify")
        router({"_route": "a"})
        router({"_route": "a"})

        lines = [json.loads(line) for line in sink.read_text().splitlines() if line]
        assert len(lines) == 2
        assert all(entry["event"] == "route" for entry in lines)

    @pytest.mark.req("REQ-YG-552")
    def test_env_path_auto_creates_parent_directories(self, monkeypatch, tmp_path):
        sink = tmp_path / "nested" / "routes" / "custom.route.jsonl"
        monkeypatch.setenv("YAMLGRAPH_ROUTE_LOG", str(sink))

        router = make_router_fn(["a"], "classify")
        router({"_route": "a"})

        assert sink.exists()
        lines = [json.loads(line) for line in sink.read_text().splitlines() if line]
        assert len(lines) == 1

    @pytest.mark.req("REQ-YG-552")
    def test_env_existing_directory_writes_default_route_jsonl(
        self, monkeypatch, tmp_path
    ):
        route_dir = tmp_path / "routes"
        route_dir.mkdir()
        monkeypatch.setenv("YAMLGRAPH_ROUTE_LOG", str(route_dir))

        router = make_router_fn(["a"], "classify")
        router({"_route": "a"})

        sink = route_dir / "route.jsonl"
        assert sink.exists()
        lines = [json.loads(line) for line in sink.read_text().splitlines() if line]
        assert len(lines) == 1

    @pytest.mark.req("REQ-YG-552")
    def test_env_trailing_separator_treated_as_directory_intent(
        self, monkeypatch, tmp_path
    ):
        route_dir = tmp_path / "new-routes"
        monkeypatch.setenv("YAMLGRAPH_ROUTE_LOG", f"{route_dir}{os.sep}")

        router = make_router_fn(["a"], "classify")
        router({"_route": "a"})

        sink = route_dir / "route.jsonl"
        assert sink.exists()
        lines = [json.loads(line) for line in sink.read_text().splitlines() if line]
        assert len(lines) == 1

    @pytest.mark.req("REQ-YG-552")
    def test_relative_env_path_resolves_from_process_cwd(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("YAMLGRAPH_ROUTE_LOG", "outputs/routes/run.route.jsonl")

        router = make_router_fn(["a"], "classify")
        router({"_route": "a"})

        sink = tmp_path / "outputs" / "routes" / "run.route.jsonl"
        assert sink.exists()
        lines = [json.loads(line) for line in sink.read_text().splitlines() if line]
        assert len(lines) == 1

    @pytest.mark.req("REQ-YG-552")
    def test_invalid_special_target_warns_once_and_continues(
        self, monkeypatch, route_records
    ):
        monkeypatch.setenv("YAMLGRAPH_ROUTE_LOG", "/dev/null")

        router = make_router_fn(["a"], "classify")
        router({"_route": "a"})
        router({"_route": "a"})

        warnings = [
            r
            for r in route_records
            if r.levelno == logging.WARNING
            and "YAMLGRAPH_ROUTE_LOG='/dev/null' ignored" in r.getMessage()
        ]
        assert len(warnings) == 1

        info_messages = [
            r.getMessage() for r in route_records if r.levelno == logging.INFO
        ]
        info_lines = [json.loads(line) for line in info_messages]
        assert len(info_lines) == 2
        assert all(line["event"] == "route" for line in info_lines)
