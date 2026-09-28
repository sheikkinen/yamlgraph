"""FR-1130 gh-issues census adapters: one validated listing per run.

`gh_issues_discover` runs ONE paginated `gh api` listing of a repository's
issues and PRs, validates every line as an `IssueRecord`, and atomically
replaces the snapshot under `tmp/gh-issues-cache/` only when the whole
listing validates. `gh_issues_versions` and `gh_issues_extract` read that
snapshot; extraction never calls the API. Any bad record raises — nothing
is logged-and-skipped (the `daily_digest` `fetch_hn` pattern is not reused).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SCHEMA_VERSION = 1
MAX_POPULATION = 10_000
MAX_BODY = 1500
MAX_LABELS = 50
TIMEOUT_S = 900
CACHE_DIR = Path("tmp/gh-issues-cache")

RECORD_JQ = (
    '{number, kind: (if .pull_request then "pr" else "issue" end), '
    "merged: (if .pull_request then (.pull_request.merged_at != null) else null end), "
    'state, state_reason, title, body_head: ((.body // "") | .[0:1500]), '
    "labels: [.labels[].name], comments, reactions: .reactions.total_count, "
    "created_at, updated_at, closed_at}"
)
LIST_JQ = ".[] | " + RECORD_JQ

_TIMESTAMP = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_SOURCE = re.compile(r"^(?P<repo>[^:@\s]+)(?::(?P<n>\d+)|@(?P<numbers>\d+(?:,\d+)*))?$")
_REF = re.compile(r"^(?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)#(?P<n>[1-9]\d*)$")


class IssueRecord(BaseModel):
    """One issue or PR, projected by `RECORD_JQ`."""

    model_config = ConfigDict(extra="forbid", strict=True)

    number: int = Field(ge=1)
    kind: Literal["issue", "pr"]
    merged: bool | None
    state: Literal["open", "closed"]
    state_reason: str | None
    title: str = Field(min_length=1)
    body_head: str = Field(max_length=MAX_BODY)
    labels: list[str] = Field(max_length=MAX_LABELS)
    comments: int = Field(ge=0)
    reactions: int = Field(ge=0)
    created_at: str = Field(pattern=_TIMESTAMP)
    updated_at: str = Field(pattern=_TIMESTAMP)
    closed_at: str | None = Field(pattern=_TIMESTAMP)

    @model_validator(mode="after")
    def _merged_matches_kind(self) -> IssueRecord:
        if self.kind == "issue" and self.merged is not None:
            raise ValueError(f"issue #{self.number} carries merged")
        if self.kind == "pr" and self.merged is None:
            raise ValueError(f"pr #{self.number} lacks merged")
        return self


class IssueSnapshot(BaseModel):
    """The whole validated listing of one repository at `retrieved_at`."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1]
    repository: str
    query: str
    retrieved_at: str = Field(pattern=_TIMESTAMP)
    count: int
    sha256: str
    items: list[IssueRecord]


# Tools are loaded by file path, outside sys.modules: resolve the deferred
# annotations now, while this module's namespace is reachable.
IssueRecord.model_rebuild(_types_namespace=globals())
IssueSnapshot.model_rebuild(_types_namespace=globals())


def parse_source(source: str) -> tuple[str, str, Any]:
    """Return (repo, mode, value): mode `all`, `sample` (n) or `named` (numbers)."""
    match = _SOURCE.match(source or "")
    if match is None or not _REPO.match(match["repo"]):
        raise ValueError(f"source {source!r} is not o/r, o/r:n or o/r@a,b")
    repo = match["repo"]
    if match["n"] is not None:
        n = int(match["n"])
        if n < 1:
            raise ValueError(f"source {source!r}: sample size must be >= 1")
        return repo, "sample", n
    if match["numbers"] is not None:
        numbers = [int(x) for x in match["numbers"].split(",")]
        if any(n < 1 for n in numbers) or len(set(numbers)) != len(numbers):
            raise ValueError(f"source {source!r}: numbers must be distinct and >= 1")
        return repo, "named", sorted(numbers)
    return repo, "all", None


def items_sha256(items: list[IssueRecord]) -> str:
    blob = json.dumps(
        [item.model_dump() for item in items], sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _query(repo: str) -> str:
    return f"repos/{repo}/issues?state=all&per_page=100"


def _snapshot_path(repo: str) -> Path:
    return CACHE_DIR / f"{repo.replace('/', '__')}.json"


def _parse_listing(stdout: str) -> list[IssueRecord]:
    lines = [line for line in stdout.splitlines() if line.strip()]
    if not lines:
        raise ValueError("gh listing is empty")
    records: list[IssueRecord] = []
    seen: set[int] = set()
    for lineno, line in enumerate(lines, 1):
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"gh listing line {lineno} is not JSON: {exc}") from exc
        record = IssueRecord.model_validate(raw)
        if record.number in seen:
            raise ValueError(f"gh listing repeats #{record.number}")
        seen.add(record.number)
        records.append(record)
    if len(records) > MAX_POPULATION:
        raise ValueError(
            f"population {len(records)} exceeds ceiling MAX_POPULATION={MAX_POPULATION}"
        )
    return sorted(records, key=lambda r: r.number)


