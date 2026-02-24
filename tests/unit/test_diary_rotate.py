"""Tests for scripts/diary_rotate.py — diary rotation and import.

FR-080: Infrastructure Script Unit Tests — Phase 3 (diary_rotate).
"""

from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts import diary_rotate


@pytest.mark.req("REQ-YG-063")
class TestLatestEntryDate:
    """Tests for latest_entry_date() function."""

    def test_parses_header(self, tmp_path: Path) -> None:
        """Should parse ## YYYY-MM-DD: header format."""
        diary = tmp_path / "diary.md"
        diary.write_text("# Diary\n\n## 2026-02-17: Entry\nContent\n")

        result = diary_rotate.latest_entry_date(diary)

        assert result == date(2026, 2, 17)

    def test_returns_most_recent(self, tmp_path: Path) -> None:
        """Should return the most recent date from multiple entries."""
        diary = tmp_path / "diary.md"
        diary.write_text("""\
# Diary

## 2026-02-15: Older
Content

## 2026-02-18: Newest
Content

## 2026-02-16: Middle
Content
""")

        result = diary_rotate.latest_entry_date(diary)

        assert result == date(2026, 2, 18)

    def test_no_entries_returns_none(self, tmp_path: Path) -> None:
        """Should return None when no dated entries exist."""
        diary = tmp_path / "diary.md"
        diary.write_text("# Diary\n\nNo dated entries here.\n")

        result = diary_rotate.latest_entry_date(diary)

        assert result is None


@pytest.mark.req("REQ-YG-063")
class TestEntryCount:
    """Tests for entry_count() function."""

    def test_counts_headers(self, tmp_path: Path) -> None:
        """Should count all ## YYYY-MM-DD: headers."""
        diary = tmp_path / "diary.md"
        diary.write_text("""\
# Diary

## 2026-02-17: First
Content

## 2026-02-18: Second
Content

## 2026-02-19: Third
Content
""")

        count = diary_rotate.entry_count(diary)

        assert count == 3


@pytest.mark.req("REQ-YG-063")
class TestOneLineSummary:
    """Tests for one_line_summary() function."""

    def test_single_date(self, tmp_path: Path) -> None:
        """Single date should show 'N entries from YYYY-MM-DD'."""
        diary = tmp_path / "diary.md"
        diary.write_text("""\
# Diary

## 2026-02-17: Entry 1
Content

## 2026-02-17: Entry 2
Content
""")

        summary = diary_rotate.one_line_summary(diary)

        assert summary == "2 entries from 2026-02-17"

    def test_date_range(self, tmp_path: Path) -> None:
        """Multiple dates should show 'N entries, from to'."""
        diary = tmp_path / "diary.md"
        diary.write_text("""\
# Diary

## 2026-02-15: Entry 1
Content

## 2026-02-18: Entry 2
Content
""")

        summary = diary_rotate.one_line_summary(diary)

        assert summary == "2 entries, 2026-02-15 to 2026-02-18"


@pytest.mark.req("REQ-YG-063")
class TestArchivePath:
    """Tests for archive_path() function."""

    def test_no_conflict(self, tmp_path: Path) -> None:
        """Should return diary-YYYY-MM-DD.md when no conflict."""
        with patch.object(diary_rotate.Path, "exists", return_value=False):
            result = diary_rotate.archive_path(date(2026, 2, 17))

        assert result == Path("docs/diary-2026-02-17.md")

    def test_with_suffix(self, tmp_path: Path) -> None:
        """Should add -N suffix when file exists."""
        call_count = [0]

        def exists_side_effect(self: Path) -> bool:
            call_count[0] += 1
            # First call: base file exists
            # Second call: -1 suffix also exists
            # Third call: -2 suffix doesn't exist
            return call_count[0] <= 2

        with patch.object(Path, "exists", exists_side_effect):
            result = diary_rotate.archive_path(date(2026, 2, 17))

        assert result == Path("docs/diary-2026-02-17-2.md")


@pytest.mark.req("REQ-YG-063")
class TestCreateFreshDiary:
    """Tests for create_fresh_diary() function."""

    def test_content(self, tmp_path: Path) -> None:
        """Fresh diary should have header, Previous link, and separator."""
        diary = tmp_path / "diary.md"

        with patch.object(diary_rotate, "DIARY", diary):
            diary_rotate.create_fresh_diary(
                "diary-2026-02-17.md", "5 entries from 2026-02-17"
            )

        content = diary.read_text()
        assert "# Development Diary" in content
        assert "Previous: [diary-2026-02-17.md](diary-2026-02-17.md)" in content
        assert "5 entries from 2026-02-17" in content
        assert "---" in content


