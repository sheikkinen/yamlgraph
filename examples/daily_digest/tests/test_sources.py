"""Tests for sources node - fetch_hn, fetch_rss."""

from unittest.mock import MagicMock, patch


class TestFetchHN:
    """Tests for Hacker News fetching."""

    def test_fetch_hn_returns_list(self):
        """fetch_hn returns a list of articles."""
        from examples.daily_digest.nodes.sources import fetch_hn

        with patch("examples.daily_digest.nodes.sources.httpx.get") as mock:
            # Mock HN API response
            mock.return_value = MagicMock(
                json=lambda: [1, 2, 3],  # Top story IDs
            )
            # Mock individual story fetch
            with patch(
                "examples.daily_digest.nodes.sources._fetch_hn_story"
            ) as mock_story:
                mock_story.return_value = {
                    "title": "Test",
                    "url": "https://example.com",
                    "source": "HN",
                    "timestamp": "2026-01-23T08:00:00",
                }
                result = fetch_hn(limit=2)

        assert isinstance(result, list)
        assert len(result) <= 2

    def test_fetch_hn_handles_missing_url(self):
        """Stories without URLs (Ask HN, etc.) get HN discussion link."""
        from examples.daily_digest.nodes.sources import _fetch_hn_story

        with patch("examples.daily_digest.nodes.sources.httpx.get") as mock:
            mock.return_value = MagicMock(
                json=lambda: {
                    "id": 12345,
                    "type": "story",
                    "title": "Ask HN: Best practices?",
                    "time": 1706000000,
                    # No 'url' field
                }
            )
            result = _fetch_hn_story(12345)

        assert result is not None
        assert "news.ycombinator.com" in result["url"]


class TestFetchRSS:
    """Tests for RSS feed fetching."""

    def test_fetch_rss_returns_list(self):
        """fetch_rss returns a list of articles."""
        from examples.daily_digest.nodes.sources import fetch_rss

        with patch("examples.daily_digest.nodes.sources.feedparser.parse") as mock:
            mock.return_value = MagicMock(
                entries=[
                    MagicMock(
                        title="RSS Article",
                        link="https://example.com/rss",
                        published_parsed=(2026, 1, 23, 8, 0, 0, 0, 0, 0),
                    )
                ]
            )
            result = fetch_rss(["https://example.com/feed"], limit=5)

        assert isinstance(result, list)
        assert len(result) >= 1
        assert result[0]["source"] == "RSS"


class TestFetchSources:
    """Tests for main fetch_sources node function."""

    def test_fetch_sources_caps_at_50(self, sample_articles):
        """fetch_sources caps total articles at 50."""
        from examples.daily_digest.nodes.sources import fetch_sources

        # Create 60 mock articles
        many_articles = sample_articles * 20  # 60 articles

        with (
            patch("examples.daily_digest.nodes.sources.fetch_hn") as mock_hn,
            patch("examples.daily_digest.nodes.sources.fetch_rss") as mock_rss,
        ):
            mock_hn.return_value = many_articles[:30]
            mock_rss.return_value = many_articles[30:]

            result = fetch_sources({})

        assert len(result["raw_articles"]) <= 50

    def test_fetch_sources_returns_dict_with_raw_articles(self):
        """fetch_sources returns dict with raw_articles key."""
        from examples.daily_digest.nodes.sources import fetch_sources

        with (
            patch("examples.daily_digest.nodes.sources.fetch_hn") as mock_hn,
            patch("examples.daily_digest.nodes.sources.fetch_rss") as mock_rss,
        ):
            mock_hn.return_value = []
            mock_rss.return_value = []

            result = fetch_sources({})

        assert "raw_articles" in result
        assert isinstance(result["raw_articles"], list)
