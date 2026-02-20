"""Tavily domain-scoped retrieval tool for YAMLGraph.

Retrieves content from a target domain via Tavily API.
Acts as a zero-indexing RAG retrieval layer.

Requires: pip install tavily-python
          export TAVILY_API_KEY="your-key"
          export TAVILY_TARGET_DOMAIN="example.com"  # optional, scopes search

Usage in graph YAML:
    tools:
      tavily_retrieve:
        type: python
        module: examples.demos.tavily_rag.nodes.tavily_retrieve
        function: tavily_retrieve
        description: "Retrieve content from target domain via Tavily"
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def tavily_retrieve(state: dict) -> str:
    """Retrieve domain-scoped content using Tavily.

    Called by YAMLGraph as a type: python node. Receives full state dict.
    Reads query from state["query"] (map sub-node) or state["question"].

    Args:
        state: Full state dictionary from YAMLGraph

    Returns:
        Formatted context string with sources and content
    """
    query = state.get("query") or state.get("question", "")
    max_results = state.get("max_results", 5)

    if not query or not query.strip():
        return "Error: Search query is empty"

    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return "Error: TAVILY_API_KEY environment variable not set"

    try:
        from tavily import TavilyClient  # noqa: F811
    except ImportError:
        return "Error: tavily-python not installed. Run: pip install tavily-python"

    try:
        client = TavilyClient(api_key=api_key)
        kwargs: dict = {
            "query": query,
            "max_results": max_results,
            "include_answer": True,
            "include_raw_content": True,
        }
        # Scope to target domain if configured
        target_domain = os.environ.get("TAVILY_TARGET_DOMAIN")
        if target_domain:
            kwargs["include_domains"] = [target_domain]

        response = client.search(**kwargs)

        sections: list[str] = []

        # Tavily's pre-synthesized answer
        answer = response.get("answer")
        if answer:
            sections.append(f"Summary: {answer}\n")

        # Individual retrieved pages
        for i, result in enumerate(response.get("results", []), 1):
            title = result.get("title", "No title")
            url = result.get("url", "No URL")
            content = result.get("content", "")
            raw = result.get("raw_content", "")
            score = result.get("score", 0)

            sections.append(f"[Source {i}] (relevance: {score:.2f})")
            sections.append(f"Title: {title}")
            sections.append(f"URL: {url}")
            # Prefer raw_content (full page) over snippet
            text = raw[:2000] if raw else content
            if text:
                sections.append(text)
            sections.append("---")

        if not sections:
            domain_note = f" on {target_domain}" if target_domain else ""
            return f"No results found for '{query}'{domain_note}"

        return "\n".join(sections)

    except Exception as e:
        logger.warning(f"Tavily retrieval failed: {e}")
        return f"Error: Retrieval failed - {e}"
