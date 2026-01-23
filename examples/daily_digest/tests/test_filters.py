"""Tests for filter_recent with dedup."""


class TestFilterRecent:
    """Tests for filter_recent node."""

    def test_filter_recent_removes_old(self, sample_articles, old_article, temp_db):
        """Articles older than 24h are filtered out."""
        from examples.daily_digest.nodes.filters import filter_recent

        state = {"raw_articles": sample_articles + [old_article]}

        result = filter_recent(state)

        # Old article should be filtered
        urls = [a["url"] for a in result["filtered_articles"]]
        assert "https://example.com/old" not in urls
        # Recent articles should remain
        assert len(result["filtered_articles"]) == len(sample_articles)

    def test_dedup_across_runs(self, sample_articles, temp_db):
        """Same URL should not appear in second run."""
        from examples.daily_digest.nodes.filters import filter_recent

        state = {"raw_articles": sample_articles}

        # First run
        result1 = filter_recent(state)
        assert len(result1["filtered_articles"]) == 3

        # Second run with same articles
        result2 = filter_recent(state)
        assert len(result2["filtered_articles"]) == 0  # All seen

    def test_dedup_within_batch(self, temp_db):
        """Duplicate URLs within same batch are deduplicated."""
        from datetime import datetime

        from examples.daily_digest.nodes.filters import filter_recent

        now = datetime.now().isoformat()
        state = {
            "raw_articles": [
                {
                    "title": "Article 1",
                    "url": "https://example.com/same",
                    "timestamp": now,
                },
                {
                    "title": "Article 2",
                    "url": "https://example.com/same",
                    "timestamp": now,
                },
            ]
        }

        result = filter_recent(state)

        assert len(result["filtered_articles"]) == 1

    def test_returns_filtered_articles_key(self, sample_articles, temp_db):
        """filter_recent returns dict with filtered_articles key."""
        from examples.daily_digest.nodes.filters import filter_recent

        state = {"raw_articles": sample_articles}
        result = filter_recent(state)

        assert "filtered_articles" in result
        assert isinstance(result["filtered_articles"], list)
