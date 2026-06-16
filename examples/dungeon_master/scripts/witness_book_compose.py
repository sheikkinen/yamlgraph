"""Live vertex witness for FR-492 — chapter-final text + deterministic Book.

Drives a real DMSession against vertex/gemini, end to end, proving the two
generative/assembly seams the deterministic tests can only mock:

  1. PER-CHAPTER FINAL CUT (generation at the chapter seam) — each chapter is
     played turn by turn until the director declares the scene complete; on close
     the chapter stores a beat-faithful final ``text`` composed over its whole
     played arc (turn_ops.invoke_final_cut), not concatenated recaps.
  2. DETERMINISTIC BOOK (assembly at the book seam) — navigating to the Book stage
     renders compose_book_deterministic over the played chapters' final texts with
     NO whole-book LLM call. The book must be non-empty and contain each chapter's
     heading + its final prose.

Run:  PYTHONPATH="$PWD" python examples/dungeon_master/scripts/witness_book_compose.py
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from dotenv import load_dotenv

from examples.dungeon_master.api import session as dm_session
from examples.dungeon_master.api import story_doc, tree

PREMISE = (
    "A tight two-chapter story: a lone courier must carry a sealed warning across "
    "a frozen river to a besieged outpost. Keep it small and fast — two short "
    "chapters, a handful of beats each."
)

TURN_CAP = 24  # safety bound on total turn-accepts across all chapters


def _hr(title: str) -> None:
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")


async def main() -> None:
    load_dotenv()  # vertex creds (PROVIDER, VERTEX_API_KEY) before any LLM call
    tmp = Path(tempfile.mkdtemp(prefix="dm_witness_"))
    dm_session.STORY_ROOT = tmp
    dm_session._reset_caches()
    story_dir = tmp / "witness"

    session = dm_session.DMSession("witness")

    _hr("1. SYNOPSIS")
    await session.weave(text="", prompt=PREMISE)
    view = await session.accept()
    doc = story_doc.read(story_dir)
    print("synopsis:", doc["synopsis"]["text"][:300])
    print("-> landed on:", view.stage)

    _hr("2. CAST (accept each character)")
    while view.stage.startswith("char:"):
        doc = story_doc.read(story_dir)
        card = doc["characters"]["cards"][view.stage[len("char:") :]]
        print(f"  {view.stage}: {card.get('text','')[:120]}")
        view = await session.accept()
    doc = story_doc.read(story_dir)
    order = doc["chapters"]["order"]
    print("-> landed on:", view.stage)
    print("chapters derived:", order)
    for cid in order:
        c = doc["chapters"]["cards"][cid]
        print(f"  chapter {cid}: {c['title']} — {c['summary'][:120]}")

    _hr("3. PLAY each chapter to its director-judged completion")
    view = await session.navigate(f"chapter:{order[0]}")
    print("opened:", view.stage)
    accepts = 0
    while accepts < TURN_CAP:
        doc = story_doc.read(story_dir)
        if tree.all_chapters_played(doc):
            print("** all chapters played **")
            break
        cur = doc["stage"]
        if not cur.startswith("turn:"):
            print("stage left the play loop unexpectedly:", cur)
            break
        cid, n = tree.parse_turn(cur)
        direction = doc["chapters"]["cards"][cid]["turns"][n - 1]["direction"]
        sc = direction.get("scene_complete")
        print(f"  {cur}  phase={direction.get('phase','?'):10} scene_complete={sc}")
        view = await session.accept()
        accepts += 1
        # When a chapter just closed, surface its per-chapter Final Cut final text.
        doc = story_doc.read(story_dir)
        card = doc["chapters"]["cards"][cid]
        if card.get("reviewed") and card.get("text"):
            print(f"    >> chapter {cid} CLOSED.")
            print(f"       world_state (carry): {card.get('world_state','')[:180]}")
            print(f"       final text (Final Cut, first 240): {card['text'][:240]}")

    _hr("4. THE BOOK (deterministic compose — NO whole-book LLM call)")
    doc = story_doc.read(story_dir)
    if not tree.all_chapters_played(doc):
        print("!! not all chapters played within cap; book gate would stay locked")
        print(
            "   chapters:",
            [(c, doc["chapters"]["cards"][c].get("reviewed")) for c in order],
        )
        return
    assert tree.all_chapters_played(doc), "book gate must be open"
    view = await session.navigate("book")
    book = view.text
    print("book stage:", view.stage, "kind:", view.kind)
    print("book length (chars):", len(book))
    # Substance checks: every played chapter's heading + its final prose must be in
    # the manuscript, and the world_state ledger must NOT be.
    ok = True
    for n, cid in enumerate(order, start=1):
        c = doc["chapters"]["cards"][cid]
        head = f"# Chapter {n}: {c['title']}"
        if head not in book:
            print(f"  !! missing heading: {head}")
            ok = False
        # A stable opening fragment of the chapter's final text should appear.
        frag = (c["text"] or "").strip()[:40]
        if frag and frag not in book:
            print(f"  !! chapter {cid} final text fragment absent: {frag!r}")
            ok = False
        if c.get("world_state") and c["world_state"][:40] in book:
            print(f"  !! chapter {cid} world_state leaked into the book")
            ok = False
    print("\n--- BOOK (first 1800 chars) ---\n")
    print(book[:1800])
    print("\n=== WITNESS", "PASS" if ok and book else "FAIL", "===")


if __name__ == "__main__":
    asyncio.run(main())
