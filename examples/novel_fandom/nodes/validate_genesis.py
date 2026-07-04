"""Validate genesis output before persist (FR-664/FR-667).

Runs referential integrity check on structured_world pages.
Warn-only — does not block persist (genesis is expensive to re-run).
"""

from __future__ import annotations

import logging
from typing import Any

from .persist_genesis import validate_referential_integrity

logger = logging.getLogger(__name__)


def validate_genesis(state: dict[str, Any]) -> dict[str, Any]:
    """Validate structured_world referential integrity."""
    world = state.get("structured_world", {})
    if not world:
        return {"gate_result": {"valid": True, "violations": []}}

    pages: list[dict] = []
    for key in ("premise", "synopsis"):
        page = world.get(key)
        if isinstance(page, dict):
            pages.append(page)
    for key in ("characters", "events", "factions", "rules", "locations"):
        items = world.get(key, [])
        if isinstance(items, list):
            pages.extend(item for item in items if isinstance(item, dict))

    result = validate_referential_integrity(pages)
    if not result["valid"]:
        logger.warning(
            "Genesis referential integrity: %d orphan IDs: %s",
            len(result["orphan_ids"]),
            ", ".join(result["orphan_ids"]),
        )
    else:
        logger.info("Genesis referential integrity: PASS")

    return {"gate_result": result}
