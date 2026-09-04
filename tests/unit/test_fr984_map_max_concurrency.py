"""FR-984: expose LangGraph ``max_concurrency`` for map fan-out (REQ-YG-645).

LangGraph throttles parallel ``Send`` tasks with a semaphore when
``RunnableConfig["max_concurrency"]`` is set. yamlgraph never passed it:
no ``config:`` key, no CLI flag. These witnesses freeze the contract from
the FR-984 judgement: positive-int at load and at the parser, CLI over
YAML, no key when absent, and a compiled-map behavioural proof at N = 2
over both ``invoke`` and ``ainvoke``.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from yamlgraph.compile.graph_loader import GraphConfig, compile_graph

REPO = Path(__file__).parent.parent.parent


def _graph(config_block: dict | None = None) -> dict:
    cfg: dict = {
        "name": "fr984",
        "version": "1.0",
        "nodes": {"noop": {"type": "passthrough"}},
        "edges": [{"from": "START", "to": "noop"}, {"from": "noop", "to": "END"}],
    }
    if config_block is not None:
        cfg["config"] = config_block
    return cfg


# ---------------------------------------------------------------------------
# AC-01 — load boundary
# ---------------------------------------------------------------------------


class TestGraphConfigMaxConcurrency:
    @pytest.mark.req("REQ-YG-645")
    def test_absent_is_none(self) -> None:
        assert GraphConfig(_graph()).max_concurrency is None
        assert GraphConfig(_graph({"recursion_limit": 10})).max_concurrency is None

    @pytest.mark.req("REQ-YG-645")
    def test_positive_int_retained(self) -> None:
        assert GraphConfig(_graph({"max_concurrency": 4})).max_concurrency == 4
        assert GraphConfig(_graph({"max_concurrency": 1})).max_concurrency == 1

    @pytest.mark.req("REQ-YG-645")
    @pytest.mark.parametrize("bad", [True, False, "4", 2.5, 0, -1])
    def test_invalid_rejected_at_load(self, bad) -> None:
        with pytest.raises(ValueError, match="max_concurrency"):
            GraphConfig(_graph({"max_concurrency": bad}))


# ---------------------------------------------------------------------------
# AC-02 — run-config builder precedence
# ---------------------------------------------------------------------------


def _args(**overrides) -> argparse.Namespace:
    base = {
        "thread": None,
        "recursion_limit": None,
        "timeout": None,
        "share_trace": False,
        "token_usage": False,
        "max_concurrency": None,
    }
    base.update(overrides)
    return argparse.Namespace(**base)


def _gc(max_concurrency=None) -> MagicMock:
    gc = MagicMock()
    gc.data = {}
    gc.raw_config = {}
    gc.recursion_limit = 50
    gc.timeout = None
    gc.max_concurrency = max_concurrency
    return gc


@patch("yamlgraph.utils.tracing.create_tracer", return_value=None)
@patch("yamlgraph.utils.tracing.inject_tracer_config")
class TestBuildRunConfigMaxConcurrency:
    @pytest.mark.req("REQ-YG-645")
    def test_absent_everywhere_omits_key(self, _i, _t) -> None:
        from yamlgraph.cli.graph_run_helpers import _build_run_config

        _, config, *_ = _build_run_config(_args(), _gc(), {})
        assert "max_concurrency" not in config

    @pytest.mark.req("REQ-YG-645")
    def test_yaml_value_used_when_cli_absent(self, _i, _t) -> None:
        from yamlgraph.cli.graph_run_helpers import _build_run_config

        _, config, *_ = _build_run_config(_args(), _gc(4), {})
        assert config["max_concurrency"] == 4

    @pytest.mark.req("REQ-YG-645")
    def test_cli_overrides_yaml(self, _i, _t) -> None:
        from yamlgraph.cli.graph_run_helpers import _build_run_config

        _, config, *_ = _build_run_config(_args(max_concurrency=2), _gc(4), {})
        assert config["max_concurrency"] == 2


# ---------------------------------------------------------------------------
# AC-03 — parser
# ---------------------------------------------------------------------------


class TestCliFlag:
    @pytest.mark.req("REQ-YG-645")
    def test_accepts_positive_int(self) -> None:
        from yamlgraph.cli import create_parser

        ns = create_parser().parse_args(
            ["graph", "run", "g.yaml", "--max-concurrency", "3"]
        )
        assert ns.max_concurrency == 3

    @pytest.mark.req("REQ-YG-645")
    def test_default_is_none(self) -> None:
        from yamlgraph.cli import create_parser

        ns = create_parser().parse_args(["graph", "run", "g.yaml"])
        assert ns.max_concurrency is None

    @pytest.mark.req("REQ-YG-645")
    @pytest.mark.parametrize("bad", ["0", "-1"])
    def test_rejects_non_positive_before_invoke(self, bad, capsys) -> None:
        from yamlgraph.cli import create_parser

        with pytest.raises(SystemExit) as exc:
            create_parser().parse_args(
                ["graph", "run", "g.yaml", "--max-concurrency", bad]
            )
        assert exc.value.code == 2
        assert "--max-concurrency" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# AC-04 — published schema
# ---------------------------------------------------------------------------


class TestSchema:
    @pytest.mark.req("REQ-YG-645")
    def test_graph_v1_publishes_max_concurrency(self) -> None:
        schema = json.loads(
            (REPO / "yamlgraph" / "schemas" / "graph-v1.json").read_text(
                encoding="utf-8"
            )
        )
        prop = schema["properties"]["config"]["properties"]["max_concurrency"]
        assert prop["type"] == "integer"
        assert prop["minimum"] == 1


# ---------------------------------------------------------------------------
# AC-05 — behavioural witness: compiled map, N = 2, invoke and ainvoke
# ---------------------------------------------------------------------------

_LOCK = threading.Lock()
_ACTIVE = 0
_PEAK = 0
ITEMS = 40


def _reset_counter() -> None:
    global _ACTIVE, _PEAK
    with _LOCK:
        _ACTIVE = 0
        _PEAK = 0


def _counting_worker(state: dict) -> int:
    """Map sub-node: hold a slot for 50 ms and record the peak occupancy."""
    global _ACTIVE, _PEAK
    with _LOCK:
        _ACTIVE += 1
        _PEAK = max(_PEAK, _ACTIVE)
    try:
        time.sleep(0.05)
    finally:
        with _LOCK:
            _ACTIVE -= 1
    return state["item"]


def _fan_out_app():
    cfg = {
        "name": "fr984-fanout",
        "version": "1.0",
        "state": {
            "items": {"type": "list"},
            "results": {"type": "list", "reducer": "sorted_add"},
        },
        "tools": {
            "counter": {
                "type": "python",
                "module": __name__,
                "function": "_counting_worker",
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
    return compile_graph(GraphConfig(cfg)).compile()


def _results(final: dict) -> list[int]:
    # scalar python sub-node returns collect as {"_map_index": i, "value": n}
    return sorted(r["value"] for r in final["results"])


def _run(app, payload: dict, use_async: bool, **config) -> dict:
    if use_async:
        return asyncio.run(app.ainvoke(payload, config=config or None))
    return app.invoke(payload, config=config or None)


class TestBehaviouralWitness:
    @pytest.mark.req("REQ-YG-645")
    @pytest.mark.parametrize("use_async", [False, True], ids=["invoke", "ainvoke"])
    def test_max_concurrency_two_caps_peak(self, use_async: bool) -> None:
        app = _fan_out_app()
        payload = {"items": list(range(ITEMS)), "results": []}

        _reset_counter()
        final = _run(app, payload, use_async, max_concurrency=2)
        assert _PEAK <= 2, f"configured N=2 but peak parallelism was {_PEAK}"
        assert _results(final) == list(range(ITEMS))

        _reset_counter()
        final = _run(app, payload, use_async)
        assert _PEAK > 2, f"unthrottled control expected peak > 2, got {_PEAK}"
        assert _results(final) == list(range(ITEMS))
