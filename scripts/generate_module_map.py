#!/usr/bin/env python3
"""Generate a deterministic Tier-2 module map for yamlgraph/ using stdlib AST."""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOT = REPO_ROOT / "yamlgraph"
TEST_ROOT = REPO_ROOT / "tests"
OUTPUT_PATH = REPO_ROOT / "reference" / "module-map.md"


@dataclass(frozen=True)
class ModuleEntry:
    """Static metadata extracted for one source module."""

    module_path: str
    line_count: int
    exports: list[str]
    dependencies: list[str]
    test_paths: list[str]


def _iter_python_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.py")
        if "__pycache__" not in path.parts and ".venv" not in path.parts
    )


def _read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def _signature_from_args(args: ast.arguments) -> str:
    parts: list[str] = []

    for arg in args.posonlyargs:
        parts.append(arg.arg)
    if args.posonlyargs:
        parts.append("/")

    for arg in args.args:
        parts.append(arg.arg)

    if args.vararg:
        parts.append(f"*{args.vararg.arg}")
    elif args.kwonlyargs:
        parts.append("*")

    for arg in args.kwonlyargs:
        parts.append(arg.arg)

    if args.kwarg:
        parts.append(f"**{args.kwarg.arg}")

    return ", ".join(parts)


def _extract_exports(tree: ast.Module) -> list[str]:
    exports: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            if node.name.startswith("_"):
                continue
            signature = _signature_from_args(node.args)
            prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
            exports.append(f"{prefix}{node.name}({signature})")
        elif isinstance(node, ast.ClassDef):
            if node.name.startswith("_"):
                continue
            exports.append(f"class {node.name}")
    return exports


def _extract_dependencies(tree: ast.Module) -> list[str]:
    deps: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                deps.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            level = "." * node.level if node.level else ""
            deps.add(f"{level}{module}".rstrip("."))
    return sorted(dep for dep in deps if dep)


def _index_tests(test_root: Path) -> dict[str, list[str]]:
    tests_by_filename: dict[str, list[str]] = {}
    for test_file in _iter_python_files(test_root):
        rel = test_file.relative_to(REPO_ROOT).as_posix()
        tests_by_filename.setdefault(test_file.name, []).append(rel)
    for test_list in tests_by_filename.values():
        test_list.sort()
    return tests_by_filename


def _candidate_test_names(module_file: Path) -> list[str]:
    rel = module_file.relative_to(SOURCE_ROOT)
    parts = list(rel.with_suffix("").parts)

    if parts and parts[-1] == "__init__":
        parts = parts[:-1]

    if not parts:
        return []

    stem = parts[-1]
    flattened = "_".join(parts)
    candidates = {f"test_{stem}.py", f"test_{flattened}.py"}
    return sorted(candidates)


def _match_tests(
    module_file: Path, tests_by_filename: dict[str, list[str]]
) -> list[str]:
    matched: set[str] = set()
    for candidate in _candidate_test_names(module_file):
        for test_path in tests_by_filename.get(candidate, []):
            matched.add(test_path)
    return sorted(matched)


def _build_entries() -> list[ModuleEntry]:
    tests_by_filename = _index_tests(TEST_ROOT)
    entries: list[ModuleEntry] = []

    for module_file in _iter_python_files(SOURCE_ROOT):
        source = module_file.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(module_file))
        line_count = len(_read_lines(module_file))
        module_path = module_file.relative_to(REPO_ROOT).as_posix()
        entries.append(
            ModuleEntry(
                module_path=module_path,
                line_count=line_count,
                exports=_extract_exports(tree),
                dependencies=_extract_dependencies(tree),
                test_paths=_match_tests(module_file, tests_by_filename),
            )
        )

    return entries


def _render_markdown(entries: list[ModuleEntry]) -> str:
    lines: list[str] = []
    lines.append("# Module Map")
    lines.append("")
    lines.append("## Metadata")
    lines.append("")
    lines.append("- source_root: `yamlgraph/`")
    lines.append("- parser: stdlib `ast.parse()`")
    lines.append("- deterministic ordering: modules sorted by relative path")
    lines.append(f"- module count: {len(entries)}")
    lines.append("")
    lines.append("## Module index/tree")
    lines.append("")

    for entry in entries:
        lines.append(f"### `{entry.module_path}`")
        lines.append(f"- line count: {entry.line_count}")
        if entry.exports:
            lines.append("- exports:")
            for exported in entry.exports:
                lines.append(f"  - `{exported}`")
        else:
            lines.append("- exports: _none_")

        if entry.dependencies:
            lines.append("- import dependencies:")
            for dep in entry.dependencies:
                lines.append(f"  - `{dep}`")
        else:
            lines.append("- import dependencies: _none_")
        lines.append("")

    lines.append("## test_map")
    lines.append("")
    lines.append("Deterministic mapping rule:")
    lines.append(
        "1. Convert module path to candidate filenames `test_<stem>.py` and `test_<flattened_path>.py`."
    )
    lines.append("2. Resolve candidates against discovered files under `tests/`.")
    lines.append("3. Emit lexicographically sorted module and test paths.")
    lines.append("")

    for entry in entries:
        lines.append(f"- `{entry.module_path}`")
        if entry.test_paths:
            for test_path in entry.test_paths:
                lines.append(f"  - `{test_path}`")
        else:
            lines.append("  - `_none_`")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    if not SOURCE_ROOT.exists():
        print(f"Missing source root: {SOURCE_ROOT}", file=sys.stderr)
        return 1

    entries = _build_entries()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(_render_markdown(entries), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(REPO_ROOT)} ({len(entries)} modules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
