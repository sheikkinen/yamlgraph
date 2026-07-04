"""Semantic entity deduplication for worldgen (FR-665).

Two-pass dedup of red_links between collect and create_skeletons:
  1. Deterministic: merge obvious ID variants (possessive, the_X/X, prefix).
  2. LLM (gated on red_link_count > 5): cluster semantic duplicates via graph-tool.

Also rewrites references in deepened pages when IDs are merged.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_LLM_DEDUP_THRESHOLD = 5


def _strip_possessive(s: str) -> str:
    """Strip trailing 's' from first segment: egils_wife → egil_wife."""
    parts = s.split("_", 1)
    if parts[0].endswith("s") and len(parts[0]) > 1:
        parts[0] = parts[0][:-1]
    return "_".join(parts)


def _deterministic_dedup(red_links: list[dict]) -> tuple[list[dict], dict[str, str]]:
    """Merge obvious ID duplicates. Returns (survivors, merge_map).

    merge_map: {dropped_id: surviving_id}
    """
    by_id = {e["id"]: e for e in red_links if "id" in e}
    merged: dict[str, str] = {}  # dropped → survivor

    for eid in list(by_id.keys()):
        if eid in merged:
            continue

        # the_X / X variants
        alt = eid[4:] if eid.startswith("the_") else f"the_{eid}"
        if alt in by_id and alt not in merged:
            merged[alt] = eid

        # Possessive variants: egils_wife / egil_wife
        for other in list(by_id.keys()):
            if other == eid or other in merged:
                continue
            if _strip_possessive(other) == _strip_possessive(eid) and other != eid:
                # Keep shorter ID
                if len(other) <= len(eid):
                    merged[eid] = other
                else:
                    merged[other] = eid

        # Prefix match: ulf_death_bear_hunt / ulf_death_in_bear_hunt
        for other in list(by_id.keys()):
            if other == eid or other in merged or eid in merged:
                continue
            # One is a subsequence of the other (ignoring stop words)
            eid_parts = set(eid.split("_"))
            other_parts = set(other.split("_"))
            stop_words = {"in", "the", "of", "a", "an"}
            eid_content = eid_parts - stop_words
            other_content = other_parts - stop_words
            if eid_content == other_content and eid != other:
                # Keep shorter ID
                if len(other) <= len(eid):
                    merged[eid] = other
                else:
                    merged[other] = eid

    survivors = [e for e in red_links if e["id"] not in merged]
    logger.info(
        "Deterministic dedup: %d → %d (merged %d)",
        len(red_links),
        len(survivors),
        len(merged),
    )
    if merged:
        for dropped, survivor in sorted(merged.items()):
            logger.info("  %s → %s", dropped, survivor)

    return survivors, merged


def _rewrite_references(
    deepened: list[dict],
    merge_map: dict[str, str],
) -> list[dict]:
    """Rewrite references in deepened pages: dropped IDs → surviving IDs."""
    if not merge_map:
        return deepened

    def _rewrite_id(ref_id: str) -> str:
        return merge_map.get(ref_id, ref_id)

    rewritten = []
    for result in deepened:
        if not isinstance(result, dict):
            rewritten.append(result)
            continue
        result = dict(result)  # shallow copy

        # Rewrite updated_page references
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

        # Rewrite new_entities references
        new_ents = result.get("new_entities")
        if isinstance(new_ents, list):
            result["new_entities"] = [
                e
                for e in new_ents
                if isinstance(e, dict) and e.get("id") not in merge_map
            ]

        rewritten.append(result)

    return rewritten


def dedup_entities(state: dict[str, Any]) -> dict[str, Any]:
    """Deduplicate red_links: deterministic pass, optional LLM pass."""
    red_links = state.get("red_links", [])
    deepened = state.get("deepened", [])

    if not red_links:
        return {"red_links": [], "red_link_count": 0}

    # Pass 1: deterministic
    survivors, merge_map = _deterministic_dedup(red_links)

    # Pass 2: LLM dedup (only if enough entities to justify cost)
    if len(survivors) > _LLM_DEDUP_THRESHOLD:
        logger.info(
            "LLM dedup pass: %d survivors exceed threshold %d",
            len(survivors),
            _LLM_DEDUP_THRESHOLD,
        )
        # LLM dedup would be invoked here via graph-tool (FR-658)
        # For now, log intent — the graph-tool integration is wired
        # when dedup_check.yaml is created
        # TODO: Wire dedup_check graph-tool (FR-665 AC-3)

    # Rewrite references in deepened pages
    if merge_map:
        deepened = _rewrite_references(deepened, merge_map)

    return {
        "red_links": survivors,
        "red_link_count": len(survivors),
        "deepened": deepened,
    }
