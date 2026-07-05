"""Referential integrity validation for novel_fandom (FR-683).

Self-contained module: pure function + state wrapper.
Loaded by ref_check.yaml (graph-tool) and persist_genesis.py (sibling import).

FR-664: Original implementation.
FR-683: Extracted from persist_genesis.py, importlib hack eliminated.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def validate_referential_integrity(
    pages: list[dict],
) -> dict[str, Any]:
    """Check all cross-references resolve to defined entity IDs.

    Returns:
        {"valid": bool, "orphan_ids": list[str], "violations": list[str]}
    """
    defined_ids = {p["id"] for p in pages if "id" in p}
    orphans: set[str] = set()

    for page in pages:
        # relationships.to
        for rel in page.get("relationships", []):
            to = rel.get("to", "") if isinstance(rel, dict) else ""
            if to and to not in defined_ids:
                orphans.add(to)

        # participants, references, members, affected_locations
        for field in (
            "participants",
            "references",
            "members",
            "affected_locations",
        ):
            for ref in page.get(field, []):
                ref_id = ref if isinstance(ref, str) else ref.get("id", "")
                if ref_id and ref_id not in defined_ids:
                    orphans.add(ref_id)

    violations = [
        f"orphan ID '{oid}' referenced but never defined" for oid in sorted(orphans)
    ]
    return {
        "valid": len(orphans) == 0,
        "orphan_ids": sorted(orphans),
        "violations": violations,
    }


def _flatten_structured_world(world: dict) -> list[dict]:
    """Extract all entity dicts from a structured_world dict."""
    pages: list[dict] = []
    for key in ("premise", "synopsis"):
        page = world.get(key)
        if isinstance(page, dict):
            pages.append(page)
    for key in ("characters", "events", "factions", "rules", "locations"):
        items = world.get(key, [])
        if isinstance(items, list):
            pages.extend(item for item in items if isinstance(item, dict))
    return pages


def ref_check(state: dict[str, Any]) -> dict[str, Any]:
    """State wrapper: validate referential integrity.

    Accepts input from two sources:
    - state["structured_world"]: dict with entity lists (genesis pipeline)
    - state["pages"]: JSON string or list of dicts (graph-tool boundary)

    Returns {"gate_result": {"valid": bool, "orphan_ids": [...], "violations": [...]}}
    """
    # Source 1: structured_world (genesis pipeline)
    world = state.get("structured_world")
    if world and isinstance(world, dict):
        pages = _flatten_structured_world(world)
    else:
        # Source 2: pages (graph-tool input — may be JSON string)
        raw = state.get("pages", [])
        if isinstance(raw, str):
            try:
                pages = json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                pages = []
        elif isinstance(raw, list):
            pages = raw
        else:
            pages = []

    if not pages:
        return {"gate_result": {"valid": True, "orphan_ids": [], "violations": []}}

    result = validate_referential_integrity(pages)
    if not result["valid"]:
        logger.warning(
            "Referential integrity: %d orphan IDs: %s",
            len(result["orphan_ids"]),
            ", ".join(result["orphan_ids"]),
        )
    else:
        logger.info("Referential integrity: PASS")

    return {"gate_result": result}
