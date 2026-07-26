#!/usr/bin/env python3
"""Mechanical example dependency taxonomy generator (FR-762).

Discovers every "example root" under examples/ — a directory containing a
graph YAML, a Python app/CLI entry point (`if __name__ == "__main__"`), or a
README.md usage command — and classifies it as either:

    - extra-backed: every third-party import resolves to a distribution
      declared somewhere in pyproject.toml. `extra` names the specific
      optional-dependencies group(s) that own the non-core distributions
      used (empty/"core" when the root needs nothing beyond core+dev).
    - externally-provisioned: at least one third-party import resolves to a
      distribution NOT declared anywhere in pyproject.toml. `external_reason`
      names the specific undeclared distribution(s). FR-762 C-4 forbids
      adding new pyproject dependencies outside its frozen table, so any
      newly-discovered gap here stays externally-provisioned rather than
      being silently declared.

Root discovery (mechanical, not hand-curated):
    - Every direct child directory of `examples/` is a root, EXCEPT
      `examples/demos/`, whose own direct child directories are each
      roots instead (examples/demos/chatterbox, examples/demos/hello, ...).
    - A candidate directory only becomes a root if it contains at least one
      of: a `*.yaml` file with a top-level `nodes:` key (a graph), a `.py`
      file with `if __name__ == "__main__"`, or a `README.md`.

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


def _is_example_root(d: Path) -> bool:
    if not d.is_dir():
        return False
    if _has_graph_yaml(d) or (d / "README.md").exists():
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
    """Mechanically discover every example root (see module docstring)."""
    roots: list[Path] = []
    for child in sorted(examples_root.iterdir()):
        if not child.is_dir() or child.name in {"__pycache__", "shared"}:
            continue
        if child.name == "demos":
            for grandchild in sorted(child.iterdir()):
                if _is_example_root(grandchild):
                    roots.append(grandchild)
            continue
        if _is_example_root(child):
            roots.append(child)
    return roots


def _root_imports(root: Path) -> list[str]:
    """Every extracted top-level import name under a root, recursively."""
    names: list[str] = []
    for f in root.rglob("*.py"):
        if "__pycache__" in f.parts:
            continue
        for import_name, _lineno in _extract_imports(f):
            names.append(import_name)
    return names


def _owning_extras(
    distribution_norm: str, deps_by_group: dict[str, list[str]]
) -> list[str]:
    """Which optional-dependencies extras (excluding core/dev) declare this distribution."""
    owners = []
    for group, deps in deps_by_group.items():
        if group in {"core", "dev"}:
            continue
        if any(_normalize(d) == distribution_norm for d in deps):
            owners.append(group)
    return owners


def _local_module_names(root: Path) -> set[str]:
    """Names importable as `import <name>` via a sys.path insert of this root
    or one of its subdirectories (the common example test-fixture idiom).

    Includes every .py file stem and every subdirectory name found anywhere
    under the root, so `import tools` from examples/rag/tools/__init__.py
    or `import canon_tools` from examples/novel_fandom/nodes/canon_tools.py
    are recognized as local, not third-party.
    """
    names: set[str] = set()
    for f in root.rglob("*.py"):
        if "__pycache__" in f.parts:
            continue
        names.add(f.stem)
    for d in root.rglob("*"):
        if d.is_dir() and "__pycache__" not in d.parts:
            names.add(d.name)
    return names


def classify_root(
    root: Path,
    stdlib: frozenset[str],
    declared: set[str],
    deps_by_group: dict[str, list[str]],
    repo_root: Path = REPO_ROOT,
) -> dict:
    local_names = _local_module_names(root)
    undeclared: list[str] = []
    extras_used: set[str] = set()
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
        extras_used.update(_owning_extras(norm, deps_by_group))

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
        "extra": sorted(extras_used) or None,
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
        rows.append(classify_root(root, stdlib, declared, deps_by_group, repo_root))
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
