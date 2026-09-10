#!/usr/bin/env python3
"""Verify all noqa suppressions are documented in docs/confessions.md.

Usage:
    python scripts/noqa_coverage.py           # summary
    python scripts/noqa_coverage.py --detail  # show all confessions
    python scripts/noqa_coverage.py --strict  # exit 1 on undocumented noqa
    python scripts/noqa_coverage.py --fix     # realign drifted line references
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

# Directories to scan for noqa comments
SCAN_DIRS = ["yamlgraph", "tests", "examples", "scripts"]

# File patterns to include
INCLUDE_PATTERNS = ["*.py"]

# Paths to exclude
EXCLUDE_PATTERNS = [
    "*/__pycache__/*",
    "*/.pytest_cache/*",
    "*/.venv/*",
    "*/node_modules/*",
]


def find_noqa_in_file(filepath: Path) -> list[tuple[int, str]]:
    """Find all noqa comments in a file.

    Returns list of (line_number, error_code) tuples.
    """
    results = []
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception:
        return results

    for i, line in enumerate(content.splitlines(), start=1):
        # Match various noqa patterns:
        # # noqa: E402
        # # noqa:E402
        # # noqa: E402, F401
        # # noqa (blanket)
        match = re.search(r"#\s*noqa(?::\s*([A-Z0-9,\s]+))?", line, re.IGNORECASE)
        if match:
            codes = match.group(1)
            if codes:
                # Split multiple codes: "E402, F401" -> ["E402", "F401"]
                for code in re.split(r"[,\s]+", codes.strip()):
                    if code:
                        results.append((i, code.upper()))
            else:
                # Blanket noqa
                results.append((i, "ALL"))
        # FR-714: bandit suppressions confess identically to ruff ones.
        # Matches "nosec B701" and blanket "nosec" markers.
        nosec = re.search(r"#\s*nosec(?:\s+(B[0-9]+))?", line)
        if nosec:
            results.append((i, nosec.group(1) or "ALL"))
    return results


def parse_confessions(confessions_path: Path) -> dict[str, set[tuple[str, int, str]]]:
    """Parse confessions.md to extract documented suppressions.

    Returns dict mapping CONF-XXX -> set of (file_path, line_number, code).
    """
    confessions: dict[str, set[tuple[str, int, str]]] = {}
    if not confessions_path.exists():
        return confessions

    content = confessions_path.read_text(encoding="utf-8")

    # Pattern for confession blocks
    # ### CONF-001
    # - **File**: [path/file.py](../path/file.py#L145)
    # - **Code**: E402

    current_conf = None
    current_file = None
    current_line = None
    current_code = None

    for line in content.splitlines():
        # Match confession header
        conf_match = re.match(r"###\s+(CONF-\d+)", line)
        if conf_match:
            # Save previous confession if complete
            if current_conf and current_file and current_line and current_code:
                if current_conf not in confessions:
                    confessions[current_conf] = set()
                confessions[current_conf].add(
                    (current_file, current_line, current_code)
                )

            current_conf = conf_match.group(1)
            current_file = None
            current_line = None
            current_code = None
            continue

        # Match file line: **File**: [text](path#L123) or **File**: [text](path#L123-L456)
        file_match = re.search(r"\*\*File\*\*:\s*\[.*?\]\(\.\./([^)#]+)#L(\d+)", line)
        if file_match and current_conf:
            current_file = file_match.group(1)
            current_line = int(file_match.group(2))
            continue

        # Match code line: **Code**: E402 or **Code**: E402 (description)
        code_match = re.search(r"\*\*Code\*\*:\s*([A-Z0-9]+)", line)
        if code_match and current_conf:
            current_code = code_match.group(1).upper()
            continue

    # Don't forget the last confession
    if current_conf and current_file and current_line and current_code:
        if current_conf not in confessions:
            confessions[current_conf] = set()
        confessions[current_conf].add((current_file, current_line, current_code))

    return confessions


def scan_codebase(root: Path) -> list[tuple[Path, int, str]]:
    """Scan codebase for all noqa comments.

    Returns list of (file_path, line_number, code).
    """
    results = []

    for scan_dir in SCAN_DIRS:
        dir_path = root / scan_dir
        if not dir_path.exists():
            continue

        for pattern in INCLUDE_PATTERNS:
            for filepath in dir_path.rglob(pattern):
                # Check excludes
                excluded = False
                for exclude in EXCLUDE_PATTERNS:
                    if filepath.match(exclude):
                        excluded = True
                        break
                if excluded:
                    continue

                # Find noqa in file
                for line_num, code in find_noqa_in_file(filepath):
                    results.append((filepath, line_num, code))

    return results


def undocumented_noqa(root: Path, confessions_path: Path) -> list[tuple[str, int, str]]:
    """Suppressions present in the code but absent from the ledger.

    This is the condition --strict fails on. The direction is one-way by
    design: a ledger entry with no matching suppression is not reported,
    because the ledger also records historical context.
    """
    documented: set[tuple[str, int, str]] = set()
    for locations in parse_confessions(confessions_path).values():
        documented.update(locations)

    missing = []
    for filepath, line_num, code in scan_codebase(root):
        rel_path = str(filepath.relative_to(root))
        if (rel_path, line_num, code) not in documented:
            missing.append((rel_path, line_num, code))
    return sorted(missing)


# The file reference of a confession entry, split so the line number can be
# rewritten without disturbing the link text or the path.
_FILE_REF = re.compile(r"(\*\*File\*\*:\s*\[.*?\]\(\.\./)([^)#]+)#L(\d+)")
_CODE_REF = re.compile(r"\*\*Code\*\*:\s*([A-Z0-9]+)")


def _ledger_records(
    confessions_path: Path,
) -> tuple[list[str], list[tuple[int, str, int, str]]]:
    """Read the ledger as raw lines plus (md_index, path, line, code) records.

    parse_confessions() returns a set keyed by CONF id, which is enough to
    compare but not to rewrite; repair needs the position of each reference
    within the markdown.
    """
    lines = confessions_path.read_text(encoding="utf-8").splitlines()
    records: list[tuple[int, str, int, str]] = []
    pending: tuple[int, str, int] | None = None

    for idx, text in enumerate(lines):
        file_match = _FILE_REF.search(text)
        if file_match:
            pending = (idx, file_match.group(2), int(file_match.group(3)))
            continue
        code_match = _CODE_REF.search(text)
        if code_match and pending:
            records.append((*pending, code_match.group(1).upper()))
            pending = None
    return lines, records


def fix_confession_lines(root: Path, confessions_path: Path) -> int:
    """Realign drifted #L references; return the number repaired.

    Inserting a line above a suppression shifts every reference below it and
    invalidates confessions that are otherwise still true. Repair is only
    safe where identity is unambiguous: for a given file, the suppressions
    must map one-to-one and in order onto that file's ledger entries by rule
    code. Any other shape -- a suppression added, removed, or its code
    changed -- is left untouched for --strict to report.
    """
    if not confessions_path.exists():
        return 0

    lines, records = _ledger_records(confessions_path)

    ledger_by_path: dict[str, list[tuple[int, str, int, str]]] = defaultdict(list)
    for record in records:
        ledger_by_path[record[1]].append(record)

    actual_by_path: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for filepath, line_num, code in scan_codebase(root):
        actual_by_path[str(filepath.relative_to(root))].append((line_num, code))

    repaired = 0
    for path, entries in ledger_by_path.items():
        actual = sorted(actual_by_path.get(path, []))
        ledger = sorted(entries, key=lambda r: (r[2], r[3]))

        if len(actual) != len(ledger):
            continue
        if [code for _, code in actual] != [record[3] for record in ledger]:
            continue

        for (new_line, _), (md_index, _, old_line, _) in zip(
            actual, ledger, strict=True
        ):
            if new_line == old_line:
                continue
            lines[md_index] = _FILE_REF.sub(
                lambda m, n=new_line: f"{m.group(1)}{m.group(2)}#L{n}",
                lines[md_index],
                count=1,
            )
            repaired += 1

    if repaired:
        confessions_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return repaired


def main() -> int:
    """Main entry point."""
    root = Path(__file__).parent.parent
    confessions_path = root / "docs" / "confessions.md"

    detail = "--detail" in sys.argv
    strict = "--strict" in sys.argv

    if "--fix" in sys.argv:
        repaired = fix_confession_lines(root, confessions_path)
        print(f"Confession line references repaired: {repaired}")
        return 0

    # Scan codebase for noqa
    codebase_noqa = scan_codebase(root)

    # Parse confessions.md
    confessions = parse_confessions(confessions_path)

    # Build set of documented locations (file, line, code)
    documented: set[tuple[str, int, str]] = set()
    for _conf_id, locations in confessions.items():
        for file_path, line_num, code in locations:
            documented.add((file_path, line_num, code))

    undocumented = undocumented_noqa(root, confessions_path)

    # Print summary
    print("=" * 60)
    print("noqa Confession Coverage Report")
    print("=" * 60)
    print()
    print(f"Total noqa in codebase:     {len(codebase_noqa)}")
    print(f"Documented confessions:     {len(documented)}")
    print(f"Undocumented:               {len(undocumented)}")
    print()

    if detail:
        print("-" * 60)
        print("Documented Confessions:")
        print("-" * 60)
        for conf_id in sorted(confessions.keys()):
            for file_path, line_num, code in sorted(confessions[conf_id]):
                print(f"  {conf_id}: {file_path}:{line_num} ({code})")
        print()

    if undocumented:
        print("-" * 60)
        print("❌ Undocumented noqa (add to docs/confessions.md):")
        print("-" * 60)
        for rel_path, line_num, code in undocumented:
            print(f"  {rel_path}:{line_num} ({code})")
        print()
        print("Each noqa requires a confession entry with:")
        print("  - CONF-XXX identifier")
        print("  - File path with line number")
        print("  - Error code being suppressed")
        print("  - Sin (what the code does)")
        print("  - Penance (why it's acceptable)")
        print()

    if strict and undocumented:
        print("FAIL -- undocumented noqa detected")
        print(
            "See docs/confessions.md for how to confess your sins and beg forgiveness."
        )
        return 1

    if not undocumented:
        print("✓ All noqa suppressions are documented")

    return 0


if __name__ == "__main__":
    sys.exit(main())
