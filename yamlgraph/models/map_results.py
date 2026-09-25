"""FR-1073: typed map result records, errors and reducers.

A map branch produces exactly one `MapAccounting` row. A failed branch
also produces one `MapFailure`. The join turns the rows of one dispatch
into a `MapVerdict`.
"""

from typing import Any, Literal

from pydantic import BaseModel


class MapFailure(BaseModel):
    """One failed map branch, kept out of `collect`."""

    map: str
    dispatch: str
    index: int
    error_type: str
    message: str
    node: str
    tolerated: bool


class MapAccounting(BaseModel):
    """One row per finished branch; the join counts these."""

    map: str
    dispatch: str
    index: int
    outcome: Literal["succeeded", "tolerated", "failed"]


class MapVerdict(BaseModel):
    """Completeness verdict for one dispatch of one map."""

    dispatch: str
    dispatched: int
    succeeded: int
    tolerated: int
    failed: int
    accepted: int
    min_success: int | float
    met: bool


class MapCompletenessError(RuntimeError):
    """The join found fewer accepted branches than `min_success` allows."""

    def __init__(self, map_name: str, verdict: MapVerdict):
        self.map_name = map_name
        self.verdict = verdict
        super().__init__(
            f"Map node '{map_name}' incomplete: accepted {verdict.accepted}"
            f"/{verdict.dispatched} (succeeded={verdict.succeeded}, "
            f"tolerated={verdict.tolerated}, failed={verdict.failed}), "
            f"min_success={verdict.min_success}"
        )


class MapAccountingError(RuntimeError):
    """Dispatch/branch accounting is inconsistent (overlap, lost rows)."""


def add_by_index(existing: list | None, new: list | None) -> list:
    """Append records, then order stably by branch index."""
    combined = list(existing or []) + list(new or [])
    return sorted(combined, key=lambda r: getattr(r, "index", 0))


def merge_map_open(existing: dict | None, new: dict | None) -> dict:
    """Per-map merge of open dispatch records; same-map overlap raises."""
    merged = dict(existing or {})
    for name, record in (new or {}).items():
        current = merged.get(name)
        if record is not None and current is not None:
            raise MapAccountingError(
                f"Map node '{name}' dispatched {record['dispatch']} while "
                f"dispatch {current['dispatch']} is still open"
            )
        merged[name] = record
    return merged


def merge_by_key(existing: dict | None, new: dict | None) -> dict:
    """Per-key dict merge so concurrent maps keep their own entries."""
    return {**(existing or {}), **(new or {})}


def compute_verdict(
    dispatch: str,
    dispatched: int,
    rows: list[MapAccounting],
    min_success: Any,
) -> MapVerdict:
    """Apply the FR-1073 item 7 arithmetic to one dispatch's rows."""
    succeeded = sum(r.outcome == "succeeded" for r in rows)
    tolerated = sum(r.outcome == "tolerated" for r in rows)
    failed = sum(r.outcome == "failed" for r in rows)
    accepted = succeeded + tolerated
    threshold = 1.0 if min_success is None else min_success
    if dispatched == 0:
        met = True
    elif isinstance(threshold, int):
        met = accepted >= threshold
    else:
        met = accepted / dispatched >= threshold
    return MapVerdict(
        dispatch=dispatch,
        dispatched=dispatched,
        succeeded=succeeded,
        tolerated=tolerated,
        failed=failed,
        accepted=accepted,
        min_success=threshold,
        met=met,
    )
