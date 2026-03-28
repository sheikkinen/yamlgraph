"""FR-205 .fi Domain Crawler — Page crawler tool node.

Fetches a URL via httpx and extracts structure using BeautifulSoup.
Returns a structured dict with title, links, meta description, and text snippet.

Requires: pip install -e ".[digest]" (httpx, beautifulsoup4)
"""

from __future__ import annotations

import logging
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 10
SNIPPET_MAX_LENGTH = 500
NOISE_TAGS = ("script", "style", "nav", "header", "footer", "aside")


def crawl_page(state: dict) -> dict:
    """Fetch a URL and extract page structure.

    Args:
        state: Must contain 'url' key with the target URL.

    Returns:
        Dict with url, title, internal_links, external_links,
        meta_description, snippet, and error fields.
    """
    url = state.get("url", "")
    base = urlparse(url)
    base_domain = base.netloc

    try:
        resp = httpx.get(url, timeout=TIMEOUT_SECONDS, follow_redirects=True)
        resp.raise_for_status()
    except Exception as e:
        logger.warning("Failed to fetch %s: %s", url, e)
        return {
            "url": url,
            "title": "",
            "internal_links": [],
            "external_links": [],
            "meta_description": "",
            "snippet": "",
            "error": str(e),
        }

    soup = BeautifulSoup(resp.text, "html.parser")

    # Title
    title = soup.title.string.strip() if soup.title and soup.title.string else ""

    # Meta description
    meta_tag = soup.find("meta", attrs={"name": "description"})
    meta_description = (
        meta_tag["content"].strip() if meta_tag and meta_tag.get("content") else ""
    )

    # Remove noise elements before text extraction
    for tag in soup(list(NOISE_TAGS)):
        tag.decompose()

    # Text snippet
    text = soup.get_text(separator=" ", strip=True)
    snippet = text[:SNIPPET_MAX_LENGTH]

    # Links
    internal_links: list[str] = []
    external_links: list[str] = []

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        absolute = urljoin(url, href)
        parsed = urlparse(absolute)

        if not parsed.scheme.startswith("http"):
            continue

        if parsed.netloc == base_domain:
            internal_links.append(absolute)
        else:
            external_links.append(absolute)

    return {
        "url": url,
        "title": title,
        "internal_links": internal_links,
        "external_links": external_links,
        "meta_description": meta_description,
        "snippet": snippet,
        "error": None,
    }
