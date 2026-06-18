"""Scan DM story.json artifacts for phantom-promise beats (FR-524 Judgement witness).

Runs ``witness_metrics.beat_coverage_gap`` over every chapter of each story doc
passed on argv and prints a per-book report. A phantom-promise beat is one a
chapter's OWN committed ``world_state`` contradicts: the ledger records an actor
terminal (dead/missing/lost) yet a beat of the same chapter promises their return
or presence — the residue of an un-playable reversal force-closed by the FR-501
turn cap. Heuristic instrument, not a gate (FR-522 posture).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from examples.dungeon_master.api import witness_metrics as wm

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
        r = wm.beat_coverage_gap(doc, cid)
        for g in r["gaps"]:
            book_gaps += 1
            lines.append(
                f"    CH{cid}: {g['actor']} | ledger={g['ledger_status']!r} | "
                f"beat[{g['beat_index']}]={g['beat']!r}"
            )
    grand += book_gaps
    flag = f"{book_gaps} PHANTOM(S)" if book_gaps else "OK"
    print(f"{path}  [{len(order)} ch]  {flag}")
    for line in lines:
        print(line)

print(f"\nGRAND TOTAL PHANTOM-PROMISE BEATS: {grand}")
