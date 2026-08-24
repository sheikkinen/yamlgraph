#!/usr/bin/env python3
"""FR-877 staleness advisory: is a curation pass worth doing?

Pure stdlib, zero LLM/network. Compares the live repo-scope corpus
(regular non-symlink *.md under <memory-root>/repo/, incl. _tombstones.md)
against the post-apply baseline in .curation-state.json by sha256.
Silent below threshold; exactly one line at/above it or when the corpus
was never curated. A malformed marker is a real error, never no-drift.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

MARKER_NAME = ".curation-state.json"


def live_corpus(memory_root: Path) -> dict[str, str]:
    repo_dir = memory_root / "repo"
    if not repo_dir.is_dir():
        raise ValueError(f"memory root has no repo scope: {repo_dir}")
    notes = {}
    for path in sorted(repo_dir.glob("*.md")):
        if path.is_symlink() or not path.is_file():
            continue
        notes[f"repo/{path.name}"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return notes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--memory-root", required=True)
    parser.add_argument("--threshold", type=int, default=5)
    args = parser.parse_args(argv)
    memory_root = Path(args.memory_root)
    try:
        notes = live_corpus(memory_root)
        marker_path = memory_root / MARKER_NAME
        if not marker_path.exists():
            if notes:
                print(
                    f"memory: corpus never curated ({len(notes)} notes)"
                    " — consider a hygiene pass"
                )
            return 0
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
        baseline = marker["notes"]
    except (ValueError, OSError, json.JSONDecodeError, KeyError) as exc:
        print(f"advisory: {exc}", file=sys.stderr)
        return 1
    new = len(set(notes) - set(baseline))
    deleted = len(set(baseline) - set(notes))
    edited = sum(1 for key in set(notes) & set(baseline) if notes[key] != baseline[key])
    drift = new + edited + deleted
    if drift >= args.threshold:
        date = marker.get("applied_at", "")[:10]
        print(
            f"memory: {drift} notes drifted ({new} new, {edited} edited,"
            f" {deleted} deleted) since last curation ({date})"
            " — consider a hygiene pass"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
