"""Shared diary writing utilities.

Used by diary_digest and .chaplain workflows.
FR-097: Extracted from examples/diary_digest/nodes/writing.py for neutral ownership.
FR-134: Refactored to write individual files to docs/diary/ folder.
"""

import logging
import re
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

DIARY_DIR = Path(__file__).resolve().parent.parent.parent / "docs" / "diary"


# ---------------------------------------------------------------------------
# Pure functions (tested directly)
# ---------------------------------------------------------------------------


def format_diary_entry(
    date_str: str,
    theme: str,
    body: str,
    seed: str,
    prefix: str = "World Digest",
) -> str:
    """Format a diary entry in the canonical format.

    Args:
        date_str: Date string (YYYY-MM-DD)
        theme: Entry theme/title
        body: Entry body content
        seed: Forward-looking question
        prefix: Header prefix (default "World Digest", use "Chaplain" for FR runs)

    Returns:
        Formatted markdown entry
    """
    return f"\n---\n\n## {date_str}: {prefix} — {theme}\n\n{body}\n\n**Seed:** {seed}\n"


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
    """Format and write diary entry as individual file in docs/diary/.

    Graph tool — reads diary_entry from state (Pydantic model with
    theme, body, seed fields), formats it, and writes to docs/diary/.
    """
    entry_data = state.get("diary_entry", {})
    date_str = state.get("date", datetime.now().strftime("%Y-%m-%d"))
    prefix = state.get("diary_prefix", "World Digest")

    # Handle Pydantic model, dict, or string representation
    if isinstance(entry_data, str):
        # Parse string representation like: theme='...' body='...' seed='...'
        theme_match = re.search(r"theme='([^']+)'", entry_data)
        # Body can contain quotes, so match until ' seed='
        body_match = re.search(r"body='(.+?)'\s+seed='", entry_data, re.DOTALL)
        seed_match = re.search(r"seed='([^']+)'", entry_data)
        theme = theme_match.group(1) if theme_match else "Developments"
        body = body_match.group(1) if body_match else "No content."
        seed = seed_match.group(1) if seed_match else "What did we miss?"
    else:
        theme = getattr(entry_data, "theme", None) or entry_data.get(
            "theme", "Developments"
        )
        body = getattr(entry_data, "body", None) or entry_data.get(
            "body", "No content."
        )
        seed = getattr(entry_data, "seed", None) or entry_data.get(
            "seed", "What did we miss?"
        )

    entry = format_diary_entry(
        date_str=date_str,
        theme=theme,
        body=body,
        seed=seed,
        prefix=prefix,
    )

    entry_type = prefix.lower().replace(" ", "-")
    filename = f"{date_str}-{entry_type}.md"
    entry_path = DIARY_DIR / filename
    DIARY_DIR.mkdir(parents=True, exist_ok=True)
    entry_path.write_text(entry)
    logger.info(f"✓ Entry written to {entry_path}")

    return {"written": True}
