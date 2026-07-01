"""Deterministic context retrieval for the plot pathfinder.

Filters canon by timeline window and character roster, extracting open tensions
(unresolved relationship edges, unmet goals, active fears, triggers).
No LLM — pure filtering over loaded data_files canon.
"""

from __future__ import annotations

from typing import Any


def retrieve_window(state: dict[str, Any]) -> dict[str, Any]:
    """Return a scoped context of roster pages + open tensions for a window.

    Reads:
        state["canon"]: dict keyed by page id (from data_files glob)
        state["window"]: timeline event id to scope retrieval
        state["roster"]: list of character ids to include

    Returns:
        {"context": {"window": str, "roster_pages": [...], "tensions": [...]}}
    """
    canon = state.get("canon", {})
    window = state.get("window", "")
    roster = state.get("roster", [])

    # CLI --var passes roster as a JSON string; parse it if needed
    if isinstance(roster, str):
        import json

        try:
            roster = json.loads(roster)
        except (json.JSONDecodeError, ValueError):
            roster = []

    roster_pages = []
    tensions: list[dict[str, Any]] = []

    for char_id in roster:
        page = canon.get(char_id)
        if page is None:
            continue
        page_data = dict(page) if isinstance(page, dict) else page

        # Only include characters
        if page_data.get("type") != "character":
            continue

        roster_pages.append(page_data)

        # Extract unmet goals as tensions
        for goal in page_data.get("goals", []):
            tensions.append(
                {
                    "type": "unmet_goal",
                    "actor": char_id,
                    "description": goal,
                }
            )

        # Extract fears as tension levers
        for fear in page_data.get("fears", []):
            tensions.append(
                {
                    "type": "fear",
                    "actor": char_id,
                    "description": fear,
                }
            )

        # Extract wants≠needs as internal conflict
        wants = page_data.get("wants", "")
        needs = page_data.get("needs", "")
        if wants and needs and wants != needs:
            tensions.append(
                {
                    "type": "internal_conflict",
                    "actor": char_id,
                    "wants": wants,
                    "needs": needs,
                }
            )

        # Extract unresolved relationship edges
        for rel in page_data.get("relationships", []):
            rel_data = dict(rel) if isinstance(rel, dict) else rel
            if rel_data.get("valence") in ("enmity", "caution", "fear", "distrust"):
                tensions.append(
                    {
                        "type": "unresolved_edge",
                        "from": char_id,
                        "to": rel_data.get("to", ""),
                        "kind": rel_data.get("kind", ""),
                        "valence": rel_data.get("valence", ""),
                    }
                )

        # Extract triggers as potential beat generators
        for trigger in page_data.get("triggers", []):
            tensions.append(
                {
                    "type": "trigger",
                    "actor": char_id,
                    "description": trigger,
                }
            )

    # Include the window event itself if it exists
    window_event = canon.get(window)
    window_data = None
    if window_event and isinstance(window_event, dict):
        window_data = window_event

    # Include rules referenced by roster characters
    rule_ids = set()
    for page in roster_pages:
        for ref in page.get("references", []):
            ref_page = canon.get(ref)
            if isinstance(ref_page, dict) and ref_page.get("type") == "rule":
                rule_ids.add(ref)

    rules = [canon[rid] for rid in sorted(rule_ids) if rid in canon]

    return {
        "context": {
            "window": window,
            "window_event": window_data,
            "roster_pages": roster_pages,
            "tensions": tensions,
            "rules": rules,
        },
    }
