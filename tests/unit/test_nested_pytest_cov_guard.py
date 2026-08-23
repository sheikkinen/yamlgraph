"""Guard: nested pytest spawns must disable coverage (FR-860 blocker fix).

A test that spawns ``python -m pytest`` with the repo root reachable via
config discovery activates pytest-cov through ``addopts``. The nested
session then combines-and-deletes every ``.coverage.*`` file in the root,
destroying the outer run's live parallel data file. The outer coverage
lazily reopens a schema-less 0-byte DB and every subsequent test errors
with ``sqlite3.OperationalError: no such table: context`` — the mass-E
wall observed in the FR-860 record phase (2026-08-23).

Cure at the callsite: every nested pytest invocation in the test corpus
must pass ``--no-cov`` (or ``-p no:cov``) so pytest-cov never activates.
"""

import ast
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent.parent

COV_DISABLE_TOKENS = {"--no-cov", "no:cov"}


def _iter_string_lists(call: ast.Call):
    """Yield lists of string constants from a call's positional args."""
    for arg in call.args:
        if isinstance(arg, ast.List):
            yield [
                elt.value
                for elt in arg.elts
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
            ]


def _find_offending_spawns(path: Path) -> list[int]:
    """Return line numbers of subprocess pytest spawns without cov disable."""
    tree = ast.parse(path.read_text(), filename=str(path))
    offenders = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for strings in _iter_string_lists(node):
            has_pytest = "pytest" in strings or (
                "-m" in strings and "pytest" in strings
            )
            if not has_pytest:
                continue
            # Must be an executable invocation, not data: require it to be
            # the command token ("pytest" first, or after "-m").
            is_spawn = strings[:1] == ["pytest"] or (
                "-m" in strings
                and strings[strings.index("-m") + 1 : strings.index("-m") + 2]
                == ["pytest"]
            )
            if not is_spawn:
                continue
            if not COV_DISABLE_TOKENS & set(strings):
                offenders.append(node.lineno)
    return offenders


@pytest.mark.req("REQ-YG-609")
def test_nested_pytest_spawns_disable_coverage():
    """Every nested pytest spawn in tests/ must pass --no-cov.

    Otherwise the nested pytest-cov session deletes the outer run's
    parallel coverage data file and the whole suite errors from that
    point on (no such table: context).
    """
    violations = {}
    for path in sorted(TESTS_DIR.rglob("test_*.py")):
        if path.name == Path(__file__).name:
            continue
        offenders = _find_offending_spawns(path)
        if offenders:
            violations[str(path.relative_to(TESTS_DIR))] = offenders
    assert not violations, (
        "Nested pytest spawns without --no-cov clobber the outer coverage DB "
        f"(FR-860 record-phase mass-error root cause): {violations}"
    )
