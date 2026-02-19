"""Tests for diary digest tools — FR-046.

Tests cover:
- Feed config loading
- Source fetching (HN + RSS)
- Diary entry formatting
- Append-to-diary behavior
- No-op when no relevant articles
"""

from unittest.mock import MagicMock, patch

import pytest


class TestFeedConfig:
    """Test feeds.yaml loading and structure."""

    @pytest.mark.req("REQ-YG-072")
    def test_feeds_yaml_exists(self):
        """feeds.yaml config file exists."""
        from scripts.diary_digest_tools import FEEDS_PATH

        assert FEEDS_PATH.exists(), f"feeds.yaml not found at {FEEDS_PATH}"

    @pytest.mark.req("REQ-YG-072")
    def test_feeds_yaml_has_required_keys(self):
        """feeds.yaml has topics and feeds keys."""
        from scripts.diary_digest_tools import load_feeds_config

        config = load_feeds_config()
        assert "topics" in config
        assert "feeds" in config
        assert isinstance(config["topics"], list)
        assert isinstance(config["feeds"], list)
        assert len(config["topics"]) > 0
        assert len(config["feeds"]) > 0

    @pytest.mark.req("REQ-YG-072")
    def test_feeds_yaml_has_seeds_context(self):
        """feeds.yaml can optionally include recent seeds for context."""
        from scripts.diary_digest_tools import load_feeds_config

        config = load_feeds_config()
        # seeds is optional but the key should be supported
        assert isinstance(config.get("seeds", []), list)


class TestFetchSources:
    """Test source fetching (HN + RSS)."""

    @pytest.mark.req("REQ-YG-072")
    def test_fetch_hn_returns_list(self):
        """fetch_hn returns a list of article dicts."""
        from scripts.diary_digest_tools import fetch_hn

        with patch("scripts.diary_digest_tools.httpx.get") as mock:
            mock.return_value = MagicMock(json=lambda: [1, 2])
            with patch("scripts.diary_digest_tools._fetch_hn_story") as mock_story:
                mock_story.return_value = {
                    "title": "Test",
                    "url": "https://example.com",
                    "source": "HN",
                    "timestamp": "2026-02-19T08:00:00",
                }
                result = fetch_hn(limit=2)

        assert isinstance(result, list)
        assert len(result) <= 2
        assert result[0]["source"] == "HN"

    @pytest.mark.req("REQ-YG-072")
    def test_fetch_rss_returns_list(self):
        """fetch_rss returns a list of article dicts."""
        from scripts.diary_digest_tools import fetch_rss

        with patch("scripts.diary_digest_tools.feedparser.parse") as mock:
            mock.return_value = MagicMock(
                entries=[
                    MagicMock(
                        title="RSS Article",
                        link="https://example.com/rss",
                        published_parsed=(2026, 2, 19, 8, 0, 0, 0, 0, 0),
                    )
                ]
            )
            result = fetch_rss(["https://example.com/feed"], limit=5)

        assert isinstance(result, list)
        assert len(result) >= 1
        assert result[0]["source"] == "RSS"

    @pytest.mark.req("REQ-YG-072")
    def test_fetch_sources_combines_hn_and_rss(self):
        """fetch_sources returns combined HN + RSS articles."""
        from scripts.diary_digest_tools import fetch_all_sources

        with (
            patch("scripts.diary_digest_tools.fetch_hn") as mock_hn,
            patch("scripts.diary_digest_tools.fetch_rss") as mock_rss,
        ):
            mock_hn.return_value = [
                {
                    "title": "HN Article",
                    "url": "https://hn.com/1",
                    "source": "HN",
                    "timestamp": "2026-02-19T08:00:00",
                }
            ]
            mock_rss.return_value = [
                {
                    "title": "RSS Article",
                    "url": "https://rss.com/1",
                    "source": "RSS",
                    "timestamp": "2026-02-19T08:00:00",
                }
            ]
            result = fetch_all_sources(
                feeds=["https://example.com/feed"],
                hn_limit=10,
                rss_limit=10,
            )

        assert len(result) == 2

    @pytest.mark.req("REQ-YG-072")
    def test_fetch_hn_handles_api_error(self):
        """fetch_hn returns empty list on API error."""
        from scripts.diary_digest_tools import fetch_hn

        with patch("scripts.diary_digest_tools.httpx.get") as mock:
            mock.side_effect = Exception("Connection error")
            result = fetch_hn(limit=5)

        assert result == []


