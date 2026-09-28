"""FR-1137 extraction and partitioning: AST identity and map payloads."""

from __future__ import annotations

import ast
import importlib.util
import math
from pathlib import Path
from typing import Any

from pydantic import BaseModel

REPO_ROOT = Path(__file__).resolve().parents[3]


def _load_req_extractor() -> Any:
    """Import `extract_req_markers` from scripts/req_coverage.py by path."""
    spec = importlib.util.spec_from_file_location(
        "_fr1137_req_coverage", REPO_ROOT / "scripts" / "req_coverage.py"
    )
    if spec is None or spec.loader is None:
        raise ImportError("scripts/req_coverage.py is not loadable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.extract_req_markers


extract_req_markers = _load_req_extractor()


class TestRow(BaseModel):
    """One AST-enumerated test function."""

    __test__ = False  # not a pytest class

    nodeid: str
    file: str
    line: int
    start_line: int
    end_line: int
    is_async: bool
    markers: list[str]
    reqs: list[str]


class Payload(BaseModel):
    """One map item: one file, or one chunk of whole tests of one file."""

    partition_id: str
    path: str
    nodeids: list[str]
    text: str
    est_tokens: int


def _mark_names(expr: ast.expr) -> list[str]:
    if isinstance(expr, ast.List | ast.Tuple):
        return [name for elt in expr.elts for name in _mark_names(elt)]
    if isinstance(expr, ast.Call):
        expr = expr.func
    if (
        isinstance(expr, ast.Attribute)
        and isinstance(expr.value, ast.Attribute)
        and expr.value.attr == "mark"
    ):
        return [expr.attr]
    return []


def _pytestmark(body: list[ast.stmt]) -> list[str]:
    names: list[str] = []
    for stmt in body:
        if isinstance(stmt, ast.Assign):
            targets, value = stmt.targets, stmt.value
        elif isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
            targets, value = [stmt.target], stmt.value
        else:
            continue
        if any(isinstance(t, ast.Name) and t.id == "pytestmark" for t in targets):
            names.extend(_mark_names(value))
    return names


def extract_tests(path: Path, relpath: str) -> list[TestRow]:
    """Enumerate collectable test functions in source order."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=relpath)
    reqs_by_key: dict[str, list[str]] = {}
    for req, keys in extract_req_markers(path).items():
        for key in keys:
            reqs_by_key.setdefault(key, []).append(req)
    stem = Path(relpath).stem
    module_marks = _pytestmark(tree.body)
    rows: list[TestRow] = []

    def add(func: ast.stmt, cls: str | None, inherited: list[str]) -> None:
        if not isinstance(func, ast.FunctionDef | ast.AsyncFunctionDef):
            return
        if not func.name.startswith("test"):
            return
        own = [n for d in func.decorator_list for n in _mark_names(d)]
        parts = [cls, func.name] if cls else [func.name]
        start = min([func.lineno, *(d.lineno for d in func.decorator_list)])
        rows.append(
            TestRow(
                nodeid="::".join([relpath, *parts]),
                file=relpath,
                line=func.lineno,
                start_line=start,
                end_line=func.end_lineno or func.lineno,
                is_async=isinstance(func, ast.AsyncFunctionDef),
                markers=sorted({*inherited, *own} - {"req"}),
                reqs=sorted(reqs_by_key.get("::".join([stem, *parts]), [])),
            )
        )

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            if not node.name.startswith("Test"):
                continue
            class_marks = [n for d in node.decorator_list for n in _mark_names(d)]
            inherited = [*module_marks, *class_marks, *_pytestmark(node.body)]
            for item in node.body:
                add(item, node.name, inherited)
        else:
            add(node, None, module_marks)
    return rows


def _tokens(text: str) -> int:
    return math.ceil(len(text) / 4)


def _payload(
    relpath: str, index: int, head: str, units: list[tuple[str, str]]
) -> Payload:
    text = head + "".join(unit for _, unit in units)
    return Payload(
        partition_id=f"{relpath}#{index}",
        path=relpath,
        nodeids=[nodeid for nodeid, _ in units],
        text=text,
        est_tokens=_tokens(text),
    )


def build_payloads(
    relpath: str, source: str, rows: list[TestRow], max_tokens: int
) -> list[Payload]:
    """Pack whole tests greedily into payloads that each carry the imports."""
    lines = source.splitlines(keepends=True)
    tree = ast.parse(source, filename=relpath)
    imports = "".join(
        "".join(lines[node.lineno - 1 : node.end_lineno])
        for node in tree.body
        if isinstance(node, ast.Import | ast.ImportFrom)
    )
    units: list[tuple[str, str]] = []
    for row in rows:
        parts = row.nodeid.split("::")
        head = f"# --- test {row.nodeid} (line {row.line})\n"
        if len(parts) == 3:
            head += f"# in class {parts[1]}\n"
        body = "".join(lines[row.start_line - 1 : row.end_line])
        units.append((row.nodeid, head + body + "\n"))

    def prefix(index: int) -> str:
        return f"# file: {relpath} (partition {index})\n# imports\n{imports}\n"

    payloads: list[Payload] = []
    current: list[tuple[str, str]] = []
    for nodeid, unit in units:
        index = len(payloads) + 1
        if _tokens(prefix(index) + unit) > max_tokens:
            raise ValueError(
                f"{nodeid} exceeds the {max_tokens}-token per-payload ceiling"
            )
        candidate = prefix(index) + "".join(u for _, u in current) + unit
        if current and _tokens(candidate) > max_tokens:
            payloads.append(_payload(relpath, index, prefix(index), current))
            current = []
        current.append((nodeid, unit))
    if current:
        index = len(payloads) + 1
        payloads.append(_payload(relpath, index, prefix(index), current))
    return payloads
