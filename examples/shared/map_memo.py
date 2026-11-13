"""FR-1116: map memo for file corpora (CAP-289, REQ-YG-706).

`map_memo_split` drops file items whose bytes and computation signature
match a stored outcome. The caller maps over `todo`, then
`map_memo_merge` stores the executed outcomes in one SQLite transaction
and returns the whole current population in FR-1073 shapes. The
`min_success` threshold is judged after commit, over that population.

No `from __future__ import annotations`: graphs load this file through an
FR-768 `path`, which leaves it out of `sys.modules`, so Pydantic could not
resolve string annotations.
"""

import hashlib
import json
import math
import sqlite3
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, ValidationError

from yamlgraph.models.map_results import (
    MapAccounting,
    MapCompletenessError,
    MapFailure,
    compute_verdict,
)

CONTRACT = "map_memo/1"
SCHEMA_VERSION = "1"
BUSY_TIMEOUT_S = 30.0

_SCHEMA = (
    "CREATE TABLE IF NOT EXISTS meta (name TEXT PRIMARY KEY, value TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS memo ("
    "key TEXT PRIMARY KEY, version TEXT NOT NULL, signature TEXT NOT NULL, "
    "status TEXT NOT NULL CHECK (status IN ('ok','failed')), "
    "payload TEXT NOT NULL)",
)
_UPSERT = (
    "INSERT INTO memo (key, version, signature, status, payload) "
    "VALUES (?, ?, ?, ?, ?) ON CONFLICT(key) DO UPDATE SET "
    "version = excluded.version, signature = excluded.signature, "
    "status = excluded.status, payload = excluded.payload"
)


class MapMemoInputError(ValueError):
    """Caller-supplied items, inputs, results or thresholds are invalid."""


class MapMemoStoreError(RuntimeError):
    """The store cannot be read or written; never degrades to a miss."""


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StoredFailure(_Model):
    error_type: str
    message: str
    node: str
    tolerated: bool


class MemoItem(_Model):
    key: str
    version: str
    index: int
    hit: Literal["none", "ok", "failed"]


class MemoPlan(_Model):
    store: str
    signature: str
    current: list[MemoItem]
    todo: list[str]
    hits: dict[str, dict[str, Any]]


class MemoMerged(_Model):
    records: list[dict[str, Any]]
    failures: list[dict[str, Any]]
    verdict: dict[str, Any]
    counts: dict[str, int]


class _Row(_Model):
    key: str
    version: str
    signature: str
    status: Literal["ok", "failed"]
    payload: dict[str, Any]


