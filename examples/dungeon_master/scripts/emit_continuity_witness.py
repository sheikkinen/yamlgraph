"""FR-530 Stage 1 -- post-generation continuity witness (visibility, not a gate).

The independent ``book_reviewer`` is the only component that reads *across* seams and
computes a pairwise chapter-seam continuity score. Today it runs after generation as a
separate example, so its verdict never travels with the run that produced the book. This
witness reads the just-written ``review.md`` and emits the continuity score in a small
machine-readable JSON alongside the book artifacts, so every run carries its own score
and FR-531's deterministic report can later join it.

**Posture (FR-522):** visibility only. A low score NEVER fails the run or CI -- the caller
wires this as a non-blocking step. An LLM continuity score is not a deterministic
guarantee, so it is reported, never gated.

The per-seam corrective re-roll (Stage 2) is explicitly OUT of scope (FR-530 J2): it is
gated behind this Stage 1 proving useful and FR-532's calibration of the axis.

Run::

    python -m examples.dungeon_master.scripts.emit_continuity_witness --out <book-dir>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from examples.dungeon_master.scripts.calibrate_continuity_axis import (
    parse_continuity_breaks,
)

__all__ = ["build_witness", "write_witness", "main"]

WITNESS_FILENAME = "continuity_witness.json"


def build_witness(book: str, review_md: str) -> dict:
    """Project the reviewer's continuity axis into a small machine-readable record."""
    score, breaks = parse_continuity_breaks(review_md)
    return {
        "book": book,
        "continuity_score": score,
        "break_count": len(breaks),
        "posture": "visibility-not-gate",
    }


def write_witness(out_dir: Path) -> dict | None:
    """Read ``<out_dir>/review.md`` and write ``<out_dir>/continuity_witness.json``.

    Returns the witness dict, or ``None`` if no review exists yet (the caller treats a
    missing review as a skipped, non-fatal step).
    """
    review = out_dir / "review.md"
    if not review.exists():
        return None
    witness = build_witness(out_dir.name, review.read_text(encoding="utf-8"))
    (out_dir / WITNESS_FILENAME).write_text(
        json.dumps(witness, indent=2) + "\n", encoding="utf-8"
    )
    return witness


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="FR-530 Stage 1 post-generation continuity witness"
    )
    parser.add_argument("--out", required=True, help="book output directory")
    args = parser.parse_args(argv)

    witness = write_witness(Path(args.out))
    if witness is None:
        print("continuity witness: no review.md found (skipped, non-blocking)")
        return 0
    print(
        f"continuity witness: {witness['book']} "
        f"continuity={witness['continuity_score']}/5 "
        f"({witness['break_count']} breaks) [visibility, not a gate]"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
