"""Tests for scripts/noqa_coverage.py — noqa confession coverage checker.

FR-080: Infrastructure Script Unit Tests — Phase 2 (noqa_coverage).
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from scripts import noqa_coverage

pytestmark = pytest.mark.process


@pytest.mark.req("REQ-YG-063")
class TestFindNoqaInFile:
    """Tests for find_noqa_in_file() function."""

    def test_find_noqa_single_code(self, tmp_path: Path) -> None:
        """Single noqa with explicit code should return that code."""
        code = "import sys  # noqa: E402\n"
        py_file = tmp_path / "single.py"
        py_file.write_text(code, encoding="utf-8")

        results = noqa_coverage.find_noqa_in_file(py_file)

        assert results == [(1, "E402")]

    def test_find_noqa_multiple_codes(self, tmp_path: Path) -> None:
        """Multiple codes on one line should each be returned."""
        code = "from typing import *  # noqa: F401, F403\n"
        py_file = tmp_path / "multi.py"
        py_file.write_text(code, encoding="utf-8")

        results = noqa_coverage.find_noqa_in_file(py_file)

        assert len(results) == 2
        assert (1, "F401") in results
        assert (1, "F403") in results

    def test_find_noqa_blanket(self, tmp_path: Path) -> None:
        """Blanket noqa without code should return ALL."""
        code = "x = 1  # noqa\n"
        py_file = tmp_path / "blanket.py"
        py_file.write_text(code, encoding="utf-8")

        results = noqa_coverage.find_noqa_in_file(py_file)

        assert results == [(1, "ALL")]

    def test_find_noqa_multiple_lines(self, tmp_path: Path) -> None:
        """Multiple noqa comments on different lines."""
        code = """\
import os  # noqa: E402
import sys
from typing import *  # noqa: F401
"""
        py_file = tmp_path / "multiline.py"
        py_file.write_text(code, encoding="utf-8")

        results = noqa_coverage.find_noqa_in_file(py_file)

        assert len(results) == 2
        assert (1, "E402") in results
        assert (3, "F401") in results

    def test_find_noqa_case_insensitive(self, tmp_path: Path) -> None:
        """noqa pattern should be case-insensitive."""
        code = "x = 1  # NOQA: e402\n"
        py_file = tmp_path / "case.py"
        py_file.write_text(code, encoding="utf-8")

        results = noqa_coverage.find_noqa_in_file(py_file)

        assert results == [(1, "E402")]  # Code normalized to uppercase

    def test_find_noqa_unreadable_file(self, tmp_path: Path) -> None:
        """Unreadable file should return empty list."""
        py_file = tmp_path / "unreadable.py"
        py_file.write_bytes(b"\x80\x81\x82")  # Invalid UTF-8

        results = noqa_coverage.find_noqa_in_file(py_file)

        assert results == []


@pytest.mark.req("REQ-YG-063")
class TestParseConfessions:
    """Tests for parse_confessions() function."""

    def test_parse_confessions_extracts_entries(self, tmp_path: Path) -> None:
        """Parse confessions.md and extract documented entries."""
        confessions_md = tmp_path / "confessions.md"
        confessions_md.write_text("""\
# Confessions

