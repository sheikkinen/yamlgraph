"""Deterministic guard expression evaluator.

Supports a strict, safe subset for node guards:
- References: state.<path>, output.<path>, output
- Comparisons: ==, !=, <, >, <=, >=, in, not in
- Logic: and, or, not
- Filters via pipe: | length, | file_exists, | dir_exists, | type, | keys
- Literals: str, int, float, bool, None, list literals
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


class GuardExpressionError(ValueError):
    """Raised when guard expression syntax is invalid or unsafe."""


_ALLOWED_FILTERS = {"length", "file_exists", "dir_exists", "type", "keys"}


def _resolve_attribute(value: Any, attr: str) -> Any:
    """Resolve attribute/key access with permissive dict/object lookup."""
    if value is None:
        return None
    if isinstance(value, dict):
        return value.get(attr)
    return getattr(value, attr, None)


def _apply_filter(filter_name: str, value: Any) -> Any:
    """Apply a supported deterministic filter."""
    if filter_name not in _ALLOWED_FILTERS:
        valid = ", ".join(sorted(_ALLOWED_FILTERS))
        raise GuardExpressionError(
            f"Unknown guard filter '{filter_name}'. Valid filters: {valid}"
        )

    if filter_name == "length":
        try:
            return len(value)
        except TypeError:
            return 0

    if filter_name == "file_exists":
        if not isinstance(value, str | Path):
            return False
        return Path(value).is_file()

    if filter_name == "dir_exists":
        if not isinstance(value, str | Path):
            return False
        return Path(value).is_dir()

    if filter_name == "type":
        return type(value).__name__

    # keys
    if isinstance(value, dict):
        return list(value.keys())
    if hasattr(value, "model_dump"):
        dumped = value.model_dump()
        if isinstance(dumped, dict):
            return list(dumped.keys())
    if hasattr(value, "__dict__"):
        return list(vars(value).keys())
    return []


def _compare_values(left: Any, op: ast.cmpop, right: Any) -> bool:
    """Evaluate a single comparison operation."""
    try:
        if isinstance(op, ast.Eq):
            return left == right
        if isinstance(op, ast.NotEq):
            return left != right
        if isinstance(op, ast.Lt):
            return left < right
        if isinstance(op, ast.Gt):
            return left > right
        if isinstance(op, ast.LtE):
            return left <= right
        if isinstance(op, ast.GtE):
            return left >= right
        if isinstance(op, ast.In):
            return left in right
        if isinstance(op, ast.NotIn):
            return left not in right
    except TypeError:
        return False
    raise GuardExpressionError(f"Unsupported comparison operator: {type(op).__name__}")


class _GuardEvaluator:
    """Safe AST evaluator for deterministic guard expressions."""

    def __init__(self, state: dict[str, Any], output: Any):
        self.state = state
        self.output = output

    def _eval_name(self, node: ast.Name) -> Any:
        if node.id == "state":
            return self.state
        if node.id == "output":
            return self.output
        raise GuardExpressionError(
            f"Unknown identifier '{node.id}'. Use state.<path> or output.<path>."
        )

    def _eval_bool(self, node: ast.BoolOp) -> bool:
        if isinstance(node.op, ast.And):
            return all(bool(self.eval(v)) for v in node.values)
        if isinstance(node.op, ast.Or):
            return any(bool(self.eval(v)) for v in node.values)
        raise GuardExpressionError(
            f"Unsupported boolean operator: {type(node.op).__name__}"
        )

    def _eval_pipe(self, node: ast.BinOp) -> Any:
        if not isinstance(node.op, ast.BitOr):
            raise GuardExpressionError(
                "Only filter pipes are allowed in guard expressions"
            )
        if not isinstance(node.right, ast.Name):
            raise GuardExpressionError(
                "Filter pipe must use a filter name, e.g. state.path | length"
            )
        return _apply_filter(node.right.id, self.eval(node.left))

    def _eval_compare(self, node: ast.Compare) -> bool:
        left = self.eval(node.left)
        for op, comparator in zip(node.ops, node.comparators, strict=False):
            right = self.eval(comparator)
            if not _compare_values(left, op, right):
                return False
            left = right
        return True

    def eval(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.List):
            return [self.eval(elt) for elt in node.elts]
        if isinstance(node, ast.Tuple):
            return tuple(self.eval(elt) for elt in node.elts)
        if isinstance(node, ast.Attribute):
            return _resolve_attribute(self.eval(node.value), node.attr)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return not bool(self.eval(node.operand))

        handlers: dict[type[ast.AST], Any] = {
            ast.Name: self._eval_name,
            ast.BoolOp: self._eval_bool,
            ast.BinOp: self._eval_pipe,
            ast.Compare: self._eval_compare,
        }
        for node_type, handler in handlers.items():
            if isinstance(node, node_type):
                return handler(node)

        forbidden = (
            ast.Call,
            ast.Subscript,
            ast.Dict,
            ast.Set,
            ast.ListComp,
            ast.SetComp,
            ast.DictComp,
            ast.GeneratorExp,
            ast.Lambda,
            ast.IfExp,
            ast.Await,
            ast.Yield,
        )
        if isinstance(node, forbidden):
            raise GuardExpressionError(
                f"Unsupported syntax in guard expression: {type(node).__name__}"
            )

        raise GuardExpressionError(
            f"Unsupported syntax in guard expression: {type(node).__name__}"
        )


def _parse_guard_expression(check: str) -> ast.Expression:
    text = (check or "").strip()
    if not text:
        raise GuardExpressionError("Guard check must be a non-empty expression")
    try:
        tree = ast.parse(text, mode="eval")
    except SyntaxError as exc:
        raise GuardExpressionError(
            f"Invalid guard expression syntax: {exc.msg}"
        ) from exc
    return tree


def validate_guard_expression(check: str) -> None:
    """Validate guard expression syntax and semantics without runtime state."""
    tree = _parse_guard_expression(check)
    evaluator = _GuardEvaluator(state={}, output=None)
    evaluator.eval(tree.body)


def evaluate_guard_expression(
    check: str, state: dict[str, Any], output: Any = None
) -> bool:
    """Evaluate a deterministic guard expression safely."""
    tree = _parse_guard_expression(check)
    evaluator = _GuardEvaluator(state=state, output=output)
    value = evaluator.eval(tree.body)
    return bool(value)


__all__ = [
    "GuardExpressionError",
    "evaluate_guard_expression",
    "validate_guard_expression",
]
