"""Reference-integrity gate for wiki-memory demo.

Checks that every reference in a drafted page resolves to an existing
page in the wiki. Pure deterministic check — no LLM call.
"""

from __future__ import annotations

from typing import Any


def check_references(state: dict[str, Any]) -> dict[str, Any]:
    """Check every reference in drafted_page resolves to an existing wiki page.

    Reads:
        state["drafted_page"]: dict with "references" list
        state["wiki"]: dict keyed by page id (from data_files glob)

    Returns:
        {"gate_result": {"valid": bool, "violations": list[str]},
         "save_path": str,
         "drafted_page": dict}  # normalized to plain dict for downstream
    """
    drafted = state.get("drafted_page", {})
    wiki = state.get("wiki", {})

    # Pydantic model → dict (normalize at boundary for downstream nodes)
    if hasattr(drafted, "model_dump"):
        drafted = drafted.model_dump()

    existing_ids = set(wiki.keys())
    refs = drafted.get("references", []) or []
    # Also include the page's own id as "will exist after persist"
    own_id = drafted.get("id", "")

    missing = [r for r in refs if r != own_id and r not in existing_ids]

    result: dict[str, Any] = {
        "gate_result": {"valid": not missing, "violations": missing},
        "drafted_page": drafted,  # always return as plain dict
    }
    # Compute save path for the persist node
    if own_id:
        result["save_path"] = f"wiki/{own_id}.yaml"
    return result
