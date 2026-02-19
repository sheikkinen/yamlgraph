#!/usr/bin/env python3
"""Rotate docs/diary.md when the day has changed.

If the most recent entry date in diary.md is before today:
  1. Move diary.md → diary-YYYY-MM-DD.md (with -N suffix if exists)
  2. Create fresh diary.md with header + Previous link
  3. Stage both files with git add

Run standalone:
    python scripts/diary_rotate.py          # rotate if needed
    python scripts/diary_rotate.py --check  # dry-run, exit 0 = no rotation needed

Pre-commit hook:
    - id: diary-rotate
      entry: python scripts/diary_rotate.py
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

DIARY = Path("docs/diary.md")
DATE_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2}):")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def latest_entry_date(path: Path) -> date | None:
    """Extract the most recent ## YYYY-MM-DD: header date."""
    latest: date | None = None
    for line in path.read_text().splitlines():
        m = DATE_RE.match(line)
        if m:
            d = date.fromisoformat(m.group(1))
            if latest is None or d > latest:
                latest = d
    return latest


def entry_count(path: Path) -> int:
    """Count ## YYYY-MM-DD: headers."""
    return sum(1 for line in path.read_text().splitlines() if DATE_RE.match(line))


def one_line_summary(path: Path) -> str:
    """Build a short summary for the Previous: link."""
    n = entry_count(path)
    dates = set()
    for line in path.read_text().splitlines():
        m = DATE_RE.match(line)
        if m:
            dates.add(m.group(1))
    date_range = sorted(dates)
    if len(date_range) == 1:
        return f"{n} entries from {date_range[0]}"
    return f"{n} entries, {date_range[0]} to {date_range[-1]}"


def archive_path(entry_date: date) -> Path:
    """Return docs/diary-YYYY-MM-DD.md, appending -N if file exists."""
    base = Path(f"docs/diary-{entry_date.isoformat()}.md")
    if not base.exists():
        return base
    n = 1
    while True:
        candidate = Path(f"docs/diary-{entry_date.isoformat()}-{n}.md")
        if not candidate.exists():
            return candidate
        n += 1


def create_fresh_diary(prev_filename: str, prev_summary: str) -> None:
    """Write a new diary.md with header and Previous link."""
    DIARY.write_text(
        "# Development Diary\n"
        "\n"
        "Metacognitive reflections on development process.\n"
        "\n"
        f"Previous: [{prev_filename}]({prev_filename})"
        f" — {prev_summary}.\n"
        "\n"
        "---\n"
    )


def git_add(*paths: Path) -> None:
    """Stage files so the rotation is included in the current commit."""
    subprocess.run(  # noqa: S603
        ["git", "add", *(str(p) for p in paths)],
        check=True,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    if not DIARY.exists():
        return 0

    latest = latest_entry_date(DIARY)
    if latest is None:
        # No dated entries — nothing to rotate
        return 0

    today = date.today()
    if latest >= today:
        # Still the same day — no rotation needed
        return 0

    # --- Dry-run mode ---
    if "--check" in sys.argv:
        print(f"diary rotation needed: latest entry {latest}, today {today}")
        return 1

    # --- Rotate ---
    dest = archive_path(latest)
    summary = one_line_summary(DIARY)

    print(f"📓 Rotating diary: {DIARY} → {dest}")
    shutil.move(str(DIARY), str(dest))

    create_fresh_diary(dest.name, summary)
    print(f"📓 Created fresh {DIARY} (Previous: {dest.name})")

    git_add(dest, DIARY)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
