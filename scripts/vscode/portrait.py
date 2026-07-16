#!/usr/bin/env python3
"""Memory: what the agents worked on, and how parallel it really is.

Spike (scripts/vscode, 2026-07-16). Two sources:
- chronicle (session-store.db): summaries, repos, most-touched files;
- chatSessions request timestamps: measured concurrency — how many
  distinct sessions were active in the same hour, per day (the
  one_session_one_repo hazard, quantified).
"""

from __future__ import annotations

import re
import sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path

USER_DIR = Path.home() / "Library/Application Support/Code/User"
CHRONICLE = USER_DIR / "globalStorage/github.copilot-chat/session-store.db"
WS_STORAGE = USER_DIR / "workspaceStorage"

TS_RE = re.compile(r'"timestamp":(\d{13})')
TITLE_RE = re.compile(r'"customTitle":"([^"]{1,120})"')
CREATED_RE = re.compile(r'"creationDate":(\d{13})')


def recent_titles(limit: int = 15) -> None:
    """Session titles from chatSessions — the richest narrative source
    (the chronicle indexes debug-logs, which are start/end markers only)."""
    rows = []
    for chat in WS_STORAGE.glob("*/chatSessions/*.jsonl"):
        try:
            head = chat.open(errors="replace").read(4000)
        except OSError:
            continue
        title = TITLE_RE.search(head)
        created = CREATED_RE.search(head)
        if not title:
            continue
        rows.append(
            (
                chat.stat().st_mtime,
                datetime.fromtimestamp(int(created.group(1)) / 1000).date().isoformat()
                if created
                else "?",
                chat.stat().st_size / 1e6,
                title.group(1),
            )
        )
    rows.sort(reverse=True)
    print("== recent sessions (chatSessions titles, by last activity) ==")
    for mtime, created, mb, title in rows[:limit]:
        touched = datetime.fromtimestamp(mtime).strftime("%m-%d %H:%M")
        print(f"  {touched}  ({created}, {mb:>6.1f} MB)  {title}")


def chronicle_portrait(days: int = 10) -> None:
    if not CHRONICLE.is_file():
        print("no chronicle db")
        return
    db = sqlite3.connect(f"file:{CHRONICLE}?mode=ro", uri=True)
    print("== recent session summaries (chronicle) ==")
    rows = db.execute(
        """SELECT date(updated_at), repository, agent_name,
                  substr(coalesce(summary,'(no summary)'),1,90)
           FROM sessions WHERE summary IS NOT NULL
           ORDER BY updated_at DESC LIMIT ?""",
        (days,),
    ).fetchall()
    for day, repo, agent, summary in rows:
        repo = (repo or "?").split("/")[-1]
        print(f"  {day}  {repo:<18} {agent or '-':<10} {summary}")

    print("\n== most-touched files, last 30 days (chronicle) ==")
    rows = db.execute(
        """SELECT sf.file_path, count(DISTINCT sf.session_id) AS n
           FROM session_files sf JOIN sessions s ON s.id = sf.session_id
           WHERE s.updated_at > datetime('now','-30 day')
           GROUP BY sf.file_path ORDER BY n DESC LIMIT 12"""
    ).fetchall()
    for path, n in rows:
        short = "…" + path[-70:] if len(path) > 71 else path
        print(f"  {n:>3} sessions  {short}")
    db.close()


def concurrency() -> None:
    """Sessions active in the same hour — parallelism, measured."""
    hour_sessions: dict[str, set[str]] = defaultdict(set)
    for chat in WS_STORAGE.glob("*/chatSessions/*.jsonl"):
        try:
            text = chat.read_text(errors="replace")
        except OSError:
            continue
        for m in TS_RE.finditer(text):
            when = datetime.fromtimestamp(int(m.group(1)) / 1000)
            hour_sessions[when.strftime("%Y-%m-%d %H")].add(chat.stem)

    day_peak: dict[str, int] = defaultdict(int)
    for hour, sessions in hour_sessions.items():
        day = hour[:10]
        day_peak[day] = max(day_peak[day], len(sessions))

    print("\n== peak concurrent sessions per day (same-hour activity) ==")
    for day in sorted(day_peak)[-14:]:
        peak = day_peak[day]
        print(f"  {day}  {'█' * peak} {peak}")


if __name__ == "__main__":
    recent_titles()
    chronicle_portrait()
    concurrency()
