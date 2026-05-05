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


def _module_parts(module_file: Path) -> tuple[list[str], bool]:
    rel = module_file.relative_to(SOURCE_ROOT).with_suffix("")
    parts = list(rel.parts)
    is_package = bool(parts and parts[-1] == "__init__")
    if is_package:
        parts = parts[:-1]
    return parts, is_package


def _extract_dependencies(tree: ast.Module, module_file: Path) -> list[str]:
    deps: set[str] = set()
    module_parts, is_package = _module_parts(module_file)
    package_parts = module_parts if is_package else module_parts[:-1]

    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "yamlgraph" or alias.name.startswith("yamlgraph."):
                    deps.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                up_steps = max(node.level - 1, 0)
                if up_steps >= len(package_parts):
                    base_parts: list[str] = []
                else:
                    base_parts = package_parts[: len(package_parts) - up_steps]
                suffix_parts = (node.module or "").split(".") if node.module else []
                rel_parts = [part for part in [*base_parts, *suffix_parts] if part]
                dep = "yamlgraph"
                if rel_parts:
                    dep = f"yamlgraph.{'.'.join(rel_parts)}"
                deps.add(dep)
            else:
                module = node.module or ""
                if module == "yamlgraph" or module.startswith("yamlgraph."):
                    deps.add(module)

    return sorted(deps)


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
                dependencies=_extract_dependencies(tree, module_file),
                test_paths=_match_tests(module_file, tests_by_filename),
            )
        )

    return entries


def _render_markdown(entries: list[ModuleEntry]) -> str:
    def _format_exports(exports: list[str]) -> str:
        if not exports:
            return "_none_"
        return ", ".join(f"`{exported}`" for exported in exports)

    def _format_dependencies(deps: list[str]) -> str:
        if not deps:
            return "_none_"
        return ", ".join(f"`{dep}`" for dep in deps)

    def _is_trivial_init(entry: ModuleEntry) -> bool:
        return (
            entry.module_path.endswith("__init__.py")
            and entry.line_count < 10
            and len(entry.exports) <= 1
        )

    lines: list[str] = []
    lines.append("# Module Map")
    lines.append("")
    lines.append("## Metadata")
    lines.append("- source_root: `yamlgraph/`")
    lines.append("- parser: stdlib `ast.parse()`")
    lines.append("- deterministic ordering: modules sorted by relative path")
    lines.append(f"- module count: {len(entries)}")
    lines.append("")
    lines.append("## Module index/tree")

    for entry in entries:
        lines.append(
            f"- `{entry.module_path}` - {entry.line_count} lines; exports: {_format_exports(entry.exports)}"
        )
        if not _is_trivial_init(entry):
            lines.append(
                f"  - import dependencies: {_format_dependencies(entry.dependencies)}"
            )

    lines.append("## test_map")
    lines.append("")
    mapped_modules = sum(1 for entry in entries if entry.test_paths)
    mapped_tests = len(
        {test_path for entry in entries for test_path in entry.test_paths}
    )
    lines.append(
        "- deterministic mapping: derive `test_<stem>.py` and `test_<flattened_path>.py`, then resolve in `tests/`."
    )
    lines.append(f"- mapped modules: {mapped_modules}/{len(entries)}")
    lines.append(f"- discovered tests: {mapped_tests}")
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
