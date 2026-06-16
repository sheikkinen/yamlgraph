"""Live vertex witness for FR-492/FR-494 — chapter-final text + deterministic Book.

Drives a real DMSession against vertex/gemini, end to end, proving the two
generative/assembly seams the deterministic tests can only mock:

  1. PER-CHAPTER FINAL CUT (generation at the chapter seam) — each chapter is
     played turn by turn until the director declares the scene complete; on close
     the chapter stores a beat-faithful final ``text`` composed over its whole
     played arc (turn_ops.invoke_final_cut), not concatenated recaps.
  2. DETERMINISTIC BOOK (assembly at the book seam) — compose_book_deterministic
     over the played chapters' final texts with NO whole-book LLM call. The book
     must be non-empty and contain each chapter's heading + its final prose; the
     full-story render (FR-494) frames it with the tagline + synopsis + cast.

The end-to-end drive loop now lives in ``generate.generate_story`` (FR-494 J5);
this witness is a thin caller that runs only the substance asserts. It keeps its
``sys.exit(1)``-on-FAIL honesty (FR-492 hardening) — it must be able to fail.

Run:  PYTHONPATH="$PWD" python examples/dungeon_master/scripts/witness_book_compose.py
"""

from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path

from dotenv import load_dotenv

from examples.dungeon_master.api import chapter_ops, render

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
    # generate.py is a sibling script (this dir is not a package): import by path,
    # inside main() so the module stays import-clean (no E402, no noqa).
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import generate

    tmp = Path(tempfile.mkdtemp(prefix="dm_witness_"))

    _hr("GENERATE — synopsis → cast → play every chapter → Book gate")
    doc = await generate.generate_story(PREMISE, story_root=tmp, turn_cap=TURN_CAP)
    order = doc["chapters"]["order"]
    print("synopsis:", doc["synopsis"]["text"][:200])
    print("chapters:", order)
    for cid in order:
        c = doc["chapters"]["cards"][cid]
        print(f"  chapter {cid}: {c['title']}")
        print(f"    world_state (carry): {c.get('world_state', '')[:160]}")
        print(f"    final text (first 200): {c.get('text', '')[:200]}")

    _hr("ASSERT — deterministic Book (no whole-book LLM call)")
    book = chapter_ops.compose_book_deterministic(doc)
    print("book length (chars):", len(book))
    ok = bool(book)
    for n, cid in enumerate(order, start=1):
        c = doc["chapters"]["cards"][cid]
        head = f"# Chapter {n}: {c['title']}"
        if head not in book:
            print(f"  !! missing heading: {head}")
            ok = False
        frag = (c["text"] or "").strip()[:40]
        if frag and frag not in book:
            print(f"  !! chapter {cid} final text fragment absent: {frag!r}")
            ok = False
        if c.get("world_state") and c["world_state"][:40] in book:
            print(f"  !! chapter {cid} world_state leaked into the book")
            ok = False

    _hr("ASSERT — full-story Markdown render (FR-494)")
    md = render.render_story_markdown(doc)
    print("markdown length (chars):", len(md))
    if not md.lstrip().startswith("> "):
        print("  !! markdown does not open with the tagline blockquote lead")
        ok = False
    for marker, label in (
        ("# Synopsis", "# Synopsis"),
        ("# Cast", "# Cast"),
        (book, "the Book body"),
    ):
        if marker not in md:
            print(f"  !! markdown missing: {label}")
            ok = False
    for cid in order:
        ws = doc["chapters"]["cards"][cid].get("world_state", "")
        if ws and ws[:40] in md:
            print(f"  !! chapter {cid} world_state leaked into the markdown")
            ok = False

    print("\n--- STORY.MD (first 1800 chars) ---\n")
    print(md[:1800])
    print("\n=== WITNESS", "PASS" if ok else "FAIL", "===")
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
