"""FR-522 witness CLI: replay one chapter and compare its continuity flags.

A thin command-line front for the controlled single-chapter replay. Loads a
finished story, measures the baseline actor-flag count for the named chapter, then
re-plays ONLY that chapter (inherited state held constant) and measures again, so
the only changed variable is the code under test. The driver and the measurement
live in the API layer (``chapter_replay`` / ``witness_metrics``); this file is
argparse + print, mirroring ``witness_continuity_metrics.py``.

Witness instrument, not a gate — efficacy is a live-LLM property; never wire this
into CI (FR-522 J6). Run as a direct script path (the example is not a package):

    PYTHONPATH="$PWD" .venv/bin/python \\
      examples/dungeon_master/scripts/replay_chapter_continuity.py \\
      --story outputs/dungeon-master/10022-BC/story.json \\
      --cid 3 --actor Arnulf \\
      --out outputs/dungeon-master/10022-BC/ch3-replay.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from dotenv import load_dotenv

from examples.dungeon_master.api import chapter_replay, witness_metrics


async def _amain(args: argparse.Namespace) -> None:
    load_dotenv()  # provider creds before any LLM call
    doc = json.loads(Path(args.story).read_text(encoding="utf-8"))

    baseline = witness_metrics.chapter_actor_flag_metrics(doc, args.cid, args.actor)
    replayed = await chapter_replay.replay_chapter(doc, args.cid)
    replay = witness_metrics.chapter_actor_flag_metrics(replayed, args.cid, args.actor)

    print(chapter_replay.render_report(args.cid, args.actor, baseline, replay))
    if chapter_replay.maybe_write_doc(replayed, args.out):
        print(f"replay doc -> {args.out}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--story", required=True, help="Path to story.json artifact")
    ap.add_argument("--cid", required=True, help="chapter id to replay (e.g. 3)")
    ap.add_argument("--actor", default="Arnulf", help="actor name to count flags for")
    ap.add_argument("--out", help="optional path to write the replayed doc")
    asyncio.run(_amain(ap.parse_args()))


if __name__ == "__main__":
    main()
