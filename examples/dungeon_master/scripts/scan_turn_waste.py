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
``direction`` side-channel (``beats_satisfied`` / ``scene_complete``) per turn and
prints a per-book report. It mutates nothing.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

CHAPTER_TURN_CAP = 16
# A short denouement after the last beat lands is normal; only a longer stall is
# flagged as waste.
STALL_THRESHOLD = 3


def _direction(turn: dict) -> dict:
    return turn.get("direction") or {}


def _satisfied_count(turn: dict) -> int:
    return len(
        {
            s.strip()
            for s in (_direction(turn).get("beats_satisfied") or [])
            if isinstance(s, str) and s.strip()
        }
    )


def _last_progress_turn(turns: list[dict]) -> int:
    """1-based index of the last turn whose ``beats_satisfied`` count grew."""
    last = 0
    high = 0
    for i, turn in enumerate(turns, 1):
        count = _satisfied_count(turn)
        if count > high:
            high = count
            last = i
    return last


def _scene_complete_turn(turns: list[dict]) -> int | None:
    for i, turn in enumerate(turns, 1):
        if _direction(turn).get("scene_complete"):
            return i
    return None


grand_waste = 0
grand_chapters = 0
for path in sys.argv[1:]:
    try:
        doc = json.loads(Path(path).read_text())
    except (OSError, ValueError) as exc:
        print(f"{path}: SKIP ({exc})")
        continue
    chapters = doc.get("chapters") or {}
    order = list(chapters.get("order") or [])
    cards = chapters.get("cards") or {}
    book_waste = 0
    lines: list[str] = []
    for cid in order:
        card = cards.get(cid) or {}
        beats = card.get("beats") or []
        turns = card.get("turns") or []
        played = len(turns)
        grand_chapters += 1
        complete_turn = _scene_complete_turn(turns)
        capped = played >= CHAPTER_TURN_CAP and complete_turn is None
        # Waste counts only when the chapter rode the hard cap (never resolved)
        # AND beat progress stalled longer than the denouement threshold.
        waste = 0
        if capped:
            progress_turn = _last_progress_turn(turns)
            stall = played - progress_turn
            if stall > STALL_THRESHOLD:
                waste = stall
        if waste > 0:
            progress_turn = _last_progress_turn(turns)
            lines.append(
                f"    CH{cid}: beat progress stalled @t{progress_turn} "
                f"({_satisfied_count(turns[progress_turn - 1])}/{len(beats)} beats), "
                f"force-closed @t{played} (cap) -> {waste} no-progress turn(s)"
            )
            book_waste += waste
    grand_waste += book_waste
    flag = f"{book_waste} WASTED TURN(S)" if book_waste else "OK"
    print(f"{path}  [{len(order)} ch]  {flag}")
    for line in lines:
        print(line)

print(f"\nGRAND TOTAL WASTED TURNS: {grand_waste} over {grand_chapters} chapters")
