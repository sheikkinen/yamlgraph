#!/usr/bin/env python3
"""Direct-import dependency scanner (FR-761).

Walks Python source under yamlgraph/ (core + optional feature surfaces),
examples/, scripts/, and tests/, extracts every third-party import via AST
(not just top-level `from X import Y` lines — nested/lazy imports inside
functions and try/except blocks are included), and verifies each resolved
distribution is declared somewhere in pyproject.toml (core dependencies or
any optional-dependencies extra).

Ownership model (frozen by FR-761 judgement, R-2):
    - yamlgraph/ core import surface: a *module-level* (unconditional)
      import must be declared in `[project.dependencies]` (core), UNLESS
      the file is a recognized optional feature surface (see
      PATH_PREFIX_OWNERS below), in which case it may also be satisfied
      by that surface's owning extra(s).
    - yamlgraph/ nested/lazy imports (inside a function or method body
      — NOT top-level try/except, which still executes at import time
      and is treated as module-level): these represent deferred,
      provider-selection-style
      loads (e.g. `utils/llm_providers.py` importing a different provider
      SDK per branch). They may be satisfied by declaration in core OR
      ANY optional extra — tightening this to per-file ownership would
      force every multi-provider factory file to enumerate every provider
      extra it might ever lazily import, which the FR's own enforcement
      notes identified as impractical. This is the one deliberately
      permissive corner of the model; everything else is owner-strict.
    - examples/, scripts/, tests/: report-only. Findings are always
      printed but never fail --strict (FR-761 AC-09; FR-762 owns
      flipping specific example roots to strict later). Local sibling
      modules/packages (first-party code living next to the importing
      file, e.g. `examples/plot_modeller/nodes/`) are excluded from
      findings entirely — they are not third-party distributions.

This closes the gap flagged in PR #463 review: previously ANY import
under yamlgraph/ passed if its distribution was declared under ANY
extra, meaning a new *required* core import would silently pass if it
happened to share a name with an unrelated extra's dependency. Now,
only nested/lazy imports get that flexibility; module-level imports in
files without an explicit owner mapping must be genuinely core.

Known pending gaps: a small number of currently-undeclared imports are
already dispositioned to a sibling FR (FR-760's langchain-core, FR-762's
example/provider dependency taxonomy). These are tracked explicitly in
PENDING_GAPS below, scoped to the exact file or directory surface they
were granted for — visible in every run, never silently ignored — so
this gate does not fail CI for defects already owned and scheduled
elsewhere, while still catching any *new* undeclared import (including
the same distribution name at any other surface) immediately.

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
    "tavily": "tavily-python",
    "chatterbox": "chatterbox-tts",
}

# Dotted-prefix distribution mapping for namespace packages (PR #463
# review round-2 P1): collapsing `langgraph.checkpoint.redis` to its
# top-level `langgraph` (declared in core) would let the actual
# `langgraph-checkpoint-redis` declaration disappear without the gate
# noticing. Longest dotted prefix wins; anything not listed falls back
# to top-level resolution via IMPORT_TO_DIST.
NAMESPACE_TO_DIST: dict[str, str] = {
    "langgraph.checkpoint.redis": "langgraph-checkpoint-redis",
    "langgraph.checkpoint.sqlite": "langgraph-checkpoint-sqlite",
    "google.protobuf": "protobuf",
}

# Known, already-dispositioned undeclared imports pending a sibling FR's
# fix. Format: (path prefix, import name) -> (owning FR, human note). The
# path prefix is an exact file path or a directory prefix relative to the
# repo root (POSIX-style) — the disposition applies ONLY to imports at
# that surface (PR #463 review P2: a name-only exemption would whitelist
# brand-new imports of the same distribution anywhere under yamlgraph/).
# Entries are always reported (never hidden) but do not fail --strict.
# Remove an entry once its owning FR declares the dependency.
PENDING_GAPS: dict[tuple[str, str], str] = {
    ("yamlgraph/utils/llm_providers.py", "litellm"): (
        "FR-762 — Replicate provider frozen table: declare litellm explicitly"
        " in replicate extra"
    ),
    ("yamlgraph/a2a", "starlette"): (
        "FR-762 — A2A frozen table: declare starlette explicitly in a2a extra"
    ),
    ("yamlgraph/cli/a2a_commands.py", "starlette"): (
        "FR-762 — A2A frozen table: declare starlette explicitly in a2a extra"
    ),
    ("yamlgraph/contrib/a2a_client.py", "starlette"): (
        "FR-762 — A2A frozen table: declare starlette explicitly in a2a extra"
    ),
    ("yamlgraph/a2a", "protobuf"): (
        "FR-762 — A2A frozen table: declare protobuf explicitly in a2a extra"
        " (google.protobuf import)"
    ),
    ("yamlgraph/cli/a2a_commands.py", "protobuf"): (
        "FR-762 — A2A frozen table: declare protobuf explicitly in a2a extra"
        " (google.protobuf import)"
    ),
    ("yamlgraph/contrib/a2a_client.py", "protobuf"): (
        "FR-762 — A2A frozen table: declare protobuf explicitly in a2a extra"
        " (google.protobuf import)"
    ),
    ("yamlgraph", "langchain_core"): (
        "FR-760 — declares langchain-core as an explicit core dependency"
        " (PR open at scanner authoring time); this worktree predates that"
        " merge. langchain_core is the effective runtime contract across"
        " core modules (executor, llm_factory, tools, streaming), so the"
        " disposition surface is yamlgraph/ itself; entry dies with FR-760."
    ),
}


# Path prefixes (relative to repo root, POSIX-style) recognized as
# optional yamlgraph/ feature surfaces: files whose module-level imports
# are only ever executed when that surface is actually used (the module
# itself is loaded lazily by callers, or is only reachable via the
# owning extra's entry point). Maps prefix -> owning extra name(s).
# A path matches if it equals a prefix exactly (file) or starts with
# "<prefix>/" (directory). Discovered by scanning yamlgraph/ for
# module-level imports not covered by [project.dependencies] (see
# scripts/direct_import_scan.py module docstring history / FR-761 PR
# #463 review). Extend this table with a new entry, rather than
# widening the any-declared-group check for nested imports, when a
# new optional surface is added.
PATH_PREFIX_OWNERS: dict[str, frozenset[str]] = {
    "yamlgraph/storage/serializers.py": frozenset({"redis-simple", "redis"}),
    "yamlgraph/storage/simple_redis.py": frozenset({"redis-simple"}),
    "yamlgraph/contrib/a2a_client.py": frozenset({"a2a"}),
    "yamlgraph/a2a": frozenset({"a2a"}),
    "yamlgraph/cli/a2a_commands.py": frozenset({"a2a"}),
    "yamlgraph/export/mcp.py": frozenset({"mcp"}),
    "yamlgraph/utils/fsm": frozenset({"fsm"}),
}


@dataclass
class Finding:
    file: str
    import_name: str
    distribution: str
    line: int
    path_class: str  # "core" | "report_only"
    nested: bool = False


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


def _extract_imports(path: Path) -> list[tuple[str, int, bool]]:
    """Return (top_level_import_name, line_number, is_nested) triples for a file.

    Uses ast.walk (not just top-level statements) so lazy/nested imports
    inside functions or try/except blocks are caught. `is_nested` is True
    only for imports that do NOT execute unconditionally at module import
    time: anything inside a function/method body or other deferred scope.
    Imports that are direct children of the module body, OR inside a
    top-level try/except/else/finally block, DO execute on import and are
    therefore module-level (PR #463 review P1: a top-level try-guarded
    import is still part of the core import surface). Relative imports
    (level > 0) are excluded — they are always first-party by definition.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return []

    module_level_ids: set[int] = set()
    stack: list[ast.stmt] = list(tree.body)
    while stack:
        node = stack.pop()
        module_level_ids.add(id(node))
        if isinstance(node, ast.Try):
            stack.extend(node.body)
            stack.extend(node.orelse)
            stack.extend(node.finalbody)
            for handler in node.handlers:
                stack.extend(handler.body)

    results: list[tuple[str, int, bool]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            nested = id(node) not in module_level_ids
            for alias in node.names:
                results.append((alias.name, node.lineno, nested))
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                continue
            if node.module:
                nested = id(node) not in module_level_ids
                results.append((node.module, node.lineno, nested))
    return results


def _resolve_distribution(import_name: str) -> str:
    """Map a (possibly dotted) import name to its distribution name.

    Longest dotted-prefix match in NAMESPACE_TO_DIST first (namespace
    packages ship submodule trees from separate distributions), then
    IMPORT_TO_DIST on the top-level segment, then the top-level segment
    itself.
    """
    parts = import_name.split(".")
    for length in range(len(parts), 0, -1):
        prefix = ".".join(parts[:length])
        if prefix in NAMESPACE_TO_DIST:
            return NAMESPACE_TO_DIST[prefix]
    top = parts[0]
    return IMPORT_TO_DIST.get(top, top)


def _owner_extras_for(rel_path_posix: str) -> frozenset[str] | None:
    """Return the owning extra(s) for a recognized optional yamlgraph/ surface.

    Matches an exact file entry, or a directory prefix ("<prefix>/..."),
    in PATH_PREFIX_OWNERS. Returns None if the path isn't a recognized
    optional surface (i.e. it's a core file: module-level imports must
    be declared in core dependencies).
    """
    for prefix, owners in PATH_PREFIX_OWNERS.items():
        if rel_path_posix == prefix or rel_path_posix.startswith(prefix + "/"):
            return owners
    return None


def _pending_note_for(
    rel_path_posix: str,
    import_name: str,
    distribution: str,
    pending: dict[tuple[str, str], str],
) -> str | None:
    """Return the pending-gap note covering this exact surface, if any.

    A pending entry (prefix, name) matches only when the finding's file is
    the prefix itself or lives under "<prefix>/" AND the name equals the
    import name or resolved distribution (PR #463 review P2: dispositions
    are surface-scoped, never global by name).
    """
    for (prefix, name), note in pending.items():
        if name not in (import_name, distribution):
            continue
        if rel_path_posix == prefix or rel_path_posix.startswith(prefix + "/"):
            return note
    return None


def _is_local_module(path: Path, import_name: str, repo_root: Path) -> bool:
    """Return True if `import_name` resolves to a first-party sibling module.

    Walks up from the importing file's directory to the repo root,
    checking at each level for a `<import_name>.py` file or
    `<import_name>/` package directory. This catches example-local
    helper modules (e.g. `examples/plot_modeller/nodes/`,
    `examples/daily_digest/api/`) that are only importable because the
    example inserts its own root onto `sys.path` — they are first-party
    code, not undeclared third-party distributions (FR-761 AC-12,
    report-only local-module exclusion; PR #463 review P2).
    """
    current = path.parent
    while True:
        if (current / f"{import_name}.py").exists():
            return True
        candidate_dir = current / import_name
        if candidate_dir.is_dir() and any(candidate_dir.glob("*.py")):
            return True
        if current == repo_root or current.parent == current:
            return False
        current = current.parent


def _sys_path_local_roots(path: Path, repo_root: Path) -> list[Path]:
    """Directories a file explicitly exposes via sys.path manipulation.

    Tests/examples routinely do
    ``sys.path.insert(0, str(Path(__file__).parent.parent / "src"))`` and
    then import first-party modules from that root; those imports are not
    third-party dependency gaps (PR #463 review round-2 P2). Deterministic
    approximation: when the source mentions ``sys.path``, every string
    constant (and every in-order constant segment chain of ``/``-joined
    Path expressions, e.g. ``... / "examples" / "book_translator"``) is a
    candidate fragment; fragments that resolve to an existing directory
    inside the repo — joined against the repo root or any ancestor of the
    importing file — become local roots. Evidence-based: an import only
    gets excluded when a matching module actually exists under a root.
    """
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    if "sys.path" not in source:
        return []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    fragments: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            segs: list[str] = []
            cur: ast.expr = node
            while isinstance(cur, ast.BinOp) and isinstance(cur.op, ast.Div):
                if isinstance(cur.right, ast.Constant) and isinstance(
                    cur.right.value, str
                ):
                    segs.append(cur.right.value)
                cur = cur.left
            if segs:
                fragments.add("/".join(reversed(segs)))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value
            if value and not value.startswith((".", "/")) and " " not in value:
                fragments.add(value)

    roots: list[Path] = []
    bases = [
        repo_root,
        *[p for p in path.parents if repo_root in p.parents or p == repo_root],
    ]
    for fragment in fragments:
        for base in bases:
            candidate = base / fragment
            if candidate.is_dir() and (
                candidate == repo_root or repo_root in candidate.parents
            ):
                roots.append(candidate)
    return roots


def _in_sys_path_roots(import_top: str, roots: list[Path]) -> bool:
    """True when `import_top` resolves to a module/package under a local root."""
    for root in roots:
        if (root / f"{import_top}.py").exists():
            return True
        candidate = root / import_top
        if candidate.is_dir() and any(candidate.glob("*.py")):
            return True
    return False


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


def _load_taxonomy_roots(taxonomy_path: Path) -> dict[str, str]:
    """Return {example root relative path: status} from a taxonomy YAML file."""
    import yaml as _yaml

    data = _yaml.safe_load(taxonomy_path.read_text(encoding="utf-8"))
    return {row["path"]: row["status"] for row in data.get("examples", [])}


def _taxonomy_status_for(
    rel_str: str, taxonomy_roots: dict[str, str]
) -> tuple[str | None, str | None]:
    """Longest-prefix match of a file's relative path against taxonomy roots.

    Returns (status, root_path) or (None, None) when the file falls under no
    taxonomy root (e.g. scripts/, tests/, or a non-example examples/ file).
    """
    match: tuple[str, str] | None = None
    for root_path, status in taxonomy_roots.items():
        if (rel_str == root_path or rel_str.startswith(root_path + "/")) and (
            match is None or len(root_path) > len(match[0])
        ):
            match = (root_path, status)
    return (match[1], match[0]) if match else (None, None)


def _local_names_for_root(root: Path) -> set[str]:
    """Names importable via a same-root sys.path-insert (the example-fixture
    idiom: `sys.path.insert(0, ...); import tools`). Matches FR-762's
    taxonomy classifier so files inside an extra-backed root are not
    misreported for importing their own local sibling modules.
    """
    names: set[str] = set()
    if not root.is_dir():
        return names
    for f in root.rglob("*.py"):
        if "__pycache__" in f.parts:
            continue
        names.add(f.stem)
    for d in root.rglob("*"):
        if d.is_dir() and "__pycache__" not in d.parts:
            names.add(d.name)
    return names


def scan(
    stdlib_names: frozenset[str] | None = None,
    *,
    repo_root: Path = REPO_ROOT,
    pyproject_path: Path | None = None,
    core_roots: tuple[str, ...] = CORE_ROOTS,
    report_only_roots: tuple[str, ...] = REPORT_ONLY_ROOTS,
    pending_gaps: dict[tuple[str, str], str] | None = None,
    taxonomy_path: Path | None = None,
) -> ScanResult:
    """Scan a repository tree and classify every third-party import.

    All location/config parameters are overridable so tests can point the
    scanner at an isolated fixture tree instead of the live repository.

    When `taxonomy_path` is given (FR-762 AC-08), files under an
    `extra-backed` example root (per `examples/dependency-taxonomy.yaml`)
    are held to the same strict standard as core: an undeclared import
    fails --strict unless pending. Files under an `externally-provisioned`
    root stay excused — the taxonomy row IS the allowlist entry, so no
    separate PENDING_GAPS note is needed for those known gaps. Local
    sibling-module imports (the sys.path-insert fixture idiom) are excluded
    per-root, matching the taxonomy classifier's own exclusion.
    """
    stdlib = (
        stdlib_names if stdlib_names is not None else frozenset(sys.stdlib_module_names)
    )
    pyproject = (
        pyproject_path if pyproject_path is not None else (repo_root / "pyproject.toml")
    )
    pending = pending_gaps if pending_gaps is not None else PENDING_GAPS
    deps_by_group = parse_pyproject_dependencies(pyproject)
    core_declared = {_normalize(d) for d in deps_by_group.get("core", [])}
    declared_any = _declared_distributions(
        deps_by_group
    )  # core + every extra, flattened
    taxonomy_roots = _load_taxonomy_roots(taxonomy_path) if taxonomy_path else {}
    local_names_cache: dict[str, set[str]] = {}

    result = ScanResult()
    all_files = _iter_python_files(repo_root, core_roots + report_only_roots)
    for path in all_files:
        path_class = _classify_path(path, repo_root, core_roots, report_only_roots)
        if path_class is None:
            continue
        rel_str = str(path.relative_to(repo_root))
        rel_posix = path.relative_to(repo_root).as_posix()
        taxonomy_status, taxonomy_root = _taxonomy_status_for(rel_str, taxonomy_roots)
        strict_via_taxonomy = (
            path_class == "report_only" and taxonomy_status == "extra-backed"
        )
        local_names: set[str] = set()
        if strict_via_taxonomy and taxonomy_root:
            if taxonomy_root not in local_names_cache:
                local_names_cache[taxonomy_root] = _local_names_for_root(
                    repo_root / taxonomy_root
                )
            local_names = local_names_cache[taxonomy_root]
        sys_path_roots: list[Path] | None = None
        for import_name, lineno, nested in _extract_imports(path):
            top = import_name.split(".")[0]
            if top in stdlib or top in FIRST_PARTY or top in local_names:
                continue
            if path_class == "report_only":
                if _is_local_module(path, top, repo_root):
                    continue
                if sys_path_roots is None:
                    sys_path_roots = _sys_path_local_roots(path, repo_root)
                if _in_sys_path_roots(top, sys_path_roots):
                    continue
            distribution = _resolve_distribution(import_name)
            normalized = _normalize(distribution)

            if path_class == "core":
                if nested:
                    # Deferred/lazy imports (provider-selection style):
                    # satisfied by core OR any declared extra.
                    allowed = declared_any
                else:
                    # Unconditional module-level imports: strict-core,
                    # unless this file is a recognized optional feature
                    # surface, in which case its owning extra(s) also count.
                    owners = _owner_extras_for(rel_posix)
                    allowed = core_declared
                    if owners:
                        for owner in owners:
                            allowed = allowed | {
                                _normalize(d) for d in deps_by_group.get(owner, [])
                            }
                if normalized in allowed:
                    continue
            else:
                if normalized in declared_any:
                    continue

            finding = Finding(
                file=rel_str,
                import_name=import_name,
                distribution=distribution,
                line=lineno,
                path_class=path_class,
                nested=nested,
            )
            result.findings.append(finding)
            if path_class != "core" and not strict_via_taxonomy:
                continue
            if _pending_note_for(rel_posix, import_name, distribution, pending):
                result.pending.append(finding)
            else:
                result.core_failures.append(finding)
    return result


def _expected_owner_label(f: Finding) -> str:
    """Human-readable label for the dependency group(s) a finding must satisfy."""
    if f.path_class != "core":
        return "any group (report-only)"
    if f.nested:
        return "core or any optional extra (deferred/lazy import)"
    owners = _owner_extras_for(f.file.replace("\\", "/"))
    if owners:
        return "core, or extra(s): " + ", ".join(sorted(owners))
    return "core (`[project.dependencies]`)"


def _format_finding(f: Finding, pending_note: str | None = None) -> str:
    base = (
        f"{f.file}:{f.line}: import '{f.import_name}' -> distribution "
        f"'{f.distribution}' not declared; expected owner: {_expected_owner_label(f)}"
    )
    if pending_note:
        return f"{base}  [PENDING: {pending_note}]"
    return base


def main() -> int:
    strict = "--strict" in sys.argv
    detail = "--detail" in sys.argv

    taxonomy_path = REPO_ROOT / "examples" / "dependency-taxonomy.yaml"
    result = scan(taxonomy_path=taxonomy_path if taxonomy_path.exists() else None)

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
                note = _pending_note_for(
                    f.file.replace("\\", "/"),
                    f.import_name,
                    f.distribution,
                    PENDING_GAPS,
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
