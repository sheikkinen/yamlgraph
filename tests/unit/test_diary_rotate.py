"""Tests for scripts/diary_rotate.py — diary import to folder.

FR-080: Infrastructure Script Unit Tests — Phase 3 (diary_rotate).
FR-134: Diary folder refactor — individual files, no rotation.
FR-124: Import logic extracted to yamlgraph.diary.importer; script is thin wrapper.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from scripts import diary_rotate
from yamlgraph.diary import importer


@pytest.mark.req("REQ-YG-063")
class TestImportScheduledEntries:
    """Tests for import_scheduled_entries() via shared importer."""

    def test_conversion_creates_individual_file(self, tmp_path: Path) -> None:
        """Should create an individual diary file for each imported entry."""
        outputs = tmp_path / "outputs"
        outputs.mkdir()
        entry_file = outputs / "diary_entry_20260217.md"
        entry_file.write_text("""\
# World Digest — Test Theme
**Date:** 2026-02-17

Content here.
""")

        diary_dir = tmp_path / "diary"
        diary_dir.mkdir()

        results = importer.import_scheduled_entries(diary_dir, outputs)

        assert len(results) == 1
        assert results[0].status == "imported"
        assert not entry_file.exists()  # Should be deleted
        expected_file = diary_dir / "2026-02-17-world-digest.md"
        assert expected_file.exists()
        content = expected_file.read_text()
        assert "## 2026-02-17: World Digest — Test Theme" in content
        assert "Content here." in content

    def test_missing_outputs_dir(self) -> None:
        """Missing outputs directory should return empty list."""
        results = importer.import_scheduled_entries(
            Path("/tmp/diary"), Path("/nonexistent")
        )
        assert results == []

    def test_skip_duplicate_entry(self, tmp_path: Path) -> None:
        """Should skip if diary file for that date/type already exists."""
        outputs = tmp_path / "outputs"
        outputs.mkdir()
        entry_file = outputs / "diary_entry_20260217.md"
        entry_file.write_text("""\
# World Digest — Test Theme
**Date:** 2026-02-17

Content here.
""")

        diary_dir = tmp_path / "diary"
        diary_dir.mkdir()
        # Pre-existing file
        (diary_dir / "2026-02-17-world-digest.md").write_text("Already exists\n")

        results = importer.import_scheduled_entries(diary_dir, outputs)

        assert len(results) == 1
        assert results[0].status == "skipped"


@pytest.mark.req("REQ-YG-063")
class TestImportGitReports:
    """Tests for import_git_reports() via shared importer."""

    def test_parsing_creates_individual_file(self, tmp_path: Path) -> None:
        """Should create an individual diary file for each imported report."""
        outputs = tmp_path / "outputs"
        git_report_dir = outputs / "git_report"
        git_report_dir.mkdir(parents=True)

        report_file = git_report_dir / "report_20260218_080000.txt"
        report_file.write_text("""\
analysis: Some analysis text
report: title="Test Report" summary="This is a summary" key_findings=['Finding 1', 'Finding 2']
""")

        diary_dir = tmp_path / "diary"
        diary_dir.mkdir()

        results = importer.import_git_reports(diary_dir, outputs)

        assert len(results) == 1
        assert results[0].status == "imported"
        assert report_file.with_suffix(".imported").exists()
        expected_file = diary_dir / "2026-02-18-git-report.md"
        assert expected_file.exists()
        content = expected_file.read_text()
        assert "## 2026-02-18: Git Report — Test Report" in content
        assert "This is a summary" in content
        assert "Finding 1" in content

    def test_missing_git_report_dir(self, tmp_path: Path) -> None:
        """Missing git_report directory should return empty list."""
        outputs = tmp_path / "outputs"
        outputs.mkdir()

        results = importer.import_git_reports(
            diary_dir=Path("/tmp/diary"), source_dir=outputs
        )
        assert results == []


@pytest.mark.req("REQ-YG-063")
class TestMain:
    """Tests for main() function."""

    def test_no_scheduled_outputs_returns_zero(self, tmp_path: Path) -> None:
        """Missing scheduled outputs should return 0."""
        diary_dir = tmp_path / "diary"
        diary_dir.mkdir()

        with (
            patch.object(diary_rotate, "DIARY_DIR", diary_dir),
            patch.object(diary_rotate, "SCHEDULED_OUTPUTS", tmp_path / "nonexistent"),
        ):
            exit_code = diary_rotate.main()

        assert exit_code == 0
