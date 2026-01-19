"""Tests for code context tools."""

import tempfile
from pathlib import Path

from examples.codegen.tools.code_context import (
    find_related_tests,
    read_lines,
    search_codebase,
    search_in_file,
)


class TestReadLines:
    """Tests for read_lines function."""

    def test_reads_specific_lines(self):
        """Reads the specified line range."""
        # Read known lines from a project file
        result = read_lines("yamlgraph/executor.py", 1, 10)

        assert isinstance(result, str)
        assert len(result) > 0
        # First line should be docstring or comment
        lines = result.split("\n")
        assert len(lines) >= 10

    def test_returns_error_for_missing_file(self):
        """Returns error dict for non-existent file."""
        result = read_lines("nonexistent_file_12345.py", 1, 10)

        assert isinstance(result, dict)
        assert "error" in result

    def test_handles_line_range_beyond_file(self):
        """Handles line numbers beyond file length gracefully."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("line1\nline2\nline3\n")
            temp_path = f.name

        try:
            result = read_lines(temp_path, 1, 100)
            assert isinstance(result, str)
            assert "line1" in result
            assert "line3" in result
        finally:
            Path(temp_path).unlink()

    def test_one_indexed_lines(self):
        """Line numbers are 1-indexed."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("first\nsecond\nthird\n")
            temp_path = f.name

        try:
            result = read_lines(temp_path, 2, 2)
            assert "second" in result
            assert "first" not in result
        finally:
            Path(temp_path).unlink()

    def test_handles_invalid_line_range(self):
        """Handles start > end gracefully."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("line1\nline2\n")
            temp_path = f.name

        try:
            result = read_lines(temp_path, 5, 3)
            # Should return empty or handle gracefully
            assert isinstance(result, str)
        finally:
            Path(temp_path).unlink()


class TestFindRelatedTests:
    """Tests for find_related_tests function."""

    def test_finds_tests_mentioning_symbol(self):
        """Finds test functions that mention the symbol."""
        result = find_related_tests("execute_prompt", "tests")

        assert isinstance(result, list)
        # Should find some tests
        assert len(result) > 0

        for test in result:
            assert "file" in test
            assert "line" in test
            assert "test_name" in test
            assert test["test_name"].startswith("test_")

    def test_returns_empty_for_unknown_symbol(self):
        """Returns empty list for symbol not in tests."""
        # Create a temp directory with a test file that doesn't have our symbol
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test_sample.py"
            test_file.write_text("""
def test_something():
    assert True
