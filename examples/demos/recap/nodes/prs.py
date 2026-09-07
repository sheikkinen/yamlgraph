"""FR-1027: the recap's pull-request axis — code-owned, bounded, honest.

The recap collects from the local git object store, so it cannot see what the
week DECIDED: a pull request closed unmerged contributes zero commits, and an
open one contributes none either. This node adds that axis and nothing else.

Three rules, all inherited rather than invented:

- FR-703/FR-704: the model neither joins nor copies. Every field here —
  number, dates, duration, title, ordering — is assembled in code, and the
  lines reach the output bit-exact so each number is paste-safe.
- Commandment 6: an axis that ran and found nothing (``available: True``,
  empty buckets) and an axis we could not look at (``available: False`` with
  a reason) are different values. Only four named exception classes are
  absorbed; anything else propagates.
- FR-922 latency budget: exactly one ``gh`` subprocess invocation per recap,
  with a finite timeout, and no invocation at all when the remote is
  ineligible.

``gh pr list --limit 300`` may paginate internally, so the bound this module
promises is one SUBPROCESS invocation, not one HTTP request.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from datetime import UTC, datetime
from typing import Any

PR_LIMIT = 300
GH_TIMEOUT = 60
GH_JSON_FIELDS = "number,title,state,createdAt,mergedAt,closedAt"
REQUIRED_FIELDS = ("number", "title", "state", "createdAt", "mergedAt", "closedAt")

GIT = shutil.which("git") or "git"
GH = shutil.which("gh") or "gh"

_NO_ORIGIN_EXIT = 2
_SECONDS_PER_DAY = 86400

# The three accepted remote families (R-3), each with an optional .git suffix.
_SLUG = r"(?P<owner>[^/:\s]+)/(?P<name>[^/:\s]+?)(?:\.git)?"
_REMOTE_FORMS = (
    re.compile(rf"^https?://(?P<host>[^/\s]+)/{_SLUG}$"),
    re.compile(rf"^ssh://(?:[^@/\s]+@)?(?P<host>[^/\s]+)/{_SLUG}$"),
    re.compile(rf"^(?:[^@/\s]+@)(?P<host>[^:/\s]+):{_SLUG}$"),
)
_GITHUB_HOSTS = frozenset({"github.com", "www.github.com"})


def _now_epoch() -> int:
    """Collection clock, isolated so tests can freeze it."""
    return int(time.time())


def _unavailable(reason: str) -> dict[str, Any]:
    """The only shape an unsuccessful axis may take (Commandment 6)."""
    return {
        "available": False,
        "reason": reason,
        "cap_reached": False,
        "merged": [],
        "closed_unmerged": [],
        "open": [],
    }


def rev_parse_argv(repo_path: str, since: str) -> list[str]:
    """Window argv, exposed so the ``since`` grammar is pinned by a test.

    ``--since=<since>`` is ONE element: a crafted window string can never
    become a second argument. Note that git's date parser degrades silently —
    an unparseable ``since`` yields the current epoch with exit 0, exactly as
    ``git log --since`` does for the five pre-existing collection tools. The
    axis inherits that behaviour rather than diverging from the graph.
    """
    return [GIT, "-C", repo_path, "rev-parse", f"--since={since}"]


def parse_origin(url: str) -> tuple[str | None, str]:
    """Derive ``owner/name`` from an origin URL, or say why it cannot be.

    Returns ``(slug, "")`` on success and ``(None, reason)`` otherwise. Every
    rejection happens BEFORE any ``gh`` invocation, and the reason strings are
    stable because the renderer prints them verbatim.
    """
    candidate = url.strip()
    if not candidate:
        return None, "no origin remote"
    if candidate.startswith("file://"):
        return None, "origin is a local path remote"
    for pattern in _REMOTE_FORMS:
        match = pattern.match(candidate)
        if not match:
            continue
        host = match.group("host").lower()
        if host not in _GITHUB_HOSTS:
            return None, f"origin host is {host}, not github.com"
        return f"{match.group('owner')}/{match.group('name')}", ""
    if "://" not in candidate and "@" not in candidate:
        return None, "origin is a local path remote"
    return None, "origin URL is malformed (no owner/name)"


def parse_max_age(output: str) -> int:
    """Extract the epoch from ``git rev-parse --since`` output.

    Loud on any other shape: the epoch is the window boundary, and a guessed
    boundary is a `plausible_wrong_answer`.
    """
    match = re.fullmatch(r"--max-age=(\d+)", output.strip())
    if not match:
        raise ValueError(f"unexpected git rev-parse --since output: {output!r}")
    return int(match.group(1))


def _ts(value: str) -> int:
    """ISO-8601 Z timestamp to epoch seconds."""
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())


def _day(epoch: int) -> str:
    return datetime.fromtimestamp(epoch, UTC).strftime("%Y-%m-%d")


def _line(row: dict[str, Any], end: int | None, now: int) -> str:
    """``#<number>|<created>→<end>|<N>d|<title>`` — assembled, never retyped.

    ``end`` is the decision timestamp, or None for an open row, whose elapsed
    days are measured against the collection clock.
    """
    created = _ts(row["createdAt"])
    closed_at = now if end is None else end
    days = max(0, (closed_at - created) // _SECONDS_PER_DAY)
    shown_end = "open" if end is None else _day(end)
    return f"#{row['number']}|{_day(created)}→{shown_end}|{days}d|{row['title']}"


def bucket_prs(
    rows: list[dict[str, Any]], epoch: int, now: int
) -> dict[str, list[str]]:
    """Partition rows into the three buckets, ordered in code (R-1).

    Membership is inclusive against the EXACT epoch — the UTC date is only
    ever printed, so midnight truncation cannot move a row in or out:

    - ``merged``          ``mergedAt`` is set and ``>= epoch``
    - ``closed_unmerged`` ``mergedAt`` is null, ``closedAt`` set and ``>= epoch``
    - ``open``            ``state == "OPEN"``, at any age — staleness is the point

    Order is decision timestamp descending then number descending for the two
    decided buckets, and ``createdAt`` descending then number descending for
    open rows, so the output never depends on undocumented ``gh`` ordering.
    """
    merged: list[tuple[int, int, str]] = []
    closed: list[tuple[int, int, str]] = []
    opened: list[tuple[int, int, str]] = []

    for row in rows:
        number = int(row["number"])
        if row.get("state") == "OPEN":
            opened.append((_ts(row["createdAt"]), number, _line(row, None, now)))
            continue
        if row.get("mergedAt"):
            decided = _ts(row["mergedAt"])
            if decided >= epoch:
                merged.append((decided, number, _line(row, decided, now)))
            continue
        if row.get("closedAt"):
            decided = _ts(row["closedAt"])
            if decided >= epoch:
                closed.append((decided, number, _line(row, decided, now)))

    def ordered(bucket: list[tuple[int, int, str]]) -> list[str]:
        return [line for _, _, line in sorted(bucket, key=lambda e: (-e[0], -e[1]))]

    return {
        "merged": ordered(merged),
        "closed_unmerged": ordered(closed),
        "open": ordered(opened),
    }


def axis_note(axis: dict[str, Any]) -> str:
    """One axis-level note, composed in code (R-4).

    The cap clause says "may be truncated": exactly ``PR_LIMIT`` returned rows
    cannot prove a further row exists, so the note must not claim it does.
    """
    clauses: list[str] = []
    if not axis.get("available"):
        clauses.append(f"pull-request axis unavailable: {axis.get('reason', '')}")
    if axis.get("cap_reached"):
        clauses.append(
            f"pull-request cap of {PR_LIMIT} reached; results may be truncated"
        )
    return "; ".join(clauses)


def _origin_url(repo_path: str) -> tuple[str | None, str]:
    """Read ``origin``. Absent origin is reportable; a non-repo stays loud."""
    try:
        result = subprocess.run(  # noqa: S603 — fixed git argv, no shell
            [GIT, "-C", repo_path, "remote", "get-url", "origin"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        if exc.returncode == _NO_ORIGIN_EXIT:
            return None, "no origin remote"
        raise
    return result.stdout, ""


def _gh_rows(slug: str) -> tuple[list[dict[str, Any]] | None, str]:
    """The one bounded ``gh`` invocation (R-2).

    Four named failure classes are absorbed, each into a stable reason. No
    broad handler: an unexpected error is a defect and must surface.
    """
    argv = [
        GH,
        "pr",
        "list",
        "--repo",
        slug,
        "--state",
        "all",
        "--limit",
        str(PR_LIMIT),
        "--json",
        GH_JSON_FIELDS,
    ]
    try:
        result = subprocess.run(  # noqa: S603 — fixed gh argv, no shell
            argv,
            check=True,
            capture_output=True,
            text=True,
            timeout=GH_TIMEOUT,
        )
    except FileNotFoundError:
        return None, "gh not found on PATH"
    except subprocess.TimeoutExpired:
        return None, f"gh timed out after {GH_TIMEOUT}s"
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        if not stderr:
            return None, f"gh exited {exc.returncode} with no stderr"
        return None, f"gh exited {exc.returncode}: {stderr.splitlines()[0].strip()}"

    try:
        rows = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None, "gh returned unparseable JSON"
    if not isinstance(rows, list):
        return None, "gh returned unparseable JSON"
    for row in rows:
        if not isinstance(row, dict):
            return None, "gh returned unparseable JSON"
        for field in REQUIRED_FIELDS:
            if field not in row:
                return None, f"gh row missing required field {field}"
    return rows, ""


def collect_prs(state: dict) -> dict:
    """Collect the pull-request axis for the recap's window.

    Returns a single state update, ``pr_axis``. Identify, bound, collect,
    bucket — each step can end the node with a recorded reason instead of an
    exception, and no step ever substitutes data it did not receive.
    """
    repo_path = state.get("repo_path") or "."
    since = state.get("since") or "1 week ago"

    url, reason = _origin_url(repo_path)
    if url is None:
        return {"pr_axis": _unavailable(reason)}
    slug, reason = parse_origin(url)
    if slug is None:
        return {"pr_axis": _unavailable(reason)}

    window = subprocess.run(  # noqa: S603 — fixed git argv, no shell
        rev_parse_argv(repo_path, since),
        check=True,
        capture_output=True,
        text=True,
    )
    epoch = parse_max_age(window.stdout)

    rows, reason = _gh_rows(slug)
    if rows is None:
        return {"pr_axis": _unavailable(reason)}

    buckets = bucket_prs(rows, epoch, _now_epoch())
    return {
        "pr_axis": {
            "available": True,
            "reason": "",
            "cap_reached": len(rows) >= PR_LIMIT,
            **buckets,
        }
    }
