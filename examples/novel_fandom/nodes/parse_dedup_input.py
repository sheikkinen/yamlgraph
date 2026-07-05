"""Parse JSON string inputs for semantic dedup graph-tool (FR-684).

Graph-tool args arrive as str (JSON). This entry node parses them
into lists for the LLM prompt.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def parse_dedup_input(state: dict[str, Any]) -> dict[str, Any]:
    """Parse candidates and canon_pages from JSON strings to lists."""
    candidates_raw = state.get("candidates", "[]")
    canon_raw = state.get("canon_pages", "{}")

    if isinstance(candidates_raw, str):
        try:
            candidates = json.loads(candidates_raw)
        except (json.JSONDecodeError, ValueError):
            candidates = []
    else:
        candidates = candidates_raw if isinstance(candidates_raw, list) else []

    if isinstance(canon_raw, str):
        try:
            canon = json.loads(canon_raw)
        except (json.JSONDecodeError, ValueError):
            canon = {}
    else:
        canon = canon_raw if isinstance(canon_raw, dict | list) else {}

    return {
        "parsed_candidates": candidates,
        "parsed_canon": canon,
    }
