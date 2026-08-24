#!/usr/bin/env python3
"""FR-875 collect stage: freeze the memory corpus for judgement.

Reads ONLY the repo scope of an explicitly configured memory root and
writes a frozen snapshot (manifest + note copies) strictly under the
out-dir. The graph judges the snapshot, never the live root.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

NOTE_NAME_RE = re.compile(r"^[A-Za-z0-9._-]+\.md$")


def collect(memory_root: Path, out_dir: Path) -> dict:
    repo_dir = memory_root / "repo"
    if not repo_dir.is_dir():
        raise ValueError(f"memory root has no repo scope: {repo_dir}")
    notes: dict[str, dict] = {}
    notes_out = out_dir / "notes" / "repo"
    notes_out.mkdir(parents=True, exist_ok=True)
    for path in sorted(repo_dir.iterdir()):
        if path.name.startswith("."):
            continue
        if path.is_symlink():
            raise ValueError(f"symlink refused in repo scope: {path.name}")
        if not path.is_file() or not NOTE_NAME_RE.match(path.name):
            continue
        data = path.read_bytes()
        key = f"repo/{path.name}"
        notes[key] = {
            "sha256": hashlib.sha256(data).hexdigest(),
            "size": len(data),
            "mtime": path.stat().st_mtime,
        }
        (notes_out / path.name).write_bytes(data)
    manifest = {"version": 1, "memory_root": str(memory_root), "notes": notes}
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def rederivation_advisories(memory_root: Path, notes: dict) -> list[str]:
    """Warn when a live note resembles a forget-tombstoned archive entry (FR-878)."""
    tomb = memory_root / "repo" / "_tombstones.md"
    if not tomb.exists():
        return []
    forget_rows: list[tuple[str, str, str, str]] = []
    restored_refs: set[str] = set()
    for line in tomb.read_text(encoding="utf-8").splitlines():
        parts = [part.strip() for part in line.split("|")]
        if len(parts) < 10:
            continue
        op_id, key, verdict, archive, pre_sha, status = (
            parts[0],
            parts[1],
            parts[2],
            parts[4],
            parts[5],
            parts[9],
        )
        if status == "restored":
            restored_refs.add(archive)
        elif verdict == "forget":
            forget_rows.append((op_id, key, archive, pre_sha))
    live_hashes = {entry["sha256"]: key for key, entry in notes.items()}
    advisories = []
    for op_id, key, archive, pre_sha in forget_rows:
        if archive in restored_refs:
            continue
        if key in notes or pre_sha in live_hashes:
            date = op_id.split("T")[0]
            advisories.append(
                f"note {key} resembles archived {archive}"
                f" (forgotten {date}) — consider restore"
            )
    return advisories


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--memory-root", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)
    try:
        manifest = collect(Path(args.memory_root), Path(args.out_dir))
    except (ValueError, OSError) as exc:
        print(f"collect: {exc}", file=sys.stderr)
        return 1
    print(f"collected {len(manifest['notes'])} notes")
    for advisory in rederivation_advisories(Path(args.memory_root), manifest["notes"]):
        print(advisory)
    return 0


if __name__ == "__main__":
    sys.exit(main())
