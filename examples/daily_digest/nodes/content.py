"""Content extraction node using BeautifulSoup."""

import logging

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

MAX_CONTENT_LENGTH = 2000


def _fetch_single_article(article: dict) -> dict:
    """Fetch and extract main text from a single article URL."""
    try:
        resp = httpx.get(article["url"], timeout=5, follow_redirects=True)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove script, style, nav elements
        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()

        # Get text, limit to ~2000 chars for LLM context
        text = soup.get_text(separator=" ", strip=True)[:MAX_CONTENT_LENGTH]

        logger.debug(f"📄 Extracted {len(text)} chars from {article['url']}")

        return {
            **article,
            "content": text,
            "fetch_error": None,
        }
    except Exception as e:
        logger.warning(f"Failed to fetch content from {article['url']}: {e}")
        return {
            **article,
            "content": "",
            "fetch_error": str(e),
        }


def fetch_article_content(state: dict) -> dict:
    """Fetch and extract content from article URL (single article for map node)."""
    article = state.get("article")
    if article:
        return _fetch_single_article(article)
    return {"content": "", "fetch_error": "No article in state"}


def fetch_all_content(state: dict) -> dict:
    """Fetch and extract content from all filtered articles."""
    articles = state.get("filtered_articles", [])
    results = []

    for article in articles:
        result = _fetch_single_article(article)
        results.append(result)

    logger.info(f"📄 Fetched content for {len(results)} articles")
    return {"articles_with_content": results}
