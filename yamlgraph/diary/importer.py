"""Shared diary import logic (FR-124).

Extracted from ``scripts/diary_rotate.py`` to enable both the pre-commit
hook and the ``yamlgraph diary import`` CLI command to share the same
import pipeline with structured results and dry-run support.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SOURCE = Path(os.path.expanduser("~/scheduled-yamlgraphs/outputs"))


@dataclass
class ImportResult:
    """Result of importing a single file."""

    filename: str
    entry_type: str  # "World Digest" | "Git Report"
    entry_date: str  # "YYYY-MM-DD"
    status: str  # "imported" | "skipped" | "error"
    message: str | None = None  # Error detail or skip reason


# ---------------------------------------------------------------------------
# Scheduled diary entries
# ---------------------------------------------------------------------------


def import_scheduled_entries(
    diary_dir: Path,
    source_dir: Path | None = None,
    *,
    dry_run: bool = False,
) -> list[ImportResult]:
    """Import pending diary entries from source directory.

    Globs ``{source_dir}/diary_entry_*.md``.  When *source_dir* is ``None``
    the default ``~/scheduled-yamlgraphs/outputs/`` is used.

    Each entry is written as an individual file to *diary_dir* following
    the ``{date}-world-digest.md`` naming convention.
    """
    source = source_dir if source_dir is not None else DEFAULT_SOURCE
    if not source.exists():
        return []

    results: list[ImportResult] = []
    for entry_file in sorted(source.glob("diary_entry_*.md")):
        match = re.search(r"diary_entry_(\d{4})(\d{2})(\d{2})\.md", entry_file.name)
        if not match:
            results.append(
                ImportResult(
                    filename=entry_file.name,
                    entry_type="World Digest",
                    entry_date="",
                    status="error",
                    message=f"Cannot parse date from filename: {entry_file.name}",
                )
            )
            continue

        entry_date = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
        target = diary_dir / f"{entry_date}-world-digest.md"

        if target.exists():
            if not dry_run:
                entry_file.unlink()
            results.append(
                ImportResult(
                    filename=entry_file.name,
                    entry_type="World Digest",
                    entry_date=entry_date,
                    status="skipped",
                    message="already in diary",
                )
            )
            continue

        if not dry_run:
            content = entry_file.read_text(encoding="utf-8")
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
            diary_dir.mkdir(parents=True, exist_ok=True)
            target.write_text(converted.strip() + "\n", encoding="utf-8")
            entry_file.unlink()

        results.append(
            ImportResult(
                filename=entry_file.name,
                entry_type="World Digest",
                entry_date=entry_date,
                status="imported",
            )
        )

    return results


# ---------------------------------------------------------------------------
# Git reports
# ---------------------------------------------------------------------------


def import_git_reports(
    diary_dir: Path,
    source_dir: Path | None = None,
    *,
    dry_run: bool = False,
) -> list[ImportResult]:
    """Import pending git reports from source directory.

    Globs ``{source_dir}/git_report/report_*.txt``.  When *source_dir*
    is ``None`` the default ``~/scheduled-yamlgraphs/outputs/`` is used.

    Each report is written as an individual file to *diary_dir* following
    the ``{date}-git-report.md`` naming convention.
    """
    source = source_dir if source_dir is not None else DEFAULT_SOURCE
    git_report_dir = source / "git_report"
    if not git_report_dir.exists():
        return []

    results: list[ImportResult] = []
    for report_file in sorted(git_report_dir.glob("report_*.txt")):
        match = re.search(r"report_(\d{4})(\d{2})(\d{2})_", report_file.name)
        if not match:
            results.append(
                ImportResult(
                    filename=report_file.name,
                    entry_type="Git Report",
                    entry_date="",
                    status="error",
                    message=f"Cannot parse date from filename: {report_file.name}",
                )
            )
            continue

        entry_date = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
        target = diary_dir / f"{entry_date}-git-report.md"

        if target.exists():
            if not dry_run:
                report_file.rename(report_file.with_suffix(".imported"))
            results.append(
                ImportResult(
                    filename=report_file.name,
                    entry_type="Git Report",
                    entry_date=entry_date,
                    status="skipped",
                    message="already in diary",
                )
            )
            continue

        content = report_file.read_text(encoding="utf-8")
        entry_lines = _parse_git_report(content, entry_date)

        if entry_lines is None:
            results.append(
                ImportResult(
                    filename=report_file.name,
                    entry_type="Git Report",
                    entry_date=entry_date,
                    status="error",
                    message=f"Could not parse report: {report_file.name}",
                )
            )
            continue

        if not dry_run:
            entry = "\n".join(entry_lines)
            diary_dir.mkdir(parents=True, exist_ok=True)
            target.write_text(entry.strip() + "\n", encoding="utf-8")
            report_file.rename(report_file.with_suffix(".imported"))

        results.append(
            ImportResult(
                filename=report_file.name,
                entry_type="Git Report",
                entry_date=entry_date,
                status="imported",
            )
        )

    return results


def _parse_git_report(content: str, entry_date: str) -> list[str] | None:
    """Parse git report content into diary entry lines.

    Returns ``None`` when the content cannot be parsed.
    """
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
        return entry_lines

    # Fallback: extract analysis section
    analysis_match = re.search(
        r"analysis:\s*(.+?)(?=\n\s*report:|$)", content, re.DOTALL
    )
    if analysis_match:
        analysis = analysis_match.group(1).strip()
        return [
            f"## {entry_date}: Git Report",
            "",
            analysis[:2000],
            "",
        ]

    return None
