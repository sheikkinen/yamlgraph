"""Shared diary writing utilities.

Used by diary_digest and .chaplain workflows.
FR-097: Extracted from examples/diary_digest/nodes/writing.py for neutral ownership.
FR-134: Refactored to write individual files to docs/diary/ folder.
FR-196: DiaryEntry/extract_json inlined to avoid dependency on examples.philosopher.
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

DIARY_DIR = Path(__file__).resolve().parent.parent.parent / "docs" / "diary"


# ---------------------------------------------------------------------------
# Models (inlined from .chaplain/graphs/philosopher/tools.py for FR-196)
# ---------------------------------------------------------------------------


class DiaryEntry(BaseModel):
    """Validated diary entry from reflect node."""

    theme: str = Field(description="Short title for the diary entry (2-4 words)")
    body: str = Field(description="Main reflection content in markdown format")
    seed: str = Field(description="A forward-looking question for future exploration")


def extract_json(text: str, node_name: str) -> str:
    """Extract JSON from copilot output, stripping markdown fences and preamble.

    Strategy:
    1. Strip markdown code fences (```json ... ```)
    2. Find first [ or { to last ] or }
    3. Raise ValueError on failure (no silent fallbacks per Commandment 6)
    """
    # Strip markdown fences
    stripped = re.sub(r"```(?:json)?\s*\n?", "", text).strip()
    if stripped.endswith("```"):
        stripped = stripped[:-3].strip()

    # Find JSON boundaries
    for start_char, end_char in [("[", "]"), ("{", "}")]:
        start = stripped.find(start_char)
        end = stripped.rfind(end_char)
        if start != -1 and end > start:
            candidate = stripped[start : end + 1]
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                continue

    raise ValueError(f"No valid JSON found in {node_name} output: {text[:200]}...")


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

    Graph tool — reads diary_entry from state (Pydantic model, CopilotResult,
    dict, or string with theme/body/seed fields), formats it, and writes to docs/diary/.
    """
    entry_data = state.get("diary_entry", {})
    date_str = state.get("date", datetime.now().strftime("%Y-%m-%d"))
    prefix = state.get("diary_prefix", "World Digest")

    # FR-185: Handle CopilotResult from copilot nodes
    from yamlgraph.models.schemas import CopilotResult

    if isinstance(entry_data, CopilotResult):
        # FR-196: Use inlined DiaryEntry/extract_json (no examples.philosopher dependency)
        json_str = extract_json(entry_data.output, "reflect")
        parsed = DiaryEntry.model_validate_json(json_str)
        theme, body, seed = parsed.theme, parsed.body, parsed.seed
    elif isinstance(entry_data, str):
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
    entry_path.write_text(entry, encoding="utf-8")
    logger.info(f"✓ Entry written to {entry_path}")

    return {"written": True}
