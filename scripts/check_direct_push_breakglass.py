#!/usr/bin/env python3
"""Check direct-push break-glass ledger coverage for a commit range.

FR-697: direct-to-main break-glass audit trail gate.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

EXPECTED_HEADER = "| sha | date | rationale | corrective_action | evidence |"
LEDGER_HEADING = "## Direct-to-main incident ledger"


@dataclass(frozen=True)
class LedgerEntry:
    sha: str
    date: str
    rationale: str
    corrective_action: str
    evidence: str


def _run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _commit_range(since_sha: str, until_sha: str) -> list[str]:
    _run_git("rev-parse", "--verify", since_sha)
    _run_git("rev-parse", "--verify", until_sha)

    commits_after = _run_git(
        "rev-list", "--reverse", "--ancestry-path", f"{since_sha}..{until_sha}"
    )
    commits = [since_sha]
    if commits_after:
        commits.extend([line for line in commits_after.splitlines() if line.strip()])
    return commits


def _parse_table_row(raw_line: str) -> list[str]:
    line = raw_line.strip()
    if not line.startswith("|") or not line.endswith("|"):
        raise ValueError(f"invalid table row format: {raw_line}")
    return [cell.strip() for cell in line.strip("|").split("|")]


def _extract_ledger_lines(content: str) -> list[str]:
    lines = content.splitlines()
    start_index: int | None = None
    for index, line in enumerate(lines):
        if line.strip() == LEDGER_HEADING:
            start_index = index
            break
    if start_index is None:
        raise ValueError(f"missing heading: {LEDGER_HEADING}")

    table_lines: list[str] = []
    in_table = False
    for line in lines[start_index + 1 :]:
        stripped = line.strip()
        if not stripped and not in_table:
            continue
        if stripped.startswith("|"):
            in_table = True
            table_lines.append(stripped)
            continue
        if in_table:
            break
    if len(table_lines) < 2:
        raise ValueError("ledger table not found or incomplete")
    return table_lines


def parse_ledger(path: Path) -> dict[str, LedgerEntry]:
    table_lines = _extract_ledger_lines(path.read_text())
    header = table_lines[0].strip()
    if header != EXPECTED_HEADER:
        raise ValueError(
            "ledger header mismatch: expected " f"'{EXPECTED_HEADER}' got '{header}'"
        )

    entries: dict[str, LedgerEntry] = {}
    for row in table_lines[2:]:
        cells = _parse_table_row(row)
        if len(cells) != 5:
            raise ValueError(f"invalid ledger row (expected 5 columns): {row}")
        entry = LedgerEntry(
            sha=cells[0],
            date=cells[1],
            rationale=cells[2],
            corrective_action=cells[3],
            evidence=cells[4],
        )
        if entry.sha:
            entries[entry.sha] = entry
    return entries


def _find_entry_for_commit(
    commit_sha: str,
    ledger_entries: dict[str, LedgerEntry],
) -> LedgerEntry | None:
    for ledger_sha, entry in ledger_entries.items():
        if commit_sha.startswith(ledger_sha) or ledger_sha.startswith(commit_sha):
            return entry
    return None


def _has_required_evidence(evidence: str) -> bool:
    return "/" in evidence or "FR-" in evidence.upper()


def check_ledger(
    commits: list[str],
    ledger_entries: dict[str, LedgerEntry],
) -> tuple[list[str], list[str]]:
    missing: list[str] = []
    invalid: list[str] = []

    for commit_sha in commits:
        entry = _find_entry_for_commit(commit_sha, ledger_entries)
        if entry is None:
            missing.append(commit_sha)
            continue

        if not entry.rationale.strip():
            invalid.append(f"{commit_sha} field=rationale")
        if not entry.corrective_action.strip():
            invalid.append(f"{commit_sha} field=corrective_action")
        if not entry.evidence.strip():
            invalid.append(f"{commit_sha} field=evidence")
        elif not _has_required_evidence(entry.evidence):
            invalid.append(f"{commit_sha} field=evidence_format")

    return missing, invalid


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate direct-push break-glass ledger coverage in a commit range."
    )
    parser.add_argument(
        "--since-sha", required=True, help="Range start SHA (inclusive)."
    )
    parser.add_argument(
        "--until-sha",
        default="HEAD",
        help="Range end SHA (inclusive). Defaults to HEAD.",
    )
    parser.add_argument(
        "--ledger-path",
        default="reference/break-glass.md",
        help="Path to break-glass markdown ledger file.",
    )
    args = parser.parse_args()

    ledger_path = Path(args.ledger_path)
    if not ledger_path.exists():
        print(f"ERROR code=missing_ledger path={ledger_path}")
        return 1

    try:
        commits = _commit_range(args.since_sha, args.until_sha)
        ledger_entries = parse_ledger(ledger_path)
    except (subprocess.CalledProcessError, ValueError) as exc:
        print(f"ERROR code=setup_failed detail={exc}")
        return 1

    missing, invalid = check_ledger(commits, ledger_entries)
    for sha in missing:
        print(f"MISSING sha={sha}")
    for item in invalid:
        print(f"INVALID {item}")

    print(
        "SUMMARY "
        f"checked={len(commits)} missing={len(missing)} invalid={len(invalid)}"
    )
    return 1 if missing or invalid else 0


if __name__ == "__main__":
    sys.exit(main())
