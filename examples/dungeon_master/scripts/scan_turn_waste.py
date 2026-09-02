"""Scan DM story.json artifacts for turn-cap waste (FR-527 instrument).

A chapter's only natural exit is its director emitting ``scene_complete``; absent
that, the FR-501 ``CHAPTER_TURN_CAP`` force-closes it. This instrument measures the
*no-progress tail*: the run of turns at the end of a force-capped chapter during
which the director's ``beats_satisfied`` set never grew -- the planner had already
covered every beat it would ever cover, yet kept the chapter open, replaying the
same material (observed live: 10025-BC CH8 reached 4 satisfied beats at turn 6,
then froze that set through turn 16, replaying the same confrontation ~10 times,
collapsing engagement to 1/5).

Why "no-progress tail" rather than "all beats satisfied": the final, closing beat
(the chapter's resolution) is frequently never reported satisfied -- it *is* the
scene end -- so a 100%-coverage test under-counts. The honest signal is that beat
progress *stalled*: ``beats_satisfied`` stopped growing well before the cap.

Heuristic instrument, not a gate (FR-522 posture): it reads the committed
``direction`` side-channel (``beats_satisfied`` / ``scene_complete``) per chapter
and prints a per-book report. It mutates nothing. The per-book measurement is
:func:`witness_metrics.book_turn_waste`, shared with the FR-531 unified report so
both reuse one implementation (no duplicated measurement).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from examples.dungeon_master.api.witness_metrics import (
    CHAPTER_TURN_CAP,
    TURN_WASTE_STALL_THRESHOLD,
    _last_progress_turn,
    _scene_complete_turn,
    _turn_satisfied_count,
    book_turn_waste,
)

__all__ = [
    "CHAPTER_TURN_CAP",
    "TURN_WASTE_STALL_THRESHOLD",
    "book_turn_waste",
]


def _main(paths: list[str]) -> None:
    grand_waste = 0
    grand_chapters = 0
    for path in paths:
        try:
            doc = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(f"{path}: SKIP ({exc})")
            continue
        chapters = doc.get("chapters") or {}
        order = list(chapters.get("order") or [])
        cards = chapters.get("cards") or {}
        lines: list[str] = []
        for cid in order:
            card = cards.get(cid) or {}
            beats = card.get("beats") or []
            turns = card.get("turns") or []
            played = len(turns)
            grand_chapters += 1
            capped = played >= CHAPTER_TURN_CAP and _scene_complete_turn(turns) is None
            if not capped:
                continue
            progress_turn = _last_progress_turn(turns)
            stall = played - progress_turn
            if stall > TURN_WASTE_STALL_THRESHOLD:
                lines.append(
                    f"    CH{cid}: beat progress stalled @t{progress_turn} "
                    f"({_turn_satisfied_count(turns[progress_turn - 1])}/{len(beats)} "
                    f"beats), force-closed @t{played} (cap) -> {stall} "
                    "no-progress turn(s)"
                )
        book_waste = book_turn_waste(doc)["wasted_turns"]
        grand_waste += book_waste
        flag = f"{book_waste} WASTED TURN(S)" if book_waste else "OK"
        print(f"{path}  [{len(order)} ch]  {flag}")
        for line in lines:
            print(line)

    print(f"\nGRAND TOTAL WASTED TURNS: {grand_waste} over {grand_chapters} chapters")


if __name__ == "__main__":
    _main(sys.argv[1:])
