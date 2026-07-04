"""Validate genesis output before persist (FR-664/FR-667).

Runs referential integrity check on structured_world pages.
Warn-only — does not block persist (genesis is expensive to re-run).
"""

from __future__ import annotations

import importlib.util
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _load_validate_fn():  # noqa: ANN202
    """Load validate_referential_integrity via importlib."""
    persist_path = Path(__file__).parent / "persist_genesis.py"
    spec = importlib.util.spec_from_file_location("_persist_genesis_val", persist_path)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod.validate_referential_integrity


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

    result = _load_validate_fn()(pages)
    if not result["valid"]:
        logger.warning(
            "Genesis referential integrity: %d orphan IDs: %s",
            len(result["orphan_ids"]),
            ", ".join(result["orphan_ids"]),
        )
    else:
        logger.info("Genesis referential integrity: PASS")

    return {"gate_result": result}
