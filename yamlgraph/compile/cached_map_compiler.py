"""FR-1161: `type: cached_map` warm-first wiring.

A cached_map is a map whose item 0 runs alone before items 1..N-1 fan
out, so a shared prompt prefix is written to the provider cache once and
read by the release wave. Topology:

    <name> (dispatch + snapshot) -> _map_<name>_warm (index 0)
      -> _map_<name>_sub (indices 1..N-1) -> _map_<name>_account
      -> _map_<name>_join

The dispatch node freezes the population and the dispatch-time inputs in
`_cached_map_snapshot`; both routers build their Sends from that snapshot
only, so items and inputs never drift with what item 0 wrote.
"""

import uuid
from collections.abc import Callable
from typing import Any

from langgraph.graph import StateGraph
from langgraph.types import Send

from yamlgraph.compile.map_contract import (
    failures_key_of,
    make_account_node,
    make_join_node,
)
from yamlgraph.models.map_results import CachedMapSnapshot, MapAccountingError
from yamlgraph.utils.route_log import emit_route

SNAPSHOT_KEY = "_cached_map_snapshot"
_PRIVATE = ("_map_open", "_map_accounting", "_map_verdict", SNAPSHOT_KEY)


def _make_snapshot_dispatch(
    name: str, resolve_items: Callable[[dict, bool], list]
) -> Callable[[dict], dict]:
    def dispatch(state: dict) -> dict:
        items = resolve_items(state, True)
        token = uuid.uuid4().hex
        update: dict[str, Any] = {
            "_map_open": {name: {"dispatch": token, "dispatched": len(items)}},
            "current_step": name,
        }
        snapshot = CachedMapSnapshot(
            dispatch=token,
            items=items,
            inputs={k: v for k, v in state.items() if k not in _PRIVATE},
        )
        # Shallow: keep Pydantic items and inputs as their own types.
        update[SNAPSHOT_KEY] = {name: dict(snapshot)}
        return update

    dispatch.__name__ = f"{name}_cached_map_dispatch"
    return dispatch


def _snapshot(name: str, state: dict) -> dict:
    record = (state.get("_map_open") or {}).get(name)
    snap = (state.get(SNAPSHOT_KEY) or {}).get(name)
    if record is None or snap is None or snap["dispatch"] != record["dispatch"]:
        raise MapAccountingError(
            f"Cached map node '{name}' routed without a matching open snapshot"
        )
    return snap


def _sends(snap: dict, target: str, item_var: str, indices: range) -> list[Send]:
    return [
        Send(
            target,
            {
                **snap["inputs"],
                item_var: snap["items"][i],
                "_map_index": i,
                "_map_dispatch": snap["dispatch"],
            },
        )
        for i in indices
    ]


def wire_cached_map(
    name: str,
    config: dict[str, Any],
    builder: StateGraph,
    wrapped_node: Callable[[dict], dict],
    resolve_items: Callable[[dict, bool], list],
    item_var: str,
) -> tuple[Callable[[dict], Any], str]:
    """Add the cached_map nodes; return (warm_router, join_name)."""
    warm_name = f"_map_{name}_warm"
    sub_name = f"_map_{name}_sub"
    account_name = f"_map_{name}_account"
    join_name = f"_map_{name}_join"
    account = make_account_node(name, config.get("min_success"))

    def account_and_close(state: dict) -> dict:
        return {**account(state), SNAPSHOT_KEY: {name: None}}

    account_and_close.__name__ = account.__name__

    def warm_route(state: dict) -> list[Send] | str:
        snap = _snapshot(name, state)
        if not snap["items"]:
            emit_route(name, "cached_map", account_name, fan_out=0)
            return account_name
        emit_route(name, "cached_map", warm_name, fan_out=1)
        return _sends(snap, warm_name, item_var, range(1))

    def release_route(state: dict) -> list[Send] | str:
        snap = _snapshot(name, state)
        count = len(snap["items"])
        if count <= 1:
            emit_route(warm_name, "cached_map", account_name, fan_out=0)
            return account_name
        emit_route(warm_name, "cached_map", sub_name, fan_out=count - 1)
        return _sends(snap, sub_name, item_var, range(1, count))

    builder.add_node(name, _make_snapshot_dispatch(name, resolve_items))
    builder.add_node(warm_name, wrapped_node)
    builder.add_node(sub_name, wrapped_node)
    builder.add_node(account_name, account_and_close)
    builder.add_node(
        join_name, make_join_node(name, config["collect"], failures_key_of(config))
    )
    builder.add_conditional_edges(name, warm_route, [warm_name, account_name])
    builder.add_conditional_edges(warm_name, release_route, [sub_name, account_name])
    builder.add_edge(sub_name, account_name)
    builder.add_edge(account_name, join_name)
    return warm_route, join_name
