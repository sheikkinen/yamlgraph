"""Pure helpers for the API discovery orchestrator graph."""

from __future__ import annotations

from typing import Any


def select_sniff_url(state: dict[str, Any]) -> dict[str, str]:
    """Select the first HTML page URL page-analysis receives."""
    html_pages = state.get("html_pages")
    if not isinstance(html_pages, list) or not html_pages:
        raise ValueError("select_sniff_url requires a non-empty html_pages list")

    first_url = html_pages[0]
    if not isinstance(first_url, str) or not first_url:
        raise ValueError(
            "select_sniff_url requires the first html_pages item to be a URL string"
        )

    return {"sniff_url": first_url}
