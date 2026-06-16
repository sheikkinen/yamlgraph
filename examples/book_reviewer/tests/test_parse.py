"""Parse-stage tests for book_reviewer (pure, no LLM)."""

from pathlib import Path

import pytest

from examples.book_reviewer.nodes.tools import parse_manuscript, parse_node

SAMPLE = (Path(__file__).parent.parent / "sample_book.md").read_text(encoding="utf-8")


class TestParseSample:
    def test_recovers_tagline(self):
        parsed = parse_manuscript(SAMPLE)
        assert parsed.tagline.startswith("A lone courier")

    def test_recovers_synopsis(self):
        parsed = parse_manuscript(SAMPLE)
        assert "Captain Jarek Cole" in parsed.synopsis
        assert "# Synopsis" not in parsed.synopsis  # heading stripped

    def test_recovers_cast_bullets(self):
        parsed = parse_manuscript(SAMPLE)
        assert len(parsed.cast) == 3
        assert parsed.cast[0].startswith("**Kaelen Vance**")

    def test_recovers_two_ordered_chapters(self):
        parsed = parse_manuscript(SAMPLE)
        assert [c.number for c in parsed.chapters] == [1, 2]
        assert parsed.chapters[0].title == "The Frozen Crossing"
        assert parsed.chapters[1].title == "The Fort Defended"

    def test_chapter_body_is_prose_only(self):
        parsed = parse_manuscript(SAMPLE)
        body = parsed.chapters[0].body
        assert "Captain Jarek Cole pressed" in body
        assert "# Chapter" not in body
        assert "The Fort Defended" not in body  # does not bleed into next chapter


class TestParseNodeGuards:
    def test_zero_chapters_raises(self):
        """J5: a manuscript with no chapters must raise, not emit an empty review."""
        md = "> tagline\n\n# Synopsis\n\nA story with no chapters.\n"
        with pytest.raises(ValueError, match="no parseable chapters"):
            parse_node({"manuscript": md})

    def test_node_returns_chapters_for_map(self):
        out = parse_node({"manuscript": SAMPLE})
        assert len(out["chapters"]) == 2
        assert out["synopsis"]
        assert out["cast"]
