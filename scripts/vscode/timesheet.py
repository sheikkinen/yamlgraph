#!/usr/bin/env python3
"""Timesheet: what was worked on, day by day, over a date range.

Spike (scripts/vscode, 2026-08-27). Reads the chronicle
(session-store.db) for sessions in [--start, --end) and prints a
day-grouped report: repo, branch, agent, and a one-line description
per session (chronicle summary, falling back to the earliest touched
files when the summary is a bare verb like "merge"/"doc"/"judge").

Local-only: this device's session store (see MAP.md), not a
cross-machine ledger — sessions recorded on other machines/devices are
invisible here (memory-tool-locality: repo/session/chat stores are all
keyed to this VS Code profile).
"""

from __future__ import annotations

import argparse
import os
import platform
import sqlite3
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

CHRONICLE_REL = "globalStorage/github.copilot-chat/session-store.db"

# Chronicle summaries this terse carry no signal on their own — fall
# back to touched files for these.
VAGUE_SUMMARIES = {
    "merge",
    "doc",
    "docs",
    "judge",
    "enforce",
    "release",
    "fold",
    "fold. enforce",
    "reflect",
    "record",
    "play",
    "wip",
    "commit",
}


def user_code_dir() -> Path:
    """VS Code's per-user config dir. Portable across users (env/home
    vars, not a hardcoded username) AND across OSes (macOS/Linux/
    Windows each place it differently) — the siblings in this folder
    hardcode the macOS path only."""
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library/Application Support/Code/User"
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) if appdata else Path.home() / "AppData/Roaming"
        return base / "Code/User"
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "Code/User"


def month_bounds(month: str) -> tuple[str, str]:
    start = datetime.strptime(month, "%Y-%m").date()
    end_year = start.year + (1 if start.month == 12 else 0)
    end_month = 1 if start.month == 12 else start.month + 1
    end = date(end_year, end_month, 1)
    return start.isoformat(), end.isoformat()


def fetch_sessions(db: sqlite3.Connection, start: str, end: str) -> list[sqlite3.Row]:
    return db.execute(
        """SELECT id, date(updated_at) AS day, repository, branch,
                  agent_name, summary, updated_at
           FROM sessions
           WHERE updated_at >= ? AND updated_at < ?
           ORDER BY updated_at ASC""",
        (start, end),
    ).fetchall()


def fetch_top_files(
    db: sqlite3.Connection, session_ids: list[str], limit: int = 3
) -> dict[str, list[str]]:
    if not session_ids:
        return {}
    placeholders = ",".join("?" for _ in session_ids)
    rows = db.execute(
        f"""SELECT session_id, file_path, MIN(first_seen_at) AS first_seen
            FROM session_files
            WHERE session_id IN ({placeholders})
            GROUP BY session_id, file_path
            ORDER BY session_id, first_seen ASC""",  # noqa: S608  # CONF-424
        session_ids,
    ).fetchall()
    out: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        bucket = out[row["session_id"]]
        if len(bucket) < limit:
            bucket.append(Path(row["file_path"]).name)
    return out


def repo_name(repository: str | None) -> str:
    if not repository:
        return "?"
    return repository.rstrip("/").removesuffix(".git").split("/")[-1]


def describe(summary: str | None, files: list[str]) -> str:
    text = (summary or "").strip()
    if text.lower() not in VAGUE_SUMMARIES and text:
        return text.splitlines()[0][:100]
    if files:
        return f"({', '.join(files)})"
    return text or "(no summary)"


def render(rows: list[sqlite3.Row], files_by_session: dict[str, list[str]]) -> None:
    by_day: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for row in rows:
        by_day[row["day"]].append(row)

    for day in sorted(by_day):
        print(f"\n{day}")
        for row in by_day[day]:
            repo = repo_name(row["repository"])
            branch = row["branch"] or "?"
            agent = row["agent_name"] or "?"
            desc = describe(row["summary"], files_by_session.get(row["id"], []))
            print(f"  {repo:<32} {branch:<28} {agent:<22} {desc}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--month",
        default=date.today().strftime("%Y-%m"),
        help="YYYY-MM, default: current month",
    )
    parser.add_argument("--start", help="ISO date, overrides --month start (inclusive)")
    parser.add_argument("--end", help="ISO date, overrides --month end (exclusive)")
    parser.add_argument("--repo", help="filter: substring match on repository URL")
    args = parser.parse_args()

    start, end = month_bounds(args.month)
    start = args.start or start
    end = args.end or end

    chronicle = user_code_dir() / CHRONICLE_REL
    if not chronicle.is_file():
        print(f"no chronicle db at {chronicle}")
        return

    db = sqlite3.connect(f"file:{chronicle}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    try:
        rows = fetch_sessions(db, start, end)
        if args.repo:
            rows = [r for r in rows if args.repo in (r["repository"] or "")]
        if not rows:
            print(f"no sessions between {start} and {end}")
            return
        files_by_session = fetch_top_files(db, [r["id"] for r in rows])
    finally:
        db.close()

    print(f"Timesheet {start} .. {end} (local chronicle only, {len(rows)} sessions)")
    render(rows, files_by_session)


if __name__ == "__main__":
    main()
