"""Integration tests for the daily digest pipeline.

Uses mocked external services to test the full pipeline flow.
"""

import os
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest


class TestDigestPipelineIntegration:
    """Integration tests for the complete pipeline."""

    @pytest.fixture(autouse=True)
    def setup_db(self, tmp_path):
        """Set up temp database for each test."""
        db_path = tmp_path / "test_digest.db"
        os.environ["DATABASE_PATH"] = str(db_path)
        yield
        os.environ.pop("DATABASE_PATH", None)

    @pytest.fixture
    def mock_external_services(self):
        """Mock all external HTTP calls and services."""
        # Mock HN API responses
        hn_stories = [
            {
                "id": 1,
                "type": "story",
                "title": "LangGraph 2.0 Released",
                "url": "https://example.com/langgraph",
                "time": int(datetime.now().timestamp()),
            },
            {
                "id": 2,
                "type": "story",
                "title": "Python 3.14 Features",
                "url": "https://example.com/python",
                "time": int(datetime.now().timestamp()),
            },
        ]

        def mock_httpx_get(url, **kwargs):
            response = MagicMock()
            if "topstories" in url:
                response.json.return_value = [1, 2]
            elif "item/1" in url:
                response.json.return_value = hn_stories[0]
            elif "item/2" in url:
                response.json.return_value = hn_stories[1]
            else:
                # Article content
                response.text = """
                <html>
                <body>
                <article>
                LangGraph 2.0 brings major improvements including
                better state management and subgraph support.
                </article>
                </body>
                </html>
                """
            return response

        with (
            patch(
                "examples.daily_digest.nodes.sources.httpx.get",
                side_effect=mock_httpx_get,
            ),
            patch("examples.daily_digest.nodes.sources.feedparser.parse") as mock_rss,
            patch(
                "examples.daily_digest.nodes.content.httpx.get",
                side_effect=mock_httpx_get,
            ),
            patch("examples.daily_digest.nodes.email.resend.Emails.send") as mock_email,
        ):
            # Mock RSS to return empty (focus on HN)
            mock_rss.return_value = MagicMock(entries=[])
            mock_email.return_value = {"id": "test-email-id"}

            yield {
                "mock_email": mock_email,
            }

    def test_nodes_return_expected_state_keys(self, mock_external_services):
        """Each node returns the expected state keys."""
        from examples.daily_digest.nodes.content import fetch_article_content
        from examples.daily_digest.nodes.email import send_email
        from examples.daily_digest.nodes.filters import filter_recent
        from examples.daily_digest.nodes.formatting import format_email
        from examples.daily_digest.nodes.sources import fetch_sources

        # Test fetch_sources
        result = fetch_sources({})
        assert "raw_articles" in result
        assert len(result["raw_articles"]) == 2

        # Test filter_recent
        result = filter_recent({"raw_articles": result["raw_articles"]})
        assert "filtered_articles" in result
        assert len(result["filtered_articles"]) == 2

        # Test fetch_article_content
        article = result["filtered_articles"][0]
        result = fetch_article_content({"article": article})
        assert "content" in result
        assert "fetch_error" in result
        assert result["content"] != ""

        # Test format_email
        ranked_stories = [
            {
                "title": "Test Story",
                "url": "https://example.com/test",
                "summary": "A test summary",
                "relevance": 0.9,
                "reason": "Very relevant",
            }
        ]
        result = format_email({"today": "2026-01-23", "ranked_stories": ranked_stories})
        assert "digest_html" in result
        assert "<html>" in result["digest_html"]
        assert "Test Story" in result["digest_html"]

        # Test send_email (dry run)
        result = send_email(
            {
                "recipient_email": "test@example.com",
                "today": "2026-01-23",
                "digest_html": "<html>Test</html>",
                "_dry_run": True,
            }
        )
        assert result["email_sent"] is False

    def test_dedup_works_across_runs(self, mock_external_services):
        """Articles seen in first run are not returned in second run."""
        from examples.daily_digest.nodes.filters import filter_recent
        from examples.daily_digest.nodes.sources import fetch_sources

        # First run
        articles1 = fetch_sources({})
        filtered1 = filter_recent({"raw_articles": articles1["raw_articles"]})
        assert len(filtered1["filtered_articles"]) == 2

        # Second run with same articles
        articles2 = fetch_sources({})
        filtered2 = filter_recent({"raw_articles": articles2["raw_articles"]})
        assert len(filtered2["filtered_articles"]) == 0  # All already seen

    def test_email_not_sent_when_dry_run(self, mock_external_services):
        """Email is not sent when _dry_run is True."""
        from examples.daily_digest.nodes.email import send_email

        result = send_email(
            {
                "recipient_email": "test@example.com",
                "today": "2026-01-23",
                "digest_html": "<html>Test</html>",
                "_dry_run": True,
            }
        )

        assert result["email_sent"] is False
        mock_external_services["mock_email"].assert_not_called()

    def test_html_template_renders_correctly(self, mock_external_services):
        """HTML template includes all story details."""
        from examples.daily_digest.nodes.formatting import format_email

        stories = [
            {
                "title": "Breaking News Story",
                "url": "https://example.com/breaking",
                "summary": "Something important happened.",
                "relevance": 0.95,
                "reason": "High impact",
            },
            {
                "title": "Another Story",
                "url": "https://example.com/another",
                "summary": "More news.",
                "relevance": 0.85,
                "reason": "Also relevant",
            },
        ]

        result = format_email({"today": "2026-01-23", "ranked_stories": stories})
        html = result["digest_html"]

        # Check structure
        assert "<html>" in html
        assert "2026-01-23" in html

        # Check both stories present
        assert "Breaking News Story" in html
        assert "https://example.com/breaking" in html
        assert "Something important happened." in html

        assert "Another Story" in html
        assert "https://example.com/another" in html
