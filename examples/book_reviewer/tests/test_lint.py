"""Lint-stage tests for book_reviewer (pure, no LLM)."""

from pathlib import Path

from examples.book_reviewer.models import (
    ChapterSection,
    ParsedBook,
)
from examples.book_reviewer.nodes.tools import lint_manuscript, parse_manuscript

SAMPLE = (Path(__file__).parent.parent / "sample_book.md").read_text(encoding="utf-8")


class TestGoldenSample:
    def test_sample_is_clean(self):
        """The captured story.md passes lint — the realised diary Seed (FR-495/496)."""
        report = lint_manuscript(parse_manuscript(SAMPLE))
        assert report.ok is True, [i.model_dump() for i in report.issues]
        assert report.issues == []


def _codes(parsed: ParsedBook) -> set[str]:
    return {i.code for i in lint_manuscript(parsed).issues}


class TestDefectsAreCaught:
    def test_leaked_label_in_cast(self):
        parsed = ParsedBook(
            tagline="t",
            synopsis="s",
            cast=["**Kaelen** — SUMMARY: a courier"],
            chapters=[ChapterSection(number=1, title="One", body="prose")],
        )
        assert "leaked-label" in _codes(parsed)

    def test_leaked_label_in_prose(self):
        parsed = ParsedBook(
            tagline="t",
            synopsis="s",
            cast=["**K** — courier"],
            chapters=[ChapterSection(number=1, title="One", body="ROLE: hero stuff")],
        )
        assert "leaked-label" in _codes(parsed)

    def test_doubled_heading(self):
        parsed = ParsedBook(
            tagline="t",
            synopsis="s",
            cast=["**K** — c"],
            chapters=[
                ChapterSection(number=1, title="Chapter 1 — The Start", body="x")
            ],
        )
        assert "doubled-heading" in _codes(parsed)

    def test_numbering_gap(self):
        parsed = ParsedBook(
            tagline="t",
            synopsis="s",
            cast=["**K** — c"],
            chapters=[
                ChapterSection(number=1, title="A", body="x"),
                ChapterSection(number=3, title="B", body="y"),
            ],
        )
        assert "heading-numbering" in _codes(parsed)

    def test_empty_chapter_body(self):
        parsed = ParsedBook(
            tagline="t",
            synopsis="s",
            cast=["**K** — c"],
            chapters=[ChapterSection(number=1, title="A", body="   ")],
        )
        assert "empty-chapter-body" in _codes(parsed)

    def test_missing_frontmatter(self):
        parsed = ParsedBook(
            tagline="",
            synopsis="",
            cast=[],
            chapters=[ChapterSection(number=1, title="A", body="prose")],
        )
        assert "missing-frontmatter" in _codes(parsed)

    def test_custom_label_set(self):
        """The leak label set is configurable (generalises beyond DM)."""
        parsed = ParsedBook(
            tagline="t",
            synopsis="s",
            cast=["**K** — WIDGET: foo"],
            chapters=[ChapterSection(number=1, title="A", body="prose")],
        )
        report = lint_manuscript(parsed, labels=["WIDGET"])
        assert any(i.code == "leaked-label" for i in report.issues)
        # The default DM labels would NOT flag WIDGET.
        assert lint_manuscript(parsed).ok is True
