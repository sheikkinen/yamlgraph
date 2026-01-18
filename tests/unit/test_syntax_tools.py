"""Tests for syntax validation tools."""

from yamlgraph.tools.analysis.syntax_tools import syntax_check


class TestSyntaxCheck:
    """Tests for syntax_check function."""

    def test_valid_python_returns_valid(self):
        """Valid Python code returns valid=True."""
        code = "def hello():\n    return 'world'"
        result = syntax_check(code)

        assert result["valid"] is True
        assert "error" not in result

    def test_valid_class_definition(self):
        """Valid class definition passes."""
        code = """
class MyClass:
    def __init__(self, name: str):
        self.name = name

    def greet(self) -> str:
        return f"Hello, {self.name}"
"""
        result = syntax_check(code)
        assert result["valid"] is True

    def test_invalid_syntax_returns_error(self):
        """Invalid syntax returns valid=False with error."""
        code = "def broken(\n    return"
        result = syntax_check(code)

        assert result["valid"] is False
        assert "error" in result
        assert isinstance(result["error"], str)

    def test_missing_colon_error(self):
        """Missing colon is detected."""
        code = "if True\n    print('oops')"
        result = syntax_check(code)

        assert result["valid"] is False
        assert "error" in result

    def test_indentation_error(self):
        """Indentation errors are detected."""
        code = "def foo():\nreturn 1"
        result = syntax_check(code)

        assert result["valid"] is False
        assert "error" in result

    def test_empty_string_is_valid(self):
        """Empty string is valid Python."""
        result = syntax_check("")
        assert result["valid"] is True

    def test_comment_only_is_valid(self):
        """Comment-only code is valid."""
        code = "# Just a comment"
        result = syntax_check(code)
        assert result["valid"] is True

    def test_import_statement_valid(self):
        """Import statements are valid."""
        code = "from typing import Optional\nimport os"
        result = syntax_check(code)
        assert result["valid"] is True

    def test_error_includes_line_number(self):
        """Error message includes line information."""
        code = "line1 = 1\nline2 =\nline3 = 3"
        result = syntax_check(code)

        assert result["valid"] is False
        # Error should mention line 2
        assert "line" in result["error"].lower() or "2" in result["error"]

    def test_multiline_string_valid(self):
        """Multiline strings are valid."""
        code = '"""This is a\nmultiline\ndocstring."""'
        result = syntax_check(code)
        assert result["valid"] is True