### CONF-001
- **File**: [yamlgraph/cli.py](../yamlgraph/cli.py#L42)
- **Code**: E402
- **Sin**: Module-level import after code
- **Penance**: Required for path setup

### CONF-002
- **File**: [tests/conftest.py](../tests/conftest.py#L10)
- **Code**: F401
- **Sin**: Unused import
- **Penance**: Needed for pytest fixtures
""", encoding="utf-8")

        confessions = noqa_coverage.parse_confessions(confessions_md)

        assert "CONF-001" in confessions
        assert ("yamlgraph/cli.py", 42, "E402") in confessions["CONF-001"]
        assert "CONF-002" in confessions
        assert ("tests/conftest.py", 10, "F401") in confessions["CONF-002"]

    def test_parse_confessions_missing_file(self, tmp_path: Path) -> None:
        """Missing confessions.md should return empty dict."""
        nonexistent = tmp_path / "missing.md"

        confessions = noqa_coverage.parse_confessions(nonexistent)

        assert confessions == {}


@pytest.mark.req("REQ-YG-063")
class TestMain:
    """Tests for main() function."""

    def test_undocumented_detected(self, tmp_path: Path) -> None:
        """Undocumented noqa should be detected."""
        # Setup: Create a scan directory with noqa
        scan_dir = tmp_path / "yamlgraph"
        scan_dir.mkdir()
        py_file = scan_dir / "module.py"
        py_file.write_text("import sys  # noqa: E402\n", encoding="utf-8")

        # Setup: Empty confessions
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        confessions = docs_dir / "confessions.md"
        confessions.write_text("# Confessions\n", encoding="utf-8")

        with (
            patch.object(noqa_coverage, "SCAN_DIRS", ["yamlgraph"]),
            patch.object(noqa_coverage.sys, "argv", ["noqa_coverage.py"]),
        ):
            # Patch Path(__file__).parent.parent to return tmp_path
            original_file = noqa_coverage.__file__
            try:
                noqa_coverage.__file__ = str(tmp_path / "scripts" / "noqa_coverage.py")
                exit_code = noqa_coverage.main()
            finally:
                noqa_coverage.__file__ = original_file

        # Without --strict, should return 0 even with undocumented
        assert exit_code == 0

    def test_strict_mode_fails(self, tmp_path: Path) -> None:
        """With --strict and undocumented noqa, should return 1."""
        # Setup: Create a scan directory with noqa
        scan_dir = tmp_path / "yamlgraph"
        scan_dir.mkdir()
        py_file = scan_dir / "module.py"
        py_file.write_text("import sys  # noqa: E402\n", encoding="utf-8")

        # Setup: Empty confessions
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        confessions = docs_dir / "confessions.md"
        confessions.write_text("# Confessions\n", encoding="utf-8")

        with patch.object(noqa_coverage.sys, "argv", ["noqa_coverage.py", "--strict"]):
            original_file = noqa_coverage.__file__
            try:
                noqa_coverage.__file__ = str(tmp_path / "scripts" / "noqa_coverage.py")
                exit_code = noqa_coverage.main()
            finally:
                noqa_coverage.__file__ = original_file

        assert exit_code == 1

    def test_documented_returns_zero(self, tmp_path: Path) -> None:
        """When all noqa are documented, should return 0."""
        # Setup: Create a scan directory with noqa
        scan_dir = tmp_path / "yamlgraph"
        scan_dir.mkdir()
        py_file = scan_dir / "module.py"
        py_file.write_text("import sys  # noqa: E402\n", encoding="utf-8")

        # Setup: Confessions documenting the noqa
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        confessions = docs_dir / "confessions.md"
        confessions.write_text("""\
# Confessions

### CONF-001
- **File**: [yamlgraph/module.py](../yamlgraph/module.py#L1)
- **Code**: E402
- **Sin**: Test
- **Penance**: Test
""", encoding="utf-8")

        with patch.object(noqa_coverage.sys, "argv", ["noqa_coverage.py", "--strict"]):
            original_file = noqa_coverage.__file__
            try:
                noqa_coverage.__file__ = str(tmp_path / "scripts" / "noqa_coverage.py")
                exit_code = noqa_coverage.main()
            finally:
                noqa_coverage.__file__ = original_file

        assert exit_code == 0

    def test_missing_scan_dir_skipped(self, tmp_path: Path) -> None:
        """Missing scan directories should be skipped gracefully."""
        # Setup: No scan directories exist
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        confessions = docs_dir / "confessions.md"
        confessions.write_text("# Confessions\n", encoding="utf-8")

        with patch.object(noqa_coverage.sys, "argv", ["noqa_coverage.py"]):
            original_file = noqa_coverage.__file__
            try:
                noqa_coverage.__file__ = str(tmp_path / "scripts" / "noqa_coverage.py")
                exit_code = noqa_coverage.main()
            finally:
                noqa_coverage.__file__ = original_file

        assert exit_code == 0
