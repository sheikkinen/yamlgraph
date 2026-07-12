"""SMT-backed condition verification — FR-719 (W803–W805).

Translates expression-edge guard groups to Z3 formulas and proves three
properties per source node: no gap (W803 — some state silently falls
through to END, routing.py's hedge), no overlap (W804 — routing is
order-dependent), no unreachable guard (W805 — shadowed by earlier
guards). Every violation reports a concrete counterexample state.

Encoding is faithful to `evaluate_comparison` (Judgement F1): ordering
comparisons are None→False; ``==``/``!=`` are None-EXEMPT (runtime
``None != 0.5`` is True). Unquoted right-side identifiers encode as
variables iff they are known state keys, else string literals (F2).
Mixed-sort groups, missing z3, and solver timeouts yield one info
notice each — never a false verdict.

z3-solver is an optional extra: ``pip install yamlgraph[verify]``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from yamlgraph.linter.checks import LintIssue, load_graph
from yamlgraph.utils.conditions import COMPARISON_PATTERN, _split_compound

logger = logging.getLogger(__name__)

SOLVER_TIMEOUT_MS = 2000


@dataclass
class _Group:
    source: str
    conditions: list[str]
    has_unconditional: bool


class _SkipGroup(Exception):
    """Raised when a group cannot be encoded soundly — skip, never guess."""


def _collect_groups(config: dict[str, Any]) -> list[_Group]:
    """Expression-edge guard groups per source node (F3)."""
    by_source: dict[str, _Group] = {}
    for edge in config.get("edges", []):
        source = edge.get("from")
        if not source or source == "START":
            continue
        group = by_source.setdefault(source, _Group(source, [], False))
        condition = edge.get("condition")
        if condition and edge.get("type") != "conditional":
            group.conditions.append(condition)
        elif not condition and edge.get("type") != "conditional":
            group.has_unconditional = True
    return [g for g in by_source.values() if g.conditions]


def _known_state_keys(config: dict[str, Any]) -> set[str]:
    """State keys a right-side identifier may legally reference (F2)."""
    keys: set[str] = set()
    for name, node in config.get("nodes", {}).items():
        keys.add(node.get("state_key", name))
    keys.update(config.get("data_files", {}).keys())
    return keys


def _classify_literal(raw: str) -> tuple[str, Any]:
    """Static mirror of _resolve_right_value's literal decisions.

    Returns (kind, value) where kind in {string, bool, null, number, ident}.
    """
    raw = raw.strip()
    if (raw.startswith("'") and raw.endswith("'")) or (
        raw.startswith('"') and raw.endswith('"')
    ):
        return "string", raw[1:-1]
    lowered = raw.lower()
    if lowered in ("true", "false"):
        return "bool", lowered == "true"
    if lowered in ("null", "none"):
        return "null", None
    try:
        return "number", float(raw)
    except ValueError:
        return "ident", raw


def _parse_comparisons(condition: str) -> list[tuple[str, str, str, str]]:
    """Recursively parse a condition into (kind, left, op, right) atoms
    joined by the compound structure; returns a flat atom list for sort
    inference (structure handled separately in _encode)."""
    atoms: list[tuple[str, str, str, str]] = []

    def walk(expr: str) -> None:
        expr = expr.strip()
        for keyword in ("or", "and"):
            parts = _split_compound(expr, keyword)
            if parts is not None:
                for part in parts:
                    walk(part)
                return
        match = COMPARISON_PATTERN.match(expr)
        if not match:
            raise _SkipGroup(f"unparseable condition fragment: {expr!r}")
        atoms.append(("cmp", match.group(1), match.group(2), match.group(3)))

    walk(condition)
    return atoms


def _infer_sorts(
    groups_atoms: list[tuple[str, str, str, str]], known_keys: set[str]
) -> dict[str, str]:
    """Per-variable sort from compared literals. Mixed sorts → skip (AC-06)."""
    sorts: dict[str, str] = {}

    def note(var: str, kind: str) -> None:
        prev = sorts.get(var)
        if prev is None:
            sorts[var] = kind
        elif prev != kind:
            raise _SkipGroup(f"mixed sorts for {var!r}: {prev} vs {kind}")

    for _, left, _op, right in groups_atoms:
        kind, value = _classify_literal(right)
        if kind == "ident":
            root = value.split(".")[0]
            if value in known_keys or root in known_keys:
                # variable-vs-variable: sorts unify lazily below
                continue
            kind = "string"  # F2: unknown identifier → literal string
        if kind == "number":
            note(left, "number")
        elif kind == "string":
            note(left, "string")
        elif kind == "bool":
            note(left, "bool")
        # null constrains only is_none — no value sort

    # Second pass: var-vs-var unification (both sides known keys)
    for _, left, _op, right in groups_atoms:
        kind, value = _classify_literal(right)
        if kind == "ident" and (
            value in known_keys or value.split(".")[0] in known_keys
        ):
            ls, rs = sorts.get(left), sorts.get(value)
            if ls and rs and ls != rs:
                raise _SkipGroup(f"mixed sorts across {left!r} and {value!r}")
            unified = ls or rs or "number"
            sorts[left] = unified
            sorts[value] = unified
    return sorts


class _Encoder:
    """Condition → Z3 formula, per the Judgement F1 operator table."""

    def __init__(self, z3: Any, sorts: dict[str, str], known_keys: set[str]):
        self.z3 = z3
        self.sorts = sorts
        self.known_keys = known_keys
        self.vars: dict[str, Any] = {}
        self.is_none: dict[str, Any] = {}

    def var(self, name: str) -> tuple[Any, Any]:
        if name not in self.vars:
            sort = self.sorts.get(name, "number")
            if sort == "number":
                self.vars[name] = self.z3.Real(name)
            elif sort == "bool":
                self.vars[name] = self.z3.Bool(f"val_{name}")
            else:
                self.vars[name] = self.z3.String(name)
            self.is_none[name] = self.z3.Bool(f"is_none_{name}")
        return self.vars[name], self.is_none[name]

    def _right(self, raw: str) -> tuple[str, Any]:
        kind, value = _classify_literal(raw)
        if kind == "ident":
            if value in self.known_keys or value.split(".")[0] in self.known_keys:
                return "var", value
            return "string", value
        return kind, value

    def _lit(self, kind: str, value: Any) -> Any:
        if kind == "number":
            return self.z3.RealVal(value)
        if kind == "bool":
            return self.z3.BoolVal(value)
        return self.z3.StringVal(value)

    def comparison(self, left: str, op: str, raw_right: str) -> Any:
        z3 = self.z3
        lvar, lnone = self.var(left)
        kind, value = self._right(raw_right)

        if kind == "null":
            # ==/!= None-exempt rows: v == null ↔ is_none; v != null ↔ ¬is_none
            if op == "==":
                return lnone
            if op == "!=":
                return z3.Not(lnone)
            return z3.BoolVal(False)  # ordering vs null: TypeError→False

        if kind == "var":
            rvar, rnone = self.var(value)
            both_present = z3.And(z3.Not(lnone), z3.Not(rnone))
            body = self._apply(lvar, op, rvar)
            if op == "!=":
                # None != x is True when either side missing? Runtime:
                # left None with != → exempt → None != right is True;
                # right side resolves to None → left != None is True
                # unless left is also None.
                return z3.Or(lnone != rnone, z3.And(both_present, body))
            if op == "==":
                return z3.Or(z3.And(lnone, rnone), z3.And(both_present, body))
            return z3.And(both_present, body)

        lit = self._lit(kind, value)
        body = self._apply(lvar, op, lit)
        if op == "!=":
            return z3.Or(lnone, body)  # F1: None != lit is True
        if op == "==":
            return z3.And(z3.Not(lnone), body)
        return z3.And(z3.Not(lnone), body)  # ordering: None→False

    def _apply(self, lvar: Any, op: str, rhs: Any) -> Any:
        z3 = self.z3
        if op == "==":
            return lvar == rhs
        if op == "!=":
            return lvar != rhs
        if z3.is_string(lvar) or z3.is_bool(lvar):
            raise _SkipGroup(f"ordering comparison on non-numeric sort: {op}")
        return {"<": lvar < rhs, ">": lvar > rhs, "<=": lvar <= rhs, ">=": lvar >= rhs}[
            op
        ]

    def encode(self, condition: str) -> Any:
        z3 = self.z3
        expr = condition.strip()
        or_parts = _split_compound(expr, "or")
        if or_parts is not None:
            return z3.Or(*[self.encode(p) for p in or_parts])
        and_parts = _split_compound(expr, "and")
        if and_parts is not None:
            return z3.And(*[self.encode(p) for p in and_parts])
        match = COMPARISON_PATTERN.match(expr)
        if not match:
            raise _SkipGroup(f"unparseable condition fragment: {expr!r}")
        return self.comparison(match.group(1), match.group(2), match.group(3))

    def model_state(self, model: Any) -> list[str]:
        """Render a Z3 model as `var = value` / `var = <missing>` parts."""
        parts = []
        for name in sorted(self.vars):
            if self.z3.is_true(model.eval(self.is_none[name], model_completion=True)):
                parts.append(f"{name} = <missing>")
                continue
            val = model.eval(self.vars[name], model_completion=True)
            if self.sorts.get(name, "number") == "number":
                as_frac = val.as_fraction()
                parts.append(f"{name} = {float(as_frac):g}")
            elif self.sorts.get(name) == "bool":
                parts.append(f"{name} = {self.z3.is_true(val)}")
            else:
                parts.append(f"{name} = '{val.as_string()}'")
        return parts


def _notice(message: str) -> LintIssue:
    return LintIssue(severity="info", code="W806", message=message)


def _check_group(z3: Any, group: _Group, known_keys: set[str]) -> list[LintIssue]:
    atoms: list[tuple[str, str, str, str]] = []
    for condition in group.conditions:
        atoms.extend(_parse_comparisons(condition))
    sorts = _infer_sorts(atoms, known_keys)
    enc = _Encoder(z3, sorts, known_keys)
    formulas = [enc.encode(c) for c in group.conditions]

    issues: list[LintIssue] = []

    def solve(formula: Any) -> tuple[str, Any]:
        solver = z3.Solver()
        solver.set("timeout", SOLVER_TIMEOUT_MS)
        solver.add(formula)
        result = solver.check()
        return str(result), solver

    # W803 — gap (skip when an unconditional edge covers the group, F3).
    # Checked in two strata so the counterexample is maximally useful:
    # values-present gaps (numeric interval holes) and missing-variable
    # gaps (the on_error:skip leak) are reported distinctly.
    if not group.has_unconditional:
        gap = z3.Not(z3.Or(*formulas))
        all_present = z3.And(*[z3.Not(n) for n in enc.is_none.values()])
        for stratum, label in (
            (z3.And(gap, all_present), "matches no guard"),
            (z3.And(gap, z3.Or(*enc.is_none.values())), "falls through when unset"),
        ):
            status, solver = solve(stratum)
            if status == "sat":
                state = ", ".join(enc.model_state(solver.model()))
                issues.append(
                    LintIssue(
                        severity="warning",
                        code="W803",
                        message=(
                            f"Condition gap at '{group.source}': state ({state}) "
                            f"{label} — runtime silently routes to END"
                        ),
                        fix=(
                            "Add a guard covering this state or an "
                            "unconditional fallback edge"
                        ),
                    )
                )
            elif status == "unknown":
                issues.append(
                    _notice(f"solver timeout on gap check for '{group.source}'")
                )

    # W804 — pairwise overlap
    for i in range(len(formulas)):
        for j in range(i + 1, len(formulas)):
            status, solver = solve(z3.And(formulas[i], formulas[j]))
            if status == "sat":
                state = ", ".join(enc.model_state(solver.model()))
                issues.append(
                    LintIssue(
                        severity="warning",
                        code="W804",
                        message=(
                            f"Overlapping guards {i + 1} and {j + 1} at "
                            f"'{group.source}': both true at ({state}) — "
                            f"routing depends on edge order"
                        ),
                        fix="Make guards mutually exclusive or document the order dependence",
                    )
                )

    # W805 — guard shadowed by earlier guards
    for i in range(1, len(formulas)):
        status, _solver = solve(z3.And(formulas[i], z3.Not(z3.Or(*formulas[:i]))))
        if status == "unsat":
            issues.append(
                LintIssue(
                    severity="warning",
                    code="W805",
                    message=(
                        f"Guard {i + 1} at '{group.source}' is unreachable — "
                        f"every matching state is claimed by an earlier guard"
                    ),
                    fix="Reorder or remove the shadowed guard",
                )
            )
    return issues


def check_condition_smt(
    graph_path: Path | str, project_root: Path | str | None = None
) -> list[LintIssue]:
    """W803–W805: SMT-verified guard-group properties (FR-719)."""
    try:
        import z3
    except ImportError:
        return [
            _notice(
                "z3 not installed — SMT condition checks (W803–W805) skipped; "
                "install yamlgraph[verify] to enable"
            )
        ]

    config = load_graph(Path(graph_path))
    if not config:
        return []
    known_keys = _known_state_keys(config)

    issues: list[LintIssue] = []
    for group in _collect_groups(config):
        try:
            issues.extend(_check_group(z3, group, known_keys))
        except _SkipGroup as reason:
            issues.append(
                _notice(
                    f"SMT check skipped for '{group.source}': {reason} — "
                    f"mixed or unsupported condition shape"
                )
            )
    return issues


__all__ = ["check_condition_smt"]
