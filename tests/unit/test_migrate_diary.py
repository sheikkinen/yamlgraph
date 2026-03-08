"""Tests for scripts/migrate_diary_to_folder.py — diary migration.

FR-134: Diary folder refactor — split monolithic diary.md into individual files.
"""

from pathlib import Path

import pytest

from scripts import migrate_diary_to_folder


@pytest.mark.req("REQ-YG-063")
class TestInferEntryType:
    """Tests for infer_entry_type() — classifies diary entry headers."""

    def test_inquisitor_audit(self) -> None:
        header = "## 2026-03-07: Inquisitor Audit XXIII — summary"
        entry_type, entry_id = migrate_diary_to_folder.infer_entry_type(header)
        assert entry_type == "inquisitor-audit"
        assert entry_id == "xxiii"

    def test_reflection_with_fr(self) -> None:
        header = "## 2026-03-07: FR-125 — Implementation Reflection"
        entry_type, entry_id = migrate_diary_to_folder.infer_entry_type(header)
        assert entry_type == "reflection"
        assert entry_id == "fr-125"

    def test_world_digest(self) -> None:
        header = "## 2026-03-08: World Digest — AI Developments"
        entry_type, entry_id = migrate_diary_to_folder.infer_entry_type(header)
        assert entry_type == "world-digest"
        assert entry_id is None

    def test_git_report(self) -> None:
        header = "## 2026-03-08: Git Report — Weekly Summary"
        entry_type, entry_id = migrate_diary_to_folder.infer_entry_type(header)
        assert entry_type == "git-report"
        assert entry_id is None

    def test_default_digest(self) -> None:
        header = "## 2026-03-08: Some Random Entry"
        entry_type, entry_id = migrate_diary_to_folder.infer_entry_type(header)
        assert entry_type == "digest"
        assert entry_id is None


@pytest.mark.req("REQ-YG-063")
class TestExtractDate:
    """Tests for extract_date() — extracts date from entry header."""

    def test_standard_format(self) -> None:
        header = "## 2026-03-07: Inquisitor Audit XXIII"
        assert migrate_diary_to_folder.extract_date(header) == "2026-03-07"

    def test_no_date_returns_none(self) -> None:
        header = "## No Date Here"
        assert migrate_diary_to_folder.extract_date(header) is None


@pytest.mark.req("REQ-YG-063")
class TestSplitDiary:
    """Tests for split_diary() — splits monolithic diary into entries."""

    def test_splits_by_separator(self, tmp_path: Path) -> None:
        """Entries separated by --- are split correctly."""
        diary = tmp_path / "diary.md"
        diary.write_text(
            "# Development Diary\n\nHeader text.\n\n---\n\n"
            "## 2026-03-07: Inquisitor Audit XXIII — summary\n\nContent 1.\n\n---\n\n"
            "## 2026-03-06: FR-125 — Implementation Reflection\n\nContent 2.\n"
        )
        entries = migrate_diary_to_folder.split_diary(diary)
        assert len(entries) == 2

    def test_extracts_content(self, tmp_path: Path) -> None:
        """Each entry contains its full content."""
        diary = tmp_path / "diary.md"
        diary.write_text(
            "# Diary\n\n---\n\n"
            "## 2026-03-07: World Digest — Theme\n\nBody text.\n\n"
            "**Seed:** Question?\n"
        )
        entries = migrate_diary_to_folder.split_diary(diary)
        assert len(entries) == 1
        assert "Body text." in entries[0]
        assert "**Seed:** Question?" in entries[0]


@pytest.mark.req("REQ-YG-063")
class TestMigrate:
    """Tests for migrate() — full migration from diary.md to diary/."""

    def test_creates_individual_files(self, tmp_path: Path) -> None:
        """Migration creates one file per entry."""
        diary = tmp_path / "diary.md"
        diary.write_text(
            "# Development Diary\n\n---\n\n"
            "## 2026-03-07: Inquisitor Audit XXIII — summary\n\n"
            "**Context:** commits `aaa1111`..`bbb2222`\n\n---\n\n"
            "## 2026-03-06: FR-125 — Implementation Reflection\n\nReflection.\n"
        )
        out_dir = tmp_path / "diary"
        out_dir.mkdir()

        count = migrate_diary_to_folder.migrate(diary, out_dir)

        assert count == 2
        assert (out_dir / "2026-03-07-inquisitor-audit-xxiii.md").exists()
        assert (out_dir / "2026-03-06-reflection-fr-125.md").exists()

    def test_duplicate_handling(self, tmp_path: Path) -> None:
        """Duplicate filenames get -N suffix."""
        diary = tmp_path / "diary.md"
        diary.write_text(
            "# Diary\n\n---\n\n"
            "## 2026-03-07: World Digest — Theme A\n\nContent A.\n\n---\n\n"
            "## 2026-03-07: World Digest — Theme B\n\nContent B.\n"
        )
        out_dir = tmp_path / "diary"
        out_dir.mkdir()

        count = migrate_diary_to_folder.migrate(diary, out_dir)

        assert count == 2
        assert (out_dir / "2026-03-07-world-digest.md").exists()
        assert (out_dir / "2026-03-07-world-digest-1.md").exists()
