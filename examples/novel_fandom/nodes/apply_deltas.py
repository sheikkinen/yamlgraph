"""Delta application tool for the novel_fandom close loop.

Applies edge-level ops to the dynamic canon:
- add_event: create a new Event page (lane: dynamic)
- add_edge: add a Relationship edge to an existing character
- update_valence: change a relationship's valence
- invalidate_edge: set valid_to on an existing edge (bi-temporal)

Invariants:
- Carry-forward floor: zero ops → canon unchanged
- Lane guard: rejects ops targeting lane:static pages
- Target validation: rejects ops referencing non-existent entities
- Invalidate-not-delete: contradicting facts set valid_to, never delete
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def apply_deltas(state: dict[str, Any]) -> dict[str, Any]:
    """Apply edge-level delta ops to canon.

    Reads:
        state["deltas"]: list of op dicts, each with "op" and op-specific fields
        state["canon"]: dict keyed by page id

    Returns:
        {"applied": list[str], "rejected": list[str]}

    Op shapes:
        {"op": "add_event", "id": str, "window": str, "participants": [str],
         "consequences": [str], "references": [str]}
        {"op": "add_edge", "character": str, "to": str, "kind": str, "valence": str}
        {"op": "update_valence", "character": str, "to": str, "new_valence": str}
        {"op": "invalidate_edge", "character": str, "to": str}
    """
    deltas = state.get("deltas", [])
    canon = state.get("canon", {})

    # Pydantic model → list
    if hasattr(deltas, "model_dump"):
        deltas = deltas.model_dump()
    if isinstance(deltas, dict) and "ops" in deltas:
        deltas = deltas["ops"]

    existing_ids = set(canon.keys())
    applied: list[str] = []
    rejected: list[str] = []
    now = datetime.now(tz=UTC).strftime("%Y-%m-%d")

    for delta in deltas:
        if not isinstance(delta, dict):
            rejected.append("invalid op: not a dict")
            continue

        op = delta.get("op", "")

        if op == "add_event":
            result = _apply_add_event(delta, canon, existing_ids, now)
        elif op == "add_edge":
            result = _apply_add_edge(delta, canon, existing_ids)
        elif op == "update_valence":
            result = _apply_update_valence(delta, canon, existing_ids)
        elif op == "invalidate_edge":
            result = _apply_invalidate_edge(delta, canon, existing_ids, now)
        else:
            rejected.append(f"unknown op: {op!r}")
            continue

        if result.startswith("OK"):
            applied.append(result)
        else:
            rejected.append(result)

    return {"applied": applied, "rejected": rejected}


def _apply_add_event(
    delta: dict,
    canon: dict,
    existing_ids: set[str],
    now: str,
) -> str:
    """Create a new Event page (lane: dynamic)."""
    event_id = delta.get("id", "")
    if not event_id:
        return "add_event: missing id"

    # Target validation: participants must exist
    participants = delta.get("participants", [])
    for p in participants:
        if p not in existing_ids:
            return f"add_event '{event_id}': participant '{p}' not in canon"

    # References must exist
    references = delta.get("references", [])
    for r in references:
        if r != event_id and r not in existing_ids:
            return f"add_event '{event_id}': reference '{r}' not in canon"

    canon[event_id] = {
        "type": "event",
        "id": event_id,
        "lane": "dynamic",
        "window": delta.get("window", ""),
        "participants": participants,
        "consequences": delta.get("consequences", []),
        "valid_from": now,
        "valid_to": None,
        "references": references,
    }
    existing_ids.add(event_id)
    return f"OK: add_event '{event_id}'"


def _apply_add_edge(
    delta: dict,
    canon: dict,
    existing_ids: set[str],
) -> str:
    """Add a Relationship edge to an existing character."""
    char_id = delta.get("character", "")
    target = delta.get("to", "")

    if char_id not in existing_ids:
        return f"add_edge: character '{char_id}' not in canon"
    if target not in existing_ids:
        return f"add_edge: target '{target}' not in canon"

    page = canon[char_id]
    if not isinstance(page, dict):
        return f"add_edge: page '{char_id}' is not a dict"

    # Lane guard
    if page.get("lane") == "static":
        return f"add_edge: character '{char_id}' is lane:static (immutable)"

    rels = list(page.get("relationships", []))
    rels.append(
        {
            "to": target,
            "kind": delta.get("kind", ""),
            "valence": delta.get("valence", ""),
        }
    )
    page["relationships"] = rels

    # Add to references if not present
    refs = list(page.get("references", []))
    if target not in refs:
        refs.append(target)
    page["references"] = refs

    return f"OK: add_edge '{char_id}'->{target}'"


def _apply_update_valence(
    delta: dict,
    canon: dict,
    existing_ids: set[str],
) -> str:
    """Update a relationship's valence on an existing character."""
    char_id = delta.get("character", "")
    target = delta.get("to", "")
    new_valence = delta.get("new_valence", "")

    if char_id not in existing_ids:
        return f"update_valence: character '{char_id}' not in canon"
    if target not in existing_ids:
        return f"update_valence: target '{target}' not in canon"

    page = canon[char_id]
    if not isinstance(page, dict):
        return f"update_valence: page '{char_id}' is not a dict"

    # Lane guard
    if page.get("lane") == "static":
        return f"update_valence: character '{char_id}' is lane:static (immutable)"

    rels = page.get("relationships", [])
    found = False
    for rel in rels:
        rel_data = rel if isinstance(rel, dict) else dict(rel)
        if rel_data.get("to") == target:
            rel_data["valence"] = new_valence
            found = True
            break

    if not found:
        return f"update_valence: no edge from '{char_id}' to '{target}'"

    return f"OK: update_valence '{char_id}'->{target}' to '{new_valence}'"


def _apply_invalidate_edge(
    delta: dict,
    canon: dict,
    existing_ids: set[str],
    now: str,
) -> str:
    """Set valid_to on an existing relationship (invalidate, not delete)."""
    char_id = delta.get("character", "")
    target = delta.get("to", "")

    if char_id not in existing_ids:
        return f"invalidate_edge: character '{char_id}' not in canon"
    if target not in existing_ids:
        return f"invalidate_edge: target '{target}' not in canon"

    page = canon[char_id]
    if not isinstance(page, dict):
        return f"invalidate_edge: page '{char_id}' is not a dict"

    # Lane guard
    if page.get("lane") == "static":
        return f"invalidate_edge: character '{char_id}' is lane:static (immutable)"

    rels = page.get("relationships", [])
    found = False
    for rel in rels:
        rel_data = rel if isinstance(rel, dict) else dict(rel)
        if rel_data.get("to") == target and not rel_data.get("valid_to"):
            rel_data["valid_to"] = now
            found = True
            break

    if not found:
        return f"invalidate_edge: no active edge from '{char_id}' to '{target}'"

    return f"OK: invalidate_edge '{char_id}'->{target}'"
