"""Diary digest output tools — filtering, formatting, writing.

Graph tool functions following the state: dict -> dict pattern.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DIARY_PATH = Path(__file__).resolve().parent.parent.parent.parent / "docs" / "diary.md"


# ---------------------------------------------------------------------------
# Graph tool: filter_relevant (state -> dict)
# ---------------------------------------------------------------------------


def filter_relevant(state: dict) -> dict:
    """Filter scored articles by relevance threshold.

    Returns relevant_articles list and relevant_count for routing.
    If relevant_count == 0, the graph routes to END (no-op).

    Map nodes wrap results as {'_map_index': N, '_map_analyze_all_sub': RelevanceScore(...)}.
    This function unwraps the Pydantic model to extract the score.
    """
    scored = state.get("scored_articles", [])
    threshold = 0.3

    relevant = []
    for article in scored:
        # Unwrap map node output: the score is inside _map_analyze_all_sub
        score_obj = article.get("_map_analyze_all_sub", article)
        # Handle Pydantic model or dict
        if hasattr(score_obj, "relevance_score"):
            score = score_obj.relevance_score
            title = getattr(score_obj, "title", "")
            reason = getattr(score_obj, "reason", "")
        else:
            score = score_obj.get("relevance_score", 0) if isinstance(score_obj, dict) else article.get("relevance_score", 0)
            title = score_obj.get("title", "") if isinstance(score_obj, dict) else article.get("title", "")
            reason = score_obj.get("reason", "") if isinstance(score_obj, dict) else ""

        if isinstance(score, int | float) and score >= threshold:
            relevant.append({
                "title": title,
                "relevance_score": score,
                "reason": reason,
                "url": article.get("url", ""),
                "source": article.get("source", ""),
            })

    if not relevant:
        logger.info("📭 No relevant developments today. Silent no-op.")
    else:
        logger.info(f"✓ {len(relevant)} articles above relevance threshold ({threshold})")

    return {
        "relevant_articles": relevant,
        "relevant_count": len(relevant),
    }


# ---------------------------------------------------------------------------
# Pure functions (tested directly)
# ---------------------------------------------------------------------------


def format_diary_entry(
    date_str: str,
    theme: str,
    body: str,
    seed: str,
) -> str:
    """Format a diary entry in the canonical format.

    Returns markdown like:
        \\n---\\n\\n## 2026-02-19: World Digest — Theme\\n\\nbody\\n\\n**Seed:** ...\\n
    """
    return (
        f"\n---\n\n## {date_str}: World Digest — {theme}\n\n"
        f"{body}\n\n"
        f"**Seed:** {seed}\n"
    )


def append_to_diary(path: Path, entry: str) -> None:
    """Append a formatted entry to the diary file."""
    with open(path, "a") as f:
        f.write(entry)


def should_write_entry(
    articles: list[dict],
    threshold: float = 0.3,
) -> bool:
    """Return True only if at least one article scores above threshold.

    When no articles are relevant, the digest should be a silent no-op.
    Expects articles already unwrapped by filter_relevant.
    """
    if not articles:
        return False
    return any(a.get("relevance_score", 0) >= threshold for a in articles)


# ---------------------------------------------------------------------------
# Graph tool: write_diary (state -> dict)
# ---------------------------------------------------------------------------


def write_diary(state: dict) -> dict:
    """Format and append diary entry from synthesized LLM output.

    Graph tool — reads diary_entry from state (Pydantic model with
    theme, body, seed fields), formats it, and appends to docs/diary.md.
    """
    entry_data = state.get("diary_entry", {})
    date_str = state.get("date", "unknown")

    # Handle Pydantic model or dict
    theme = getattr(entry_data, "theme", None) or entry_data.get(
        "theme", "Developments"
    )
    body = getattr(entry_data, "body", None) or entry_data.get("body", "No content.")
    seed = getattr(entry_data, "seed", None) or entry_data.get(
        "seed", "What did we miss?"
    )

    entry = format_diary_entry(
        date_str=date_str,
        theme=theme,
        body=body,
        seed=seed,
    )

    append_to_diary(DIARY_PATH, entry)
    logger.info(f"✓ Entry appended to {DIARY_PATH}")

    return {"written": True}
