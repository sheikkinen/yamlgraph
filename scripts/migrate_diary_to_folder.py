#!/usr/bin/env python3
"""Migrate docs/diary.md to docs/diary/ folder with individual entry files.

FR-134: One-time migration script that splits the monolithic diary.md into
date-prefixed individual files following the naming convention:
  YYYY-MM-DD-<type>-<id>.md

Usage:
    python scripts/migrate_diary_to_folder.py
    python scripts/migrate_diary_to_folder.py --dry-run
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

DATE_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2}):")
ROMAN_RE = re.compile(r"Audit\s+([IVXLCDM]+)", re.IGNORECASE)
FR_RE = re.compile(r"FR-(\d+)", re.IGNORECASE)

DIARY_FILE = Path("docs/diary.md")
DIARY_DIR = Path("docs/diary")


def extract_date(header: str) -> str | None:
    """Extract YYYY-MM-DD date from a ## header line."""
    m = DATE_RE.match(header)
    return m.group(1) if m else None


def infer_entry_type(header: str) -> tuple[str, str | None]:
    """Infer entry type and optional ID from header text.

    Returns:
        (entry_type, entry_id) where entry_id may be None.
    """
    text = header.split(":", 1)[1] if ":" in header else header

    if "Inquisitor Audit" in text:
        m = ROMAN_RE.search(text)
        entry_id = m.group(1).lower() if m else None
        return "inquisitor-audit", entry_id

    if "Implementation Reflection" in text or FR_RE.search(text):
        m = FR_RE.search(text)
        entry_id = f"fr-{m.group(1)}" if m else None
        return "reflection", entry_id

    if "World Digest" in text:
        return "world-digest", None

    if "Git Report" in text:
        return "git-report", None

    return "digest", None


def split_diary(path: Path) -> list[str]:
    """Split diary.md into individual entries by --- separator.

    Skips the file header (everything before the first ## entry).
    """
    content = path.read_text()
    blocks = re.split(r"\n---\n", content)

    entries = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        # Only keep blocks that start with a dated ## header
        if DATE_RE.match(block):
            entries.append(block)

    return entries


def make_filename(date_str: str, entry_type: str, entry_id: str | None) -> str:
    """Build filename from date, type, and optional ID."""
    parts = [date_str, entry_type]
    if entry_id:
        parts.append(entry_id)
    return "-".join(parts) + ".md"


def migrate(diary_path: Path, out_dir: Path, *, dry_run: bool = False) -> int:
    """Migrate diary.md entries to individual files in out_dir.

    Returns count of files created.
    """
    entries = split_diary(diary_path)
    used_names: dict[str, int] = {}
    count = 0

    for entry in entries:
        first_line = entry.split("\n", 1)[0]
        date_str = extract_date(first_line)
        if not date_str:
            continue

        entry_type, entry_id = infer_entry_type(first_line)
        filename = make_filename(date_str, entry_type, entry_id)

        # Handle duplicates
        if filename in used_names:
            used_names[filename] += 1
            stem = filename[:-3]  # Remove .md
            filename = f"{stem}-{used_names[filename]}.md"
        else:
            used_names[filename] = 0

        if dry_run:
            print(f"  Would create: {out_dir / filename}")
        else:
            (out_dir / filename).write_text(entry + "\n")
            print(f"  Created: {out_dir / filename}")
        count += 1

    return count


def main() -> int:
    dry_run = "--dry-run" in sys.argv

    if not DIARY_FILE.exists():
        print(f"❌ {DIARY_FILE} not found")
        return 1

    DIARY_DIR.mkdir(parents=True, exist_ok=True)

    print(f"📓 Migrating {DIARY_FILE} → {DIARY_DIR}/")
    count = migrate(DIARY_FILE, DIARY_DIR, dry_run=dry_run)
    print(f"✅ {count} entries {'would be ' if dry_run else ''}migrated")

    if not dry_run:
        print(f"\nRemove {DIARY_FILE} manually after verifying migration.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
