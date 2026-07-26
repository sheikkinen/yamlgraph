#!/usr/bin/env python3
"""Direct-import dependency scanner (FR-761).

Walks Python source under yamlgraph/ (core + optional feature surfaces),
examples/, scripts/, and tests/, extracts every third-party import via AST
(not just top-level `from X import Y` lines — nested/lazy imports inside
functions and try/except blocks are included), and verifies each resolved
distribution is declared somewhere in pyproject.toml (core dependencies or
any optional-dependencies extra).

Ownership model (frozen by FR-761 judgement):
    - yamlgraph/ (core + optional feature surfaces): an import is
      satisfied if its distribution is declared in EITHER core
      dependencies OR any optional extra. This never charges an
      optional-extra import to core (FR-761 C-4) — the module living
      under yamlgraph/ does not force core ownership.
    - examples/, scripts/, tests/: report-only. Findings are always
      printed but never fail --strict (FR-761 AC-09; FR-762 owns
      flipping specific example roots to strict later).

Known pending gaps: a small number of currently-undeclared imports are
already dispositioned to a sibling FR (FR-760's langchain-core, FR-762's
example/provider dependency taxonomy). These are tracked explicitly in
PENDING_GAPS below — visible in every run, never silently ignored — so
this gate does not fail CI for defects already owned and scheduled
elsewhere, while still catching any *new* undeclared import immediately.

Usage:
    python scripts/direct_import_scan.py           # summary + all findings
    python scripts/direct_import_scan.py --strict  # exit 1 on core failures
    python scripts/direct_import_scan.py --detail  # show every import site

FR-761: Reproducible Dependency Governance.
"""

from __future__ import annotations

import ast
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dependency_rationale import parse_pyproject_dependencies  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"

# Path classes: core (strict) vs report-only (examples/scripts/tests).
CORE_ROOTS = ("yamlgraph",)
REPORT_ONLY_ROOTS = ("examples", "scripts", "tests")

# First-party top-level module names excluded from the scan (never a
# third-party dependency regardless of directory).
FIRST_PARTY = {"yamlgraph", "examples", "scripts", "tests", "capabilities"}

# Import name -> distribution name, for cases where they differ. Anything
# not listed here is assumed to have an identical import/distribution name
# (e.g. "pydantic" -> "pydantic").
IMPORT_TO_DIST: dict[str, str] = {
    "yaml": "pyyaml",
    "dotenv": "python-dotenv",
    "google": "protobuf",  # google.protobuf.* usage in this repo
    "bs4": "beautifulsoup4",
    "ddgs": "ddgs",
    "z3": "z3-solver",
    "a2a": "a2a-sdk",
    "statemachine_engine": "statemachine-engine",
    "langgraph_checkpoint_sqlite": "langgraph-checkpoint-sqlite",
    "langgraph_checkpoint_redis": "langgraph-checkpoint-redis",
}

# Known, already-dispositioned undeclared imports pending a sibling FR's
# fix. Format: import name -> (owning FR, human note). These are always
# reported (never hidden) but do not fail --strict. Remove an entry once
# its owning FR declares the dependency — a stale entry here would then be
# harmless (the import will simply resolve as declared and stop matching
# the "undeclared" branch).
PENDING_GAPS: dict[str, str] = {
    "litellm": "FR-762 — Replicate provider frozen table: declare litellm explicitly in replicate extra",
    "starlette": "FR-762 — A2A/openai-proxy frozen table: declare starlette explicitly in a2a extra",
    "protobuf": "FR-762 — A2A frozen table: declare protobuf explicitly in a2a extra (google.protobuf import)",
    "langchain_core": "FR-760 — declares langchain-core as an explicit core dependency (PR open at scanner authoring time); this worktree predates that merge",
}


@dataclass
class Finding:
    file: str
    import_name: str
    distribution: str
    line: int
    path_class: str  # "core" | "report_only"


@dataclass
class ScanResult:
    findings: list[Finding] = field(default_factory=list)
    core_failures: list[Finding] = field(default_factory=list)
    pending: list[Finding] = field(default_factory=list)


def _classify_path(
    path: Path,
    repo_root: Path,
    core_roots: tuple[str, ...],
    report_only_roots: tuple[str, ...],
) -> str | None:
    """Return "core", "report_only", or None (excluded) for a scanned file."""
    try:
        rel = path.relative_to(repo_root)
    except ValueError:
        rel = path
    top = rel.parts[0] if rel.parts else ""
    if top in core_roots:
        return "core"
    if top in report_only_roots:
        return "report_only"
    return None


def _iter_python_files(repo_root: Path, roots: tuple[str, ...]) -> list[Path]:
    files: list[Path] = []
    for root_name in roots:
        root = repo_root / root_name
        if not root.exists():
            continue
        for f in root.rglob("*.py"):
            if "__pycache__" in f.parts or ".venv" in f.parts:
                continue
            files.append(f)
    return files


