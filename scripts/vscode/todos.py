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

import hashlib
import json
import re
import sqlite3
import time
from pathlib import Path

WS_STORAGE = Path.home() / "Library/Application Support/Code/User/workspaceStorage"
TITLE_RE = re.compile(r'"customTitle":"([^"]{1,120})"')
REF_RE = re.compile(r"\b((?:FR|NC)-\d{2,4})\b")
DIARY_RE = re.compile(r"diary|reflect|distill", re.I)
DIARY_DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
LIVE_WINDOW_S = 3600
BRIEFING_AGE_CAP_S = 30 * 86400  # F1: arms only after backlog-zero (AC-04)
BRIEFING_ROW_CAP = 10
DIARY_WINDOW_BEFORE_S = 7 * 86400  # FR-742 F2: [last_active-7d, +1d]
DIARY_WINDOW_AFTER_S = 86400
DISPOSITIONS_PATH = Path(__file__).resolve().parent / "orphan-dispositions.jsonl"


def is_diary_class(title: str) -> bool:
    """FR-742 AC-01: the Distill debt class. Doctrine debt does not expire."""
    return bool(DIARY_RE.search(title))


def diary_debt_verdict(
    last_active: float, diary_dirs: list[Path], refs: list[str] | None = None
) -> str:
    """FR-742 AC-02: delivery verdict for a dead session's diary debt.

    With refs (FR/NC ids from the session's own todos): DELIVERED iff an
    in-window diary filename names one — substance, not presence (this
    repo diaries daily; any-entry-in-window is vacuous). Without refs:
    LIKELY DELIVERED on any in-window entry — explicitly weak, hence
    'LIKELY'. Window = [last_active - 7d, last_active + 1d]; a
    successor's later posthumous entry must not count (F2).
    """
    from datetime import datetime

    lo = last_active - DIARY_WINDOW_BEFORE_S
    hi = last_active + DIARY_WINDOW_AFTER_S
    in_window = []
    for d in diary_dirs:
        for p in d.glob("*.md"):
            m = DIARY_DATE_RE.search(p.name)
            if not m:
                continue
            ts = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).timestamp()
            if lo <= ts <= hi:
                in_window.append(p.name.lower())
    if refs:
        # hyphens are noise at this boundary (field defect: nc393 vs NC-393)
        flat = [n.replace("-", "") for n in in_window]
        for ref in refs:
            needle = ref.lower().replace("-", "")
            if any(needle in name for name in flat):
                return "DELIVERED"
        return "UNWRITTEN"
    return "LIKELY DELIVERED" if in_window else "UNWRITTEN"


def material_for(sid: str) -> Path | None:
    """FR-742 F1: best-available material — transcript if present, else
    chatSessions (which holds the full session). Age of debt
    anti-correlates with material richness."""
    for p in WS_STORAGE.glob(f"*/GitHub.copilot-chat/transcripts/{sid}*.jsonl"):
        return p
    for p in WS_STORAGE.glob(f"*/chatSessions/{sid}*.jsonl"):
        return p
    return None


def cross_check(title: str, roots: list[Path]) -> str | None:
    """AC-01: an orphan naming an FR/NC id is resolved against git-tracked
    reality. Git overrules the todo, mechanically, every time (A1)."""
    m = REF_RE.search(title)
    if not m:
        return None
    ref = m.group(1)
    for root in roots:
        if list(root.glob(f"feature-requests/{ref}-*")) or list(
            root.glob(f"projects/*/feature-requests/{ref}-*")
        ):
            return "DELIVERED ELSEWHERE"
    return "NO ARTIFACT"


def drop_key(sid: str, title: str) -> str:
    """F3: content key, never positional."""
    sha8 = hashlib.sha1(title.encode()).hexdigest()[:8]  # noqa: S324  # CONF-395
    return f"{sid}:{sha8}"


def record_drop(sidecar: Path, sid: str, title: str, reason: str) -> bool:
    key = drop_key(sid, title)
    if key in load_dispositions(sidecar):
        return False
    with sidecar.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {"key": key, "title": title, "reason": reason, "ts": time.time()}
            )
            + "\n"
        )
    return True


def load_dispositions(sidecar: Path = DISPOSITIONS_PATH) -> set[str]:
    if not sidecar.is_file():
        return set()
    return {
        json.loads(ln)["key"] for ln in sidecar.read_text(encoding="utf-8").splitlines() if ln.strip()
    }


