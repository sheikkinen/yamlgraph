"""Chapter-navigation primitives for DM v2 (FR-536 Workstream B).

The single home for the "walk the chapter order" reads that were duplicated across
``turn_ops`` (``inherited_world_state`` vs ``inherited_seam_packet`` shared the same
previous-card walk) and ``witness_metrics`` (a second ``_previous_chapter_id``).

A near-**leaf** module by design: it imports only :mod:`story_doc` (itself a leaf
over ``json``/``pathlib``), so ``lifecycle_resolver`` can depend on it directly at
module load instead of lazily importing ``turn_ops`` inside functions to dodge a
circular import (the FR-534 workaround this dissolves, FR-536 J4). The single typed
home for chapter reads AND writes (FR-556 Contract A): the getters are pure
read-mostly views; :func:`write_chapter_card` is the one structural write seam.

Pure reads: no LLM, no I/O. The setter validates structure but performs no I/O.
"""

from __future__ import annotations

from examples.dungeon_master.api import story_doc


def chapter_order(doc: dict) -> list:
    """The play order of chapter ids (empty if none)."""
    return (doc.get("chapters") or {}).get("order") or []


def chapter_cards(doc: dict) -> dict:
    """The chapter-id -> card mapping (empty if none)."""
    return (doc.get("chapters") or {}).get("cards") or {}


def chapter_card(doc: dict, cid: str) -> dict:
    """Read-only view of chapter ``cid``'s card (empty if absent)."""
    return chapter_cards(doc).get(cid, {})


def chapter_turns(doc: dict, cid: str) -> list:
    """Read-only view of chapter ``cid``'s played turns (FR-491 C; empty if none).

    The single accessor for ``cards[<cid>]["turns"]`` the instrument cluster reads
    (FR-556 Contract A) -- migrated off the raw ``(cards.get(cid) or {}).get("turns")``
    reach-in that was duplicated across the witness/salience metrics.
    """
    return chapter_card(doc, cid).get("turns") or []


def write_chapter_card(doc: dict, cid: str, card: dict) -> None:
    """Write chapter ``cid``'s card through the one validated write seam (FR-556 J4).

    Validates the card's structure via :func:`story_doc.validate_chapter_card` and
    raises :class:`story_doc.InvalidChapterCard` BEFORE committing, so a
    structurally-broken card never reaches the doc. The funnel every card-authoring
    path routes through; FR-558 (Contract C) binds the playability gate battery here
    too, so no writer can bypass either check.
    """
    story_doc.validate_chapter_card(card)
    chapters = doc.setdefault("chapters", {})
    cards = chapters.setdefault("cards", {})
    cards[cid] = card


def previous_chapter_id(doc: dict, cid: str) -> str | None:
    """The chapter id immediately before ``cid`` in play order, or ``None``.

    Returns ``None`` for the first chapter and for a ``cid`` not in the order
    (the honest contract; callers that need the legacy ``""`` coerce with ``or ""``).
    """
    order = chapter_order(doc)
    try:
        i = order.index(cid)
    except ValueError:
        return None
    return str(order[i - 1]) if i > 0 else None


def previous_chapter_card(doc: dict, cid: str) -> dict:
    """The previous chapter's card (empty for the first chapter or unknown ``cid``)."""
    prev = previous_chapter_id(doc, cid)
    return chapter_cards(doc).get(prev, {}) if prev is not None else {}


def inherited_world_state(doc: dict, cid: str) -> dict:
    """The structured world_state chapter ``cid`` inherits — the PREVIOUS ledger.

    The load-bearing forward-carry (FR-488 J7, preserved through play): each
    chapter is played from where the last one left off. The carried value is the
    typed ledger (FR-499A) the previous chapter closed with. Empty (``{}``) for the
    first chapter, or when the chapter id is not in the derived order.
    """
    return previous_chapter_card(doc, cid).get("world_state", {}) or {}


def inherited_seam_packet(doc: dict, cid: str) -> dict:
    """The seam packet chapter ``cid`` inherits from the previous chapter (FR-506)."""
    return previous_chapter_card(doc, cid).get("seam_packet", {}) or {}
