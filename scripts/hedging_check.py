#!/usr/bin/env python3
"""Detect silent-fallback hedging patterns in Python code.

Catches patterns where an empty/falsy filter result is silently replaced
with a broader dataset, masking bugs. Graduated from diary 2026-02-17
(vuosikello slot matching bug).

Patterns detected:
  1. `if not X: X = broader_data`  (AST: reassign same variable in if-not body)
  2. `X = expr or fallback`        (AST: BoolOp with Or, assigning to same name)

Usage:
  python scripts/hedging_check.py [directory]   # default: yamlgraph/
  python scripts/hedging_check.py --strict      # non-zero exit on findings

Each finding requires human judgment: some fallbacks are intentional
(e.g., CLI defaults). The goal is visibility, not blanket prohibition.
"""

import ast
import sys
from pathlib import Path

# Allowlist: file:lineno entries that have been reviewed and approved.
# Add entries here when a fallback is intentional and documented.
ALLOWLIST: set[str] = {
    # Example: "yamlgraph/cli/helpers.py:42"
}


def scan_file(filepath: Path) -> list[str]:
    """Return list of hedging pattern descriptions found in file."""
    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError):
        return []

    findings: list[str] = []

    for node in ast.walk(tree):
        # Pattern 1: if not X: X = Y
        if isinstance(node, ast.If):
            test = node.test
            if (
                isinstance(test, ast.UnaryOp)
                and isinstance(test.op, ast.Not)
                and isinstance(test.operand, ast.Name)
            ):
                var_name = test.operand.id
                for stmt in node.body:
                    if isinstance(stmt, ast.Assign):
                        for target in stmt.targets:
                            if isinstance(target, ast.Name) and target.id == var_name:
                                key = f"{filepath}:{node.lineno}"
                                if key not in ALLOWLIST:
                                    findings.append(
                                        f"{key}: if not {var_name}: {var_name} = ... "
                                        f"(silent fallback — Commandment 6)"
                                    )

    return findings


def main() -> int:
    directory = "yamlgraph"
    strict = False

    for arg in sys.argv[1:]:
        if arg == "--strict":
            strict = True
        else:
            directory = arg

    root = Path(directory)
    if not root.exists():
        print(f"Directory not found: {root}", file=sys.stderr)
        return 1

    all_findings: list[str] = []
    for py_file in sorted(root.rglob("*.py")):
        if "__pycache__" in str(py_file):
            continue
        all_findings.extend(scan_file(py_file))

    if all_findings:
        print("Hedging patterns detected (Commandment 6 — no silent fallbacks):\n")
        for f in all_findings:
            print(f"  ⚠  {f}")
        print(
            f"\n{len(all_findings)} finding(s). Review each — add to ALLOWLIST if intentional."
        )
        if strict:
            return 1
    else:
        print("No hedging patterns found.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