""")
            result = find_related_tests("nonexistent", tmpdir)

            assert isinstance(result, list)
            assert len(result) == 0

    def test_returns_empty_for_nonexistent_path(self):
        """Returns empty list for non-existent tests path."""
        result = find_related_tests("anything", "nonexistent_tests_dir")

        assert isinstance(result, list)
        assert len(result) == 0

    def test_finds_tests_in_subdirectories(self):
        """Finds tests in nested test directories."""
        result = find_related_tests("graph", "tests")

        # Should find tests in unit/ and possibly integration/
        files = [t["file"] for t in result]
        assert any("unit" in f for f in files)

    def test_case_insensitive_search(self):
        """Symbol search is case-insensitive."""
        # Search for something that exists in different cases
        result_lower = find_related_tests("execute", "tests")
        result_upper = find_related_tests("EXECUTE", "tests")

        # Both should find some results
        assert len(result_lower) > 0
        assert len(result_upper) > 0

    def test_skips_non_test_functions(self):
        """Only returns functions starting with test_."""
        result = find_related_tests("execute_prompt", "tests")

        for test in result:
            assert test["test_name"].startswith("test_")


class TestSearchInFile:
    """Tests for search_in_file function."""

    def test_finds_matching_lines(self):
        """Finds lines containing the search pattern."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def foo():\n    timeout = 30\n    return timeout\n")
            temp_path = f.name

        try:
            result = search_in_file(temp_path, "timeout")

            assert isinstance(result, list)
            assert len(result) == 2
            # Line 2 and 3 contain "timeout"
            assert result[0]["line"] == 2
            assert "timeout = 30" in result[0]["text"]
            assert result[1]["line"] == 3
        finally:
            Path(temp_path).unlink()

    def test_returns_error_for_missing_file(self):
        """Returns error dict for non-existent file."""
        result = search_in_file("nonexistent_12345.py", "pattern")

        assert isinstance(result, dict)
        assert "error" in result

    def test_returns_empty_for_no_matches(self):
        """Returns empty list when pattern not found."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def foo():\n    return 42\n")
            temp_path = f.name

        try:
            result = search_in_file(temp_path, "nonexistent_pattern")

            assert isinstance(result, list)
            assert len(result) == 0
        finally:
            Path(temp_path).unlink()

    def test_case_insensitive_by_default(self):
        """Search is case-insensitive by default."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("TIMEOUT = 30\ntimeout = 10\nTimeOut = 20\n")
            temp_path = f.name

        try:
            result = search_in_file(temp_path, "timeout")

            assert len(result) == 3
        finally:
            Path(temp_path).unlink()

    def test_case_sensitive_option(self):
        """Can enable case-sensitive search."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("TIMEOUT = 30\ntimeout = 10\n")
            temp_path = f.name

        try:
            result = search_in_file(temp_path, "timeout", case_sensitive=True)

            assert len(result) == 1
            assert result[0]["line"] == 2
        finally:
            Path(temp_path).unlink()

    def test_limits_context(self):
        """Returns only matching lines, not context."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("line1\ntarget\nline3\n")
            temp_path = f.name

        try:
            result = search_in_file(temp_path, "target")

            assert len(result) == 1
            assert "line1" not in result[0]["text"]
            assert "target" in result[0]["text"]
        finally:
            Path(temp_path).unlink()


class TestSearchCodebase:
    """Tests for search_codebase function."""

    def test_finds_matches_across_files(self):
        """Finds pattern matches in multiple files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            (Path(tmpdir) / "file1.py").write_text("timeout = 30\n")
            (Path(tmpdir) / "file2.py").write_text("max_timeout = 60\n")
            (Path(tmpdir) / "file3.py").write_text("no match here\n")

            result = search_codebase(tmpdir, "timeout")

            assert isinstance(result, list)
            assert len(result) == 2  # file1 and file2

            # Each result should have file and matches
            for r in result:
                assert "file" in r
                assert "matches" in r
                assert len(r["matches"]) > 0

    def test_respects_file_pattern(self):
        """Only searches files matching the pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "code.py").write_text("timeout = 30\n")
            (Path(tmpdir) / "config.yaml").write_text("timeout: 60\n")

            result = search_codebase(tmpdir, "timeout", pattern="*.py")

            assert len(result) == 1
            assert "code.py" in result[0]["file"]

    def test_returns_empty_for_no_matches(self):
        """Returns empty list when no matches found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "file.py").write_text("def foo(): pass\n")

            result = search_codebase(tmpdir, "nonexistent_xyz")

            assert isinstance(result, list)
            assert len(result) == 0

    def test_searches_subdirectories(self):
        """Recursively searches subdirectories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = Path(tmpdir) / "sub" / "dir"
            subdir.mkdir(parents=True)
            (subdir / "nested.py").write_text("timeout = 99\n")

            result = search_codebase(tmpdir, "timeout")

            assert len(result) == 1
            assert "nested.py" in result[0]["file"]

    def test_skips_pycache(self):
        """Skips __pycache__ directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = Path(tmpdir) / "__pycache__"
            cache.mkdir()
            (cache / "cached.pyc").write_text("timeout = 30\n")
            (Path(tmpdir) / "real.py").write_text("timeout = 30\n")

            result = search_codebase(tmpdir, "timeout")

            assert len(result) == 1
            assert "__pycache__" not in result[0]["file"]

    def test_returns_line_numbers(self):
        """Each match includes line number."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "test.py").write_text("line1\ntimeout = 30\nline3\n")

            result = search_codebase(tmpdir, "timeout")

            assert len(result) == 1
            assert result[0]["matches"][0]["line"] == 2
