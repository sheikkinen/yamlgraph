#!/usr/bin/env python3
"""Shared coverage-context boundary for requirement traceability (FR-850).

Single source of truth for reading ``.coverage`` context data. Consumed by
both ``req_coverage.py --implementation`` and ``req_audit_questions.py`` —
no second resolution truth (AC-01, AC-07).

Contract:
- Hard refusal (``CoverageContextError``) on a missing, context-free, or
  poisoned coverage DB — never a warning-and-continue (AC-03).
- ``[param]`` suffixes are normalized away at the boundary so parametrized
  contexts match AST marker keys (AC-05).
- ``derive_resolution`` is the shared five-class witness classification.
- ``reconcile_modules`` partitions declared modules into measured
  never-hit vs unmeasured-by-this-run (AC-08).

Recording command (the only instrument state this boundary accepts):
    COVERAGE_CORE=ctrace pytest tests/unit tests/integration -q \
        --cov=yamlgraph --cov-context=test
(sequential — do NOT use ``-n auto``; xdist workers drop contexts, and the
sysmon core silently records first-test-wins poisoned contexts.)
"""

from __future__ import annotations

import ast
import re
import sqlite3
from pathlib import Path

#: Tripwire threshold: distinct recorded contexts must be at least this
#: fraction of distinct tagged test ids, else the DB is poisoned (AC-03).
POISON_RATIO = 0.25

REMEDY = (
    "Re-record with: COVERAGE_CORE=ctrace pytest tests/unit "
    "tests/integration -q --cov=yamlgraph --cov-context=test "
    "(sequential — do not use -n auto)."
)


class CoverageContextError(RuntimeError):
    """The .coverage DB cannot serve as a witness instrument (AC-03)."""


def normalize_context(context: str) -> str:
    """Normalize a raw coverage context to an AST marker key (AC-05).

    ``tests/unit/test_p.py::TestC::test_q[case-1]|run`` →
    ``test_p::TestC::test_q``
    """
    test_id = context.split("|")[0]
    parts = test_id.split("::")
    parts[0] = Path(parts[0]).stem
    parts[-1] = re.sub(r"\[.*\]$", "", parts[-1])
    return "::".join(parts)


def load_coverage_contexts(
    root: Path, tagged_test_ids: set[str] | None = None
) -> tuple[dict[str, set[str]], set[str]]:
    """Load (test_id → source files, recorded test ids) from ``.coverage``.

    Both the map keys and the recorded set are normalized marker keys.
    Raises ``CoverageContextError`` when the DB is missing, context-free,
    or poisoned (distinct contexts < POISON_RATIO × tagged tests).
    """
    db_path = root / ".coverage"
    if not db_path.exists():
        raise CoverageContextError(
            f"No .coverage database found at {db_path}. {REMEDY}"
        )

    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT context FROM context WHERE context != ''"
        ).fetchall()
        if not rows:
            raise CoverageContextError(
                f".coverage DB at {db_path} has no test contexts. {REMEDY}"
            )
        recorded = {normalize_context(ctx) for (ctx,) in rows}
        link_rows = conn.execute(
            "SELECT DISTINCT f.path, ctx.context "
            "FROM line_bits lb "
            "JOIN file f ON lb.file_id = f.id "
            "JOIN context ctx ON lb.context_id = ctx.id "
            "WHERE ctx.context != ''"
        ).fetchall()
    finally:
        conn.close()

    if tagged_test_ids and len(recorded) < POISON_RATIO * len(tagged_test_ids):
        raise CoverageContextError(
            f"Poisoned .coverage DB at {db_path}: {len(recorded)} distinct "
            f"test contexts for {len(tagged_test_ids)} tagged tests "
            f"(< {POISON_RATIO} ratio — first-test-wins context poisoning, "
            f"typically the sysmon core or -n auto). {REMEDY}"
        )

    coverage_map: dict[str, set[str]] = {}
    root_str = str(root) + "/"
    for file_path, context in link_rows:
        rel_path = file_path.replace(root_str, "")
        if rel_path.startswith("yamlgraph/") and "/test" not in rel_path:
            coverage_map.setdefault(normalize_context(context), set()).add(rel_path)
    return coverage_map, recorded


def reconcile_modules(
    declared_modules: list[str], resolved_files: set[str]
) -> tuple[list[str], list[str]]:
    """Partition declared modules into (never_hit_measured, unmeasured).

    Only declarations under ``yamlgraph/`` are measured by the coverage
    run; anything else is reported as unmeasured, never never-hit (AC-08,
    C-3). A directory declaration is hit when any resolved file lives
    under it; a file declaration requires an exact match.
    """
    never_hit: list[str] = []
    unmeasured: list[str] = []
    for module in declared_modules:
        mod = module.rstrip("/")
        if not (mod == "yamlgraph" or mod.startswith("yamlgraph/")):
            unmeasured.append(module)
            continue
        if mod.endswith(".py"):
            hit = mod in resolved_files
        else:
            # A bare declaration may be a directory or an extensionless
            # module file ("yamlgraph/edge_compiler") — accept either.
            prefix = mod + "/"
            hit = any(
                f == mod or f == mod + ".py" or f.startswith(prefix)
                for f in resolved_files
            )
        if not hit:
            never_hit.append(module)
    return never_hit, unmeasured


