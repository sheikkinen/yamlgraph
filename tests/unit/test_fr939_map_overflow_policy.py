"""FR-939: typed map overflow policy (``on_overflow: error | truncate``).

Two independent resolution paths:
- cap: node ``max_items`` > graph ``config.max_map_items`` > 100;
- policy: node ``on_overflow`` > graph ``defaults.on_overflow`` > ``"error"``.

Every witness loads and compiles real YAML written under ``tmp_path``; the
map sub-node is a counting Python tool so "no sub-node ran" is observable.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any

import pytest
import yaml
from langgraph.types import Send

MAP_LOGGER = "yamlgraph.compile.map_compiler"
# The overflow error, not a load-time schema error, must satisfy pytest.raises.
OVERFLOW = r"'fan'.*exceed"

_LOCK = threading.Lock()
_CALLS = 0


def recording_worker(state: dict) -> Any:
    """Map sub-node: count invocations, echo the item."""
    global _CALLS
    with _LOCK:
        _CALLS += 1
    return state["item"]


def _write(
    tmp_path: Path,
    *,
    node_extra: dict | None = None,
    defaults: dict | None = None,
    graph_config: dict | None = None,
) -> Path:
    fan: dict = {
        "type": "map",
        "over": "{state.items}",
        "as": "item",
        "node": {"type": "python", "tool": "echo", "state_key": "result"},
        "collect": "results",
        **(node_extra or {}),
    }
    cfg: dict = {
        "name": "fr939-overflow",
        "version": "1.0",
        "state": {"items": {"type": "list"}, "results": {"type": "list"}},
        "tools": {
            "echo": {
                "type": "python",
                "module": __name__,
                "function": "recording_worker",
            }
        },
        "nodes": {"fan": fan},
        "edges": [{"from": "START", "to": "fan"}, {"from": "fan", "to": "END"}],
    }
    if defaults is not None:
        cfg["defaults"] = defaults
    if graph_config is not None:
        cfg["config"] = graph_config
    path = tmp_path / "graph.yaml"
    path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return path


def _builder(path: Path):
    from yamlgraph.compile.graph_loader import compile_graph, load_graph_config

    return compile_graph(load_graph_config(path))


def _sends(path: Path, items: list) -> list[Send]:
    """Dispatch node, then the map router: the fan-out LangGraph would run."""
    builder = _builder(path)
    state = {"items": items, "results": []}
    update = builder.nodes["fan"].runnable.invoke(state)
    (branch,) = builder.branches["fan"].values()
    return branch.path.invoke({**state, **update})


def _run(path: Path, items: list) -> dict:
    global _CALLS
    _CALLS = 0
    return _builder(path).compile().invoke({"items": items, "results": []})


def _overflow_warnings(caplog) -> list[logging.LogRecord]:
    return [
        r
        for r in caplog.records
        if r.name == MAP_LOGGER and r.levelno == logging.WARNING
    ]


ITEMS = [9, 3, 7, 1, 8, 2, 6, 0, 5, 4]  # order-revealing, not sorted


# ---------------------------------------------------------------------------
# AC-02 — typed policy values at both levels, rejected at load
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-699")
@pytest.mark.parametrize("policy", ["error", "truncate"])
def test_ac02_node_policy_values_load(policy, tmp_path):
    from yamlgraph.compile.graph_loader import load_graph_config

    load_graph_config(_write(tmp_path, node_extra={"on_overflow": policy}))


@pytest.mark.req("REQ-YG-699")
@pytest.mark.parametrize("policy", ["error", "truncate"])
def test_ac02_default_policy_values_load(policy, tmp_path):
    from yamlgraph.compile.graph_loader import load_graph_config

    load_graph_config(_write(tmp_path, defaults={"on_overflow": policy}))


@pytest.mark.req("REQ-YG-699")
@pytest.mark.parametrize("bad", ["warn", "ERROR", "", 1, True, ["error"]])
def test_ac02_node_policy_invalid_rejected_at_load(bad, tmp_path):
    from yamlgraph.compile.graph_loader import load_graph_config

    with pytest.raises(ValueError, match="on_overflow"):
        load_graph_config(_write(tmp_path, node_extra={"on_overflow": bad}))


@pytest.mark.req("REQ-YG-699")
@pytest.mark.parametrize("bad", ["warn", "ERROR", "", 1, True, ["error"]])
def test_ac02_default_policy_invalid_rejected_at_load(bad, tmp_path):
    from yamlgraph.compile.graph_loader import load_graph_config

    with pytest.raises(ValueError, match="on_overflow"):
        load_graph_config(_write(tmp_path, defaults={"on_overflow": bad}))


# ---------------------------------------------------------------------------
# AC-03 — policy precedence: node > defaults > "error"
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-699")
def test_ac03_implicit_default_is_error(tmp_path):
    path = _write(tmp_path, node_extra={"max_items": 3})
    with pytest.raises(ValueError, match=OVERFLOW):
        _sends(path, ITEMS)


@pytest.mark.req("REQ-YG-699")
def test_ac03_graph_default_truncate_applies(tmp_path):
    path = _write(
        tmp_path, node_extra={"max_items": 3}, defaults={"on_overflow": "truncate"}
    )
    assert [s.arg["item"] for s in _sends(path, ITEMS)] == ITEMS[:3]


@pytest.mark.req("REQ-YG-699")
def test_ac03_node_truncate_overrides_default_error(tmp_path):
    path = _write(
        tmp_path,
        node_extra={"max_items": 3, "on_overflow": "truncate"},
        defaults={"on_overflow": "error"},
    )
    assert [s.arg["item"] for s in _sends(path, ITEMS)] == ITEMS[:3]


@pytest.mark.req("REQ-YG-699")
def test_ac03_node_error_overrides_default_truncate(tmp_path):
    path = _write(
        tmp_path,
        node_extra={"max_items": 3, "on_overflow": "error"},
        defaults={"on_overflow": "truncate"},
    )
    with pytest.raises(ValueError, match=OVERFLOW):
        _sends(path, ITEMS)


# ---------------------------------------------------------------------------
# AC-04 — cap precedence through real load/compile (R-3 propagation repair)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-699")
def test_ac04_config_max_map_items_controls_fan_out(tmp_path):
    path = _write(
        tmp_path,
        node_extra={"on_overflow": "truncate"},
        graph_config={"max_map_items": 4},
    )
    assert [s.arg["item"] for s in _sends(path, ITEMS)] == ITEMS[:4]


@pytest.mark.req("REQ-YG-699")
def test_ac04_config_max_map_items_triggers_error_policy(tmp_path):
    path = _write(tmp_path, graph_config={"max_map_items": 4})
    with pytest.raises(ValueError, match=OVERFLOW):
        _sends(path, ITEMS)


@pytest.mark.req("REQ-YG-699")
def test_ac04_node_max_items_overrides_graph_cap(tmp_path):
    path = _write(
        tmp_path,
        node_extra={"max_items": 2, "on_overflow": "truncate"},
        graph_config={"max_map_items": 4},
    )
    assert [s.arg["item"] for s in _sends(path, ITEMS)] == ITEMS[:2]


@pytest.mark.req("REQ-YG-699")
def test_ac04_builtin_cap_is_100(tmp_path):
    path = _write(tmp_path, node_extra={"on_overflow": "truncate"})
    items = list(range(150))
    assert [s.arg["item"] for s in _sends(path, items)] == items[:100]


# ---------------------------------------------------------------------------
# AC-05 / AC-06 — pre-dispatch ValueError naming node, count and cap
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-699")
def test_ac05_overflow_raises_before_any_sub_node_runs(tmp_path):
    path = _write(tmp_path, node_extra={"max_items": 3})
    with pytest.raises(ValueError, match=OVERFLOW):
        _run(path, ITEMS)
    assert _CALLS == 0


@pytest.mark.req("REQ-YG-699")
def test_ac05_dispatch_raises_before_router_builds_sends(tmp_path):
    builder = _builder(_write(tmp_path, node_extra={"max_items": 3}))
    with pytest.raises(ValueError, match=OVERFLOW):
        builder.nodes["fan"].runnable.invoke({"items": ITEMS, "results": []})


@pytest.mark.req("REQ-YG-699")
def test_ac06_error_message_names_node_count_and_cap(tmp_path):
    path = _write(tmp_path, node_extra={"max_items": 3})
    with pytest.raises(ValueError, match=OVERFLOW) as exc:
        _sends(path, ITEMS)
    message = str(exc.value)
    assert "'fan'" in message
    assert str(len(ITEMS)) in message
    assert "3" in message
    assert "on_overflow" in message


# ---------------------------------------------------------------------------
# AC-07 — explicit truncate: exact prefix, one WARNING with the numbers
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-699")
def test_ac07_truncate_keeps_prefix_and_warns_once(tmp_path, caplog):
    path = _write(tmp_path, node_extra={"max_items": 3, "on_overflow": "truncate"})
    with caplog.at_level(logging.WARNING, logger=MAP_LOGGER):
        sends = _sends(path, ITEMS)
    assert [s.arg["item"] for s in sends] == ITEMS[:3]
    (record,) = _overflow_warnings(caplog)
    message = record.getMessage()
    assert "'fan'" in message and str(len(ITEMS)) in message and "3" in message


@pytest.mark.req("REQ-YG-699")
def test_ac07_truncate_end_to_end_runs_only_the_prefix(tmp_path):
    path = _write(tmp_path, node_extra={"max_items": 3, "on_overflow": "truncate"})
    result = _run(path, ITEMS)
    assert _CALLS == 3
    ordered = sorted(result["results"], key=lambda r: r["_map_index"])
    assert [r["value"] for r in ordered] == ITEMS[:3]


# ---------------------------------------------------------------------------
# AC-08 — at and below the cap: one Send per item, in order, no warning
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-699")
@pytest.mark.parametrize("policy", [None, "error", "truncate"])
@pytest.mark.parametrize("count", [0, 1, 10])
def test_ac08_within_cap_is_untouched(policy, count, tmp_path, caplog):
    extra: dict = {"max_items": 10}
    if policy is not None:
        extra["on_overflow"] = policy
    path = _write(tmp_path, node_extra=extra)
    items = ITEMS[:count]
    with caplog.at_level(logging.WARNING, logger=MAP_LOGGER):
        if count == 0:
            result = _run(path, items)
            assert result["results"] == []
        else:
            assert [s.arg["item"] for s in _sends(path, items)] == items
    assert _overflow_warnings(caplog) == []
