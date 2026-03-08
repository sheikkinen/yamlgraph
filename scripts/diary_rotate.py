#!/usr/bin/env python3
"""Import scheduled diary entries into docs/diary/ as individual files.

FR-134: Diary folder refactor — replaced monolithic diary.md rotation with
per-file imports. Each scheduled entry (world digest, git report) becomes
an individual file in docs/diary/.

FR-124: Import logic extracted to yamlgraph.diary.importer; this script
is now a thin wrapper for the pre-commit hook.

Run standalone:
    python scripts/diary_rotate.py          # import pending entries

Pre-commit hook:
    - id: diary-rotate
      entry: python scripts/diary_rotate.py
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from yamlgraph.diary.importer import import_git_reports, import_scheduled_entries

DIARY_DIR = Path("docs/diary")
SCHEDULED_OUTPUTS = Path("~/scheduled-yamlgraphs/outputs").expanduser()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def git_add(*paths: Path) -> None:
    """Stage files so the import is included in the current commit."""
    subprocess.run(  # noqa: S603
        ["git", "add", *(str(p) for p in paths)],
        check=True,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    DIARY_DIR.mkdir(parents=True, exist_ok=True)

    results = import_scheduled_entries(DIARY_DIR, SCHEDULED_OUTPUTS)
    results += import_git_reports(DIARY_DIR, SCHEDULED_OUTPUTS)
    imported = sum(1 for r in results if r.status == "imported")

    if imported > 0:
        git_add(DIARY_DIR)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
