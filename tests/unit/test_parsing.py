"""Tests for shared parsing utilities."""

from yamlgraph.utils.parsing import parse_literal


class TestParseLiteral:
    """Tests for parse_literal function."""

    def test_parse_quoted_double_string(self):
        """Double-quoted strings should be unquoted."""
        assert parse_literal('"hello"') == "hello"

    def test_parse_quoted_single_string(self):
        """Single-quoted strings should be unquoted."""
        assert parse_literal("'world'") == "world"

    def test_parse_true(self):
        """'true' should parse to True."""
        assert parse_literal("true") is True
        assert parse_literal("True") is True
        assert parse_literal("TRUE") is True

    def test_parse_false(self):
        """'false' should parse to False."""
        assert parse_literal("false") is False
        assert parse_literal("False") is False

    def test_parse_null(self):
        """'null' and 'none' should parse to None."""
        assert parse_literal("null") is None
        assert parse_literal("none") is None
        assert parse_literal("None") is None

    def test_parse_integer(self):
        """Integer strings should parse to int."""
        assert parse_literal("42") == 42
        assert parse_literal("-10") == -10

    def test_parse_float(self):
        """Float strings should parse to float."""
        assert parse_literal("3.14") == 3.14
        assert parse_literal("-0.5") == -0.5

    def test_parse_unquoted_string(self):
        """Unquoted non-numeric strings should return as-is."""
        assert parse_literal("hello") == "hello"

    def test_strips_whitespace(self):
        """Leading/trailing whitespace should be stripped."""
        assert parse_literal("  42  ") == 42
        assert parse_literal("  true  ") is True
