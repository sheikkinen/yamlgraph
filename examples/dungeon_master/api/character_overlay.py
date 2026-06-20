"""Derived per-chapter character state overlay for DM v2 (FR-541).

The character-grain twin of the world-grain ``world_state`` ledger. A character's
ORIGIN sheet (``characters.cards[id]["text"]``) is immutable -- voice, backstory,
speech -- so the intent node reads the same sheet in chapter 1 and chapter 7, and
a character who has died and returned still acts from their pre-death self. This
module derives a CURRENT STATE *overlay* from the committed
``character_state_deltas`` of prior chapters, layered ALONGSIDE (never replacing)
the origin sheet at intent time.

Deterministic, no LLM: the overlay is the last-write-wins accrual of a character's
prior ``to_state`` transitions. It REUSES :func:`lifecycle_resolver._state_map_from_memory`
-- the existing per-chapter delta fold -- rather than re-implementing one, so a
single accrual rule governs character-over-time state (FR-541 J1; the "one
narrowing point, two paths" lesson of FR-537). Empty until a delta exists, so a
chapter with no prior committed state reproduces today's intent context exactly.
"""

from __future__ import annotations

from examples.dungeon_master.api.lifecycle_resolver import (
    _norm_name,
    _state_map_from_memory,
)


def derive_overlay(doc: dict, cid: str, name: str) -> dict:
    """The character's CURRENT STATE as chapter ``cid`` opens, accrued from prior deltas.

    Walks the chapters BEFORE ``cid`` in ``chapters.order`` and folds each
    committed ``chapter_memory`` through the shared lifecycle fold, recording every
    state transition for ``name`` in order. Returns
    ``{"status": <most recent to_state>, "history": ["chapter <id>: <state>", ...]}``
    or ``{}`` when the character has no prior committed transition (additive: the
    intent node then reads exactly today's context). Pure; never mutates ``doc``.
    """
    name_key = _norm_name(name)
    chapters = doc.get("chapters", {})
    order = list(chapters.get("order") or [])
    cards = chapters.get("cards") or {}
    prior_cids = order[: order.index(cid)] if cid in order else order

    status = ""
    history: list[str] = []
    for pcid in prior_cids:
        memory = (cards.get(pcid) or {}).get("chapter_memory") or {}
        states = _state_map_from_memory(memory)
        if name_key in states:
            status = states[name_key]
            history.append(f"chapter {pcid}: {status}")
    if not status:
        return {}
    return {"status": status, "history": history}
