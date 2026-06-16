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

import re

from examples.dungeon_master.api import turn_ops
from examples.dungeon_master.api.graph_app import field, get_app
from examples.dungeon_master.api.tree import CHAPTER_CLOSE_GRAPH, CHAPTER_OUTLINE_GRAPH
from examples.dungeon_master.api.world_state import (
    format_world_state,
    parse_world_state,
)

# FR-495: the LLM-authored chapter title tends to self-assert its own ordinal
# ("Chapter 1 — …", "Chapter 2:", "Ch. 3 -"). The composer's positional ``n`` is
# the authority, so strip a single leading "Chapter <ordinal><separator>" prefix
# before the title enters the heading — otherwise the ordinal doubles. The
# ``\s+`` after the label is the safety guard: a real title that merely begins
# with "Ch…" / "Chapter <word>" without a separator is left untouched (e.g.
# "Children of the Thaw", "Chapter Endings").
_LEADING_CHAPTER_LABEL = re.compile(
    r"^\s*ch(?:apter|\.)?\s+[\w-]+\s*[—–:\-.]\s*",
    re.IGNORECASE,
)


def _clean_chapter_title(title: str) -> str:
    """Drop a self-asserted 'Chapter N —' prefix; the composer owns the ordinal."""
    return _LEADING_CHAPTER_LABEL.sub("", title or "").strip()


def _beat_list(item: object) -> list[str]:
    """The ordered key-event beats from an outline entry (FR-503; ``[]`` if absent).

    The director selects satisfied beats by number from this finite list, so the
    phrases are kept verbatim (not coerced through ``field``, which flattens to a
    single string). Blank entries are dropped; a missing/non-list ``beats`` yields
    an empty list, which routes the chapter through the FR-491 free-text fallback.
    """
    raw = item.get("beats") if isinstance(item, dict) else getattr(item, "beats", None)
    if not isinstance(raw, list):
        return []
    return [str(b).strip() for b in raw if str(b).strip()]


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
        {
            "title": field(item, "title"),
            "summary": field(item, "summary"),
            "beats": _beat_list(item),
        }
        for item in (raw or [])
    ]
    if not chapters:
        raise ValueError("chapter outline returned no chapters")
    return chapters


async def close_chapter(doc: dict, cid: str) -> dict:
    """Close played chapter ``cid``: derive its end-of-chapter ``{text, world_state}``.

    The adapter-facing entry to the **Scene lifecycle** (FR-493 J5, hosted in
    :mod:`turn_ops`): the terminal step that derives ``world_state_out`` + final
    text once a chapter's scene completes. Invoked from
    :func:`doc_ops.apply_chapter_close`; stays here (not in ``turn_ops``) as the
    chapter-level seam, distinct from the write-wrapper that records its result.

    The forward-carry seam (FR-491 G2/B, preserving FR-488 J7 through play): a
    chapter is no longer expanded from its summary in one shot — it is PLAYED, and
    when its scene completes this derives two artifacts. ``world_state`` runs
    ``chapter_close.yaml`` once over the inherited ledger (where the previous
    chapter left off) + this chapter's played recaps, returning the end-of-chapter
    ledger the NEXT chapter inherits. ``text`` is the chapter's *final text*: the
    per-chapter Final Cut (FR-492), one continuous beat-faithful passage composed
    over the whole played arc (:func:`turn_ops.invoke_final_cut`) rather than the
    raw recaps. A pure read: the adapter records the result onto the card.
    """
    card = doc.get("chapters", {}).get("cards", {}).get(cid, {})
    recaps = turn_ops.chapter_recaps_text(doc, cid)
    result = await get_app(CHAPTER_CLOSE_GRAPH).ainvoke(
        {
            "synopsis": doc.get("synopsis", {}).get("text", ""),
            "summary": card.get("summary", ""),
            "index": cid,
            "previous_world_state": format_world_state(
                turn_ops.inherited_world_state(doc, cid)
            ),
            "recaps": recaps,
            "chapter_close": {},
        }
    )
    closed = result.get("chapter_close") or {}
    text = await turn_ops.invoke_final_cut(doc, cid)
    return {
        "text": text,
        "world_state": parse_world_state(closed.get("world_state")),
    }


def compose_book_deterministic(doc: dict) -> str:
    """Assemble the played chapters into one reader manuscript — pure, no LLM.

    The book seam (FR-492 Phase 3): a deterministic read over the chapters'
    already-final texts, so the model is off the path to a *first* book —
    composition is free, reproducible, and never empty when a chapter is played.
    Walks ``chapters.order`` and heads each PLAYED chapter (one whose per-chapter
    Final Cut produced a non-empty ``text``) as ``# Chapter {n}: {title}``
    followed by its beat-faithful prose; sections are joined by a blank line. The
    number ``n`` is the chapter's position in ``order`` so it stays stable when an
    earlier chapter is not yet played. The forward-carry ``world_state`` ledger is
    plumbing for the next chapter's play, not manuscript, so it never appears.
    Raises rather than returning "" when no chapter has been played (Commandment
    6: no silent fallback). LLM voice/continuity passes are a later revision seam
    (FR-492 Phase 4), not this first composition.
    """
    chapters = doc.get("chapters", {})
    cards = chapters.get("cards", {})
    sections: list[str] = []
    for n, cid in enumerate(chapters.get("order", []), start=1):
        card = cards.get(cid, {})
        text = (card.get("text") or "").strip()
        if not text:
            continue
        title = _clean_chapter_title(card.get("title", ""))
        heading = f"# Chapter {n}: {title}" if title else f"# Chapter {n}"
        sections.append(f"{heading}\n\n{text}")
    if not sections:
        raise ValueError("book composition has no played chapter")
    return "\n\n".join(sections)
