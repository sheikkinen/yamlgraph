"""Scan DM story.json artifacts for unbridged lethal seams (FR-523 witness).

Runs ``gap_detectors.seam_precondition_gap`` over every chapter of each story
doc passed on argv and prints a per-book gap report. Heuristic instrument, not a
gate (FR-522 posture): a gap is corroborating evidence of the state-blind-outliner
seam-teleport, to be read alongside the prose, not a pass/fail.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from examples.dungeon_master.api import gap_detectors as wm

grand = 0
for path in sys.argv[1:]:
    try:
        doc = json.loads(Path(path).read_text())
    except (OSError, ValueError) as exc:
        print(f"{path}: SKIP ({exc})")
        continue
    order = list((doc.get("chapters") or {}).get("order") or [])
    book_gaps = 0
    lines: list[str] = []
    for cid in order:
        r = wm.seam_precondition_gap(doc, cid)
        for g in r["gaps"]:
            book_gaps += 1
            lines.append(
                f"    CH{cid}: {g['actor']} | carried={g['carried_location']!r} "
                f"| beat={g['exit_beat']!r}"
            )
    grand += book_gaps
    tag = "OK" if book_gaps == 0 else f"{book_gaps} GAP(S)"
    print(f"{path}  [{len(order)} ch]  {tag}")
    for line in lines:
        print(line)
print(f"\nGRAND TOTAL GAPS: {grand}")
