#!/usr/bin/env python3
"""Collect @pytest.mark.req markers and report requirement coverage.

Usage:
    python scripts/req_coverage.py                 # summary
    python scripts/req_coverage.py --detail        # per-req test list
    python scripts/req_coverage.py --strict        # exit 1 on gaps
    python scripts/req_coverage.py --prefix FOO    # use FOO- prefix (default: REQ)

Standalone script — no framework imports required.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def extract_req_markers(filepath: Path, prefix: str) -> dict[str, list[str]]:
    """Extract @pytest.mark.req(...) markers from a test file.

    Returns mapping of requirement ID -> list of test names.
    """
    try:
        source = filepath.read_text()
        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError):
        return {}

    results: dict[str, list[str]] = defaultdict(list)
    pattern = re.compile(rf"{re.escape(prefix)}-\d+")

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue

        for decorator in node.decorator_list:
            req_id = _extract_req_from_decorator(decorator, pattern)
            if req_id:
                results[req_id].append(node.name)

    return dict(results)


def _extract_req_from_decorator(decorator: ast.expr, pattern: re.Pattern) -> str | None:
    """Extract REQ-XXX from a @pytest.mark.req("REQ-XXX") decorator."""
    # Handle @pytest.mark.req("REQ-001")
    if (
        isinstance(decorator, ast.Call)
        and decorator.args
        and isinstance(decorator.args[0], ast.Constant)
    ):
        value = str(decorator.args[0].value)
        if pattern.match(value):
            return value
    return None


def scan_tests(test_dir: Path, prefix: str) -> dict[str, list[str]]:
    """Scan all test files and collect requirement markers."""
    all_markers: dict[str, list[str]] = defaultdict(list)

    if not test_dir.exists():
        return dict(all_markers)

    for test_file in test_dir.rglob("test_*.py"):
        markers = extract_req_markers(test_file, prefix)
        for req_id, tests in markers.items():
            all_markers[req_id].extend(
                f"{test_file.relative_to(REPO_ROOT)}::{t}" for t in tests
            )

    return dict(all_markers)


def main() -> int:
    parser = argparse.ArgumentParser(description="Requirement coverage report")
    parser.add_argument(
        "--prefix",
        default="REQ",
        help="Requirement ID prefix (default: REQ)",
    )
    parser.add_argument(
        "--detail",
        action="store_true",
        help="Show per-requirement test list",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on coverage gaps",
    )
    parser.add_argument(
        "--test-dir",
        default="tests",
        help="Test directory to scan (default: tests)",
    )
    args = parser.parse_args()

    prefix = args.prefix
    test_dir = REPO_ROOT / args.test_dir

    markers = scan_tests(test_dir, prefix)

    if not markers:
        print(f"No {prefix}-XXX markers found in {test_dir}")
        return 1 if args.strict else 0

    # Sort by numeric part
    def sort_key(req_id: str) -> int:
        match = re.search(r"(\d+)$", req_id)
        return int(match.group(1)) if match else 0

    sorted_reqs = sorted(markers.keys(), key=sort_key)

    print(f"Requirement Coverage Report (prefix: {prefix})")
    print(f"{'=' * 50}")
    print(f"Total requirements with tests: {len(sorted_reqs)}")
    print()

    if args.detail:
        for req_id in sorted_reqs:
            tests = markers[req_id]
            print(f"  {req_id}: {len(tests)} test(s)")
            for test in tests:
                print(f"    - {test}")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
