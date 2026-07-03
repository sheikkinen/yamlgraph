"""Select thin entities for deepening.

Deterministic filter: checks field presence per page type.
No LLM. No semantic judgment. Sorted by thin_score (most thin first).
Coupled to canon.py schema — update criteria when schema changes.
"""

from __future__ import annotations

from typing import Any


def _character_thin(page: dict) -> list[str]:
    """Return list of reasons this character is thin."""
    reasons = []
    backstory = page.get("backstory", "")
    if not backstory or len(backstory.split()) < 50:
        reasons.append("backstory empty or < 50 words")
    if not page.get("triggers"):
        reasons.append("no triggers")
    if len(page.get("relationships", [])) < 2:
        reasons.append("< 2 relationships")
    return reasons


def _event_thin(page: dict) -> list[str]:
    reasons = []
    if not page.get("consequences"):
        reasons.append("no consequences")
    if len(page.get("participants", [])) < 2:
        reasons.append("< 2 participants")
    if not page.get("description"):
        reasons.append("no description")
    if not page.get("references"):
        reasons.append("no references")
    return reasons


def _faction_thin(page: dict) -> list[str]:
    reasons = []
    if len(page.get("members", [])) < 2:
        reasons.append("< 2 members")
    return reasons


def _location_thin(page: dict) -> list[str]:
    reasons = []
    if not page.get("atmosphere") and not page.get("sensory"):
        reasons.append("no atmosphere or sensory details")
    return reasons


_THIN_CHECKS = {
    "character": _character_thin,
    "event": _event_thin,
    "faction": _faction_thin,
    "location": _location_thin,
}

# FR-654: Seed pages (depth 0) get a thin_score bonus so they're deepened
# before new skeletons that compete for limited map slots.
_SEED_DEPTH_BONUS = 2


def select_thin(state: dict[str, Any]) -> dict[str, Any]:
    """Select entities that need deepening, sorted by thinness."""
    canon_pages = state.get("canon_pages", {})
    max_depth = int(state.get("max_depth", 2))

    thin_entities = []
    for pid, page in canon_pages.items():
        page_type = page.get("type", "")
        page_depth = page.get("depth", 0)

        # Skip pages at or beyond max_depth
        if page_depth >= max_depth:
            continue

        # Skip types without thinness checks (premise, synopsis, rule)
        check_fn = _THIN_CHECKS.get(page_type)
        if not check_fn:
            continue

        reasons = check_fn(page)
        if reasons:
            score = len(reasons)
            # FR-654: boost seed pages so they're deepened before skeletons
            if page_depth == 0 or "depth" not in page:
                score += _SEED_DEPTH_BONUS
            thin_entities.append(
                {
                    "entity": page,
                    "entity_id": pid,
                    "entity_type": page_type,
                    "thin_reasons": reasons,
                    "thin_reason": "; ".join(reasons),
                    "thin_score": score,
                }
            )

    # Sort by thin_score descending — thinnest entities first
    thin_entities.sort(key=lambda x: x["thin_score"], reverse=True)

    done = len(thin_entities) == 0
    return {"thin_entities": thin_entities, "done": done}
