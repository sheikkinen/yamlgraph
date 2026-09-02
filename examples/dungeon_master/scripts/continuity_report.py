"""FR-531: one deterministic continuity report over a corpus, with per-premise trend.

The continuity program grew six hand-run witnesses (``scan_seam_gaps``,
``scan_beat_gaps``, ``scan_turn_waste``, ``replay_chapter_continuity``,
``witness_continuity_metrics``, ``cue_metrics``) and never showed a trend
(``continuity-issues.md`` 5.5): many detectors, no demonstrated movement
(``detection_without_enforcement``). This collapses the *deterministic* ones into a
single per-book table so "did this FR move the needle?" is one command.

The load-bearing constraint (FR-531 J2): the recorded corpus mixes premises (three
exact ``tagline`` strings -- em-dash floodmark, hyphen floodmark, and "Romance,
Adventure, Erotica" floodmark). A raw slot-ordered delta across them would compare
unlike books and manufacture a false trend, so the report GROUPS rows by exact
premise and computes each metric's delta only against the PRIOR book of the SAME
premise.

Pure shelf, no LLM (FR-531 J3): every metric is reused from the importable
deterministic witnesses (:mod:`witness_metrics`) -- no measurement is re-implemented
here. The non-deterministic reviewer score belongs to FR-530 and is joined later.

Run: ``python -m examples.dungeon_master.scripts.continuity_report \\
        --out outputs/dungeon-master/``
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from examples.dungeon_master.api import gap_detectors, witness_metrics

# The deterministic continuity metrics, in display order. Each is summed across the
# book from one importable witness -- the single shelf this report assembles.
_METRIC_KEYS: tuple[str, ...] = (
    "seam_gaps",
    "beat_gaps",
    "reversal_packs",
    "unplayable_beats",
    "wasted_turns",
    "completed_chapters",
)

_UNKNOWN_PREMISE = "(unknown premise)"


def premise_of(doc: dict) -> str:
    """The exact premise key a book is grouped by -- its ``tagline`` (FR-531 J2).

    Stripped of surrounding whitespace but otherwise verbatim: the em-dash vs hyphen
    vs "Romance, Adventure, Erotica" prefixes are *different* authored premises, so
    they must remain distinct groups (a normalized merge would re-introduce the
    cross-premise comparison J2 forbids).
    """
    tag = doc.get("tagline")
    if not isinstance(tag, str) or not tag.strip():
        return _UNKNOWN_PREMISE
    return tag.strip()


def book_metrics(doc: dict) -> dict:
    """Aggregate every deterministic continuity witness into one per-book row.

    Reuses the importable witnesses (no duplicated measurement, FR-531 J1):
    ``seam_precondition_gap`` and ``beat_coverage_gap`` per chapter, ``reversal_pack_gap``
    and ``unplayable_beat_gap`` per card, and ``book_turn_waste`` for the no-progress
    turn-cap tail. Returns ``{metric: int}`` for every key in :data:`_METRIC_KEYS`.
    """
    chapters = doc.get("chapters") or {}
    order = list(chapters.get("order") or [])
    cards = chapters.get("cards") or {}

    seam_gaps = sum(
        gap_detectors.seam_precondition_gap(doc, cid)["gap_count"] for cid in order
    )
    beat_gaps = sum(
        gap_detectors.beat_coverage_gap(doc, cid)["gap_count"] for cid in order
    )
    reversal_packs = sum(
        gap_detectors.reversal_pack_gap(cards.get(cid) or {})["gap_count"]
        for cid in order
    )
    unplayable_beats = sum(
        gap_detectors.unplayable_beat_gap(cards.get(cid) or {})["gap_count"]
        for cid in order
    )
    wasted_turns = witness_metrics.book_turn_waste(doc)["wasted_turns"]
    completed = witness_metrics.parse_story_progress_metrics(doc)[
        "completed_chapter_count"
    ]
    return {
        "seam_gaps": seam_gaps,
        "beat_gaps": beat_gaps,
        "reversal_packs": reversal_packs,
        "unplayable_beats": unplayable_beats,
        "wasted_turns": wasted_turns,
        "completed_chapters": completed,
    }


def _slot_of(story_path: Path) -> str:
    """The book slot id (``10025-BC``) from a ``.../<slot>/story.json`` path."""
    return story_path.parent.name


def collect(out_dir: str | Path) -> list[dict]:
    """Build one ``{slot, premise, metrics}`` row per ``*-BC/story.json`` under ``out_dir``.

    Sorted by slot id so the in-group order is chronological. Reads the filesystem;
    the measurement itself stays pure (:func:`book_metrics`).
    """
    root = Path(out_dir)
    rows: list[dict] = []
    for story_path in sorted(root.glob("*/story.json"), key=lambda p: p.parent.name):
        try:
            doc = json.loads(story_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:  # pragma: no cover - corpus hygiene
            print(f"{story_path}: SKIP ({exc})", file=sys.stderr)
            continue
        rows.append(
            {
                "slot": _slot_of(story_path),
                "premise": premise_of(doc),
                "metrics": book_metrics(doc),
            }
        )
    return rows


def _delta(curr: int, prev: int | None) -> str:
    """A signed delta string vs the prior SAME-premise book (blank for the first)."""
    if prev is None:
        return ""
    d = curr - prev
    if d == 0:
        return "0"
    return f"+{d}" if d > 0 else str(d)


def render_markdown(rows: list[dict]) -> str:
    """One markdown report: a section per premise, each a per-book metric table with
    a same-premise delta column (FR-531 J2 -- no cross-premise comparison).
    """
    by_premise: dict[str, list[dict]] = {}
    for row in rows:
        by_premise.setdefault(row["premise"], []).append(row)

    out: list[str] = ["# DM v2 Continuity Report (deterministic shelf)", ""]
    if not rows:
        out.append("_No books found._")
        return "\n".join(out)

    header = "| Book | " + " | ".join(f"{k} (Δ)" for k in _METRIC_KEYS) + " |"
    divider = "| --- | " + " | ".join("---" for _ in _METRIC_KEYS) + " |"

    for premise in sorted(by_premise):
        group = sorted(by_premise[premise], key=lambda r: r["slot"])
        out.append(f"## Premise: {premise}")
        out.append("")
        out.append(header)
        out.append(divider)
        prev: dict | None = None
        for row in group:
            cells = []
            for key in _METRIC_KEYS:
                val = row["metrics"].get(key, 0)
                prior = prev["metrics"].get(key) if prev else None
                delta = _delta(val, prior)
                cells.append(f"{val} ({delta})" if delta else f"{val}")
            out.append(f"| {row['slot']} | " + " | ".join(cells) + " |")
            prev = row
        out.append("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        required=True,
        help="corpus directory holding <slot>/story.json books",
    )
    args = parser.parse_args(argv)
    rows = collect(args.out)
    print(render_markdown(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
