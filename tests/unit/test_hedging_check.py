"""Tests for scripts/hedging_check.py — silent-fallback hedging detector.

FR-080: Infrastructure Script Unit Tests — Phase 1 (hedging_check).
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from scripts import hedging_check


@pytest.mark.req("REQ-YG-063")
class TestScanFile:
    """Tests for scan_file() function."""

    def test_detects_if_not_x_reassign(self, tmp_path: Path) -> None:
        """Pattern 1: `if not X: X = Y` should be detected."""
        code = """\
result = filter_data(items)
if not result:
    result = all_items  # reviewed branch
"""
        py_file = tmp_path / "fallback.py"
        py_file.write_text(code)

        findings = hedging_check.scan_file(py_file)

        assert len(findings) == 1
        assert "if not result: result = ..." in findings[0]
        assert "Commandment 6" in findings[0]

    def test_ignores_different_variable(self, tmp_path: Path) -> None:
        """Non-matching pattern: different variable names should not trigger."""
        code = """\
result = filter_data(items)
if not result:
    other = all_items  # assigns different var
"""
        py_file = tmp_path / "different_var.py"
        py_file.write_text(code)

        findings = hedging_check.scan_file(py_file)

        assert findings == []

    def test_allowlist_suppresses(self, tmp_path: Path) -> None:
        """Allowlisted entries should not appear in findings."""
        code = """\
result = filter_data(items)
if not result:
    result = all_items
"""
        py_file = tmp_path / "allowed.py"
        py_file.write_text(code)
        allowlist_key = f"{py_file}:2"

        with patch.object(hedging_check, "ALLOWLIST", {allowlist_key: "CONF-999"}):
            findings = hedging_check.scan_file(py_file)

        assert findings == []

    def test_syntax_error_skipped(self, tmp_path: Path) -> None:
        """Files with syntax errors should be skipped gracefully."""
        py_file = tmp_path / "broken.py"
        py_file.write_text("def broken(:\n    pass")

        findings = hedging_check.scan_file(py_file)

        assert findings == []

    def test_unicode_error_skipped(self, tmp_path: Path) -> None:
        """Files with encoding errors should be skipped gracefully."""
        py_file = tmp_path / "binary.py"
        py_file.write_bytes(b"\x80\x81\x82")  # Invalid UTF-8

        findings = hedging_check.scan_file(py_file)

        assert findings == []


@pytest.mark.req("REQ-YG-063")
class TestMain:
    """Tests for main() function."""

    def test_no_findings_returns_zero(self, tmp_path: Path) -> None:
        """Clean directory should return exit code 0."""
        # Create a clean Python file
        py_file = tmp_path / "clean.py"
        py_file.write_text("x = 1\ny = 2\n")

        with patch.object(
            hedging_check.sys, "argv", ["hedging_check.py", str(tmp_path)]
        ):
            exit_code = hedging_check.main()

        assert exit_code == 0

    def test_findings_without_strict_returns_zero(self, tmp_path: Path) -> None:
        """Findings without --strict should still return 0."""
        code = """\
if not result:
    result = fallback
"""
        py_file = tmp_path / "fallback.py"
        py_file.write_text(code)

        with patch.object(
            hedging_check.sys, "argv", ["hedging_check.py", str(tmp_path)]
        ):
            exit_code = hedging_check.main()

        assert exit_code == 0

    def test_strict_mode_returns_one(self, tmp_path: Path) -> None:
        """Findings with --strict should return exit code 1."""
        code = """\
if not result:
    result = fallback
"""
        py_file = tmp_path / "fallback.py"
        py_file.write_text(code)

        with patch.object(
            hedging_check.sys, "argv", ["hedging_check.py", str(tmp_path), "--strict"]
        ):
            exit_code = hedging_check.main()

        assert exit_code == 1

    def test_directory_not_found(self, tmp_path: Path) -> None:
        """Non-existent directory should return exit code 1."""
        nonexistent = tmp_path / "does_not_exist"

        with patch.object(
            hedging_check.sys, "argv", ["hedging_check.py", str(nonexistent)]
        ):
            exit_code = hedging_check.main()

        assert exit_code == 1

    def test_skips_pycache(self, tmp_path: Path) -> None:
        """Files in __pycache__ directories should be skipped."""
        # Create a __pycache__ directory with a file that would trigger
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        py_file = pycache / "cached.py"
        py_file.write_text("if not result:\n    result = fallback\n")

        # Create a clean file outside __pycache__
        clean_file = tmp_path / "clean.py"
        clean_file.write_text("x = 1\n")

        with patch.object(
            hedging_check.sys, "argv", ["hedging_check.py", str(tmp_path)]
        ):
            exit_code = hedging_check.main()

        assert exit_code == 0
