"""Tests for content fetching node."""


class TestFetchArticleContent:
    """Tests for fetch_article_content node."""

    def test_extracts_text_from_html(self, mock_httpx):
        """Extracts main text content from HTML."""
        from examples.daily_digest.nodes.content import fetch_article_content

        state = {
            "article": {
                "title": "Test Article",
                "url": "https://example.com/test",
            }
        }

        result = fetch_article_content(state)

        assert "content" in result
        assert "main article content" in result["content"].lower()
        # Navigation and footer should be removed
        assert "navigation" not in result["content"].lower()
        assert "footer" not in result["content"].lower()

    def test_handles_timeout(self, mock_httpx_timeout):
        """Returns empty content on timeout, doesn't raise."""
        from examples.daily_digest.nodes.content import fetch_article_content

        state = {
            "article": {
                "title": "Test Article",
                "url": "https://example.com/test",
            }
        }

        result = fetch_article_content(state)

        assert result["content"] == ""
        assert result["fetch_error"] is not None
        # httpx.TimeoutException message varies
        assert "timed out" in result["fetch_error"].lower()

    def test_preserves_original_article_fields(self, mock_httpx):
        """Original article fields are preserved in output."""
        from examples.daily_digest.nodes.content import fetch_article_content

        state = {
            "article": {
                "title": "Test Article",
                "url": "https://example.com/test",
                "source": "HN",
                "timestamp": "2026-01-23T08:00:00",
            }
        }

        result = fetch_article_content(state)

        assert result["title"] == "Test Article"
        assert result["url"] == "https://example.com/test"
        assert result["source"] == "HN"

    def test_limits_content_length(self, mock_httpx):
        """Content is limited to prevent huge LLM context."""
        # Patch with very long content
        from unittest.mock import MagicMock, patch

        from examples.daily_digest.nodes.content import fetch_article_content

        with patch("examples.daily_digest.nodes.content.httpx.get") as mock:
            response = MagicMock()
            response.text = "<html><body>" + "x" * 10000 + "</body></html>"
            mock.return_value = response

            state = {"article": {"title": "Test", "url": "https://example.com/test"}}
            result = fetch_article_content(state)

        assert len(result["content"]) <= 2000
