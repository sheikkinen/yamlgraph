"""Collect and deduplicate red links from parallel deepen results.

Deterministic set operation: union of new_entities from all deepen
calls, minus existing canon page ids.
"""

from __future__ import annotations

from typing import Any


def collect_red_links(state: dict[str, Any]) -> dict[str, Any]:
    """Deduplicate new entities from parallel deepen calls."""
    deepened_results = state.get("deepened", [])
    canon_pages = state.get("canon_pages", {})

    seen: dict[str, dict] = {}
    for result in deepened_results:
        if not isinstance(result, dict):
            continue
        for entity in result.get("new_entities", []):
            eid = entity.get("id", "")
            if eid and eid not in canon_pages and eid not in seen:
                seen[eid] = entity

    red_links = list(seen.values())
    return {"red_links": red_links, "red_link_count": len(red_links)}
