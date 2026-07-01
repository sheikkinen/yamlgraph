"""Prose mention gate adapter for novel_fandom.

Takes LLM-extracted entity mentions from prose and checks they resolve
against the canon. Bridges between the extract_prose_mentions LLM step
and the existing orphan detection logic.
"""

from __future__ import annotations

from typing import Any


def check_prose_mentions(state: dict[str, Any]) -> dict[str, Any]:
    """Check extracted prose mentions resolve to canon entities.

    Reads:
        state["prose_mentions"]: dict with "mentions" list of entity id strings
        state["canon"]: dict keyed by page id

    Returns:
        {"gate_result": {"valid": bool, "violations": list[str]}}
    """
    mentions_data = state.get("prose_mentions", {})
    canon = state.get("canon", {})

    if hasattr(mentions_data, "model_dump"):
        mentions_data = mentions_data.model_dump()

    mentions = mentions_data.get("mentions", [])
    existing_ids = set(canon.keys())
    violations: list[str] = []

    for mention in mentions:
        if mention not in existing_ids:
            violations.append(f"prose mentions non-canon entity: '{mention}'")

    return {
        "gate_result": {"valid": not violations, "violations": violations},
    }
