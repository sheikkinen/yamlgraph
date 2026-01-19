"""Tests for code navigation tools."""

import tempfile
from pathlib import Path

from examples.codegen.tools.code_nav import list_package_modules


class TestListPackageModules:
    """Tests for list_package_modules function."""

    def test_finds_all_python_files_in_package(self):
        """Returns all .py files in the package."""
        result = list_package_modules("yamlgraph/tools")

        assert isinstance(result, list)
        assert len(result) > 0

        # Should find known files
        files = [r["file"] for r in result]
        assert any("shell.py" in f for f in files)
        assert any("websearch.py" in f for f in files)

    def test_includes_module_summaries(self):
        """Each module has docstring, classes, functions."""
        result = list_package_modules("yamlgraph/tools")

        for module in result:
            assert "file" in module
            assert "docstring" in module
            assert "classes" in module
            assert "functions" in module
            assert isinstance(module["classes"], list)
            assert isinstance(module["functions"], list)

    def test_skips_files_with_syntax_errors(self):
        """Files with syntax errors are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a valid file
            valid_file = Path(tmpdir) / "valid.py"
            valid_file.write_text('"""Valid module."""\ndef foo(): pass')

            # Create an invalid file
            invalid_file = Path(tmpdir) / "invalid.py"
            invalid_file.write_text("def broken(\n")

            result = list_package_modules(tmpdir)

            # Should have only the valid file
            assert len(result) == 1
            assert "valid.py" in result[0]["file"]

    def test_returns_empty_list_for_nonexistent_path(self):
        """Returns empty list for non-existent directory."""
        result = list_package_modules("nonexistent_directory_12345")

        assert result == []

    def test_returns_empty_list_for_empty_directory(self):
        """Returns empty list for directory with no Python files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = list_package_modules(tmpdir)
            assert result == []

    def test_finds_nested_modules(self):
        """Finds Python files in subdirectories."""
        result = list_package_modules("yamlgraph")

        files = [r["file"] for r in result]
        # Should find files in subdirectories
        assert any("utils" in f for f in files)
        assert any("models" in f for f in files)
        assert any("tools" in f for f in files)

    def test_class_names_are_strings(self):
        """Class names are extracted as strings, not dicts."""
        result = list_package_modules("yamlgraph/models")

        for module in result:
            for cls_name in module["classes"]:
                assert isinstance(cls_name, str)

    def test_function_names_are_strings(self):
        """Function names are extracted as strings, not dicts."""
        result = list_package_modules("yamlgraph/tools")

        for module in result:
            for func_name in module["functions"]:
                assert isinstance(func_name, str)
