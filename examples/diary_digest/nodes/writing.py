"""Diary digest output tools — filtering and diary_digest-specific helpers.

Graph tool functions following the state: dict -> dict pattern.
FR-097: Shared diary writing utilities moved to examples.shared.diary.
"""

import logging

# Re-export shared diary utilities (FR-097, FR-134)
from examples.shared.diary import (
    DIARY_DIR,
    format_diary_entry,
    should_write_entry,
    write_diary,
)

__all__ = [
    # Shared (re-exported from examples.shared.diary)
    "DIARY_DIR",
    "format_diary_entry",
    "should_write_entry",
    "write_diary",
    # Local (diary_digest-specific)
    "filter_relevant",
]

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Graph tool: filter_relevant (state -> dict)
# ---------------------------------------------------------------------------


def _extract_score(article: dict) -> float:
    """Extract relevance_score from article.

    With flatten_output: true (FR-052), relevance_score is at top level.
    """
    score = article.get("relevance_score", 0)
    if isinstance(score, int | float):
        return float(score)
    return 0.0


def _flatten_article(article: dict, raw_articles: list[dict]) -> dict:
    """Merge original article data with score data.

    With flatten_output: true (FR-052), score fields are already at top level.
    We still need to merge with raw_articles for original fields like 'url'.
    """
    flat: dict = {}

    # Get original article data via _map_index
    idx = article.get("_map_index")
    if idx is not None and idx < len(raw_articles):
        flat.update(raw_articles[idx])

    # Overlay score fields (already flattened by FR-052)
    for key, value in article.items():
        if not key.startswith("_map_"):
            flat[key] = value

    return flat


def filter_relevant(state: dict) -> dict:
    """Filter scored articles by relevance threshold.

    Returns relevant_articles list and relevant_count for routing.
    If relevant_count == 0, the graph routes to curate_seeds (no-op for diary).

    With flatten_output: true (FR-052), relevance_score is at top level.
    """
    scored = state.get("scored_articles", [])
    raw = state.get("raw_articles", [])
    threshold = 0.5

    relevant = []
    for article in scored:
        score = _extract_score(article)
        if score >= threshold:
            relevant.append(_flatten_article(article, raw))

    if not relevant:
        logger.info("📭 No relevant developments today. Silent no-op.")
    else:
        logger.info(
            f"✓ {len(relevant)} articles above relevance threshold ({threshold})"
        )

    return {
        "relevant_articles": relevant,
        "relevant_count": len(relevant),
    }
