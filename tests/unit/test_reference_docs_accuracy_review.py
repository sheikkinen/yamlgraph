"""Docs contract tests for FR-317 reference documentation accuracy review."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_DIR = REPO_ROOT / "reference"
REVIEW_MARKER = "Last reviewed: 2026-05-03"
LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def _iter_reference_docs() -> list[Path]:
    return sorted(REFERENCE_DIR.glob("*.md"))


def _normalize_link_target(link: str) -> str:
    """Normalize markdown link target, dropping fragment and optional title."""
    target = link.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    target = target.split("#", 1)[0].strip()
    if " " in target:
        target = target.split(" ", 1)[0].strip()
    return target


@pytest.mark.req("REQ-YG-317")
class TestReferenceDocsAccuracyReview:
    """Global contract for reference docs review marker and local links."""

    def test_all_reference_docs_end_with_last_reviewed_marker(self) -> None:
        not_reviewed: list[str] = []
        for path in _iter_reference_docs():
            content = path.read_text(encoding="utf-8").rstrip()
            if not content.endswith(REVIEW_MARKER):
                not_reviewed.append(path.name)

        assert not not_reviewed, (
            f"Missing or misplaced review marker in {len(not_reviewed)} files: "
            + ", ".join(not_reviewed)
        )

    def test_reference_docs_have_no_broken_local_markdown_links(self) -> None:
        broken: list[tuple[str, str]] = []

        for md_file in _iter_reference_docs():
            content = md_file.read_text(encoding="utf-8")
            for raw_link in LINK_PATTERN.findall(content):
                target = _normalize_link_target(raw_link)
                if not target or target.startswith(
                    ("http://", "https://", "mailto:", "#")
                ):
                    continue

                resolved = (md_file.parent / target).resolve()
                if REPO_ROOT not in resolved.parents and resolved != REPO_ROOT:
                    continue
                if not resolved.exists():
                    broken.append((str(md_file.relative_to(REPO_ROOT)), raw_link))

        assert not broken, "Broken local links: " + "; ".join(
            f"{src} -> {link}" for src, link in broken
        )
