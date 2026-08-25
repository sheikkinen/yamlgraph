#!/usr/bin/env python3
"""FR-884 Phase-2 input: per-session turn skeletons with fork-prefix dedupe.

Writes tmp/fr884-skeletons.jsonl (gitignored). Fork rule: when a session's
first-K user turns are identical to another session's prefix, the shorter
shared prefix is attributed once (to the longer session) and dropped from
the fork; the fork keeps only its divergent tail.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from session_shapes import inventory, replay, turn_skeleton  # noqa: E402

OUT = Path("tmp/fr884-skeletons.jsonl")
PREFIX_K = 5  # identical first-K user texts ⇒ shared-prefix fork


def main() -> None:
    rows = inventory()
    sessions = []
    for row in rows:
        state = replay(Path(row["path"]))
        turns = turn_skeleton(state) if state else []
        sessions.append({"row": row, "turns": turns})

    # fork dedupe: group by first-K user texts
    by_prefix: dict[tuple, list[dict]] = {}
    for sess in sessions:
        key = tuple(t["user"][:200] for t in sess["turns"][:PREFIX_K])
        if len(key) == PREFIX_K and any(key):
            by_prefix.setdefault(key, []).append(sess)

    deduped_turns = 0
    for group in by_prefix.values():
        if len(group) < 2:
            continue
        group.sort(key=lambda s: len(s["turns"]), reverse=True)
        canonical = group[0]["turns"]
        for fork in group[1:]:
            shared = 0
            for a, b in zip(fork["turns"], canonical, strict=False):
                if a["user"] != b["user"]:
                    break
                shared += 1
            fork["turns"] = fork["turns"][shared:]
            fork["row"]["fork_prefix_dropped"] = shared
            deduped_turns += shared

    kept = 0
    with OUT.open("w") as fh:
        for sess in sessions:
            if not sess["turns"]:
                continue
            row = sess["row"]
            lines = [
                f"[{t['index']}] USER: {t['user'][:200]}\nAGENT: {t['agent'][:150]}"
                for t in sess["turns"][:250]
            ]
            fh.write(
                json.dumps(
                    {
                        "session_id": row["session_id"],
                        "workspace": row["workspace"][:8],
                        "requests": row["requests"],
                        "prompt_tokens": row["prompt_tokens"],
                        "fork_prefix_dropped": row.get("fork_prefix_dropped", 0),
                        "skeleton": "\n".join(lines),
                    }
                )
                + "\n"
            )
            kept += 1
    print(f"sessions={len(sessions)} written={kept} fork_turns_deduped={deduped_turns}")


if __name__ == "__main__":
    main()
