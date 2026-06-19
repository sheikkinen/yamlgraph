"""Chapter-navigation primitives for DM v2 (FR-536 Workstream B).

The single home for the "walk the chapter order" reads that were duplicated across
``turn_ops`` (``inherited_world_state`` vs ``inherited_seam_packet`` shared the same
previous-card walk) and ``witness_metrics`` (a second ``_previous_chapter_id``).

A **leaf** module by design: it imports nothing from the DM ``api`` package, so
``lifecycle_resolver`` can depend on it directly at module load instead of lazily
importing ``turn_ops`` inside functions to dodge a circular import (the FR-534
workaround this dissolves, FR-536 J4).

Pure: no LLM, no I/O.
"""

from __future__ import annotations


def chapter_order(doc: dict) -> list:
    """The play order of chapter ids (empty if none)."""
    return (doc.get("chapters") or {}).get("order") or []


def chapter_cards(doc: dict) -> dict:
    """The chapter-id -> card mapping (empty if none)."""
    return (doc.get("chapters") or {}).get("cards") or {}


def chapter_card(doc: dict, cid: str) -> dict:
    """Read-only view of chapter ``cid``'s card (empty if absent)."""
    return chapter_cards(doc).get(cid, {})


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
