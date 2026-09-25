"""FR-1073: map result contract.

REQ-YG-692 witnesses. A map compiles to dispatch -> sub -> join. Branch
failures leave `collect` and land as typed `MapFailure` records in
`failures`; the join accounts every dispatched index against the exact
dispatch token and enforces `min_success` (strict by default).

Graphs are built from real YAML via load_and_compile so the dispatch,
wrapper, reducers and join run as compiled. New symbols are checked by
class name so RED fails on behaviour, not on imports (AC-21).
"""

import re
import textwrap
from pathlib import Path

import pytest
from langgraph.checkpoint.memory import MemorySaver

from yamlgraph.compile.graph_loader import load_and_compile
from yamlgraph.models.state_builder import build_state_class

TOOLS_SRC = textwrap.dedent(
    '''
    """FR-1073 test tools."""

    import time


    def ok(state):
        return {"out": {"v": state["item"]}}


    def fail_on_b(state):
        if state["item"] == "b":
            raise ValueError("poison b")
        return {"out": {"v": state["item"]}}


    def fail_on_7(state):
        if state["item"] == 7:
            raise ValueError("poison 7")
        return {"out": {"v": state["item"]}}


    def only_a(state):
        if state["item"] != "a":
            raise ValueError("not a")
        return {"out": {"v": state["item"]}}


    def errors_on_b(state):
        if state["item"] == "b":
            return {"out": None, "errors": ["bad b"]}
        return {"out": {"v": state["item"]}}


    def slow_on_b(state):
        if state["item"] == "b":
            time.sleep(2.0)
        return {"out": {"v": state["item"]}}


    def skip_on_b(state):
        if state["item"] == "b":
            return {"out": None, "_skipped": True, "errors": ["nested skip"]}
        return {"out": {"v": state["item"]}}


    def empty_error_keys(state):
        return {"out": {"v": state["item"]}, "errors": [], "error": None}


    def mutate_over(state):
        return {"out": {"v": state["item"]}, "items": list(state["items"]) + ["z"]}


    def consume(state):
        return {"seen": [r["v"] for r in state.get("results") or []]}


    def passthrough(state):
        return {}
    '''
)

