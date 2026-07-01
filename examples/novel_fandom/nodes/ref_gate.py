"""Reference-integrity gate for novel_fandom canon.

Adapted from FR-628 wiki-memory gate. Adds lane-immutability check:
writes to existing lane:static pages are rejected.
"""

from __future__ import annotations

from typing import Any


def check_references(state: dict[str, Any]) -> dict[str, Any]:
    """Check references resolve and lane immutability is respected.

    Reads:
        state["drafted_page"]: dict with "references" and "lane" fields
        state["canon"]: dict keyed by page id (from data_files glob)

    Returns:
        {"gate_result": {"valid": bool, "violations": list[str]},
         "save_path": str,
         "drafted_page": dict}
    """
    drafted = state.get("drafted_page", {})
    canon = state.get("canon", {})

    # Pydantic model → dict (normalize at boundary)
    if hasattr(drafted, "model_dump"):
        drafted = drafted.model_dump()

    existing_ids = set(canon.keys())
    own_id = drafted.get("id", "")
    violations: list[str] = []

    # --- Lane immutability check ---
    if own_id and own_id in existing_ids:
        existing_page = canon[own_id]
        existing_data = (
            existing_page if isinstance(existing_page, dict) else existing_page
        )
        if isinstance(existing_data, dict) and existing_data.get("lane") == "static":
            violations.append(
                f"lane:static page '{own_id}' already exists and is immutable"
            )

    # --- Orphan reference check ---
    refs = drafted.get("references", []) or []
    missing = [r for r in refs if r != own_id and r not in existing_ids]
    violations.extend(f"orphan reference: '{r}'" for r in missing)

    result: dict[str, Any] = {
        "gate_result": {"valid": not violations, "violations": violations},
        "drafted_page": drafted,
    }
    if own_id:
        result["save_path"] = f"canon/{own_id}.yaml"
    return result
