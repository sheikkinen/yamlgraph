#!/usr/bin/env python3
"""Mechanical example dependency taxonomy generator (FR-762).

Discovers every "example root" under examples/ — a directory containing a
graph YAML, a Python app/CLI entry point (`if __name__ == "__main__"`), or a
README.md usage command — and classifies it as either:

    - extra-backed: every third-party import resolves to a distribution
      declared somewhere in pyproject.toml. `extra` names the extra(s)
      that a user must install for `pip install -e ".[<extra>]"` to be
      sufficient — prefers a single extra whose declared distributions
      fully cover the root's non-core import surface over crediting any
      partial owner (empty/None when the root needs nothing beyond
      core+dev).
    - externally-provisioned: at least one third-party import resolves to a
      distribution NOT declared anywhere in pyproject.toml. `external_reason`
      names the specific undeclared distribution(s). FR-762 C-4 forbids
      adding new pyproject dependencies outside its frozen table, so any
      newly-discovered gap here stays externally-provisioned rather than
      being silently declared.

Root discovery (mechanical, not hand-curated):
    - Every directory anywhere under `examples/` (at any nesting depth) is
      independently evaluated against the "example root" markers below —
      matching FR-762 R-2's literal definition (a nested directory such as
      `examples/dungeon_master/api/` or
      `examples/demos/interrupt/subgraphs/` gets its own row even though it
      sits inside another qualifying root).
    - A candidate directory becomes a root if it contains at least one of:
      a `*.yaml` file with a top-level `nodes:` key (a graph), a `.py` file
      with `if __name__ == "__main__"`, or a `README.md` containing a
      fenced code block with a recognizable runnable command (`python`,
      `yamlgraph`, `pytest`, `uvicorn`, `node`, `npm`, `docker`, `make`,
      `curl`, or `go` as the first token) — mere README.md *existence* is
      not sufficient, since fixture/docs READMEs without a usage command
      (e.g. `examples/plot_modeller/fixtures/README.md`) must not count.
    - Noise directories (`__pycache__`, VCS/tooling caches, hidden dirs)
      are pruned from the walk.

Reuses scripts/direct_import_scan.py's import extraction/resolution/
normalization so classification is consistent with the core/report-only
gate (FR-761) rather than a second parallel implementation (FR-762 R-3).

Usage:
    python scripts/example_taxonomy_scan.py            # print + write YAML
    python scripts/example_taxonomy_scan.py --check     # exit 1 if the
                                                          committed YAML is
                                                          stale vs. discovery
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dependency_rationale import parse_pyproject_dependencies  # noqa: E402
from direct_import_scan import (  # noqa: E402
    FIRST_PARTY,
    _extract_imports,
    _normalize,
    _resolve_distribution,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_ROOT = REPO_ROOT / "examples"
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"
TAXONOMY_PATH = REPO_ROOT / "examples" / "dependency-taxonomy.yaml"

# Directories that are pure tooling/VCS noise and never example content;
# pruned during the recursive walk so they can't be mistaken for roots
# or slow down discovery.
NOISE_DIR_NAMES = {
    "__pycache__",
    "node_modules",
    ".git",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    "htmlcov",
}

# First token of a fenced-code-block line that counts as a "README usage
# command" per FR-762 R-2. A README merely existing (e.g. a fixture-corpus
# README with no runnable command) does not make its directory a root.
_USAGE_CMD_RE = re.compile(
    r"^\$?\s*(python3?|yamlgraph|pytest|uvicorn|node|npm|docker|make|curl|go)\b"
)


def _has_graph_yaml(d: Path) -> bool:
    for f in d.glob("*.yaml"):
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if "nodes:" in text:
            return True
    return False


def _has_main_entrypoint(d: Path, repo_root: Path = REPO_ROOT) -> list[str]:
    entrypoints = []
    for f in d.glob("*.py"):
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if '__name__ == "__main__"' in text or "__name__ == '__main__'" in text:
            entrypoints.append(str(f.relative_to(repo_root)))
    return entrypoints


def _has_readme_usage_command(d: Path) -> bool:
    readme = d / "README.md"
    if not readme.exists():
        return False
    try:
        text = readme.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return False
    in_fence = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence and _USAGE_CMD_RE.match(stripped):
            return True
    return False


def _is_example_root(d: Path) -> bool:
    if not d.is_dir():
        return False
    if _has_graph_yaml(d) or _has_readme_usage_command(d):
        return True
    for f in d.glob("*.py"):
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if '__name__ == "__main__"' in text or "__name__ == '__main__'" in text:
            return True
    return False


def discover_roots(examples_root: Path = EXAMPLES_ROOT) -> list[Path]:
    """Mechanically discover every example root (see module docstring).

    Walks every directory under examples_root at any nesting depth —
    a directory qualifies as a root independent of whether its parent or
    a child directory also qualifies, matching FR-762 R-2's literal
    "any directory under examples/" definition.
    """
    roots: list[Path] = []
    for dirpath, dirnames, _filenames in os.walk(examples_root):
        dirnames[:] = sorted(
            name
            for name in dirnames
            if name not in NOISE_DIR_NAMES and not name.startswith(".")
        )
        current = Path(dirpath)
        if current == examples_root:
            continue
        if _is_example_root(current):
            roots.append(current)
    return sorted(roots)


def _root_imports(root: Path) -> list[str]:
    """Every extracted top-level import name under a root, recursively."""
    names: list[str] = []
    for f in root.rglob("*.py"):
        if "__pycache__" in f.parts:
            continue
        for import_name, _lineno, _nested in _extract_imports(f):
            names.append(import_name)
    return names


def _extras_covering(
    required_norms: set[str], deps_by_group: dict[str, list[str]]
) -> list[str]:
    """Return the extra(s) needed so `pip install -e ".[<extra>]"` alone
    installs every distribution in required_norms.

    Prefers a single extra whose declared distributions are a superset of
    required_norms (the common case, and what "extra-backed by a named
    extra" means per FR-762 R-2/AC-02) over unioning several partial
    owners — a partial owner alone is not a complete install story.
    Falls back to a minimal greedy combination only when no single extra
    covers everything (still declared, per the caller's undeclared check,
    just split across more than one group).
    """
    if not required_norms:
        return []
    group_norms = {
        group: {_normalize(d) for d in deps}
        for group, deps in deps_by_group.items()
        if group not in {"core", "dev"}
    }
    full_owners = sorted(
        group for group, norms in group_norms.items() if required_norms <= norms
    )
    if full_owners:
        return [full_owners[0]]

    remaining = set(required_norms)
    chosen: list[str] = []
    while remaining:
        best_group, best_covered = None, set()
        for group, norms in group_norms.items():
            covered = remaining & norms
            if len(covered) > len(best_covered):
                best_group, best_covered = group, covered
        if best_group is None:
            break
        chosen.append(best_group)
        remaining -= best_covered
    return sorted(chosen)


def _local_module_names(root: Path, examples_root: Path = EXAMPLES_ROOT) -> set[str]:
    """Names importable as `import <name>` via a sys.path insert of this root
    or one of its subdirectories (the common example test-fixture idiom).

    Includes every .py file stem and every subdirectory name found anywhere
    under the root, so `import tools` from examples/rag/tools/__init__.py
    or `import canon_tools` from examples/novel_fandom/nodes/canon_tools.py
    are recognized as local, not third-party.

    Also walks upward from `root` to `examples_root`, adding each ancestor
    level's direct children as local names. This covers a nested root
    (e.g. `examples/fsm-router/tests/`, discovered as its own root per
    FR-762 R-2) whose test suite imports a *sibling* package one level up
    (`examples/fsm-router/actions/`) rather than something under its own
    subtree — the sys.path-insert idiom is commonly rooted at the parent
    example package, not at the nested root itself.
    """
    names: set[str] = set()
    for f in root.rglob("*.py"):
        if "__pycache__" in f.parts:
            continue
        names.add(f.stem)
    for d in root.rglob("*"):
        if d.is_dir() and "__pycache__" not in d.parts:
            names.add(d.name)

    ancestor = root.parent
    while True:
        try:
            ancestor.relative_to(examples_root)
        except ValueError:
            break
        for child in ancestor.iterdir():
            if child.name.startswith(".") or child.name in NOISE_DIR_NAMES:
                continue
            names.add(child.stem if child.is_file() else child.name)
        if ancestor == examples_root:
            break
        ancestor = ancestor.parent
    return names


def classify_root(
    root: Path,
    stdlib: frozenset[str],
    declared: set[str],
    deps_by_group: dict[str, list[str]],
    repo_root: Path = REPO_ROOT,
    examples_root: Path = EXAMPLES_ROOT,
) -> dict:
    local_names = _local_module_names(root, examples_root)
    undeclared: list[str] = []
    required_norms: set[str] = set()
    for import_name in _root_imports(root):
        if (
            import_name in stdlib
            or import_name in FIRST_PARTY
            or import_name in local_names
        ):
            continue
        distribution = _resolve_distribution(import_name)
        norm = _normalize(distribution)
        if norm not in declared:
            undeclared.append(distribution)
            continue
        required_norms.add(norm)

    rel = str(root.relative_to(repo_root))
    entrypoints = _has_main_entrypoint(root, repo_root)
    if _has_graph_yaml(root):
        entrypoints = entrypoints + [
            str(f.relative_to(repo_root))
            for f in sorted(root.glob("*.yaml"))
            if "nodes:" in f.read_text(encoding="utf-8")
        ]

    if undeclared:
        return {
            "path": rel,
            "status": "externally-provisioned",
            "external_reason": (
                "Undeclared distribution(s) not in FR-762's frozen table: "
                + ", ".join(sorted(set(undeclared)))
            ),
            "entrypoints": sorted(set(entrypoints)),
        }
    return {
        "path": rel,
        "status": "extra-backed",
        "extra": _extras_covering(required_norms, deps_by_group) or None,
        "entrypoints": sorted(set(entrypoints)),
    }


def build_taxonomy(
    examples_root: Path = EXAMPLES_ROOT,
    pyproject_path: Path = PYPROJECT_PATH,
    repo_root: Path = REPO_ROOT,
) -> list[dict]:
    stdlib = frozenset(sys.stdlib_module_names)
    deps_by_group = parse_pyproject_dependencies(pyproject_path)
    declared: set[str] = set()
    for group_deps in deps_by_group.values():
        declared.update(_normalize(d) for d in group_deps)

    rows = []
    for root in discover_roots(examples_root):
        rows.append(
            classify_root(
                root, stdlib, declared, deps_by_group, repo_root, examples_root
            )
        )
    return rows


def main() -> int:
    check = "--check" in sys.argv
    rows = build_taxonomy()
    output = {
        "# NOTE": (
            "Generated by scripts/example_taxonomy_scan.py (FR-762). Do not "
            "hand-edit — regenerate after adding/removing example roots or "
            "pyproject.toml dependency changes."
        ),
        "examples": rows,
    }
    rendered = yaml.dump(output, sort_keys=False, default_flow_style=False, width=100)

    if check:
        if not TAXONOMY_PATH.exists():
            print(
                f"✗ {TAXONOMY_PATH} does not exist — run without --check to generate it"
            )
            return 1
        current = TAXONOMY_PATH.read_text(encoding="utf-8")
        if current != rendered:
            print(
                f"✗ {TAXONOMY_PATH} is stale — re-run scripts/example_taxonomy_scan.py"
            )
            return 1
        print(f"✓ {TAXONOMY_PATH} is up to date ({len(rows)} example roots)")
        return 0

    TAXONOMY_PATH.write_text(rendered, encoding="utf-8")
    externally_provisioned = [
        r for r in rows if r["status"] == "externally-provisioned"
    ]
    print(f"Wrote {TAXONOMY_PATH} ({len(rows)} example roots)")
    print(f"  extra-backed: {len(rows) - len(externally_provisioned)}")
    print(f"  externally-provisioned: {len(externally_provisioned)}")
    for r in externally_provisioned:
        print(f"    · {r['path']}: {r['external_reason']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
