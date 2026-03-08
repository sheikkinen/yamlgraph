"""Tests for yamlgraph.cli.diary_commands — diary CLI command.

FR-124: Diary Import CLI Command — tests for the CLI surface including
dry-run, missing directory warning, and error exit codes.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from yamlgraph.cli import create_parser
from yamlgraph.cli.diary_commands import cmd_diary_import

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

DIARY_ENTRY_CONTENT = """\
# World Digest — Test Theme
**Date:** 2026-03-07

Content here.
"""

GIT_REPORT_CONTENT = """\
analysis: Some analysis text
report: title="Test Report" summary="Summary" key_findings=['Finding 1']
"""


def _make_args(*, dry_run: bool = False, source: str | None = None):
    """Build a minimal Namespace matching the diary import CLI args."""
    parser = create_parser()
    argv = ["diary", "import"]
    if dry_run:
        argv.append("--dry-run")
    if source:
        argv.extend(["--source", source])
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# CLI parser tests
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-122")
class TestDiaryCliParser:
    """Tests for diary CLI argument parsing."""

    def test_diary_import_parsed(self) -> None:
        """'diary import' should parse to correct command and defaults."""
        parser = create_parser()
        args = parser.parse_args(["diary", "import"])
        assert args.command == "diary"
        assert args.diary_command == "import"
        assert args.dry_run is False
        assert args.source is None

    def test_diary_import_dry_run_flag(self) -> None:
        """'--dry-run' flag should be captured."""
        parser = create_parser()
        args = parser.parse_args(["diary", "import", "--dry-run"])
        assert args.dry_run is True

    def test_diary_import_source_flag(self) -> None:
        """'--source' flag should capture the path."""
        parser = create_parser()
        args = parser.parse_args(["diary", "import", "--source", "/tmp/test"])
        assert args.source == "/tmp/test"


# ---------------------------------------------------------------------------
# cmd_diary_import tests
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-122")
class TestCmdDiaryImport:
    """Tests for cmd_diary_import() handler."""

    def test_imports_pending_entries(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Should import files and print success summary."""
        source = tmp_path / "outputs"
        source.mkdir()
        (source / "diary_entry_20260307.md").write_text(DIARY_ENTRY_CONTENT)

        diary_dir = tmp_path / "diary"
        diary_dir.mkdir()

        args = _make_args(source=str(source))
        monkeypatch.chdir(tmp_path)
        # diary_dir is relative "docs/diary" — create it in the monkeypatched cwd
        (tmp_path / "docs" / "diary").mkdir(parents=True)

        args = _make_args(source=str(source))
        cmd_diary_import(args)

        out = capsys.readouterr().out
        assert "Imported" in out
        assert "1 file(s) imported" in out

    def test_dry_run_lists_pending(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Dry-run should list pending files and not import."""
        source = tmp_path / "outputs"
        source.mkdir()
        (source / "diary_entry_20260307.md").write_text(DIARY_ENTRY_CONTENT)

        monkeypatch.chdir(tmp_path)
        (tmp_path / "docs" / "diary").mkdir(parents=True)

        args = _make_args(dry_run=True, source=str(source))
        cmd_diary_import(args)

        out = capsys.readouterr().out
        assert "Pending" in out or "📋" in out
        assert "ready to import" in out
        # Source file not deleted
        assert (source / "diary_entry_20260307.md").exists()

    def test_nothing_to_import(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """No pending files should print 'Nothing to import'."""
        source = tmp_path / "outputs"
        source.mkdir()

        monkeypatch.chdir(tmp_path)
        (tmp_path / "docs" / "diary").mkdir(parents=True)

        args = _make_args(source=str(source))
        cmd_diary_import(args)

        out = capsys.readouterr().out
        assert "Nothing to import" in out

    def test_missing_default_source_exits_cleanly(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Missing default source dir should print 'Nothing to import' and not crash."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "docs" / "diary").mkdir(parents=True)

        # source=None → defaults to ~/scheduled-yamlgraphs/outputs/ which won't exist
        args = _make_args()
        cmd_diary_import(args)

        out = capsys.readouterr().out
        assert "Nothing to import" in out

    def test_explicit_missing_source_warns(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Explicit --source with nonexistent path should emit warning."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "docs" / "diary").mkdir(parents=True)

        args = _make_args(source=str(tmp_path / "nonexistent"))
        cmd_diary_import(args)

        out = capsys.readouterr().out
        assert "not found" in out.lower() or "⚠" in out
        assert "Nothing to import" in out

    def test_malformed_file_exits_nonzero(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Malformed file should cause non-zero exit."""
        source = tmp_path / "outputs"
        source.mkdir()
        (source / "diary_entry_baddate.md").write_text("Bad content\n")

        monkeypatch.chdir(tmp_path)
        (tmp_path / "docs" / "diary").mkdir(parents=True)

        args = _make_args(source=str(source))
        with pytest.raises(SystemExit) as exc_info:
            cmd_diary_import(args)
        assert exc_info.value.code == 1
