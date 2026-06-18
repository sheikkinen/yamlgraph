"""FR-532 -- reviewer continuity-axis calibration harness.

A pure, deterministic study tool (no LLM). It answers the Red-Hat question "is the
pain real?" for the ``book_reviewer`` continuity 1/5: does that score measure a
defect a *reader* notices, or a sensitivity unique to an LLM that diffs across
seams?

The autonomous half (this script) extracts every continuity break the critic
recorded across a sample of books and joins it to a committed per-seam human
classification (``continuity-calibration-labels.yaml``). It then tabulates
critic-vs-human agreement and recomputes the continuity score counting only the
*reader-real* breaks, using the reviewer's own ``max(1, 5 - n)`` formula.

The human classification itself is a manual gate (FR-532 J2) -- this script never
synthesizes it; it only reads the committed labels.

Run::

    python -m examples.dungeon_master.scripts.calibrate_continuity_axis \
        --out outputs/dungeon-master \
        --labels examples/dungeon_master/docs/continuity-calibration-labels.yaml
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

__all__ = [
    "parse_continuity_breaks",
    "load_sample",
    "load_labels",
    "recalibrated_score",
    "tabulate",
    "render_markdown",
    "main",
]

_REAL = "real"
_MICRO = "micro"
_VALID_LABELS = (_REAL, _MICRO)


def recalibrated_score(real_break_count: int) -> int:
    """Mirror ``book_reviewer``'s deterministic formula: 0 breaks -> 5, each break
    costs a point, floored at 1. Applied to the reader-real subset only."""
    return max(1, 5 - real_break_count)


def parse_continuity_breaks(review_md: str) -> tuple[int, list[str]]:
    """Recover ``(critic_score, breaks)`` from a ``review.md`` body.

    Reads the ``## Continuity`` section: the ``Score: N/5`` line and every ``- ``
    bullet up to the next ``## `` heading.
    """
    score = 0
    breaks: list[str] = []
    in_section = False
    for line in review_md.splitlines():
        if line.startswith("## Continuity"):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if not in_section:
            continue
        stripped = line.strip()
        if stripped.startswith("Score:"):
            token = stripped.split(":", 1)[1].strip()
            score = int(token.split("/", 1)[0])
        elif stripped.startswith("- "):
            breaks.append(stripped[2:].strip())
    return score, breaks


def load_sample(out_dir: Path, books: list[str]) -> dict[str, dict]:
    """For each named book, parse its ``review.md`` continuity section."""
    sample: dict[str, dict] = {}
    for book in books:
        review = out_dir / book / "review.md"
        if not review.exists():
            raise FileNotFoundError(f"missing review for sampled book: {review}")
        score, breaks = parse_continuity_breaks(review.read_text(encoding="utf-8"))
        sample[book] = {"critic_score": score, "breaks": breaks}
    return sample


def load_labels(labels_path: Path) -> dict[str, dict]:
    """Load the committed per-seam human classification (the manual gate output)."""
    data = yaml.safe_load(labels_path.read_text(encoding="utf-8")) or {}
    books = data.get("books") or {}
    for book, entry in books.items():
        for i, brk in enumerate(entry.get("breaks") or [], start=1):
            label = brk.get("label")
            if label not in _VALID_LABELS:
                raise ValueError(
                    f"{book} break {i}: label {label!r} not in {_VALID_LABELS}"
                )
    return books


def tabulate(sample: dict[str, dict], labels: dict[str, dict]) -> list[dict]:
    """Join the extracted breaks to the human labels and compute per-book rows.

    Raises if the label count for a book does not match the number of breaks the
    critic recorded -- the calibration must classify every break, no more, no less.
    """
    rows: list[dict] = []
    for book in sorted(sample):
        critic = sample[book]
        label_entry = labels.get(book)
        if label_entry is None:
            raise ValueError(f"no human labels for sampled book {book}")
        label_breaks = label_entry.get("breaks") or []
        n_critic = len(critic["breaks"])
        if len(label_breaks) != n_critic:
            raise ValueError(
                f"{book}: critic flagged {n_critic} breaks but "
                f"{len(label_breaks)} labels were supplied -- re-align the labels"
            )
        real = sum(1 for b in label_breaks if b["label"] == _REAL)
        micro = n_critic - real
        rows.append(
            {
                "book": book,
                "critic_breaks": n_critic,
                "real": real,
                "micro": micro,
                "critic_score": critic["critic_score"],
                "recalibrated_score": recalibrated_score(real),
            }
        )
    return rows


def render_markdown(rows: list[dict]) -> str:
    """Render the agreement tabulation and the headline divergence statistic."""
    total_breaks = sum(r["critic_breaks"] for r in rows)
    total_real = sum(r["real"] for r in rows)
    total_micro = sum(r["micro"] for r in rows)
    micro_pct = (100.0 * total_micro / total_breaks) if total_breaks else 0.0

    out: list[str] = []
    out.append("# FR-532 -- Reviewer continuity-axis calibration")
    out.append("")
    out.append(
        "Critic-vs-human agreement over the sampled continuity breaks. "
        "`recalibrated` counts only reader-real breaks via `max(1, 5 - n)`."
    )
    out.append("")
    out.append("| Book | critic breaks | real | micro | critic score | recalibrated |")
    out.append("| --- | --- | --- | --- | --- | --- |")
    for r in rows:
        out.append(
            f"| {r['book']} | {r['critic_breaks']} | {r['real']} | {r['micro']} "
            f"| {r['critic_score']}/5 | {r['recalibrated_score']}/5 |"
        )
    out.append(
        f"| **total** | **{total_breaks}** | **{total_real}** | **{total_micro}** "
        f"| -- | -- |"
    )
    out.append("")
    out.append(
        f"**Divergence: {total_micro}/{total_breaks} "
        f"({micro_pct:.0f}%) of critic-flagged breaks are physical micro-state** "
        "a reader glides past; the reader-real residual is entirely "
        "lifecycle / plot / relationship -- lanes the upstream march already "
        "hardened (FR-507 / FR-526 / FR-528), none addressable by a coarse "
        "positional pin."
    )
    out.append("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="FR-532 continuity-axis calibration")
    parser.add_argument(
        "--out",
        default="outputs/dungeon-master",
        help="corpus output directory (default: outputs/dungeon-master)",
    )
    parser.add_argument(
        "--labels",
        default="examples/dungeon_master/docs/continuity-calibration-labels.yaml",
        help="committed per-seam human classification YAML",
    )
    args = parser.parse_args(argv)

    labels = load_labels(Path(args.labels))
    sample = load_sample(Path(args.out), sorted(labels))
    rows = tabulate(sample, labels)
    print(render_markdown(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
