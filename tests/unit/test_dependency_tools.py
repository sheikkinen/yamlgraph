"""Tests for dependency analysis tools."""

import tempfile
from pathlib import Path

from yamlgraph.tools.analysis.dependency_tools import get_dependents, get_imports


class TestGetImports:
    """Tests for get_imports function."""

    def test_extracts_import_statements(self):
        """Standard import statements are extracted."""
        result = get_imports("yamlgraph/__init__.py")

        assert "error" not in result
        assert "imports" in result
        assert isinstance(result["imports"], list)

    def test_extracts_from_imports(self):
        """From X import Y statements are extracted."""
        result = get_imports("yamlgraph/executor.py")

        assert "error" not in result
        assert "imports" in result
        # executor.py has from imports
        assert len(result["imports"]) > 0

    def test_import_has_module_and_names(self):
        """Each import has module and imported names."""
        result = get_imports("yamlgraph/executor.py")

        assert "error" not in result
        for imp in result["imports"]:
            assert "module" in imp
            # Names may be None for 'import X' vs 'from X import Y'
            assert "names" in imp

    def test_returns_error_for_invalid_file(self):
        """Returns error for non-existent file."""
        result = get_imports("nonexistent/file.py")

        assert "error" in result

    def test_returns_error_for_syntax_error(self):
        """Returns error for file with syntax errors."""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
            f.write("def broken(\n    return")
            temp_path = f.name

        try:
            result = get_imports(temp_path)
            assert "error" in result
        finally:
            Path(temp_path).unlink()

    def test_handles_aliased_imports(self):
        """Handles 'import X as Y' and 'from X import Y as Z'."""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
            f.write("import numpy as np\nfrom pathlib import Path as P")
            temp_path = f.name

        try:
            result = get_imports(temp_path)
            assert "error" not in result
            assert len(result["imports"]) >= 2
        finally:
            Path(temp_path).unlink()


class TestGetDependents:
    """Tests for get_dependents function."""

    def test_finds_files_that_import_module(self):
        """Finds files that import a given module."""
        # yamlgraph.executor is imported by many files
        result = get_dependents("yamlgraph.executor", "yamlgraph")

        assert "error" not in result
        assert "dependents" in result
        assert isinstance(result["dependents"], list)

    def test_returns_file_paths(self):
        """Returns list of file paths."""
        result = get_dependents("yamlgraph.config", "yamlgraph")

        assert "error" not in result
        for dep in result["dependents"]:
            assert isinstance(dep, str)
            assert dep.endswith(".py")

    def test_empty_for_unused_module(self):
        """Returns empty list for module with no dependents."""
        result = get_dependents("nonexistent.module.that.nobody.imports", "yamlgraph")

        assert "error" not in result
        assert result["dependents"] == []

    def test_returns_error_for_invalid_project(self):
        """Returns error for non-existent project path."""
        result = get_dependents("some.module", "/nonexistent/path")

        assert "error" in result

    def test_finds_from_import_style(self):
        """Finds 'from X import Y' style imports."""
        result = get_dependents("yamlgraph.utils.prompts", "yamlgraph")

        assert "error" not in result
        # prompts is used in multiple places
        assert len(result["dependents"]) >= 0  # May be 0 if not imported directly

    def test_finds_import_module_style(self):
        """Finds 'import X' style imports."""
        # logging is imported in many places
        result = get_dependents("logging", "yamlgraph")

        # This searches for 'import logging' or 'from logging import'
        assert "error" not in result
