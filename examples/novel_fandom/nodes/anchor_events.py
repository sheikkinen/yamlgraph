"""Anchor events pre-pass for worldgen (FR-647).

Scans event pages, computes per-character event context with spatial
scoping (world/regional/local) and age arithmetic from absolute dates.
Pure computation — no LLM calls.
"""

import logging

logger = logging.getLogger(__name__)


def anchor_events(state: dict) -> dict:
    """Build per-character event context from event pages and spatial scoping."""
    canon = state.get("canon_pages", {})
    events = sorted(
        [p for p in canon.values() if p.get("type") == "event"],
        key=lambda e: e.get("year") or 9999,
    )
    characters = {p["id"]: p for p in canon.values() if p.get("type") == "character"}

    event_context: dict[str, list[dict]] = {cid: [] for cid in characters}

    for event in events:
        scope = event.get("scope", "world")
        affected_locs = set(event.get("affected_locations", []))
        participants = set(event.get("participants", []))
        event_year = event.get("year")

        for cid, char in characters.items():
            affected = False
            if scope == "world":
                affected = True
            elif scope == "regional":
                char_locs = {char.get("faction", "")} | set(char.get("references", []))
                affected = bool(char_locs & affected_locs) or cid in participants
            elif scope == "local":
                affected = cid in participants

            if affected:
                birth_year = char.get("birth_year")
                age_at_event = (
                    event_year - birth_year
                    if event_year is not None and birth_year is not None
                    else None
                )
                event_context[cid].append(
                    {
                        "event_id": event["id"],
                        "window": event.get("window", ""),
                        "year": event_year,
                        "age_at_event": age_at_event,
                        "consequences": event.get("consequences", []),
                        "scope": scope,
                    }
                )

    logger.info(
        "📅 Anchored %d events across %d characters",
        len(events),
        len(characters),
    )
    return {"event_context": event_context}