GRAPH = """
name: fr1073
description: Map result contract witness.

state:
  items: list
  results: list
  seen: list

tools:
  sub:
    type: python
    path: tools_fr1073.py
    function: @FN@
  consume:
    type: python
    path: tools_fr1073.py
    function: consume
  passthrough:
    type: python
    path: tools_fr1073.py
    function: passthrough

nodes:
  fan:
    type: map
    over: "{state.items}"
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


def _compile(
    tmp_path: Path,
    fn: str = "ok",
    extra: str = "",
    nodes: str = "",
    edges: str = DEFAULT_EDGES,
):
    (tmp_path / "tools_fr1073.py").write_text(TOOLS_SRC, encoding="utf-8")
    text = (
        GRAPH.replace("@FN@", fn)
        .replace("@EXTRA@", textwrap.indent(textwrap.dedent(extra), "    "))
        .replace("@NODES@", nodes)
        .replace("@EDGES@", edges)
    )
    path = tmp_path / "graph.yaml"
    path.write_text(text, encoding="utf-8")
    return load_and_compile(str(path))


def _run(tmp_path: Path, items: list, **kwargs) -> dict:
    return _compile(tmp_path, **kwargs).compile().invoke({"items": items})


def _field(record, name):
    return record[name] if isinstance(record, dict) else getattr(record, name)


# ---------------------------------------------------------------------------
# AC-01 / AC-02 / AC-08: load-time schema
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-692")
class TestPolicySchema:
    @pytest.mark.parametrize("value", ["true", "'0.5'", ".nan", ".inf", "-1", "1.5"])
    def test_invalid_min_success_fails_at_load(self, tmp_path, value):
        with pytest.raises(ValueError, match=r"Map node 'fan': min_success"):
            _compile(tmp_path, extra=f"min_success: {value}")

    @pytest.mark.parametrize("value", ["0", "1", "5", "0.0", "0.5", "1.0"])
    def test_valid_min_success_loads(self, tmp_path, value):
        _compile(tmp_path, extra=f"min_success: {value}")

    @pytest.mark.parametrize(
        "value",
        ["results", "''", "errors", "current_step", "_loop_counts", "_map_open"],
    )
    def test_invalid_failures_key_fails_at_load(self, tmp_path, value):
        with pytest.raises(ValueError, match=r"Map node 'fan': failures"):
            _compile(tmp_path, extra=f"failures: {value}")

    def test_failures_defaults_to_collect_failures(self, tmp_path):
        out = _run(tmp_path, ["a", "b"], fn="fail_on_b", extra="min_success: 0")
        assert len(out["results_failures"]) == 1

    def test_custom_failures_key(self, tmp_path):
        out = _run(
            tmp_path,
            ["a", "b"],
            fn="fail_on_b",
            extra="failures: bad_rows\nmin_success: 0",
        )
        assert len(out["bad_rows"]) == 1
        assert "results_failures" not in out or not out["results_failures"]


# ---------------------------------------------------------------------------
# AC-04 / AC-05 / AC-09: branch outcome classification
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-692")
class TestBranchOutcome:
    FAILURE_FIELDS = {
        "map",
        "dispatch",
        "index",
        "error_type",
        "message",
        "node",
        "tolerated",
    }

    def _single_failure(self, out):
        failures = out["results_failures"]
        assert len(failures) == 1
        failure = failures[0]
        assert type(failure).__name__ == "MapFailure"
        assert set(type(failure).model_fields) == self.FAILURE_FIELDS
        return failure

    @pytest.mark.parametrize(
        ("fn", "extra"),
        [
            ("fail_on_b", "min_success: 0"),
            ("errors_on_b", "min_success: 0"),
            ("slow_on_b", "min_success: 0\ntimeout: 0.2"),
        ],
    )
    def test_failure_paths_share_one_shape(self, tmp_path, fn, extra):
        out = _run(tmp_path, ["a", "b", "c"], fn=fn, extra=extra)
        failure = self._single_failure(out)
        assert failure.map == "fan"
        assert failure.index == 1
        assert failure.node == "_map_fan_sub"
        assert failure.tolerated is False
        assert re.fullmatch(r"[0-9a-f]{32}", failure.dispatch)
        map_errors = [e for e in out["errors"] if e.node == "_map_fan_sub"]
        assert len(map_errors) == 1
        assert [r["v"] for r in out["results"]] == ["a", "c"]
        assert all("_error" not in r for r in out["results"])

    def test_empty_errors_and_none_error_are_success(self, tmp_path):
        out = _run(tmp_path, ["a", "b"], fn="empty_error_keys")
        assert [r["v"] for r in out["results"]] == ["a", "b"]
        assert not out.get("results_failures")
        assert out["seen"] == ["a", "b"]

    def test_skipped_is_tolerated_under_strict(self, tmp_path):
        out = _run(tmp_path, ["a", "b", "c"], fn="skip_on_b")
        failure = self._single_failure(out)
        assert failure.tolerated is True
        assert not [e for e in out.get("errors") or [] if "skip" in str(e)]
        assert not [
            e
            for e in out.get("errors") or []
            if getattr(e, "node", "") == "_map_fan_sub"
        ]
        verdict = out["_map_verdict"]["fan"]
        assert (verdict.succeeded, verdict.tolerated, verdict.failed) == (2, 1, 0)
        assert verdict.accepted == 3
        assert verdict.met is True
        assert out["seen"] == ["a", "c"]

    @pytest.mark.parametrize("model", ["MapFailure", "MapAccounting"])
    def test_record_requires_dispatch_token(self, model):
        from pydantic import ValidationError

        from yamlgraph.models import map_results

        fields = {"map": "fan", "dispatch": None, "index": 0}
        if model == "MapFailure":
            fields |= {
                "error_type": "ValueError",
                "message": "m",
                "node": "_map_fan_sub",
                "tolerated": False,
            }
        else:
            fields["outcome"] = "succeeded"
        with pytest.raises(ValidationError):
            getattr(map_results, model)(**fields)

    def test_branch_without_dispatch_token_fails(self):
        from yamlgraph.compile.map_contract import success_accounting
        from yamlgraph.models.map_results import MapAccountingError

        with pytest.raises(MapAccountingError, match="fan"):
            success_accounting("fan", {"_map_index": 0})

    def test_timeout_is_never_tolerated(self, tmp_path):
        out = _run(
            tmp_path,
            ["a", "b"],
            fn="slow_on_b",
            extra="timeout: 0.2\nmin_success: 0",
        )
        failure = self._single_failure(out)
        assert failure.tolerated is False
        assert failure.error_type == "TimeoutError"
        assert out["_map_verdict"]["fan"].failed == 1


# ---------------------------------------------------------------------------
# AC-06 / AC-07 / AC-08 / AC-10 / AC-19: join verdict
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-692")
class TestJoinVerdict:
    def test_strict_failure_raises_and_checkpoint_keeps_results(self, tmp_path):
        app = _compile(tmp_path, fn="fail_on_b").compile(checkpointer=MemorySaver())
        config = {"configurable": {"thread_id": "fr1073-strict"}}
        with pytest.raises(Exception) as exc_info:
            app.invoke({"items": ["a", "b", "c"]}, config)
        assert type(exc_info.value).__name__ == "MapCompletenessError"
        values = app.get_state(config).values
        assert [r["v"] for r in values["results"]] == ["a", "c"]
        assert len(values["results_failures"]) == 1
        assert sorted(row.index for row in values["_map_accounting"]) == [0, 1, 2]
        assert "seen" not in values or values["seen"] is None
        verdict = values["_map_verdict"]["fan"]
        assert (verdict.succeeded, verdict.failed, verdict.met) == (2, 1, False)
        assert values["_map_open"]["fan"] is None

    def test_fraction_threshold_passes_only_real_results(self, tmp_path):
        out = _run(
            tmp_path, list(range(100)), fn="fail_on_7", extra="min_success: 0.98"
        )
        v = out["_map_verdict"]["fan"]
        assert (v.dispatched, v.succeeded, v.tolerated, v.failed) == (100, 99, 0, 1)
        assert v.accepted == 99
        assert v.met is True
        assert len(out["seen"]) == 99
        assert 7 not in out["seen"]

    def test_int_one_accepts_one_item(self, tmp_path):
        out = _run(tmp_path, ["a", "b", "c"], fn="only_a", extra="min_success: 1")
        assert out["seen"] == ["a"]

    @pytest.mark.parametrize(
        ("fn", "extra"),
        [("only_a", "min_success: 1.0"), ("ok", "min_success: 5")],
    )
    def test_unmet_threshold_raises(self, tmp_path, fn, extra):
        with pytest.raises(Exception) as exc_info:
            _run(tmp_path, ["a", "b", "c"], fn=fn, extra=extra)
        assert type(exc_info.value).__name__ == "MapCompletenessError"

    def test_zero_items_routes_to_join(self, tmp_path):
        out = _run(tmp_path, [])
        v = out["_map_verdict"]["fan"]
        assert (v.dispatched, v.succeeded, v.tolerated, v.failed) == (0, 0, 0, 0)
        assert v.met is True
        assert out["seen"] == []

    def test_branch_mutating_over_cannot_change_dispatch(self, tmp_path):
        out = _run(tmp_path, ["a", "b", "c"], fn="mutate_over")
        assert out["_map_verdict"]["fan"].dispatched == 3
        assert out["seen"] == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# AC-12 / AC-13 / AC-16: tokens, shared channels, overlap, reducers
# ---------------------------------------------------------------------------

SECOND_MAP = """
  fan2:
    type: map
    over: "{state.items}"
    as: item
    node:
      type: python
      tool: sub
      state_key: out
    collect: results
