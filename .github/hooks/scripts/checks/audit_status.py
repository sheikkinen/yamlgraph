#!/usr/bin/env python3
"""Audit-log status summary for the lockdown command channel.

Extracted from pre-command-guard.sh by FR-889 (size gate AC-07).
Env: LOG_DIR (audit.jsonl location), LOCKFILE (lockdown marker path).
"""

import collections
import datetime as dt
import json
import os
import pathlib


def main() -> None:
    logfile = pathlib.Path(os.environ.get("LOG_DIR", ".")) / "audit.jsonl"
    if not logfile.exists():
        print("No audit log found.")
        return
    lines = logfile.read_text(encoding="utf-8").strip().splitlines()
    decisions: collections.Counter = collections.Counter()
    tools: collections.Counter = collections.Counter()
    errors: collections.Counter = collections.Counter()
    cutoff = dt.datetime.now(dt.UTC) - dt.timedelta(days=7)
    for line in lines:
        d = json.loads(line)
        decisions[d.get("decision", "")] += 1
        tools[d.get("tool", "")] += 1
        if d.get("decision") == "error":
            try:
                ts = dt.datetime.fromisoformat(d.get("ts", ""))
            except ValueError:
                continue
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=dt.UTC)
            if ts >= cutoff:
                errors[d.get("hook", "?") + "/" + d.get("reason", "?")] += 1
    total = sum(decisions.values())
    dec_str = ", ".join(f"{k}={v}" for k, v in decisions.most_common())
    tool_str = ", ".join(f"{k}={v}" for k, v in tools.most_common(5))
    err_str = (
        ", ".join(f"{k}={v}" for k, v in errors.most_common()) if errors else "none"
    )
    lockfile = os.environ.get("LOCKFILE", "")
    lockdown = "YES" if lockfile and pathlib.Path(lockfile).exists() else "no"
    print(
        f"Audit: {total} total entries. Decisions: {dec_str}. "
        f"Top tools: {tool_str}. Hook errors (7d): {err_str}. "
        f"Lockdown: {lockdown}"
    )


if __name__ == "__main__":
    main()
