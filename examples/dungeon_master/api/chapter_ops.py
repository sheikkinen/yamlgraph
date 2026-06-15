"""Book-chapter operations for DM v2 (FR-488).

The synopsis is the whole book in outline. This module owns the two chapter
graph invocations, kept apart from the stage adapter (mirroring ``turn_ops`` for
the play loop) so the structured outline parse and the forward-carried
``world_state`` plumbing live in one place and ``session`` stays under the size
gate.

Both functions are PURE reads of the story ``doc`` — they invoke a graph and
return its normalized output, never mutating ``doc``. The adapter owns the writes
(spawning cards, recording text). The load-bearing seam is the forward-carry
(J7): expanding ``chapter:n`` threads ``chapter:n-1``'s ``world_state`` into the
graph so each chapter is written consistently from where the last left off.
"""

from __future__ import annotations

from examples.dungeon_master.api.graph_app import field, get_app
from examples.dungeon_master.api.tree import CHAPTER_GRAPH, CHAPTER_OUTLINE_GRAPH


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


async def invoke_chapter(
    doc: dict, n: int, *, instruction: str = "", draft: str = ""
) -> dict:
    """Expand chapter ``n``: return its ``{text, world_state}``.

    Reads chapter ``n``'s summary and — the forward-carry seam (J7) — chapter
    ``n-1``'s ``world_state`` (empty for the first chapter), runs ``chapter.yaml``
    once, and returns the expanded prose plus the world-state ledger at the end of
    this chapter. Empty ``draft`` => first expansion; non-empty => apply
    ``instruction`` to the existing text. A pure read: the adapter records the
    result onto the card.
    """
    cards = doc.get("chapters", {}).get("cards", {})
    card = cards.get(str(n), {})
    prev = cards.get(str(n - 1), {})
    previous_world_state = prev.get("world_state", "") if n > 1 else ""
    result = await get_app(CHAPTER_GRAPH).ainvoke(
        {
            "synopsis": doc.get("synopsis", {}).get("text", ""),
            "summary": card.get("summary", ""),
            "index": str(n),
            "previous_world_state": previous_world_state,
            "draft": draft,
            "instruction": instruction,
            "chapter": {},
        }
    )
    chapter = result.get("chapter") or {}
    return {
        "text": field(chapter, "text"),
        "world_state": field(chapter, "world_state"),
    }
