"""FR-659: Coverage gaps in guard_evaluator.py (73% → ≥90%).

Tests for uncovered branches: comparison operators, boolean logic,
filters, pipe errors, tuple/not/output, forbidden syntax, attribute
resolution on non-dict objects.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from yamlgraph.utils.guard_evaluator import (
    GuardExpressionError,
    evaluate_guard_expression,
)

# ---------------------------------------------------------------------------
# Comparison operators (NotEq, Lt, Gt, LtE, GtE, NotIn)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-154")
class TestComparisonOperators:
    """Cover _compare_values branches for all comparison operators."""

    def test_not_equal(self):
        assert evaluate_guard_expression("state.x != 3", state={"x": 5}, output=None)
        assert not evaluate_guard_expression(
            "state.x != 5", state={"x": 5}, output=None
        )

    def test_less_than(self):
        assert evaluate_guard_expression("state.x < 10", state={"x": 5}, output=None)
        assert not evaluate_guard_expression("state.x < 3", state={"x": 5}, output=None)

    def test_greater_than(self):
        assert evaluate_guard_expression("state.x > 3", state={"x": 5}, output=None)
        assert not evaluate_guard_expression(
            "state.x > 10", state={"x": 5}, output=None
        )

    def test_less_than_or_equal(self):
        assert evaluate_guard_expression("state.x <= 5", state={"x": 5}, output=None)
        assert evaluate_guard_expression("state.x <= 6", state={"x": 5}, output=None)
        assert not evaluate_guard_expression(
            "state.x <= 4", state={"x": 5}, output=None
        )

    def test_greater_than_or_equal(self):
        assert evaluate_guard_expression("state.x >= 5", state={"x": 5}, output=None)
        assert evaluate_guard_expression("state.x >= 4", state={"x": 5}, output=None)
        assert not evaluate_guard_expression(
            "state.x >= 6", state={"x": 5}, output=None
        )

    def test_not_in(self):
        assert evaluate_guard_expression(
            "'z' not in state.tags", state={"tags": ["a", "b"]}, output=None
        )
        assert not evaluate_guard_expression(
            "'a' not in state.tags", state={"tags": ["a", "b"]}, output=None
        )

    def test_type_error_returns_false(self):
        """Comparing incompatible types returns False via TypeError catch."""
        assert not evaluate_guard_expression(
            "state.x < 'text'", state={"x": 5}, output=None
        )


# ---------------------------------------------------------------------------
# Boolean operators (or, not)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-154")
class TestBooleanOperators:
    """Cover _eval_bool Or branch and UnaryOp Not."""

    def test_or_true(self):
        assert evaluate_guard_expression(
            "state.a or state.b",
            state={"a": False, "b": True},
            output=None,
        )

    def test_or_false(self):
        assert not evaluate_guard_expression(
            "state.a or state.b",
            state={"a": False, "b": False},
            output=None,
        )

    def test_not_true(self):
        assert evaluate_guard_expression(
            "not state.flag", state={"flag": False}, output=None
        )

    def test_not_false(self):
        assert not evaluate_guard_expression(
            "not state.flag", state={"flag": True}, output=None
        )


# ---------------------------------------------------------------------------
# Output identifier
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-154")
class TestOutputIdentifier:
    """Cover _eval_name output branch."""

    def test_output_attribute_access(self):
        assert evaluate_guard_expression(
            "output.score > 0.5",
            state={},
            output={"score": 0.8},
        )

    def test_output_is_none_attribute_returns_none(self):
        """output.attr on None output returns None (falsy)."""
        assert not evaluate_guard_expression("output.score", state={}, output=None)

    def test_unknown_identifier_raises(self):
        with pytest.raises(GuardExpressionError, match="Unknown identifier"):
            evaluate_guard_expression("foo.bar == 1", state={}, output=None)


# ---------------------------------------------------------------------------
# Tuple literals
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-154")
class TestTupleLiteral:
    """Cover ast.Tuple branch in eval."""

    def test_in_tuple(self):
        assert evaluate_guard_expression(
            "state.x in (1, 2, 3)", state={"x": 2}, output=None
        )

    def test_not_in_tuple(self):
        assert not evaluate_guard_expression(
            "state.x in (1, 2, 3)", state={"x": 5}, output=None
        )


# ---------------------------------------------------------------------------
# Filter branches
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-154")
class TestFilterBranches:
    """Cover uncovered _apply_filter branches."""

    def test_length_type_error_returns_zero(self):
        """length filter on non-iterable returns 0."""
        assert evaluate_guard_expression(
            "state.x | length == 0", state={"x": 42}, output=None
        )

    def test_file_exists_non_string_returns_false(self):
        assert not evaluate_guard_expression(
            "state.x | file_exists", state={"x": 123}, output=None
        )

    def test_dir_exists_non_string_returns_false(self):
        assert not evaluate_guard_expression(
            "state.x | dir_exists", state={"x": 123}, output=None
        )

    def test_dir_exists_with_real_dir(self, tmp_path: Path):
        assert evaluate_guard_expression(
            "state.d | dir_exists", state={"d": str(tmp_path)}, output=None
        )

    def test_type_filter(self):
        assert evaluate_guard_expression(
            "state.x | type == 'int'", state={"x": 42}, output=None
        )
        assert evaluate_guard_expression(
            "state.x | type == 'str'", state={"x": "hello"}, output=None
        )

    def test_keys_filter_on_object_with_dict(self):
        """keys filter on __dict__ object."""

        class Obj:
            def __init__(self):
                self.a = 1
                self.b = 2

        assert evaluate_guard_expression(
            "'a' in state.obj | keys", state={"obj": Obj()}, output=None
        )

    def test_keys_filter_on_non_dict_non_object(self):
        """keys filter on plain int returns empty list."""
        assert not evaluate_guard_expression(
            "'x' in state.val | keys", state={"val": 42}, output=None
        )


# ---------------------------------------------------------------------------
# Pipe error branches
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-154")
class TestPipeErrors:
    """Cover _eval_pipe error branches."""

    def test_non_bitor_operator_raises(self):
        """Arithmetic operators like + trigger pipe error."""
        with pytest.raises(GuardExpressionError, match="Only filter pipes"):
            evaluate_guard_expression("state.x + 1", state={"x": 5}, output=None)

    def test_non_name_rhs_raises(self):
        """Pipe with non-name RHS (e.g. literal) raises."""
        with pytest.raises(GuardExpressionError, match="Filter pipe must use"):
            evaluate_guard_expression("state.x | 5", state={"x": 5}, output=None)


# ---------------------------------------------------------------------------
# Forbidden syntax
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-154")
class TestForbiddenSyntax:
    """Cover forbidden AST node types."""

    def test_subscript_rejected(self):
        with pytest.raises(GuardExpressionError, match="Unsupported syntax"):
            evaluate_guard_expression(
                "state.tags[0]", state={"tags": ["a"]}, output=None
            )

    def test_dict_literal_rejected(self):
        with pytest.raises(GuardExpressionError, match="Unsupported syntax"):
            evaluate_guard_expression("{'a': 1}", state={}, output=None)

    def test_lambda_rejected(self):
        with pytest.raises(GuardExpressionError, match="Unsupported syntax"):
            evaluate_guard_expression("lambda: state.x", state={"x": 1}, output=None)

    def test_ternary_rejected(self):
        with pytest.raises(GuardExpressionError, match="Unsupported syntax"):
            evaluate_guard_expression(
                "1 if state.x else 0", state={"x": True}, output=None
            )


# ---------------------------------------------------------------------------
# Attribute resolution on non-dict objects
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-154")
class TestAttributeResolution:
    """Cover _resolve_attribute getattr path."""

    def test_attribute_on_none_returns_none(self):
        assert not evaluate_guard_expression(
            "state.missing.nested", state={}, output=None
        )

    def test_attribute_on_object(self):
        """getattr path for non-dict values."""

        class Config:
            enabled = True

        assert evaluate_guard_expression(
            "state.cfg.enabled", state={"cfg": Config()}, output=None
        )


# ---------------------------------------------------------------------------
# Empty expression
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-154")
class TestEmptyExpression:
    """Cover _parse_guard_expression empty string."""

    def test_empty_string_raises(self):
        with pytest.raises(GuardExpressionError, match="non-empty"):
            evaluate_guard_expression("", state={}, output=None)

    def test_whitespace_only_raises(self):
        with pytest.raises(GuardExpressionError, match="non-empty"):
            evaluate_guard_expression("   ", state={}, output=None)
