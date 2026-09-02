"""Tests for yamlgraph.diary.importer — shared diary import logic.

FR-124: Diary Import CLI Command — extract import logic from diary_rotate.py
into a reusable module with structured results and dry-run support.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from yamlgraph.diary import importer
from yamlgraph.diary.importer import (
    ImportResult,
    import_git_reports,
    import_scheduled_entries,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

DIARY_ENTRY_CONTENT = """\
# World Digest — Test Theme
**Date:** 2026-02-17

Content here.
"""

GIT_REPORT_CONTENT = """\
analysis: Some analysis text
report: title="Test Report" summary="This is a summary" key_findings=['Finding 1', 'Finding 2']
"""


@pytest.fixture()
def source_dir(tmp_path: Path) -> Path:
    """Create a source directory with sample files."""
    source = tmp_path / "outputs"
    source.mkdir()
    return source


@pytest.fixture()
def diary_dir(tmp_path: Path) -> Path:
    """Create a diary target directory."""
    d = tmp_path / "diary"
    d.mkdir()
    return d


# ---------------------------------------------------------------------------
# import_scheduled_entries
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-122")
class TestImportScheduledEntries:
    """Tests for import_scheduled_entries() with structured results."""

    def test_imports_entry_and_returns_result(
        self, source_dir: Path, diary_dir: Path
    ) -> None:
        """Should import entry, delete source, return ImportResult with status='imported'."""
        entry = source_dir / "diary_entry_20260217.md"
        entry.write_text(DIARY_ENTRY_CONTENT, encoding="utf-8")

        results = import_scheduled_entries(diary_dir, source_dir)

        assert len(results) == 1
        r = results[0]
        assert isinstance(r, ImportResult)
        assert r.filename == "diary_entry_20260217.md"
        assert r.entry_type == "World Digest"
        assert r.entry_date == "2026-02-17"
        assert r.status == "imported"

        # Source deleted, target created
        assert not entry.exists()
        target = diary_dir / "2026-02-17-world-digest.md"
        assert target.exists()
        content = target.read_text(encoding="utf-8")
        assert "## 2026-02-17: World Digest — Test Theme" in content
        assert "Content here." in content

    def test_missing_source_dir_returns_empty(self, diary_dir: Path) -> None:
        """Missing source directory returns empty list."""
        results = import_scheduled_entries(diary_dir, Path("/nonexistent"))
        assert results == []

    def test_default_source_dir(
        self, diary_dir: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """When source_dir is None, uses ~/scheduled-yamlgraphs/outputs/."""
        # Force deterministic default source regardless of host HOME contents.
        monkeypatch.setattr(importer, "DEFAULT_SOURCE", tmp_path / "missing-default")
        results = import_scheduled_entries(diary_dir)
        assert results == []

    def test_skips_duplicate_entry(self, source_dir: Path, diary_dir: Path) -> None:
        """Should skip if target file already exists."""
        entry = source_dir / "diary_entry_20260217.md"
        entry.write_text(DIARY_ENTRY_CONTENT, encoding="utf-8")
        (diary_dir / "2026-02-17-world-digest.md").write_text("Already exists\n", encoding="utf-8")

        results = import_scheduled_entries(diary_dir, source_dir)

        assert len(results) == 1
        assert results[0].status == "skipped"
        assert "already" in results[0].message.lower()

    def test_dry_run_does_not_delete_source(
        self, source_dir: Path, diary_dir: Path
    ) -> None:
        """Dry-run must not delete, rename, or write anything."""
        entry = source_dir / "diary_entry_20260217.md"
        entry.write_text(DIARY_ENTRY_CONTENT, encoding="utf-8")

        results = import_scheduled_entries(diary_dir, source_dir, dry_run=True)

        assert len(results) == 1
        assert results[0].status == "imported"
        # Source NOT deleted
        assert entry.exists()
        # Target NOT created
        assert not (diary_dir / "2026-02-17-world-digest.md").exists()

    def test_malformed_filename_returns_error(
        self, source_dir: Path, diary_dir: Path
    ) -> None:
        """File matching glob but with bad date should return error result."""
        bad = source_dir / "diary_entry_baddate.md"
        bad.write_text("Some content\n", encoding="utf-8")

        results = import_scheduled_entries(diary_dir, source_dir)

        assert len(results) == 1
        assert results[0].status == "error"
        assert results[0].message is not None


# ---------------------------------------------------------------------------
# import_git_reports
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-122")
class TestImportGitReports:
    """Tests for import_git_reports() with structured results."""

    def test_imports_report_and_returns_result(
        self, source_dir: Path, diary_dir: Path
    ) -> None:
        """Should import report, rename source to .imported, return ImportResult."""
        git_dir = source_dir / "git_report"
        git_dir.mkdir()
        report = git_dir / "report_20260218_080000.txt"
        report.write_text(GIT_REPORT_CONTENT, encoding="utf-8")

        results = import_git_reports(diary_dir, source_dir)

        assert len(results) == 1
        r = results[0]
        assert r.filename == "report_20260218_080000.txt"
        assert r.entry_type == "Git Report"
        assert r.entry_date == "2026-02-18"
        assert r.status == "imported"

        # Source renamed, target created
        assert report.with_suffix(".imported").exists()
        target = diary_dir / "2026-02-18-git-report.md"
        assert target.exists()
        content = target.read_text(encoding="utf-8")
        assert "## 2026-02-18: Git Report — Test Report" in content
        assert "This is a summary" in content

    def test_missing_git_report_dir_returns_empty(
        self, source_dir: Path, diary_dir: Path
    ) -> None:
        """Missing git_report subdirectory returns empty list."""
        results = import_git_reports(diary_dir, source_dir)
        assert results == []

    def test_skips_duplicate_report(self, source_dir: Path, diary_dir: Path) -> None:
        """Should skip if target file already exists."""
        git_dir = source_dir / "git_report"
        git_dir.mkdir()
        report = git_dir / "report_20260218_080000.txt"
        report.write_text(GIT_REPORT_CONTENT, encoding="utf-8")
        (diary_dir / "2026-02-18-git-report.md").write_text("Already exists\n", encoding="utf-8")

        results = import_git_reports(diary_dir, source_dir)

        assert len(results) == 1
        assert results[0].status == "skipped"

    def test_dry_run_does_not_rename_source(
        self, source_dir: Path, diary_dir: Path
    ) -> None:
        """Dry-run must not rename source or write target."""
        git_dir = source_dir / "git_report"
        git_dir.mkdir()
        report = git_dir / "report_20260218_080000.txt"
        report.write_text(GIT_REPORT_CONTENT, encoding="utf-8")

        results = import_git_reports(diary_dir, source_dir, dry_run=True)

        assert len(results) == 1
        assert results[0].status == "imported"
        # Source NOT renamed
        assert report.exists()
        assert not report.with_suffix(".imported").exists()
        # Target NOT created
        assert not (diary_dir / "2026-02-18-git-report.md").exists()

    def test_unparseable_report_returns_error(
        self, source_dir: Path, diary_dir: Path
    ) -> None:
        """Report that can't be parsed should return error result."""
        git_dir = source_dir / "git_report"
        git_dir.mkdir()
        report = git_dir / "report_20260218_080000.txt"
        report.write_text("totally unparseable garbage\n", encoding="utf-8")

        results = import_git_reports(diary_dir, source_dir)

        assert len(results) == 1
        assert results[0].status == "error"
        assert results[0].message is not None
