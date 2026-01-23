"""Tests for email formatting node."""


class TestFormatEmail:
    """Tests for format_email node."""

    def test_generates_html(self, sample_ranked_stories):
        """format_email generates valid HTML."""
        from examples.daily_digest.nodes.formatting import format_email

        state = {
            "today": "2026-01-23",
            "ranked_stories": sample_ranked_stories,
        }

        result = format_email(state)

        assert "digest_html" in result
        assert "<html>" in result["digest_html"]
        assert "</html>" in result["digest_html"]

    def test_includes_date(self, sample_ranked_stories):
        """Generated HTML includes the date."""
        from examples.daily_digest.nodes.formatting import format_email

        state = {
            "today": "2026-01-23",
            "ranked_stories": sample_ranked_stories,
        }

        result = format_email(state)

        assert "2026-01-23" in result["digest_html"]

    def test_includes_story_titles(self, sample_ranked_stories):
        """Generated HTML includes story titles."""
        from examples.daily_digest.nodes.formatting import format_email

        state = {
            "today": "2026-01-23",
            "ranked_stories": sample_ranked_stories,
        }

        result = format_email(state)

        assert "LangGraph 2.0 Released" in result["digest_html"]

    def test_includes_story_urls(self, sample_ranked_stories):
        """Generated HTML includes story URLs as links."""
        from examples.daily_digest.nodes.formatting import format_email

        state = {
            "today": "2026-01-23",
            "ranked_stories": sample_ranked_stories,
        }

        result = format_email(state)

        assert "https://example.com/langgraph-2" in result["digest_html"]

    def test_handles_empty_stories(self):
        """Handles empty stories list gracefully."""
        from examples.daily_digest.nodes.formatting import format_email

        state = {
            "today": "2026-01-23",
            "ranked_stories": [],
        }

        result = format_email(state)

        assert "digest_html" in result
        assert "<html>" in result["digest_html"]