# ── AST witness resolution (moved from req_coverage.py, FR-850 AC-01) ──────


def _module_to_path(module: str) -> str:
    """Convert dotted module name to filesystem path.

    ``yamlgraph.utils.llm_factory`` → ``yamlgraph/utils/llm_factory.py``
    ``yamlgraph.cli`` → ``yamlgraph/cli/__init__.py`` (if directory exists)
    """
    parts = module.split(".")
    candidate = "/".join(parts) + ".py"
    pkg_init = "/".join(parts) + "/__init__.py"
    root = Path(__file__).parent.parent
    if (root / candidate).exists():
        return candidate
    if (root / pkg_init).exists():
        return pkg_init
    # Default: assume .py file (even if missing — the import may be removed code)
    return candidate


def _collect_yamlgraph_imports(nodes: list[ast.stmt]) -> set[str]:
    """Extract yamlgraph/ file paths from import statements in AST nodes."""
    paths: set[str] = set()
    for node in ast.walk(ast.Module(body=nodes, type_ignores=[])):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.startswith("yamlgraph")
        ):
            paths.add(_module_to_path(node.module))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("yamlgraph"):
                    paths.add(_module_to_path(alias.name))
    return paths


def _collect_mock_patch_targets(nodes: list[ast.stmt]) -> set[str]:
    """Extract yamlgraph/ file paths from mock.patch("yamlgraph...") calls."""
    paths: set[str] = set()
    for node in ast.walk(ast.Module(body=nodes, type_ignores=[])):
        if not isinstance(node, ast.Call):
            continue
        # Match @patch("yamlgraph.x.y.z") or mock.patch("yamlgraph.x.y.z")
        func = node.func
        is_patch = (isinstance(func, ast.Attribute) and func.attr == "patch") or (
            isinstance(func, ast.Name) and func.id == "patch"
        )
        if not is_patch or not node.args:
            continue
        arg = node.args[0]
        if (
            isinstance(arg, ast.Constant)
            and isinstance(arg.value, str)
            and arg.value.startswith("yamlgraph")
        ):
            # "yamlgraph.utils.llm_factory.create_llm" → "yamlgraph.utils.llm_factory"
            dotted = arg.value.rsplit(".", 1)[0]
            paths.add(_module_to_path(dotted))
    return paths


def _extract_imports_from_test(filepath: Path, test_key: str) -> set[str]:
    """Extract yamlgraph/ source file paths from a test file using AST analysis.

    Parses both module-level imports and inline imports within the specific
    test function identified by *test_key* (``stem::Class::method`` or
    ``stem::function``).  Also resolves ``mock.patch("yamlgraph.X.Y.func")``
    targets.

    Returns set of relative paths like ``{"yamlgraph/utils/llm_factory.py"}``.
    """
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"), filename=str(filepath))
    except SyntaxError:
        return set()

    # Parse test_key: "test_foo::ClassName::method" or "test_foo::func"
    parts = test_key.split("::")
    # parts[0] is stem (ignored — we already have filepath)
    class_name = parts[1] if len(parts) == 3 else None
    func_name = parts[-1]

    # 1. Module-level imports (always included)
    module_nodes = [n for n in tree.body if isinstance(n, ast.Import | ast.ImportFrom)]
    paths = _collect_yamlgraph_imports(module_nodes)

    # 2. Find the specific test function and extract inline imports + mock targets
    func_body: list[ast.stmt] = []
    for node in ast.iter_child_nodes(tree):
        if class_name and isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if (
                    isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef)
                    and item.name == func_name
                ):
                    func_body = item.body + item.decorator_list  # type: ignore[operator]
                    break
            break
        elif (
            not class_name
            and isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            and node.name == func_name
        ):
            func_body = node.body + node.decorator_list  # type: ignore[operator]
            break

    if func_body:
        paths |= _collect_yamlgraph_imports(func_body)
        paths |= _collect_mock_patch_targets(func_body)

    # Also check class-level decorators for mock.patch
    if class_name:
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                paths |= _collect_mock_patch_targets(node.decorator_list)
                break

    return paths


# ── Five-class witness derivation (moved from req_audit_questions.py) ──────

RESOLUTION_CLASSES = (
    "coverage",
    "ast",
    "no-link-ran",
    "no-link-unrecorded",
    "doc-witness",
)


def _reads_repo_docs(test_file: Path) -> bool:
    """True when the test file references .md documents (doc-witness)."""
    try:
        tree = ast.parse(test_file.read_text(encoding="utf-8"), filename=str(test_file))
    except (OSError, SyntaxError):
        return False
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value.endswith(".md")
        ):
            return True
    return False


def derive_resolution(
    test_key: str,
    coverage_map: dict[str, set[str]],
    recorded_contexts: set[str],
    test_file: Path | None,
) -> tuple[str, list[str]]:
    """Classify one test's witness link (frozen enum) and resolved files."""
    cov_files = coverage_map.get(test_key, set())
    if cov_files:
        return "coverage", sorted(cov_files)
    if test_file is not None:
        ast_files = _extract_imports_from_test(test_file, test_key)
        if ast_files:
            return "ast", sorted(ast_files)
        if _reads_repo_docs(test_file):
            return "doc-witness", []
    if test_key in recorded_contexts:
        return "no-link-ran", []
    return "no-link-unrecorded", []