def _extract_imports(path: Path) -> list[tuple[str, int]]:
    """Return (top_level_import_name, line_number) pairs for a file.

    Uses ast.walk (not just top-level statements) so lazy/nested imports
    inside functions or try/except blocks are caught. Relative imports
    (level > 0) are excluded — they are always first-party by definition.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return []

    results: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                results.append((alias.name.split(".")[0], node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                continue
            if node.module:
                results.append((node.module.split(".")[0], node.lineno))
    return results


def _resolve_distribution(import_name: str) -> str:
    return IMPORT_TO_DIST.get(import_name, import_name)


def _normalize(name: str) -> str:
    """PEP 503 style normalization for distribution-name comparison.

    "langchain_anthropic" and "langchain-anthropic" (and "Langchain.Anthropic")
    all normalize to "langchain-anthropic" so import-name underscores match
    pyproject's hyphenated distribution names.
    """
    return re.sub(r"[-_.]+", "-", name).lower()


def _declared_distributions(deps_by_group: dict[str, list[str]]) -> set[str]:
    """Flatten every declared dependency across core + all optional extras.

    Returned set contains normalized names (see _normalize).
    """
    declared: set[str] = set()
    for group_deps in deps_by_group.values():
        declared.update(_normalize(d) for d in group_deps)
    return declared


def scan(
    stdlib_names: frozenset[str] | None = None,
    *,
    repo_root: Path = REPO_ROOT,
    pyproject_path: Path | None = None,
    core_roots: tuple[str, ...] = CORE_ROOTS,
    report_only_roots: tuple[str, ...] = REPORT_ONLY_ROOTS,
    pending_gaps: dict[str, str] | None = None,
) -> ScanResult:
    """Scan a repository tree and classify every third-party import.

    All location/config parameters are overridable so tests can point the
    scanner at an isolated fixture tree instead of the live repository.
    """
    stdlib = (
        stdlib_names if stdlib_names is not None else frozenset(sys.stdlib_module_names)
    )
    pyproject = (
        pyproject_path if pyproject_path is not None else (repo_root / "pyproject.toml")
    )
    pending = pending_gaps if pending_gaps is not None else PENDING_GAPS
    deps_by_group = parse_pyproject_dependencies(pyproject)
    declared = _declared_distributions(deps_by_group)

    result = ScanResult()
    all_files = _iter_python_files(repo_root, core_roots + report_only_roots)
    for path in all_files:
        path_class = _classify_path(path, repo_root, core_roots, report_only_roots)
        if path_class is None:
            continue
        rel_str = str(path.relative_to(repo_root))
        for import_name, lineno in _extract_imports(path):
            if import_name in stdlib or import_name in FIRST_PARTY:
                continue
            distribution = _resolve_distribution(import_name)
            if _normalize(distribution) in declared:
                continue
            finding = Finding(
                file=rel_str,
                import_name=import_name,
                distribution=distribution,
                line=lineno,
                path_class=path_class,
            )
            result.findings.append(finding)
            if path_class != "core":
                continue
            if distribution in pending or import_name in pending:
                result.pending.append(finding)
            else:
                result.core_failures.append(finding)
    return result


def _format_finding(f: Finding, pending_note: str | None = None) -> str:
    base = (
        f"{f.file}:{f.line}: import '{f.import_name}' -> distribution "
        f"'{f.distribution}' not declared in pyproject.toml (any group)"
    )
    if pending_note:
        return f"{base}  [PENDING: {pending_note}]"
    return base


def main() -> int:
    strict = "--strict" in sys.argv
    detail = "--detail" in sys.argv

    result = scan()

    print("=" * 60)
    print("Direct-Import Dependency Scan (FR-761)")
    print("=" * 60)
    print()
    print(f"Total findings (core + report-only): {len(result.findings)}")
    print(f"Core failures (blocking in --strict): {len(result.core_failures)}")
    print(f"Core pending (tracked, non-blocking):  {len(result.pending)}")
    print()

    if detail or result.core_failures:
        report_only = [f for f in result.findings if f.path_class == "report_only"]
        if result.core_failures:
            print("Core failures:")
            for f in result.core_failures:
                print(f"  ✗ {_format_finding(f)}")
        if result.pending:
            print("Core pending (see PENDING_GAPS):")
            for f in result.pending:
                note = PENDING_GAPS.get(f.distribution) or PENDING_GAPS.get(
                    f.import_name
                )
                print(f"  ⏳ {_format_finding(f, note)}")
        if detail and report_only:
            print("Report-only (examples/scripts/tests):")
            for f in report_only:
                print(f"  · {_format_finding(f)}")
        print()

    if result.core_failures:
        print(f"✗ {len(result.core_failures)} undeclared core direct import(s)")
        if strict:
            return 1
    else:
        print("✓ No undeclared (non-pending) core direct imports")

    return 0


if __name__ == "__main__":
    sys.exit(main())
