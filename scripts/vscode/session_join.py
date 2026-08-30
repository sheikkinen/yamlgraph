#!/usr/bin/env python3
"""FR-902 AC-11: join event-store requests to lane checkpoint commits.

Request-Index trailers on session/<id> checkpoints (session-checkpoint.sh)
are the join key against the replayed chatSessions event store (FR-898
session_ledger). Output: TSV, one row per request; '-' where a request
produced no checkpoint (read-only turn or unflushed store).

Run:  python3 scripts/vscode/session_join.py \
        --repo . --store <chatSessions/*.jsonl> --session <session-id>
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

from session_ledger import replay, request_rows, session_header

GIT = shutil.which("git") or "git"


def checkpoint_map(repo: Path, session_id: str) -> dict[str, str]:
    """Request-Index -> commit sha from the session branch (first wins)."""
    out = subprocess.run(  # noqa: S603  # CONF-440
        [
            GIT,
            "-C",
            str(repo),
            "log",
            "--format=%H%x00%(trailers:key=Request-Index,valueonly)",
            f"session/{session_id}",
        ],
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    cps: dict[str, str] = {}
    for line in out.splitlines():
        if "\x00" not in line:
            continue
        sha, idx = line.split("\x00", 1)
        idx = idx.strip()
        if idx and idx not in cps:
            cps[idx] = sha
    return cps


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, type=Path)
    ap.add_argument("--store", required=True, type=Path)
    ap.add_argument("--session", required=True)
    args = ap.parse_args()

    doc = replay(args.store)
    cps = checkpoint_map(args.repo, args.session)
    print("request\tcheckpoint\tmodel\tcredits\tprompt")
    for row in request_rows(doc, session_header(doc, args.store)):
        credits = row["credits"]
        credits_s = f"{credits:g}" if isinstance(credits, int | float) else "-"
        print(
            f"{row['request']}\t{cps.get(str(row['request']), '-')}\t"
            f"{row['model']}\t{credits_s}\t{'yes' if row['prompt'] else 'no'}"
        )


if __name__ == "__main__":
    main()