"""


@pytest.mark.req("REQ-YG-692")
class TestTokensAndChannels:
    def test_shared_channel_accounts_per_map(self, tmp_path):
        edges = """  - from: START
    to: fan
  - from: fan
    to: fan2
  - from: fan2
    to: consume
  - from: consume
    to: END
"""
        out = _run(tmp_path, ["a", "b"], nodes=SECOND_MAP, edges=edges)
        verdicts = out["_map_verdict"]
        assert verdicts["fan"].dispatched == 2
        assert verdicts["fan2"].dispatched == 2
        assert verdicts["fan"].dispatch != verdicts["fan2"].dispatch
        maps = sorted(row.map for row in out["_map_accounting"])
        assert maps == ["fan", "fan", "fan2", "fan2"]

    def test_parallel_maps_keep_both_verdicts(self, tmp_path):
        edges = """  - from: START
    to: [fan, fan2]
  - from: fan
    to: consume
  - from: fan2
    to: consume
  - from: consume
    to: END
"""
        out = _run(tmp_path, ["a", "b"], nodes=SECOND_MAP, edges=edges)
        assert set(out["_map_verdict"]) == {"fan", "fan2"}

    def test_sequential_loop_uses_distinct_tokens(self, tmp_path):
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
        out = _run(tmp_path, ["a", "b"], edges=edges)
        tokens = [row.dispatch for row in out["_map_accounting"]]
        assert len(set(tokens)) == 2
        assert out["_map_verdict"]["fan"].dispatch == tokens[-1]
        assert out["_map_open"].get("fan") is None

    def test_overlapping_invocations_fail_closed(self, tmp_path):
        nodes = """
  a:
    type: python
    tool: passthrough
  b:
    type: python
    tool: passthrough
  c:
    type: python
    tool: passthrough
