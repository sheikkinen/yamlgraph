#!/usr/bin/env python3
"""Import scheduled diary entries into docs/diary/ as individual files.

FR-134: Diary folder refactor — replaced monolithic diary.md rotation with
per-file imports. Each scheduled entry (world digest, git report) becomes
an individual file in docs/diary/.

Run standalone:
    python scripts/diary_rotate.py          # import pending entries

Pre-commit hook:
    - id: diary-rotate
      entry: python scripts/diary_rotate.py
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

DIARY_DIR = Path("docs/diary")
SCHEDULED_OUTPUTS = Path(os.path.expanduser("~/scheduled-yamlgraphs/outputs"))

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def git_add(*paths: Path) -> None:
    """Stage files so the import is included in the current commit."""
    subprocess.run(  # noqa: S603
        ["git", "add", *(str(p) for p in paths)],
        check=True,
    )


def import_scheduled_entries() -> int:
    """Import pending diary entries from ~/scheduled-yamlgraphs/outputs/.

    Converts World Digest format to diary entry format, writes as individual
    files to docs/diary/, and removes the processed source file.

    Returns count of imported entries.
    """
    if not SCHEDULED_OUTPUTS.exists():
        return 0

    imported = 0
    for entry_file in sorted(SCHEDULED_OUTPUTS.glob("diary_entry_*.md")):
        content = entry_file.read_text()

        # Extract date from filename: diary_entry_20260221.md → 2026-02-21
        match = re.search(r"diary_entry_(\d{4})(\d{2})(\d{2})\.md", entry_file.name)
        if not match:
            continue

        entry_date = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"

        # Skip if this date's World Digest already exists in diary folder
        target = DIARY_DIR / f"{entry_date}-world-digest.md"
        if target.exists():
            print(f"⏭️  Skipping {entry_file.name} (already in diary)")
            entry_file.unlink()
            continue

        # Convert format: "# World Digest — Theme" → "## YYYY-MM-DD: World Digest — Theme"
        # Remove "**Date:** YYYY-MM-DD" line
        lines = content.splitlines()
        converted_lines = []

        for line in lines:
            if line.startswith("# World Digest"):
                theme = line[len("# World Digest — ") :]
                converted_lines.append(f"## {entry_date}: World Digest — {theme}")
            elif line.startswith("**Date:**"):
                continue
            else:
                converted_lines.append(line)

        converted = "\n".join(converted_lines)

        # Write as individual file
        DIARY_DIR.mkdir(parents=True, exist_ok=True)
        target.write_text(converted.strip() + "\n")

        print(f"📥 Imported {entry_file.name} → {target}")
        entry_file.unlink()
        imported += 1

    return imported


def import_git_reports() -> int:
    """Import git reports from ~/scheduled-yamlgraphs/outputs/git_report/.

    Parses CLI output (text format), extracts report field,
    formats as diary entry, writes as individual file to docs/diary/,
    and renames processed files to .imported.

    Returns count of imported reports.
    """
    git_report_dir = SCHEDULED_OUTPUTS / "git_report"
    if not git_report_dir.exists():
        return 0

    imported = 0
    for report_file in sorted(git_report_dir.glob("report_*.txt")):
        content = report_file.read_text()

        # Extract date from filename: report_20260221_080000.txt → 2026-02-21
        match = re.search(r"report_(\d{4})(\d{2})(\d{2})_", report_file.name)
        if not match:
            continue

        entry_date = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"

        # Check if already in diary folder
        target = DIARY_DIR / f"{entry_date}-git-report.md"
        if target.exists():
            print(f"⏭️  Skipping {report_file.name} (already in diary)")
            report_file.rename(report_file.with_suffix(".imported"))
            continue

        # Extract report field from CLI output
        report_match = re.search(
            r'report:\s*title="([^"]*)".*?summary="([^"]*)".*?'
            r"key_findings=\[([^\]]*)\]",
            content,
            re.DOTALL,
        )

        if report_match:
            title = report_match.group(1)
            summary = report_match.group(2).replace("\\n", "\n")
            findings_raw = report_match.group(3)
            findings = re.findall(r"'([^']*)'", findings_raw)

            entry_lines = [
                f"## {entry_date}: Git Report — {title}",
                "",
                summary,
                "",
            ]

            if findings:
                entry_lines.append("**Key Findings:**")
                for finding in findings:
                    entry_lines.append(f"- {finding}")
                entry_lines.append("")
        else:
            # Fallback: extract analysis section
            analysis_match = re.search(
                r"analysis:\s*(.+?)(?=\n\s*report:|$)", content, re.DOTALL
            )
            if analysis_match:
                analysis = analysis_match.group(1).strip()
                entry_lines = [
                    f"## {entry_date}: Git Report",
                    "",
                    analysis[:2000],
                    "",
                ]
            else:
                print(f"⚠️  Could not parse report: {report_file.name}")
                continue

        entry = "\n".join(entry_lines)

        # Write as individual file
        DIARY_DIR.mkdir(parents=True, exist_ok=True)
        target.write_text(entry.strip() + "\n")

        print(f"📥 Imported git report {report_file.name} → {target}")
        report_file.rename(report_file.with_suffix(".imported"))
        imported += 1

    return imported


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    DIARY_DIR.mkdir(parents=True, exist_ok=True)

    # Import scheduled entries
    imported = import_scheduled_entries()
    imported += import_git_reports()
    if imported > 0:
        git_add(DIARY_DIR)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