def _dumps(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _file_sha(raw: Any, role: str) -> str:
    if not isinstance(raw, str) or not raw:
        raise MapMemoInputError(f"{role} must be a non-empty path string: {raw!r}")
    path = Path(raw)
    if not path.is_file():
        raise MapMemoInputError(f"{role} is not a readable file: {raw}")
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as e:
        raise MapMemoInputError(f"{role} is not readable: {raw}: {e}") from e


def _hash_files(paths: Any, role: str) -> dict[str, str]:
    if not isinstance(paths, list) or not paths:
        raise MapMemoInputError(f"{role} must be a non-empty list of paths")
    hashes: dict[str, str] = {}
    for raw in paths:
        sha = _file_sha(raw, role)
        if raw in hashes:
            raise MapMemoInputError(f"{role} contains a duplicate: {raw}")
        hashes[raw] = sha
    return hashes


def _signature(signature_files: Any, inputs: Any) -> str:
    files = _hash_files(signature_files, "signature file")
    if inputs is None:
        inputs = {}
    if not isinstance(inputs, dict):
        raise MapMemoInputError("inputs must be a JSON object or None")
    try:
        canonical = _dumps({"contract": CONTRACT, "files": files, "inputs": inputs})
    except (TypeError, ValueError) as e:
        raise MapMemoInputError(f"inputs are not JSON-serializable: {e}") from e
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _connect(store: Path, *, read_only: bool) -> sqlite3.Connection:
    target = f"{store.as_uri()}?mode=ro" if read_only else str(store)
    try:
        return sqlite3.connect(
            target,
            uri=read_only,
            timeout=BUSY_TIMEOUT_S,
            isolation_level=None,
        )
    except sqlite3.Error as e:
        raise MapMemoStoreError(f"cannot open memo store {store}: {e}") from e


def _check_schema(db: sqlite3.Connection, store: Path) -> None:
    row = db.execute("SELECT value FROM meta WHERE name = 'schema_version'").fetchone()
    if row is None or row[0] != SCHEMA_VERSION:
        found = None if row is None else row[0]
        raise MapMemoStoreError(
            f"memo store {store} has schema_version {found!r}, "
            f"expected {SCHEMA_VERSION!r}"
        )


def _parse_row(raw: tuple) -> _Row:
    key, version, signature, status, payload = raw
    try:
        row = _Row(
            key=key,
            version=version,
            signature=signature,
            status=status,
            payload=json.loads(payload),
        )
        if row.status == "failed":
            StoredFailure.model_validate(row.payload)
    except (ValidationError, ValueError, TypeError) as e:
        raise MapMemoStoreError(f"malformed memo row for {key!r}: {e}") from e
    return row


def _read_rows(store: Path, keys: list[str]) -> dict[str, _Row]:
    if not store.exists() or store.stat().st_size == 0:
        return {}
    db = _connect(store, read_only=True)
    try:
        db.execute("BEGIN")
        _check_schema(db, store)
        rows: dict[str, _Row] = {}
        for key in keys:
            raw = db.execute(
                "SELECT key, version, signature, status, payload "
                "FROM memo WHERE key = ?",
                (key,),
            ).fetchone()
            if raw is not None:
                rows[key] = _parse_row(raw)
        db.execute("COMMIT")
        return rows
    except sqlite3.Error as e:
        raise MapMemoStoreError(f"cannot read memo store {store}: {e}") from e
    finally:
        db.close()


def _supplied_versions(items: Any, versions: Any) -> dict[str, str]:
    """FR-1120: item versions from the caller; no item path is read."""
    if not isinstance(items, list) or not items:
        raise MapMemoInputError("items must be a non-empty list of keys")
    if len(set(map(repr, items))) != len(items):
        raise MapMemoInputError("items contain a duplicate")
    for key in items:
        if not isinstance(key, str) or not key:
            raise MapMemoInputError(f"item must be a non-empty string: {key!r}")
    if not isinstance(versions, dict):
        raise MapMemoInputError("versions must be an object keyed by item")
    if set(versions) != set(items):
        missing = sorted(set(items) - set(versions))
        extra = sorted(map(str, set(versions) - set(items)))
        raise MapMemoInputError(
            f"versions keys must equal items: missing {missing}, extra {extra}"
        )
    for key in items:
        value = versions[key]
        if not isinstance(value, str) or not value:
            raise MapMemoInputError(
                f"version for {key!r} must be a non-empty string: {value!r}"
            )
    return {key: versions[key] for key in items}


def map_memo_split(
    items: list[str],
    signature_files: list[str],
    store: str,
    inputs: dict[str, Any] | None = None,
    versions: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Return the memo plan: current items, the keys to run, and the hits.

    Without `versions`, each item is a file path versioned by its SHA-256.
    With `versions` (FR-1120), each item is an opaque key versioned by the
    caller-supplied string; no item path is read.
    """
    if not isinstance(store, str) or not store:
        raise MapMemoInputError(f"store must be a non-empty path string: {store!r}")
    if versions is None:
        item_versions = _hash_files(items, "item")
    else:
        item_versions = _supplied_versions(items, versions)
    signature = _signature(signature_files, inputs)
    store_path = Path(store).resolve()
    rows = _read_rows(store_path, list(item_versions))

    current: list[MemoItem] = []
    todo: list[str] = []
    hits: dict[str, dict[str, Any]] = {}
    for index, (key, version) in enumerate(item_versions.items()):
        row = rows.get(key)
        if row is not None and (row.version, row.signature) == (version, signature):
            hits[key] = row.payload
            hit = row.status
        else:
            todo.append(key)
            hit = "none"
        current.append(MemoItem(key=key, version=version, index=index, hit=hit))

    return MemoPlan(
        store=str(store_path),
        signature=signature,
        current=current,
        todo=todo,
        hits=hits,
    ).model_dump()


def _check_min_success(value: Any) -> int | float:
    if type(value) is int and value >= 0:
        return value
    if type(value) is float and math.isfinite(value) and 0.0 <= value <= 1.0:
        return value
    raise MapMemoInputError(
        f"min_success must be a non-negative int or a float in [0, 1]: {value!r}"
    )


def _index(value: Any, size: int, seen: set[int]) -> int:
    if type(value) is not int or not 0 <= value < size:
        raise MapMemoInputError(f"index {value!r} does not point into todo")
    if value in seen:
        raise MapMemoInputError(f"index {value} is reported more than once")
    seen.add(value)
    return value


def _executed(
    plan: MemoPlan,
    results: Any,
    failures: Any,
    map_name: str,
    map_dispatch: str,
) -> dict[str, tuple[str, dict[str, Any]]]:
    """Attribute each executed outcome to its todo key, or raise."""
    size, seen = len(plan.todo), set()
    outcomes: dict[str, tuple[str, dict[str, Any]]] = {}
    for record in results or []:
        if not isinstance(record, dict) or "_map_index" not in record:
            raise MapMemoInputError(f"result lacks _map_index: {record!r}")
        index = _index(record["_map_index"], size, seen)
        payload = {k: v for k, v in record.items() if k != "_map_index"}
        try:
            _dumps(payload)
        except (TypeError, ValueError) as e:
            raise MapMemoInputError(f"result {index} is not JSON: {e}") from e
        outcomes[plan.todo[index]] = ("ok", payload)
    for raw in failures or []:
        try:
            failure = MapFailure.model_validate(raw)
        except ValidationError as e:
            raise MapMemoInputError(f"invalid map failure: {e}") from e
        if (failure.map, failure.dispatch) != (map_name, map_dispatch):
            raise MapMemoInputError(
                f"failure {failure.index} belongs to "
                f"{failure.map}/{failure.dispatch}, not {map_name}/{map_dispatch}"
            )
        index = _index(failure.index, size, seen)
        stored = StoredFailure(
            error_type=failure.error_type,
            message=failure.message,
            node=failure.node,
            tolerated=failure.tolerated,
        )
        outcomes[plan.todo[index]] = ("failed", stored.model_dump())
    if len(seen) != size:
        missing = sorted(set(range(size)) - seen)
        raise MapMemoInputError(f"todo indices without an outcome: {missing}")
    return outcomes


def _write(plan: MemoPlan, outcomes: dict[str, tuple[str, dict[str, Any]]]) -> None:
    store = Path(plan.store)
    versions = {item.key: item.version for item in plan.current}
    try:
        store.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise MapMemoStoreError(f"cannot create {store.parent}: {e}") from e
    db = _connect(store, read_only=False)
    try:
        db.execute("BEGIN IMMEDIATE")
        for statement in _SCHEMA:
            db.execute(statement)
        db.execute(
            "INSERT OR IGNORE INTO meta (name, value) VALUES ('schema_version', ?)",
            (SCHEMA_VERSION,),
        )
        _check_schema(db, store)
        for key, (status, payload) in outcomes.items():
            db.execute(
                _UPSERT,
                (key, versions[key], plan.signature, status, _dumps(payload)),
            )
        db.execute("COMMIT")
    except (sqlite3.Error, MapMemoStoreError) as e:
        if db.in_transaction:
            db.execute("ROLLBACK")
        if isinstance(e, MapMemoStoreError):
            raise
        raise MapMemoStoreError(f"cannot write memo store {store}: {e}") from e
    finally:
        db.close()


def map_memo_merge(
    plan: dict[str, Any],
    results: list[dict[str, Any]] | None,
    failures: list[Any] | None,
    map_name: str,
    map_dispatch: str,
    min_success: int | float = 1.0,
) -> dict[str, Any]:
    """Store executed outcomes, then return the whole current population."""
    threshold = _check_min_success(min_success)
    if not isinstance(map_name, str) or not map_name:
        raise MapMemoInputError("map_name must be a non-empty string")
    if not isinstance(map_dispatch, str) or not map_dispatch:
        raise MapMemoInputError("map_dispatch must be a non-empty string")
    try:
        memo_plan = MemoPlan.model_validate(plan)
    except ValidationError as e:
        raise MapMemoInputError(f"invalid memo plan: {e}") from e
    outcomes = _executed(memo_plan, results, failures, map_name, map_dispatch)
    if outcomes:
        _write(memo_plan, outcomes)

    records: list[dict[str, Any]] = []
    merged_failures: list[MapFailure] = []
    rows: list[MapAccounting] = []
    counts = dict.fromkeys(
        ("executed_ok", "executed_failed", "reused_ok", "reused_failed"), 0
    )
    for item in memo_plan.current:
        source = "executed" if item.key in outcomes else "reused"
        status, payload = outcomes.get(item.key) or (item.hit, memo_plan.hits[item.key])
        counts[f"{source}_{status}"] += 1
        if status == "ok":
            records.append({**payload, "_map_index": item.index})
            outcome = "succeeded"
        else:
            stored = StoredFailure.model_validate(payload)
            merged_failures.append(
                MapFailure(
                    map=map_name,
                    dispatch=map_dispatch,
                    index=item.index,
                    **stored.model_dump(),
                )
            )
            outcome = "tolerated" if stored.tolerated else "failed"
        rows.append(
            MapAccounting(
                map=map_name, dispatch=map_dispatch, index=item.index, outcome=outcome
            )
        )

    verdict = compute_verdict(map_dispatch, len(memo_plan.current), rows, threshold)
    if not verdict.met:
        raise MapCompletenessError(map_name, verdict)
    return MemoMerged(
        records=records,
        failures=[f.model_dump() for f in merged_failures],
        verdict=verdict.model_dump(),
        counts=counts,
    ).model_dump()