def _list(repo: str) -> list[IssueRecord]:
    argv = ["gh", "api", "--paginate", "--jq", LIST_JQ, _query(repo)]
    done = subprocess.run(
        argv, capture_output=True, text=True, timeout=TIMEOUT_S, check=False
    )
    if done.returncode != 0:
        raise RuntimeError(
            f"gh api listing failed (exit {done.returncode}): {done.stderr.strip()}"
        )
    return _parse_listing(done.stdout)


def _write_snapshot(repo: str, records: list[IssueRecord]) -> None:
    snapshot = IssueSnapshot(
        schema_version=SCHEMA_VERSION,
        repository=repo,
        query=_query(repo),
        retrieved_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        count=len(records),
        sha256=items_sha256(records),
        items=records,
    )
    path = _snapshot_path(repo)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".snapshot-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(snapshot.model_dump_json(indent=1))
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


_CACHE: dict[str, tuple[tuple[int, int, int], IssueSnapshot]] = {}
_CACHE_LOCK = threading.Lock()


def load_snapshot(repo: str) -> IssueSnapshot:
    """Read and integrity-check the snapshot; memoized per file identity."""
    path = _snapshot_path(repo)
    stat = path.stat()
    identity = (stat.st_ino, stat.st_size, stat.st_mtime_ns)
    key = str(path.resolve())
    with _CACHE_LOCK:
        cached = _CACHE.get(key)
        if cached is not None and cached[0] == identity:
            return cached[1]
    snapshot = IssueSnapshot.model_validate_json(path.read_text(encoding="utf-8"))
    if snapshot.repository != repo:
        raise ValueError(f"snapshot {path} is for {snapshot.repository}, not {repo}")
    if snapshot.count != len(snapshot.items) or snapshot.sha256 != items_sha256(
        snapshot.items
    ):
        raise ValueError(f"snapshot {path} fails its count/sha256 check")
    with _CACHE_LOCK:
        _CACHE[key] = (identity, snapshot)
    return snapshot


def _select(repo: str, mode: str, value: Any, records: list[IssueRecord]) -> list[str]:
    numbers = [r.number for r in records]
    if mode == "sample":
        population = len(numbers)
        if value > population:
            raise ValueError(f"sample {value} exceeds population {population}")
        if value == 1:
            picked = [numbers[0]]
        else:
            picked = [
                numbers[i * (population - 1) // (value - 1)] for i in range(value)
            ]
    elif mode == "named":
        absent = sorted(set(value) - set(numbers))
        if absent:
            raise ValueError(f"numbers {absent} not in snapshot of {repo}")
        picked = list(value)
    else:
        picked = numbers
    return [f"{repo}#{n}" for n in picked]


def _state(state: dict[str, Any] | None, kwargs: dict[str, Any]) -> dict[str, Any]:
    return state if isinstance(state, dict) else kwargs


def gh_issues_discover(state: dict[str, Any] | None = None, **kwargs: Any) -> list[str]:
    """Refresh the snapshot with one listing; return the selected refs."""
    repo, mode, value = parse_source(str(_state(state, kwargs).get("source") or ""))
    records = _list(repo)
    refs = _select(repo, mode, value, records)
    _write_snapshot(repo, records)
    return refs


def gh_issues_versions(
    state: dict[str, Any] | None = None, **kwargs: Any
) -> dict[str, str]:
    """`{ref: updated_at}` for the selected refs, from this run's snapshot."""
    repo, mode, value = parse_source(str(_state(state, kwargs).get("source") or ""))
    snapshot = load_snapshot(repo)
    by_number = {r.number: r.updated_at for r in snapshot.items}
    refs = _select(repo, mode, value, snapshot.items)
    return {ref: by_number[int(ref.rsplit("#", 1)[1])] for ref in refs}


def gh_issues_extract(state: dict[str, Any] | None = None, **kwargs: Any) -> str:
    """One ref -> its record as a JSON bundle, read from the snapshot."""
    ref = str(_state(state, kwargs).get("item") or "")
    match = _REF.match(ref)
    if match is None:
        raise ValueError(f"item {ref!r} is not <owner>/<repo>#<number>")
    number = int(match["n"])
    for record in load_snapshot(match["repo"]).items:
        if record.number == number:
            return json.dumps(record.model_dump())
    raise ValueError(f"item {ref} absent from snapshot")
