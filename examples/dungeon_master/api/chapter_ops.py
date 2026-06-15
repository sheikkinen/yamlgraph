"""Book-chapter operations for DM v2 (FR-488 / FR-491).

The synopsis is the whole book in outline. This module owns the two chapter
graph invocations, kept apart from the stage adapter (mirroring ``turn_ops`` for
the play loop) so the structured outline parse and the forward-carried
``world_state`` plumbing live in one place and ``session`` stays under the size
gate.

Both functions are PURE reads of the story ``doc`` — they invoke a graph and
return its normalized output, never mutating ``doc``. The adapter owns the writes
(spawning cards, recording text). The load-bearing seam is the forward-carry
(J7): each chapter is PLAYED turn by turn (FR-491), and when its scene completes
:func:`close_chapter` derives the end-of-chapter ``world_state`` from the
inherited ledger + this chapter's played recaps so the NEXT chapter is played
from where this one left off.
"""

from __future__ import annotations

from examples.dungeon_master.api import turn_ops
from examples.dungeon_master.api.graph_app import clean_text, field, get_app
from examples.dungeon_master.api.tree import (
    BOOK_GRAPH,
    CHAPTER_CLOSE_GRAPH,
    CHAPTER_OUTLINE_GRAPH,
)


async def outline_chapters(doc: dict) -> list[dict]:
    """Split the accepted synopsis into an ordered list of ``{title, summary}``.

    Runs ``chapter_outline.yaml`` once over the synopsis and returns the structured
    chapter list (J1: a titled paragraph per chapter — a shape a plain line-split
    cannot hold). Raises rather than substituting an empty book when the model
    returns no chapters (Commandment 6: no silent fallback).
    """
    synopsis = doc.get("synopsis", {}).get("text", "")
    result = await get_app(CHAPTER_OUTLINE_GRAPH).ainvoke(
        {"synopsis": synopsis, "outline": {}}
    )
    outline = result.get("outline") or {}
    raw = outline.get("chapters") if isinstance(outline, dict) else None
    chapters = [
        {"title": field(item, "title"), "summary": field(item, "summary")}
        for item in (raw or [])
    ]
    if not chapters:
        raise ValueError("chapter outline returned no chapters")
    return chapters


async def close_chapter(doc: dict, cid: str) -> dict:
    """Close played chapter ``cid``: derive its end-of-chapter ``{text, world_state}``.

    The forward-carry seam (FR-491 G2/B, preserving FR-488 J7 through play): a
    chapter is no longer expanded from its summary in one shot — it is PLAYED, and
    when its scene completes this runs ``chapter_close.yaml`` once over the
    inherited ``world_state`` (where the previous chapter left off) + this
    chapter's played recaps, returning the end-of-chapter ledger the NEXT chapter
    inherits. ``text`` is the chapter's prose — the played recaps themselves. A
    pure read: the adapter records the result onto the card.
    """
    card = doc.get("chapters", {}).get("cards", {}).get(cid, {})
    recaps = turn_ops.chapter_recaps_text(doc, cid)
    result = await get_app(CHAPTER_CLOSE_GRAPH).ainvoke(
        {
            "synopsis": doc.get("synopsis", {}).get("text", ""),
            "summary": card.get("summary", ""),
            "index": cid,
            "previous_world_state": turn_ops.inherited_world_state(doc, cid),
            "recaps": recaps,
            "chapter_close": {},
        }
    )
    closed = result.get("chapter_close") or {}
    return {
        "text": recaps,
        "world_state": field(closed, "world_state"),
    }


def played_chapters_text(doc: dict) -> str:
    """The played material the Book composes from: every chapter in order (FR-491 E).

    A pure read over the closed chapter cards — each contributes its title, its
    played prose (``text``, the woven recaps), and the end-of-chapter
    ``world_state`` that the next chapter inherited. This is the whole played book
    laid end to end, the raw material the Book graph renders into one manuscript.
    Raises rather than composing from nothing when no chapter is played
    (Commandment 6: no silent fallback) — the Book stage is gated on
    ``all_chapters_played`` so this is a contract check, not a user path.
    """
    chapters = doc.get("chapters", {})
    cards = chapters.get("cards", {})
    blocks: list[str] = []
    for cid in chapters.get("order", []):
        card = cards.get(cid, {})
        title = card.get("title", "").strip()
        prose = (card.get("text") or "").strip()
        world_state = (card.get("world_state") or "").strip()
        block = f"## Chapter {cid}: {title}\n\n{prose}"
        if world_state:
            block += f"\n\nWORLD STATE AT CHAPTER END:\n{world_state}"
        blocks.append(block)
    if not blocks:
        raise ValueError("compose_book called with no played chapters")
    return "\n\n".join(blocks)


async def compose_book(doc: dict, *, instruction: str = "", draft: str = "") -> str:
    """Compose the finished manuscript from every played chapter (FR-491 E).

    The single whole-book finish, retiring the three single-scene finishes: where
    the play loop produced each chapter's prose and forward-carried world_state,
    this renders them into one continuous book. Runs ``book.yaml`` (plain prose,
    ``parse_json: false``) over the synopsis + the played chapters, optionally
    steered by a writer's ``instruction``/``draft``. A pure read; the adapter
    records the returned text onto the Book card.
    """
    result = await get_app(BOOK_GRAPH).ainvoke(
        {
            "synopsis": doc.get("synopsis", {}).get("text", ""),
            "chapters": played_chapters_text(doc),
            "instruction": instruction,
            "draft": draft,
            "book": "",
        }
    )
    return clean_text(result.get("book"))
