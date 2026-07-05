"""Apply semantic merge map to red_links and deepened (FR-684).

Takes merge decisions from the semantic dedup graph-tool and:
1. Removes merged IDs from red_links
2. Rewrites references in deepened pages
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def apply_merge_map(state: dict[str, Any]) -> dict[str, Any]:
    """Apply semantic merge map: drop merged IDs, rewrite references."""
    red_links = state.get("red_links", [])
    deepened = state.get("deepened", [])
    merge_map = state.get("semantic_merge_map", {})

    if not merge_map:
        return {
            "red_links": red_links,
            "red_link_count": len(red_links),
            "deepened": deepened,
        }

    logger.info(
        "Applying semantic merge map: %d merges",
        len(merge_map),
    )
    for dropped, survivor in sorted(merge_map.items()):
        logger.info("  %s → %s", dropped, survivor)

    # Remove merged IDs from red_links
    survivors = [r for r in red_links if r.get("id") not in merge_map]

    # Rewrite references in deepened pages
    def _rewrite_id(ref_id: str) -> str:
        return merge_map.get(ref_id, ref_id)

    rewritten = []
    for result in deepened:
        if not isinstance(result, dict):
            rewritten.append(result)
            continue
        result = dict(result)  # shallow copy

        page = result.get("updated_page")
        if isinstance(page, dict):
            page = dict(page)
            for field in (
                "participants",
                "references",
                "members",
                "affected_locations",
            ):
                items = page.get(field)
                if isinstance(items, list):
                    page[field] = [
                        _rewrite_id(r) if isinstance(r, str) else r for r in items
                    ]
            rels = page.get("relationships")
            if isinstance(rels, list):
                page["relationships"] = [
                    {**r, "to": _rewrite_id(r.get("to", ""))}
                    if isinstance(r, dict) and r.get("to")
                    else r
                    for r in rels
                ]
            result["updated_page"] = page

        # Remove merged new_entities
        new_ents = result.get("new_entities")
        if isinstance(new_ents, list):
            result["new_entities"] = [
                e
                for e in new_ents
                if isinstance(e, dict) and e.get("id") not in merge_map
            ]

        rewritten.append(result)

    return {
        "red_links": survivors,
        "red_link_count": len(survivors),
        "deepened": rewritten,
    }
