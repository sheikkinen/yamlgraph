"""Persist genesis structured world output to canon/ (FR-655).

Takes the structured_world dict from the structure_world LLM node
and writes each entity as a separate YAML file via persist_pages logic.
FR-664: Validate referential integrity before writing.
FR-683: Validation extracted to ref_integrity.py.
"""

from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path
from typing import Any

# Sibling import shim (FR-683): tools loaded via spec_from_file_location
# don't have their directory on sys.path.
_nodes_dir = str(Path(__file__).parent)
if _nodes_dir not in sys.path:
    sys.path.insert(0, _nodes_dir)

from ref_integrity import validate_referential_integrity  # noqa: E402

logger = logging.getLogger(__name__)


def _load_persist_impl():  # noqa: ANN202
    """Load _persist_impl via importlib to avoid relative import issues."""
    persist_path = Path(__file__).parent / "persist_pages.py"
    spec = importlib.util.spec_from_file_location(
        "_persist_pages_genesis", persist_path
    )
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod._persist_impl


def persist_genesis(state: dict[str, Any]) -> dict[str, Any]:
    """Flatten structured_world into deepened format and persist."""
    canon_dir = Path(__file__).parent.parent / "canon"
    return _persist_genesis_impl(state, canon_dir)


def _persist_genesis_impl(
    state: dict[str, Any],
    canon_dir: Path,
    page_models: dict | None = None,
) -> dict[str, Any]:
    """Implementation with injectable canon_dir and page_models for testing."""
    world = state.get("structured_world", {})
    if not world:
        logger.warning("No structured_world in state — nothing to persist")
        return {"written_paths": [], "written_count": 0}

    pages: list[dict] = []

    # Premise and synopsis are single dicts
    for key in ("premise", "synopsis"):
        page = world.get(key)
        if isinstance(page, dict):
            pages.append(page)

    # Lists of entities
    for key in ("characters", "events", "factions", "rules", "locations"):
        items = world.get(key, [])
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    pages.append(item)

    # Wrap each page as {updated_page: page} — the format _persist_impl expects
    # for the "deepened" list. Also set depth: 0 and lane: dynamic as defaults.
    deepened = []
    for page in pages:
        page.setdefault("depth", 0)
        page.setdefault("lane", "dynamic")
        deepened.append({"updated_page": page})

    # FR-664: validate referential integrity (warn-only)
    result = validate_referential_integrity(pages)
    if not result["valid"]:
        logger.warning(
            "Genesis referential integrity violations (%d orphan IDs):",
            len(result["orphan_ids"]),
        )
        for v in result["violations"]:
            logger.warning("  %s", v)

    return _load_persist_impl()(
        {"deepened": deepened}, canon_dir, page_models=page_models
    )
