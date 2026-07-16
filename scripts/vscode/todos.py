#!/usr/bin/env python3
"""Todo forensics: last-known intentions of every session (CSI spike).

Reads `memento/chat-todo-list` from state.vscdb (read-only): one todo
list per session UUID, frozen at whatever the session last believed
remained. Never garbage-collected, never reconciled across sessions —
a graveyard of intentions. Joined with chatSessions titles and mtimes.

Verdicts:
- CLEAN CLOSE   all todos completed (the session finished its story)
- DIED OPEN     open todos + session inactive (abandoned OR completed
                elsewhere without the record updating — see the Vertex
                case: dee997c4 died mid-plan, e06433d5 did the work)
- LIVE OPEN     open todos + session active (work in flight, normal)
"""

from __future__ import annotations

import json
import re
import sqlite3
import time
from pathlib import Path

WS_STORAGE = Path.home() / "Library/Application Support/Code/User/workspaceStorage"
TITLE_RE = re.compile(r'"customTitle":"([^"]{1,120})"')
LIVE_WINDOW_S = 3600


def load_todos() -> dict[str, list[dict]]:
    merged: dict[str, list[dict]] = {}
    for db in WS_STORAGE.glob("*/state.vscdb"):
        try:
            conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
            row = conn.execute(
                "SELECT value FROM ItemTable WHERE key='memento/chat-todo-list'"
            ).fetchone()
            conn.close()
        except sqlite3.Error:
            continue
        if row:
            merged.update(json.loads(row[0]))
    return merged


def session_meta(sid: str) -> tuple[str, float | None]:
    for p in WS_STORAGE.glob(f"*/chatSessions/{sid}.jsonl"):
        m = TITLE_RE.search(p.open(errors="replace").read(4000))
        return (m.group(1) if m else "", p.stat().st_mtime)
    return ("", None)


def verdict(todos: list[dict], mtime: float | None, now: float) -> str:
    open_n = sum(1 for t in todos if t.get("status") != "completed")
    if open_n == 0:
        return "CLEAN CLOSE"
    if mtime and now - mtime <= LIVE_WINDOW_S:
        return "LIVE OPEN"
    return "DIED OPEN"


def main() -> None:
    now = time.time()
    rows = []
    for sid, todos in load_todos().items():
        if not todos:
            continue
        title, mtime = session_meta(sid)
        v = verdict(todos, mtime, now)
        open_items = [t for t in todos if t.get("status") != "completed"]
        rows.append((v, sid, title, todos, open_items, mtime))

    order = {"DIED OPEN": 0, "LIVE OPEN": 1, "CLEAN CLOSE": 2}
    rows.sort(key=lambda r: (order[r[0]], -(r[5] or 0)))
    n_orphaned = sum(len(r[4]) for r in rows if r[0] == "DIED OPEN")
    print(
        f"todo slots: {len(load_todos())} sessions, {len(rows)} non-empty; "
        f"orphaned open intentions: {n_orphaned}\n"
    )
    for v, sid, title, _todos, open_items, mtime in rows:
        ago = f"{(now - mtime) / 86400:.1f}d ago" if mtime else "no chat file"
        print(f"[{v:<11}] {sid[:8]}  {ago:<12} {title[:52]}")
        for t in open_items if v != "CLEAN CLOSE" else []:
            print(f"    [{t.get('status', '?'):<11}] {t.get('title', '')[:64]}")


if __name__ == "__main__":
    main()
