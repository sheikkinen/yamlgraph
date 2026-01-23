"""Test fixtures for daily_digest."""

import os
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def sample_articles():
    """Sample raw articles from HN/RSS."""
    now = datetime.now().isoformat()
    return [
        {
            "title": "LangGraph 2.0 Released",
            "url": "https://example.com/langgraph-2",
            "source": "HN",
            "timestamp": now,
        },
        {
            "title": "Python 3.14 Features",
            "url": "https://example.com/python-314",
            "source": "RSS",
            "timestamp": now,
        },
        {
            "title": "AI Agents in Production",
            "url": "https://example.com/ai-agents",
            "source": "HN",
            "timestamp": now,
        },
    ]


@pytest.fixture
def old_article():
    """An article from a week ago."""
    return {
        "title": "Old News",
        "url": "https://example.com/old",
        "source": "HN",
        "timestamp": "2026-01-01T00:00:00",
    }


@pytest.fixture
def sample_analyzed():
    """Sample analyzed articles (LLM output)."""
    return [
        {
            "title": "LangGraph 2.0 Released",
            "url": "https://example.com/langgraph-2",
            "summary": "Major update with new orchestration features.",
            "relevance_score": 0.95,
            "key_insight": "Subgraph support improved",
            "category": "LangGraph",
        },
        {
            "title": "Python 3.14 Features",
            "url": "https://example.com/python-314",
            "summary": "New features including pattern matching improvements.",
            "relevance_score": 0.85,
            "key_insight": "Better type hints",
            "category": "Python",
        },
    ]


@pytest.fixture
def sample_ranked_stories():
    """Sample ranked stories from LLM."""
    return [
        {
            "title": "LangGraph 2.0 Released",
            "url": "https://example.com/langgraph-2",
            "summary": "Major update with new orchestration features.",
            "relevance": 0.95,
            "reason": "Directly relevant to LangGraph topic",
        },
    ]


@pytest.fixture
def mock_httpx():
    """Mock httpx for content fetching tests."""
    with patch("examples.daily_digest.nodes.content.httpx.get") as mock:
        response = MagicMock()
        response.text = """
        <html>
        <head><title>Test Article</title></head>
        <body>
            <nav>Navigation</nav>
            <article>
                <p>This is the main article content about AI and Python.</p>
                <p>It contains important information about LangGraph.</p>
            </article>
            <footer>Footer content</footer>
        </body>
        </html>
        """
        mock.return_value = response
        yield mock


@pytest.fixture
def mock_httpx_timeout():
    """Mock httpx that times out."""
    with patch("examples.daily_digest.nodes.content.httpx.get") as mock:
        import httpx

        mock.side_effect = httpx.TimeoutException("Connection timed out")
        yield mock


@pytest.fixture
def mock_resend():
    """Mock Resend email API."""
    with patch("examples.daily_digest.nodes.email.resend.Emails.send") as mock:
        mock.return_value = {"id": "test-email-id"}
        yield mock


@pytest.fixture
def temp_db(tmp_path):
    """Temporary SQLite database for dedup tests."""
    db_path = tmp_path / "test_digest.db"
    os.environ["DATABASE_PATH"] = str(db_path)
    yield db_path
    # Cleanup
    os.environ.pop("DATABASE_PATH", None)
    if db_path.exists():
        db_path.unlink()
