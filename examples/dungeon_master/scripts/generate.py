"""Headless stand-alone story generator for DM v2 (FR-494 Part 2).

The one place that sequences a *complete* story end to end without the HTTP UI:
synopsis → derive cast → accept each character → play every chapter to its
director-judged ``scene_complete`` → reach the Book gate. Extracted from the live
witness so the drive loop is reusable and the finished story is an artifact, not
console noise.

It drives the **same adapter methods the routes call** (``weave`` / ``accept`` /
``navigate``) — it adds no doc-shape coupling of its own. Its stop condition is
the public :func:`tree.all_chapters_played` gate (FR-494 J5), not a hand-rolled
per-turn ``scene_complete`` walk. When the Book gate does not open within
``turn_cap`` it **raises** rather than returning a half-played doc a caller might
mistake for finished.

The CLI writes **both** serializations to ``--out``: the canonical machine
``story.json`` (via the adapter) and the reader ``story.md``
(:func:`render.render_story_markdown`, derived on demand — never stored in the
JSON, mirroring FR-492's no-stored-book rule, J6). Run as a direct script path —
``examples/dungeon_master`` is not a package (J4):

    PYTHONPATH="$PWD" python examples/dungeon_master/scripts/generate.py \\
        --premise "A lone courier crosses a frozen river…" \\
        --out outputs/dungeon-master/courier --turn-cap 24
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from examples.dungeon_master.api import render, story_doc, tree
from examples.dungeon_master.api import session as dm_session

DEFAULT_TURN_CAP = 24  # safety bound on total turn-accepts across all chapters


async def generate_story(
    premise: str,
    *,
    story_root: Path,
    session_id: str = "story",
    turn_cap: int = DEFAULT_TURN_CAP,
) -> dict:
    """Drive a ``DMSession`` to a complete book and return the finished doc.

    Synopsis → accept cast → play every chapter to ``scene_complete`` → Book gate.
    Persists ``story.json`` via the adapter (the single source of truth). Raises
    ``RuntimeError`` if the Book gate does not open within ``turn_cap`` — no
    half-finished story masquerading as done (J5).
    """
    dm_session.STORY_ROOT = Path(story_root)
    dm_session._reset_caches()
    story_dir = Path(story_root) / session_id
    session = dm_session.DMSession(session_id)

    # 1. Synopsis: the premise is the first-stage instruction; accept derives cast.
    await session.weave(text="", prompt=premise)
    view = await session.accept()

    # 2. Cast: accept each derived character card in turn. Accepting the last one
    #    derives the chapter outline and lands on the Chapters overview.
    while view.stage.startswith("char:"):
        view = await session.accept()

    doc = story_doc.read(story_dir)
    order = doc.get("chapters", {}).get("order", [])
    if not order:
        raise RuntimeError("no chapters were derived from the synopsis")

    # 3. Play: open the first chapter and keep accepting turns. The adapter closes
    #    each chapter when its director reports the scene complete and advances to
    #    the next chapter's first turn; we stop on the public Book gate.
    await session.navigate(f"chapter:{order[0]}")
    accepts = 0
    while accepts < turn_cap:
        doc = story_doc.read(story_dir)
        if tree.all_chapters_played(doc):
            break
        if not doc.get("stage", "").startswith("turn:"):
            raise RuntimeError(
                f"play loop left the turn stages unexpectedly at {doc.get('stage')!r}"
            )
        await session.accept()
        accepts += 1

    doc = story_doc.read(story_dir)
    if not tree.all_chapters_played(doc):
        raise RuntimeError(
            f"book gate did not open within turn_cap={turn_cap}; "
            f"chapters played: "
            f"{[(c, doc['chapters']['cards'][c].get('reviewed')) for c in order]}"
        )
    return doc


def _write_outputs(doc: dict, out_dir: Path) -> tuple[Path, Path]:
    """Write the machine ``story.json`` and the reader ``story.md`` to ``out_dir``."""
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = story_doc.doc_path(out_dir)
    story_doc.write(out_dir, doc)
    md_path = out_dir / "story.md"
    md_path.write_text(render.render_story_markdown(doc), encoding="utf-8")
    return json_path, md_path


async def _amain(args: argparse.Namespace) -> None:
    from dotenv import load_dotenv

    load_dotenv()  # provider creds before any LLM call (kept inside main; J4)
    out_dir = Path(args.out)
    doc = await generate_story(
        args.premise,
        story_root=out_dir,
        session_id=args.session_id,
        turn_cap=args.turn_cap,
    )
    json_path, md_path = _write_outputs(doc, out_dir)
    print(f"✓ story.json → {json_path}")
    print(f"✓ story.md   → {md_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a complete DM v2 story headlessly (json + markdown)."
    )
    parser.add_argument("--premise", required=True, help="The opening premise/tagline.")
    parser.add_argument(
        "--out", required=True, help="Output dir for story.json + story.md."
    )
    parser.add_argument("--session-id", default="story", help="Session id (subdir).")
    parser.add_argument(
        "--turn-cap",
        type=int,
        default=DEFAULT_TURN_CAP,
        help="Max total turn-accepts before the book gate must open.",
    )
    asyncio.run(_amain(parser.parse_args()))


if __name__ == "__main__":
    main()
