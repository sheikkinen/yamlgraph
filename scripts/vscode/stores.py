#!/usr/bin/env python3
"""Habitat: where agent-session data lives, how big, what's active.

Spike (scripts/vscode, 2026-07-16). Walks every workspaceStorage hash
dir, resolves its workspace folder, and reports store sizes, session
counts, and recent activity.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

USER_DIR = Path.home() / "Library/Application Support/Code/User"
WS_STORAGE = USER_DIR / "workspaceStorage"
ACTIVE_WINDOW_S = 24 * 3600


def dir_size(path: Path) -> int:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def workspace_folder(hash_dir: Path) -> str:
    meta = hash_dir / "workspace.json"
    if not meta.is_file():
        return "?"
    try:
        data = json.loads(meta.read_text(encoding="utf-8"))
    except ValueError:
        return "?"
    return data.get("folder", data.get("workspace", "?")).replace("file://", "")


def main() -> None:
    now = time.time()
    rows = []
    for hash_dir in sorted(WS_STORAGE.iterdir()):
        chat = hash_dir / "chatSessions"
        if not chat.is_dir():
            continue
        sessions = list(chat.glob("*.jsonl"))
        if not sessions:
            continue
        active = [s for s in sessions if now - s.stat().st_mtime < ACTIVE_WINDOW_S]
        newest = max(s.stat().st_mtime for s in sessions)
        rows.append(
            {
                "folder": workspace_folder(hash_dir),
                "sessions": len(sessions),
                "active_24h": len(active),
                "chat_mb": dir_size(chat) / 1e6,
                "editing_mb": dir_size(hash_dir / "chatEditingSessions") / 1e6
                if (hash_dir / "chatEditingSessions").is_dir()
                else 0.0,
                "newest": time.strftime("%Y-%m-%d %H:%M", time.localtime(newest)),
            }
        )
    rows.sort(key=lambda r: -r["chat_mb"])

    total_mb = sum(r["chat_mb"] + r["editing_mb"] for r in rows)
    print(
        f"{'workspace':<52} {'sess':>5} {'act24h':>6} {'chatMB':>8} {'editMB':>8}  newest"
    )
    for r in rows:
        folder = r["folder"]
        folder = "…" + folder[-49:] if len(folder) > 50 else folder
        print(
            f"{folder:<52} {r['sessions']:>5} {r['active_24h']:>6} "
            f"{r['chat_mb']:>8.1f} {r['editing_mb']:>8.1f}  {r['newest']}"
        )
    print(
        f"\ntotal session storage: {total_mb / 1000:.2f} GB across {len(rows)} workspaces"
    )

    chronicle = USER_DIR / "globalStorage/github.copilot-chat/session-store.db"
    if chronicle.is_file():
        print(f"chronicle db: {chronicle.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
