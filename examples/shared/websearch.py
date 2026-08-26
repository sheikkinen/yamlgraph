"""Web search tool for YAMLGraph examples.

Provides web search via DuckDuckGo for agent nodes.
No API key required.

Usage in graph YAML (agent node):
    tools:
      search_web:
        type: python
        module: examples.shared.websearch
        function: search_web
        description: "Search the web for information"

Requires: pip install ddgs
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Import DuckDuckGo
try:
    from ddgs import DDGS

    DUCKDUCKGO_AVAILABLE = True
except ImportError:
    DDGS = None  # type: ignore[assignment, misc]
    DUCKDUCKGO_AVAILABLE = False


def search_web(query: str, max_results: int = 5) -> str:
    """Search the web using DuckDuckGo.

    This function is designed to be used as an agent tool.
    It takes a search query and returns formatted results.

    Args:
        query: Search query string
        max_results: Maximum number of results (default: 5)

    Returns:
        Formatted string with search results, or a "No results found"
        data string for genuinely empty result sets.

    Raises:
        ValueError: Empty or whitespace-only query (FR-891).
        ImportError: ddgs not installed (FR-891, fail-closed at call time).
        Exception: Transport/search failures propagate (FR-891) — the
            agent boundary aggregates them; no error-string returns.
    """
    if not query or not query.strip():
        raise ValueError("Search query is empty")

    if not DUCKDUCKGO_AVAILABLE:
        raise ImportError("ddgs not installed — pip install 'yamlgraph[websearch]'")

    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=max_results))

    if not results:
        return f"No results found for: '{query}'"

    lines = [f"Search results for '{query}':\n"]
    for i, item in enumerate(results, 1):
        title = item.get("title", "No title")
        url = item.get("href", item.get("url", "No URL"))
        body = item.get("body", item.get("snippet", ""))

        lines.append(f"{i}. {title}")
        lines.append(f"   URL: {url}")
        if body:
            lines.append(f"   {body}")
        lines.append("")

    return "\n".join(lines)
