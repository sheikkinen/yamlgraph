"""FR-1073: map dispatch, branch classification and completeness join.

A map compiles to three nodes: `<name>` (dispatch) opens a dispatch token
and fixes the item count; `_map_<name>_sub` runs once per item; and
`_map_<name>_join` accounts every dispatched index against the exact
token and enforces `min_success`.
"""

import logging
import uuid
from collections.abc import Callable
from typing import Any

from langgraph.types import Send

from yamlgraph.models.map_results import (
    MapAccounting,
    MapAccountingError,
    MapCompletenessError,
    MapFailure,
    compute_verdict,
)
from yamlgraph.models.schemas import ErrorType, PipelineError
from yamlgraph.utils.route_log import emit_route

logger = logging.getLogger(__name__)


def branch_failure(
    map_name: str,
    state: dict,
    failures_key: str,
    error_type: str,
    message: str,
    tolerated: bool,
    pipeline_error: PipelineError | None,
) -> dict:
    """Update for a failed branch: one MapFailure, one accounting row,
    and exactly one PipelineError unless the failure is tolerated."""
    index = state.get("_map_index", 0)
    dispatch = state.get("_map_dispatch")
    sub_node_name = f"_map_{map_name}_sub"
    update: dict[str, Any] = {
        failures_key: [
            MapFailure(
                map=map_name,
                dispatch=dispatch,
                index=index,
                error_type=error_type,
                message=message,
                node=sub_node_name,
                tolerated=tolerated,
            )
        ],
        "_map_accounting": [
            MapAccounting(
                map=map_name,
                dispatch=dispatch,
                index=index,
                outcome="tolerated" if tolerated else "failed",
            )
        ],
    }
    if not tolerated:
        update["errors"] = [pipeline_error]
    return update


def classify_result(
    map_name: str, state: dict, failures_key: str, result: Any
) -> dict | None:
    """Return a failure update for a skipped or error-bearing result, else None."""
    if not isinstance(result, dict):
        return None
    if result.get("_skipped"):
        message = str(result.get("_skip_reason") or result.get("errors") or "skipped")
        return branch_failure(
            map_name, state, failures_key, "Skipped", message, True, None
        )
    reported = result.get("errors") or result.get("error")
    if not reported:
        return None
    first = reported[0] if isinstance(reported, list) else reported
    etype = first.type if isinstance(first, PipelineError) else ErrorType.UNKNOWN_ERROR
    message = str(reported)
    return branch_failure(
        map_name,
        state,
        failures_key,
        str(etype),
        message,
        False,
        PipelineError(type=etype, message=message, node=f"_map_{map_name}_sub"),
    )


def success_accounting(map_name: str, state: dict) -> list[MapAccounting]:
    return [
        MapAccounting(
            map=map_name,
            dispatch=state.get("_map_dispatch"),
            index=state.get("_map_index", 0),
            outcome="succeeded",
        )
    ]


def make_dispatch_node(
    name: str, resolve_items: Callable[[dict, bool], list]
) -> Callable[[dict], dict]:
    """Dispatch node: open a fresh token and fix the dispatched count."""

    def dispatch(state: dict) -> dict:
        items = resolve_items(state, True)
        return {
            "_map_open": {
                name: {"dispatch": uuid.uuid4().hex, "dispatched": len(items)}
            },
            "current_step": name,
        }

    dispatch.__name__ = f"{name}_map_dispatch"
    return dispatch


def make_dispatch_router(
    name: str,
    sub_node_name: str,
    join_name: str,
    item_var: str,
    resolve_items: Callable[[dict, bool], list],
) -> Callable[[dict], list[Send] | str]:
    """Router after dispatch: one Send per item, or the join for zero items."""

    def route(state: dict) -> list[Send] | str:
        record = (state.get("_map_open") or {}).get(name)
        if record is None:
            raise MapAccountingError(
                f"Map node '{name}' routed without an open dispatch"
            )
        items = resolve_items(state, False)
        if len(items) != record["dispatched"]:
            raise MapAccountingError(
                f"Map node '{name}' dispatch {record['dispatch']} opened "
                f"{record['dispatched']} items but routing resolved {len(items)}"
            )
        if not items:
            emit_route(name, "map", join_name, fan_out=0)
            return join_name
        emit_route(name, "map", sub_node_name, fan_out=len(items))
        return [
            Send(
                sub_node_name,
                {
                    **state,
                    item_var: item,
                    "_map_index": i,
                    "_map_dispatch": record["dispatch"],
                },
            )
            for i, item in enumerate(items)
        ]

    return route


def make_join_node(name: str, min_success: Any) -> Callable[[dict], dict]:
    """Join: account the exact token's rows, write the verdict, enforce policy."""

    def join(state: dict) -> dict:
        record = (state.get("_map_open") or {}).get(name)
        if record is None:
            raise MapAccountingError(
                f"Map node '{name}' joined without an open dispatch"
            )
        token, dispatched = record["dispatch"], record["dispatched"]
        rows = [
            r
            for r in state.get("_map_accounting") or []
            if r.map == name and r.dispatch == token
        ]
        indices = sorted(r.index for r in rows)
        if indices != list(range(dispatched)):
            raise MapAccountingError(
                f"Map node '{name}' dispatch {token}: expected indices "
                f"0..{dispatched - 1}, got {indices}"
            )
        verdict = compute_verdict(token, dispatched, rows, min_success)
        if not verdict.met:
            raise MapCompletenessError(name, verdict)
        return {
            "_map_verdict": {name: verdict},
            "_map_open": {name: None},
            "current_step": f"_map_{name}_join",
        }

    join.__name__ = f"{name}_map_join"
    return join