"""
        edges = """  - from: START
    to: [a, b]
  - from: a
    to: fan
  - from: b
    to: c
  - from: c
    to: fan
  - from: fan
    to: consume
  - from: consume
    to: END
"""
        with pytest.raises(Exception) as exc_info:
            _run(tmp_path, ["a", "b"], nodes=nodes, edges=edges)
        assert type(exc_info.value).__name__ == "MapAccountingError"
        assert len(re.findall(r"[0-9a-f]{32}", str(exc_info.value))) == 2

    def test_state_declares_map_channels(self):
        config = {
            "state": {"items": "list"},
            "nodes": {
                "fan": {
                    "type": "map",
                    "over": "{state.items}",
                    "as": "item",
                    "node": {"type": "python", "tool": "sub"},
                    "collect": "results",
                }
            },
            "edges": [],
        }
        fields = build_state_class(config).__annotations__
        for key in (
            "results",
            "results_failures",
            "_map_accounting",
            "_map_open",
            "_map_verdict",
        ):
            assert key in fields, key


# ---------------------------------------------------------------------------
# AC-14: topology
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-692")
class TestTopology:
    def test_four_nodes_and_join_owns_outgoing(self, tmp_path):
        drawable = _compile(tmp_path).compile().get_graph()
        nodes = {"fan", "_map_fan_sub", "_map_fan_account", "_map_fan_join"}
        assert nodes <= set(drawable.nodes)
        sub_targets = {e.target for e in drawable.edges if e.source == "_map_fan_sub"}
        assert sub_targets == {"_map_fan_account"}
        account_targets = {
            e.target for e in drawable.edges if e.source == "_map_fan_account"
        }
        assert account_targets == {"_map_fan_join"}
        into_consume = {e.source for e in drawable.edges if e.target == "consume"}
        assert into_consume == {"_map_fan_join"}

    def test_join_name_collision_fails_naming_node(self, tmp_path):
        nodes = """
  _map_fan_join:
    type: python
    tool: passthrough
"""
        with pytest.raises(ValueError, match="_map_fan_join"):
            _compile(tmp_path, nodes=nodes)