@pytest.mark.req("REQ-YG-063")
class TestMain:
    """Tests for main() function."""

    def test_no_diary_returns_zero(self, tmp_path: Path) -> None:
        """Missing diary.md should return 0."""
        diary = tmp_path / "diary.md"
        # Don't create the file

        with patch.object(diary_rotate, "DIARY", diary):
            exit_code = diary_rotate.main()

        assert exit_code == 0

    def test_check_mode_no_rotation(self, tmp_path: Path) -> None:
        """--check should return 0 when no rotation needed (today's date)."""
        diary = tmp_path / "diary.md"
        today = date.today()
        diary.write_text(f"# Diary\n\n## {today.isoformat()}: Today\nContent\n")

        with (
            patch.object(diary_rotate, "DIARY", diary),
            patch.object(diary_rotate.sys, "argv", ["diary_rotate.py", "--check"]),
        ):
            exit_code = diary_rotate.main()

        assert exit_code == 0

    def test_check_mode_rotation_needed(self, tmp_path: Path) -> None:
        """--check should return 1 when rotation needed (old date)."""
        diary = tmp_path / "diary.md"
        diary.write_text("# Diary\n\n## 2020-01-01: Old\nContent\n")

        with (
            patch.object(diary_rotate, "DIARY", diary),
            patch.object(diary_rotate.sys, "argv", ["diary_rotate.py", "--check"]),
        ):
            exit_code = diary_rotate.main()

        assert exit_code == 1

    def test_rotation_moves_file(self, tmp_path: Path) -> None:
        """Rotation should move diary.md to archived name."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        diary = docs_dir / "diary.md"
        diary.write_text("# Diary\n\n## 2020-01-01: Old\nContent\n")
        archive = docs_dir / "diary-2020-01-01.md"

        with (
            patch.object(diary_rotate, "DIARY", diary),
            patch.object(diary_rotate, "SCHEDULED_OUTPUTS", tmp_path / "outputs"),
            patch.object(diary_rotate.sys, "argv", ["diary_rotate.py"]),
            patch.object(diary_rotate, "git_add"),  # Mock git_add
            patch.object(diary_rotate, "archive_path", return_value=archive),
        ):
            exit_code = diary_rotate.main()

        assert exit_code == 0
        # Original diary should be renamed to archive
        assert archive.exists()
        # New diary should be created
        assert diary.exists()
        assert "Previous:" in diary.read_text()


@pytest.mark.req("REQ-YG-063")
class TestImportScheduledEntries:
    """Tests for import_scheduled_entries() function."""

    def test_conversion(self, tmp_path: Path) -> None:
        """Should convert World Digest format to diary entry format."""
        # Setup scheduled outputs directory
        outputs = tmp_path / "outputs"
        outputs.mkdir()
        entry_file = outputs / "diary_entry_20260217.md"
        entry_file.write_text("""\
# World Digest — Test Theme
**Date:** 2026-02-17

Content here.
""")

        diary = tmp_path / "diary.md"
        diary.write_text("# Diary\n")

        with (
            patch.object(diary_rotate, "SCHEDULED_OUTPUTS", outputs),
            patch.object(diary_rotate, "DIARY", diary),
        ):
            imported = diary_rotate.import_scheduled_entries()

        assert imported == 1
        assert not entry_file.exists()  # Should be deleted
        content = diary.read_text()
        assert "## 2026-02-17: World Digest — Test Theme" in content
        assert "Content here." in content

    def test_missing_outputs_dir(self, tmp_path: Path) -> None:
        """Missing outputs directory should return 0."""
        outputs = tmp_path / "nonexistent"

        with patch.object(diary_rotate, "SCHEDULED_OUTPUTS", outputs):
            imported = diary_rotate.import_scheduled_entries()

        assert imported == 0


@pytest.mark.req("REQ-YG-063")
class TestImportGitReports:
    """Tests for import_git_reports() function."""

    def test_parsing(self, tmp_path: Path) -> None:
        """Should parse CLI output format and extract report."""
        # Setup git_report directory
        outputs = tmp_path / "outputs"
        git_report_dir = outputs / "git_report"
        git_report_dir.mkdir(parents=True)

        report_file = git_report_dir / "report_20260218_080000.txt"
        report_file.write_text("""\
analysis: Some analysis text
report: title="Test Report" summary="This is a summary" key_findings=['Finding 1', 'Finding 2']
""")

        diary = tmp_path / "diary.md"
        diary.write_text("# Diary\n")

        with (
            patch.object(diary_rotate, "SCHEDULED_OUTPUTS", outputs),
            patch.object(diary_rotate, "DIARY", diary),
        ):
            imported = diary_rotate.import_git_reports()

        assert imported == 1
        assert report_file.with_suffix(".imported").exists()
        content = diary.read_text()
        assert "## 2026-02-18: Git Report — Test Report" in content
        assert "This is a summary" in content
        assert "Finding 1" in content

    def test_missing_git_report_dir(self, tmp_path: Path) -> None:
        """Missing git_report directory should return 0."""
        outputs = tmp_path / "outputs"
        outputs.mkdir()
        # Don't create git_report subdirectory

        with patch.object(diary_rotate, "SCHEDULED_OUTPUTS", outputs):
            imported = diary_rotate.import_git_reports()

        assert imported == 0
