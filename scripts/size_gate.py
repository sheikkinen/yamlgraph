#!/usr/bin/env python3
"""File-size gate — widened by FR-889 (AC-11) to cover enforcement infra;
extended by FR-942 (AC-09) with an instruction-byte ceiling.

Errors above LIMIT lines for *.py and *.sh under yamlgraph/, scripts/,
.github/ and top-level *.sh. Pre-existing oversize files are held by a
shrink-only BASELINE ratchet: they may never grow, and entries go stale
loudly when a file shrinks below LIMIT or disappears.

FR-942: the two per-turn instruction files must exist, be non-empty,
and together stay within BYTE_CEILING bytes (60% of the frozen
56,610-byte baseline).

pre-command-guard.sh is deliberately NOT baselined — AC-07 forces it
under the limit permanently.

Usage: python scripts/size_gate.py [--root DIR]
Exit 1 when any in-scope file exceeds its allowance.
"""

import argparse
import sys
from pathlib import Path

LIMIT = 450
WARN = 400
SCAN_DIRS = ("yamlgraph", "scripts", ".github")
SUFFIXES = {".py", ".sh"}
EXCLUDE_PARTS = {"__pycache__", ".venv", "node_modules", "build"}

# FR-942: combined byte budget for the per-turn instruction files.
INSTRUCTION_FILES = (".github/copilot-instructions.md", "CLAUDE.md")
BYTE_CEILING = 33_966

# Shrink-only ratchet (FR-889): sizes frozen at gate introduction.
# A file may shrink (update the number) but never grow past its entry.
BASELINE = {
    ".github/hooks/tests/test_pre_command_guard.py": 807,
    "scripts/direct_import_scan.py": 675,
    ".github/hooks/tests/test_main_write_guard.py": 550,
    "scripts/worktree.sh": 615,
    "scripts/extract_fr_graph.py": 607,
    ".github/hooks/tests/test_reasoning_pattern_check.py": 592,
    "scripts/example_taxonomy_scan.py": 589,
    "scripts/vscode/now.py": 510,
    "scripts/migrate_capabilities.py": 501,
}


def in_scope(root: Path) -> list[Path]:
    files: list[Path] = []
    for d in SCAN_DIRS:
        base = root / d
        if base.is_dir():
            files += [
                p
                for p in base.rglob("*")
                if p.suffix in SUFFIXES
                and p.is_file()
                and not (set(p.parts) & EXCLUDE_PARTS)
            ]
    files += [p for p in root.glob("*.sh") if p.is_file()]
    return files


def instruction_budget_failures(root: Path) -> list[str]:
    """FR-942: missing/empty instruction file or combined bytes > ceiling."""
    sizes = {}
    failures = []
    for rel in INSTRUCTION_FILES:
        p = root / rel
        if not p.is_file() or p.stat().st_size == 0:
            failures.append(f"✗ {rel}: missing or empty instruction file")
        else:
            sizes[rel] = p.stat().st_size
    total = sum(sizes.values())
    if not failures and total > BYTE_CEILING:
        detail = " + ".join(f"{rel} ({n}B)" for rel, n in sizes.items())
        failures.append(
            f"✗ instruction byte budget: {detail} = {total} bytes "
            f"exceeds ceiling {BYTE_CEILING} (FR-942)"
        )
    return failures


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    root = ap.parse_args().root.resolve()
    failures = []
    for p in in_scope(root):
        try:
            n = len(p.read_text(errors="replace", encoding="utf-8").splitlines())
        except OSError:
            continue
        rel = str(p.relative_to(root))
        allowed = BASELINE.get(rel, LIMIT)
        if n > allowed:
            failures.append((rel, n, allowed))
        elif n > WARN and rel not in BASELINE:
            print(f"⚠ {rel}: {n} lines (warn at {WARN}, error at {LIMIT})")
    for rel, n, allowed in failures:
        print(f"✗ {rel}: {n} lines exceeds {allowed} — split into submodules")
    byte_failures = instruction_budget_failures(root)
    for msg in byte_failures:
        print(msg)
    return 1 if failures or byte_failures else 0


if __name__ == "__main__":
    sys.exit(main())
