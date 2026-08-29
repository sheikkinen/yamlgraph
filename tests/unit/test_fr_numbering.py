"""FR-907 — FR number uniqueness (CAP-252 / REQ-YG-627).

Concurrent sessions in one repo allocate FR numbers by reading the
directory and incrementing, so two sessions reliably pick the same
number. The shared index and working tree already have guards
(`one_session_one_repo`); the ID namespace did not, and FR-900/901/902
each landed on `main` twice before anyone noticed.

A duplicated FR number means the identifier stops identifying: changelog
fragments, diary filenames, commit subjects, and cross-FR gates all cite
a number that resolves to two documents.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FR_DIR = REPO_ROOT / "feature-requests"

FR_NUMBER = re.compile(r"^FR-(\d+)\b")

# Sibling artifacts legitimately share their parent's number. Matched on the
# WHOLE remainder, never as a substring: FR-215-research-agent-demo.md is a
# primary FR whose slug merely starts with a sibling word.
SIBLING_SUFFIXES = (
    ".judgement.md",
    ".research.md",
    ".receipt.md",
)
SIBLING_SLUGS = ("evidence",)

# Numbers already duplicated when this guard was introduced (2026-08-29).
# A ratchet, not an amnesty: the list may shrink, never grow. Renumbering
# 36 historical FRs would rewrite references in merged judgements, commit
# subjects, and changelog fragments for no present benefit — but every
# NEW collision now fails at commit time.
GRANDFATHERED: set[str] = {
    "082", "179", "185", "186", "191", "195",
    "196", "198", "201", "203", "204", "219",
    "221", "236", "237", "239", "243", "271",
    "275", "276", "291", "319", "391", "392",
    "409", "421", "424", "448", "464", "465",
    "466", "467", "573", "681", "896", "898",
}  # fmt: skip


def _is_sibling(name: str, number: str) -> bool:
    if name.endswith(SIBLING_SUFFIXES):
        return True
    return any(name == f"FR-{number}-{slug}.md" for slug in SIBLING_SLUGS)


def _primary_fr_files() -> dict[str, list[str]]:
    by_number: dict[str, list[str]] = defaultdict(list)
    for path in sorted(FR_DIR.glob("FR-*.md")):
        match = FR_NUMBER.match(path.name)
        if match and not _is_sibling(path.name, match.group(1)):
            by_number[match.group(1)].append(path.name)
    return by_number


@pytest.mark.req("REQ-YG-627")
class TestFeatureRequestNumbering:
    def test_fr_directory_exists(self) -> None:
        assert FR_DIR.is_dir()

    def test_no_duplicate_fr_numbers(self) -> None:
        duplicates = {
            number: names
            for number, names in _primary_fr_files().items()
            if len(names) > 1 and number not in GRANDFATHERED
        }
        assert not duplicates, (
            "Duplicate FR numbers — each number must identify one document:\n"
            + "\n".join(
                f"  FR-{number}: {', '.join(names)}"
                for number, names in sorted(duplicates.items())
            )
            + "\n\nPick the next free number (concurrent sessions collide; see "
            "one_session_one_repo) and rename, updating every reference."
        )

    def test_every_judgement_has_a_parent_fr(self) -> None:
        numbers = set(_primary_fr_files())
        orphans = [
            path.name
            for path in sorted(FR_DIR.glob("FR-*.judgement.md"))
            if (m := FR_NUMBER.match(path.name)) and m.group(1) not in numbers
        ]
        assert not orphans, f"Judgements with no parent FR: {orphans}"

    def test_sibling_words_in_slugs_are_not_treated_as_siblings(self) -> None:
        """FR-215-research-agent-demo.md is a primary FR, not a research sibling."""
        assert "FR-215-research-agent-demo.md" in _primary_fr_files().get("215", [])

    def test_grandfathered_entries_are_still_duplicated(self) -> None:
        """The ratchet may only shrink: a resolved number must leave the list."""
        duplicated = {n for n, v in _primary_fr_files().items() if len(v) > 1}
        stale = sorted(GRANDFATHERED - duplicated)
        assert not stale, f"No longer duplicated — remove from GRANDFATHERED: {stale}"