def briefing_lines(
    sessions: dict[str, dict],
    live: set[str],
    roots: list[Path],
    dispositions: set[str],
    now: float | None = None,
) -> list[str]:
    """AC-02 + A1: DIED OPEN orphans (≤30d, capped) as fact-adjacent rows;
    LIVE intent rows as testimony (`claims:` prefix — render_claims_as_claims);
    stale claims overruled by git."""
    now = time.time() if now is None else now
    lines: list[str] = []
    dead_rows = []
    for sid, sess in sessions.items():
        open_items = [
            t
            for t in sess["todos"]
            if t.get("status") != "completed"
            and drop_key(sid, t.get("title", "")) not in dispositions
        ]
        if not open_items:
            continue
        mtime = sess.get("mtime")
        if sid in live:
            claims = []
            for t in open_items:
                flag = (
                    "  ← STALE CLAIM (artifact in git)"
                    if cross_check(t.get("title", ""), roots) == "DELIVERED ELSEWHERE"
                    else ""
                )
                claims.append(
                    f"    claims: [{t.get('status', '?')}] {t.get('title', '')[:60]}{flag}"
                )
            lines.append(f"  {sid[:8]}  LIVE  {sess.get('title', '')[:48]}")
            lines.extend(claims)
        elif mtime:
            age_s = now - mtime
            for t in open_items:
                title_t = t.get("title", "")
                diary = is_diary_class(title_t)
                if not diary and age_s > BRIEFING_AGE_CAP_S:
                    continue  # ordinary orphans expire; doctrine debt does not
                verdict_t = cross_check(title_t, roots)
                tag = f" [{verdict_t}]" if verdict_t else ""
                label = "DIARY DEBT" if diary else "DIED OPEN"
                dead_rows.append(
                    f"  {sid[:8]}  {label} ({age_s / 86400:.1f}d)"
                    f"  {title_t[:56]}{tag}"
                    f"  key={drop_key(sid, title_t).split(':')[1]}"
                )
    lines.extend(dead_rows[:BRIEFING_ROW_CAP])
    return lines


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


def _handle_drop(all_todos: dict, s8: str, sha8: str, reason: str) -> None:
    for sid, items in all_todos.items():
        if not sid.startswith(s8):
            continue
        for t in items or []:
            title = t.get("title", "")
            if drop_key(sid, title).endswith(sha8):
                done = record_drop(DISPOSITIONS_PATH, sid, title, reason)
                print(f"{'dropped' if done else 'already dropped'}: {title}")
                return
    print(f"no orphan matching {s8}:{sha8}")


def _print_listing(all_todos: dict, dispositions: set[str], now: float) -> None:
    rows = []
    for sid, items in all_todos.items():
        if not items:
            continue
        title, mtime = session_meta(sid)
        open_items = [
            t
            for t in items
            if t.get("status") != "completed"
            and drop_key(sid, t.get("title", "")) not in dispositions
        ]
        v = verdict(items, mtime, now) if open_items else "CLEAN CLOSE"
        rows.append((v, sid, title, open_items, mtime))

    order = {"DIED OPEN": 0, "LIVE OPEN": 1, "CLEAN CLOSE": 2}
    rows.sort(key=lambda r: (order[r[0]], -(r[4] or 0)))
    n_orphaned = sum(len(r[3]) for r in rows if r[0] == "DIED OPEN")
    roots = [Path.home() / "src/yamlgraph"]
    print(
        f"todo slots: {len(all_todos)} sessions, {len(rows)} non-empty; "
        f"orphaned open intentions (undropped): {n_orphaned}\n"
    )
    for v, sid, title, open_items, mtime in rows:
        ago = f"{(now - mtime) / 86400:.1f}d ago" if mtime else "no chat file"
        print(f"[{v:<11}] {sid[:8]}  {ago:<12} {title[:52]}")
        for t in open_items if v != "CLEAN CLOSE" else []:
            check = cross_check(t.get("title", ""), roots)
            tag = f"  [{check}]" if check else ""
            key = drop_key(sid, t.get("title", "")).split(":")[1]
            print(
                f"    [{t.get('status', '?'):<11}] {t.get('title', '')[:58]}{tag}"
                f"  key={key}"
            )


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--drop", nargs=2, metavar=("SESSION8", "SHA8"))
    ap.add_argument("--reason", default="triaged")
    args = ap.parse_args()
    all_todos = load_todos()
    if args.drop:
        _handle_drop(all_todos, args.drop[0], args.drop[1], args.reason)
        return
    _print_listing(all_todos, load_dispositions(), time.time())


if __name__ == "__main__":
    main()
