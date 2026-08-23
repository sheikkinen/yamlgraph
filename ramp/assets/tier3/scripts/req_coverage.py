#!/usr/bin/env python3
"""Requirement coverage gate (ramp Tier-3 curated copy).

Collects @pytest.mark.req markers from tests/ and reports coverage of
the capability registry in capabilities/. Generic: requirement IDs are
whatever the registry declares — no prefix is hardcoded.

Usage:
    python3 scripts/req_coverage.py            # summary
    python3 scripts/req_coverage.py --detail   # per-requirement test list
    python3 scripts/req_coverage.py --strict   # exit 1 on gaps

Curated from the ramp source repo's scripts/req_coverage.py — see
ramp/curation-diffs.md#req-coverage in the source repo.
"""

from __future__ import annotations

import ast
import sys
from collections import defaultdict
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CAPABILITIES_DIR = REPO_ROOT / "capabilities"
TEST_DIRS = ("tests",)


def load_registry() -> dict[str, tuple[str, list[str]]]:
    """Return {cap_id: (name, [req_ids])} from capabilities/CAP-*.yaml."""
    files = sorted(CAPABILITIES_DIR.glob("CAP-*.yaml"))
    if not files:
        raise SystemExit(f"no capability files found in {CAPABILITIES_DIR}")
    caps: dict[str, tuple[str, list[str]]] = {}
    for path in files:
        data = yaml.safe_load(path.read_text())
        if data.get("status") == "retired":
            continue
        caps[data["id"]] = (
            data["name"],
            [r["id"] for r in data.get("requirements", [])],
        )
    return caps


def _req_ids_from_decorator(node: ast.expr) -> list[str]:
    if not isinstance(node, ast.Call):
        return []
    func = node.func
    parts: list[str] = []
    while isinstance(func, ast.Attribute):
        parts.append(func.attr)
        func = func.value
    if "req" not in parts[:1]:
        return []
    return [a.value for a in node.args if isinstance(a, ast.Constant)]


def collect_marks() -> dict[str, list[str]]:
    """Return {req_id: [test names]} from @pytest.mark.req decorators."""
    marks: dict[str, list[str]] = defaultdict(list)
    for test_dir in TEST_DIRS:
        for path in sorted((REPO_ROOT / test_dir).rglob("test_*.py")):
            tree = ast.parse(path.read_text(), filename=str(path))
            module_reqs: list[str] = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if getattr(target, "id", "") == "pytestmark":
                            module_reqs += _req_ids_from_decorator(node.value)
                if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                    if not node.name.startswith("test_"):
                        continue
                    ids = [
                        rid
                        for dec in node.decorator_list
                        for rid in _req_ids_from_decorator(dec)
                    ] or module_reqs
                    for rid in ids:
                        marks[rid].append(f"{path.name}::{node.name}")
    return marks


def main(argv: list[str]) -> int:
    detail = "--detail" in argv
    strict = "--strict" in argv
    caps = load_registry()
    marks = collect_marks()
    gaps: list[str] = []
    for cap_id, (name, req_ids) in sorted(caps.items()):
        covered = [r for r in req_ids if marks.get(r)]
        status = "✅" if len(covered) == len(req_ids) else "❌"
        print(f"{status} {cap_id} {name}: {len(covered)}/{len(req_ids)} reqs")
        for rid in req_ids:
            tests = marks.get(rid, [])
            if not tests:
                gaps.append(rid)
            if detail:
                print(f"    {rid}: {len(tests)} test(s)")
                for t in tests:
                    print(f"      - {t}")
    if gaps:
        print(f"\n❌ {len(gaps)} requirement(s) without a witnessing test:")
        for rid in gaps:
            print(f"  - {rid}")
        if strict:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
