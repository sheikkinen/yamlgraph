"""FR-205 .fi Domain Crawler — Seed discovery tool node.

Discovers .fi domain URLs via DuckDuckGo search, filtering results
to the .fi TLD. Returns a deduplicated list of seed URLs.

Requires: pip install -e ".[websearch]" (ddgs)
"""

from __future__ import annotations

import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS  # type: ignore[no-redef]
    except ImportError:
        DDGS = None  # type: ignore[assignment,misc]

MAX_RESULTS_PER_QUERY = 10


def _is_fi_domain(url: str) -> bool:
    """Check whether a URL belongs to a .fi top-level domain."""
    parsed = urlparse(url)
    return parsed.netloc.endswith(".fi") or parsed.netloc.endswith(".fi.")


def discover_seeds(state: dict) -> dict:
    """Discover .fi domain URLs from search queries.

    Reads ``search_queries`` from state, executes each query via DuckDuckGo,
    and returns only URLs with a ``.fi`` TLD.

    Args:
        state: Must contain 'search_queries' (list[str]).

    Returns:
        Dict with 'discovered_urls' — a deduplicated list of .fi URLs.
    """
    queries: list[str] = state.get("search_queries", [])

    if not queries:
        return {"discovered_urls": []}

    if DDGS is None:
        logger.error("ddgs package not installed. Run: pip install ddgs")
        return {"discovered_urls": []}

    seen: set[str] = set()
    urls: list[str] = []

    for query in queries:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=MAX_RESULTS_PER_QUERY))
            for item in results:
                href = item.get("href", item.get("url", ""))
                if href and _is_fi_domain(href) and href not in seen:
                    seen.add(href)
                    urls.append(href)
        except Exception as e:
            logger.warning("Search failed for query '%s': %s", query, e)

    return {"discovered_urls": urls}