class TestDiaryEntryFormatting:
    """Test diary entry output format."""

    @pytest.mark.req("REQ-YG-072")
    def test_format_diary_entry_has_header(self):
        """Formatted entry has ## YYYY-MM-DD: World Digest header."""
        from scripts.diary_digest_tools import format_diary_entry

        entry = format_diary_entry(
            date_str="2026-02-19",
            theme="Test Theme",
            body="Test body content",
            seed="Test seed question?",
        )
        assert "## 2026-02-19: World Digest — Test Theme" in entry

    @pytest.mark.req("REQ-YG-072")
    def test_format_diary_entry_has_seed(self):
        """Formatted entry ends with a Seed."""
        from scripts.diary_digest_tools import format_diary_entry

        entry = format_diary_entry(
            date_str="2026-02-19",
            theme="Test",
            body="Body",
            seed="What does this mean?",
        )
        assert "**Seed:**" in entry
        assert "What does this mean?" in entry

    @pytest.mark.req("REQ-YG-072")
    def test_format_diary_entry_has_separator(self):
        """Entry starts with --- separator for diary append."""
        from scripts.diary_digest_tools import format_diary_entry

        entry = format_diary_entry(
            date_str="2026-02-19",
            theme="Test",
            body="Body",
            seed="Question?",
        )
        assert entry.startswith("\n---\n\n##")


class TestAppendToDiary:
    """Test appending entries to diary.md."""

    @pytest.mark.req("REQ-YG-072")
    def test_append_adds_entry_to_end(self, tmp_path):
        """append_to_diary adds entry at end of file."""
        from scripts.diary_digest_tools import append_to_diary

        diary = tmp_path / "diary.md"
        diary.write_text("# Development Diary\n\nExisting content.\n")

        entry = "\n---\n\n## 2026-02-19: World Digest — Test\n\nBody.\n\n**Seed:** Q?\n"
        append_to_diary(diary, entry)

        content = diary.read_text()
        assert "Existing content." in content
        assert "## 2026-02-19: World Digest — Test" in content
        assert content.index("Existing content.") < content.index("World Digest")

    @pytest.mark.req("REQ-YG-072")
    def test_append_preserves_existing(self, tmp_path):
        """append_to_diary doesn't modify existing content."""
        from scripts.diary_digest_tools import append_to_diary

        original = "# Development Diary\n\n## 2026-02-18: Old Entry\n\nOld content.\n"
        diary = tmp_path / "diary.md"
        diary.write_text(original)

        entry = "\n---\n\n## 2026-02-19: World Digest — New\n\nNew content.\n"
        append_to_diary(diary, entry)

        content = diary.read_text()
        assert "Old content." in content
        assert "New content." in content


class TestNoOpBehavior:
    """Test that no entry is written when nothing is relevant."""

    @pytest.mark.req("REQ-YG-072")
    def test_should_write_false_when_no_articles(self):
        """should_write_entry returns False for empty articles list."""
        from scripts.diary_digest_tools import should_write_entry

        assert should_write_entry([]) is False

    @pytest.mark.req("REQ-YG-072")
    def test_should_write_false_when_below_threshold(self):
        """should_write_entry returns False when all scores below threshold."""
        from scripts.diary_digest_tools import should_write_entry

        articles = [
            {"title": "Irrelevant", "relevance_score": 0.2},
            {"title": "Also irrelevant", "relevance_score": 0.4},
        ]
        assert should_write_entry(articles, threshold=0.7) is False

    @pytest.mark.req("REQ-YG-072")
    def test_should_write_true_when_above_threshold(self):
        """should_write_entry returns True when any article above threshold."""
        from scripts.diary_digest_tools import should_write_entry

        articles = [
            {"title": "Irrelevant", "relevance_score": 0.2},
            {"title": "Relevant!", "relevance_score": 0.8},
        ]
        assert should_write_entry(articles, threshold=0.7) is True
