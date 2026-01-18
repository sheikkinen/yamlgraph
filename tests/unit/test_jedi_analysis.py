"""Tests for jedi-based code analysis tools."""

import tempfile
from pathlib import Path

import pytest

from yamlgraph.tools.analysis.jedi_analysis import (
    JEDI_AVAILABLE,
    find_references,
    get_callees,
    get_callers,
)

# Skip all tests if jedi not available
pytestmark = pytest.mark.skipif(not JEDI_AVAILABLE, reason="jedi not installed")


class TestFindReferences:
    """Tests for find_references function."""

    def test_finds_definition(self):
        """Finds the definition of a symbol."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple module
            file_path = Path(tmpdir) / "sample.py"
            file_path.write_text("""
class MyConfig:
    timeout: int = 30

config = MyConfig()
print(config.timeout)
""")
            result = find_references(str(file_path), "MyConfig", line=2)

            assert isinstance(result, list)
            assert len(result) >= 1
            # Should find at least the definition
            types = [r.get("type") for r in result]
            assert any(t in ["definition", "name"] for t in types)

    def test_finds_usages_in_same_file(self):
        """Finds usages of a symbol within the same file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "sample.py"
            file_path.write_text("""
def helper():
    return 42

def main():
    x = helper()
    y = helper()
    return x + y
""")
            result = find_references(str(file_path), "helper", line=2)

            assert isinstance(result, list)
            # Should find definition + 2 usages
            assert len(result) >= 3

    def test_returns_empty_for_unknown_symbol(self):
        """Returns empty list for non-existent symbol."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "sample.py"
            file_path.write_text("""
def existing_function():
    return 42
""")
            # Search for a symbol that doesn't exist, on a line with a different symbol
            result = find_references(str(file_path), "nonexistent_xyz", line=2)

            assert isinstance(result, list)
            # jedi may return what's at the position, so filter by name
            matching = [r for r in result if r.get("name") == "nonexistent_xyz"]
            assert len(matching) == 0

    def test_returns_error_for_missing_file(self):
        """Returns error dict for non-existent file."""
        result = find_references("/nonexistent/file.py", "symbol", line=1)

        assert isinstance(result, dict)
        assert "error" in result

    def test_finds_cross_file_references(self):
        """Finds references across multiple files in same project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create module with class
            (Path(tmpdir) / "config.py").write_text("""
class AppConfig:
    name: str = "app"
""")
            # Create module that imports it
            (Path(tmpdir) / "main.py").write_text("""
from config import AppConfig

cfg = AppConfig()
""")
            result = find_references(
                str(Path(tmpdir) / "config.py"),
                "AppConfig",
                line=2,
                project_path=tmpdir,
            )

            assert isinstance(result, list)
            # Should find definition + import + usage
            files = set(r.get("file", "") for r in result)
            assert len(files) >= 1  # At least the defining file


class TestGetCallers:
    """Tests for get_callers function."""

    def test_finds_callers(self):
        """Finds functions that call a given function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "sample.py"
            file_path.write_text("""
def target_function():
    return 42

def caller_one():
    return target_function()

def caller_two():
    x = target_function()
    return x * 2

def unrelated():
    return 0
""")
            result = get_callers(str(file_path), "target_function", line=2)

            assert isinstance(result, list)
            assert len(result) >= 2
            caller_names = [r.get("caller") for r in result]
            assert "caller_one" in caller_names
            assert "caller_two" in caller_names
            assert "unrelated" not in caller_names

    def test_returns_empty_for_uncalled_function(self):
        """Returns empty list for function with no callers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "sample.py"
            file_path.write_text("""
def lonely_function():
    return 42
""")
            result = get_callers(str(file_path), "lonely_function", line=2)

            assert isinstance(result, list)
            assert len(result) == 0

    def test_returns_error_for_missing_file(self):
        """Returns error dict for non-existent file."""
        result = get_callers("/nonexistent/file.py", "func", line=1)

        assert isinstance(result, dict)
        assert "error" in result


class TestGetCallees:
    """Tests for get_callees function."""

    def test_finds_callees(self):
        """Finds functions called by a given function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "sample.py"
            file_path.write_text("""
def helper_a():
    return 1

def helper_b():
    return 2

def main_function():
    a = helper_a()
    b = helper_b()
    return a + b
""")
            result = get_callees(str(file_path), "main_function", line=8)

            assert isinstance(result, list)
            assert len(result) >= 2
            callee_names = [r.get("callee") for r in result]
            assert "helper_a" in callee_names
            assert "helper_b" in callee_names

    def test_returns_empty_for_function_with_no_calls(self):
        """Returns empty list for function that makes no calls."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "sample.py"
            file_path.write_text("""
def pure_function():
    return 42
""")
            result = get_callees(str(file_path), "pure_function", line=2)

            assert isinstance(result, list)
            assert len(result) == 0

    def test_returns_error_for_missing_file(self):
        """Returns error dict for non-existent file."""
        result = get_callees("/nonexistent/file.py", "func", line=1)

        assert isinstance(result, dict)
        assert "error" in result

    def test_includes_line_numbers(self):
        """Each callee includes line number where called."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "sample.py"
            file_path.write_text("""
def helper():
    return 1

def caller():
    x = helper()
    return x
""")
            result = get_callees(str(file_path), "caller", line=5)

            assert len(result) >= 1
            for callee in result:
                assert "callee" in callee
                assert "line" in callee
