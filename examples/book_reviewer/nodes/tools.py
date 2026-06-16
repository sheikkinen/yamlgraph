"""Pure tools + graph-node wrappers for book_reviewer.

The *pure* functions (``parse_manuscript``, ``lint_manuscript``,
``make_chapter_pairs``, ``compute_review``) take/return typed values and contain no
I/O — they are unit-tested directly. The ``*_node`` wrappers adapt them to the
YAMLGraph python-node contract (take ``state: dict``, return a state-update dict),
and own the only side effects: reading the manuscript file and writing ``review.md``.

No DM package import and no DM JSON: the reviewer reads a Markdown manuscript
only (FR-497 J1/J3).
"""

from __future__ import annotations

import logging
import re
import statistics
from pathlib import Path

from examples.book_reviewer.models import (
    BookReview,
    ChapterReview,
    ChapterSection,
    ContinuityReport,
    CriterionScore,
    LintIssue,
    LintReport,
    PairContinuity,
    ParsedBook,
    SynopsisBeats,
    SynopsisDelivery,
)

logger = logging.getLogger(__name__)

# Default scaffolding labels that must not leak into a DM manuscript (FR-496).
# Configurable so the check generalises beyond dungeon_master.
DEFAULT_LEAK_LABELS = (
    "SUMMARY",
    "ROLE",
    "ORIGIN",
    "APPEARANCE",
    "PERSONALITY",
    "DRIVE",
    "BOND",
    "FLAW",
)

_H1 = re.compile(r"^#\s+(.*)$")
_CHAPTER_HEADING = re.compile(
    r"^#\s+Chapter\s+(\d+)\s*[:.\-—–]?\s*(.*)$", re.IGNORECASE
)
# A chapter title that *still* starts with "Chapter N …" => doubled heading (FR-495).
_DOUBLED_TITLE = re.compile(r"^\s*Chapter\s+\d+\b", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Stage 0 — parse (pure)
# ---------------------------------------------------------------------------


def parse_manuscript(markdown: str) -> ParsedBook:
    """Recover the book structure from a book-shaped Markdown manuscript.

    Walks the H1 sections: a leading ``> `` blockquote becomes the tagline, the
    ``# Synopsis`` body and ``# Cast`` bullets are captured, and each
    ``# Chapter N: …`` section's prose is collected up to the next H1. Pure text;
    no DM import, no JSON.
    """
    lines = markdown.splitlines()

    tagline = ""
    synopsis_lines: list[str] = []
    cast: list[str] = []
    chapters: list[ChapterSection] = []

    # Leading blockquote (tagline) — first non-empty line(s) starting with "> ".
    for line in lines:
        if not line.strip():
            continue
        if line.lstrip().startswith(">"):
            tagline = line.lstrip()[1:].strip()
        break

    # Section walk.
    current: str | None = None  # "synopsis" | "cast" | "chapter"
    chapter_number = 0
    chapter_title = ""
    chapter_body: list[str] = []

    def _flush_chapter() -> None:
        nonlocal chapter_body
        if current == "chapter":
            chapters.append(
                ChapterSection(
                    number=chapter_number,
                    title=chapter_title,
                    body="\n".join(chapter_body).strip(),
                )
            )
        chapter_body = []

    for line in lines:
        h1 = _H1.match(line)
        if h1:
            heading = h1.group(1).strip()
            chap = _CHAPTER_HEADING.match(line)
            if chap:
                _flush_chapter()
                current = "chapter"
                chapter_number = int(chap.group(1))
                chapter_title = chap.group(2).strip()
                continue
            # Non-chapter H1: close any open chapter, switch section.
            _flush_chapter()
            low = heading.lower()
            if low.startswith("synopsis"):
                current = "synopsis"
            elif low.startswith("cast"):
                current = "cast"
            else:
                current = None
            continue

        if current == "synopsis":
            synopsis_lines.append(line)
        elif current == "cast":
            stripped = line.strip()
            if stripped.startswith("- ") or stripped.startswith("* "):
                cast.append(stripped[2:].strip())
        elif current == "chapter":
            chapter_body.append(line)

    _flush_chapter()

    return ParsedBook(
        tagline=tagline,
        synopsis="\n".join(synopsis_lines).strip(),
        cast=cast,
        chapters=chapters,
    )


# ---------------------------------------------------------------------------
# Stage 1 — lint (pure)
# ---------------------------------------------------------------------------


def lint_manuscript(
    parsed: ParsedBook, labels: tuple[str, ...] | list[str] | None = None
) -> LintReport:
    """Deterministic pre-pass over the parsed structure (no LLM, no I/O).

    Re-asserts the FR-494/495/496 render invariants from the reader's side.
    """
    label_set = tuple(labels) if labels is not None else DEFAULT_LEAK_LABELS
    leak_re = re.compile(
        r"\b(" + "|".join(re.escape(label) for label in label_set) + r")\s*:",
    )
    issues: list[LintIssue] = []

    # leaked-label — scaffolding labels in cast or prose (FR-496).
    for entry in parsed.cast:
        if leak_re.search(entry):
            issues.append(LintIssue(code="leaked-label", detail=entry))
    for chapter in parsed.chapters:
        match = leak_re.search(chapter.body)
        if match:
            issues.append(
                LintIssue(
                    code="leaked-label",
                    detail=f"Chapter {chapter.number}: '{match.group(0)}'",
                )
            )

    # doubled-heading — a chapter title still beginning "Chapter N …" (FR-495).
    for chapter in parsed.chapters:
        if _DOUBLED_TITLE.match(chapter.title):
            issues.append(
                LintIssue(
                    code="doubled-heading",
                    detail=f"Chapter {chapter.number}: '{chapter.title}'",
                )
            )

    # heading-numbering — chapter numbers must be 1..k, monotonic (FR-494).
    numbers = [c.number for c in parsed.chapters]
    if numbers and numbers != list(range(1, len(numbers) + 1)):
        issues.append(LintIssue(code="heading-numbering", detail=f"numbers={numbers}"))

    # missing-frontmatter — tagline + synopsis (+ cast if any chapters) present.
    if parsed.chapters:
        if not parsed.tagline.strip():
            issues.append(LintIssue(code="missing-frontmatter", detail="empty tagline"))
        if not parsed.synopsis.strip():
            issues.append(
                LintIssue(code="missing-frontmatter", detail="empty synopsis")
            )

    # empty-chapter-body — every chapter must have prose.
    for chapter in parsed.chapters:
        if not chapter.body.strip():
            issues.append(
                LintIssue(code="empty-chapter-body", detail=f"Chapter {chapter.number}")
            )

    return LintReport(ok=not issues, issues=issues)


# ---------------------------------------------------------------------------
# Stage 3 helper — adjacent self-contained pairs (pure)
# ---------------------------------------------------------------------------


def make_chapter_pairs(parsed: ParsedBook) -> list[dict]:
    """Build self-contained adjacent-seam items for the continuity map (K2).

    Each item carries *both* chapter bodies so the map sub-node — which sees only
    its injected item plus parent state — has everything it needs.
    """
    pairs: list[dict] = []
    chapters = parsed.chapters
    for left, right in zip(chapters, chapters[1:], strict=False):
        pairs.append(
            {
                "between": [left.number, right.number],
                "body_n": left.body,
                "body_n1": right.body,
            }
        )
    return pairs


# ---------------------------------------------------------------------------
# Stage 5 — deterministic reduce (pure, K3: every score is COMPUTED)
# ---------------------------------------------------------------------------

CRITERIA_ORDER = ("coherence", "engagement", "prose", "character")


def _book_criteria(reviews: list[ChapterReview]) -> list[CriterionScore]:
    """Mean each criterion across chapters; justification flags the weakest chapter."""
    out: list[CriterionScore] = []
    for name in CRITERIA_ORDER:
        scored: list[tuple[int, int]] = []  # (chapter_number, score)
        for review in reviews:
            for crit in review.criteria:
                if crit.name == name:
                    scored.append((review.number, crit.score))
        if not scored:
            continue
        scores = [s for _, s in scored]
        mean = round(statistics.fmean(scores))
        worst_ch, worst = min(scored, key=lambda t: t[1])
        out.append(
            CriterionScore(
                name=name,
                score=mean,
                justification=(
                    f"mean {statistics.fmean(scores):.2f} over {len(scores)} "
                    f"chapters; weakest is chapter {worst_ch} ({worst})"
                ),
            )
        )
    return out


def _continuity_score(break_count: int) -> int:
    """0 breaks -> 5; each break costs a point, floored at 1."""
    return max(1, 5 - break_count)


def _synopsis_score(promised: int, undelivered: int) -> int:
    """covered / promised on a 1–5 scale; an empty synopsis is neutral (3)."""
    if promised <= 0:
        return 3
    covered = max(0, promised - undelivered)
    return max(1, min(5, round(5 * covered / promised)))


def compute_review(
    chapter_reviews: list[ChapterReview],
    pair_continuities: list[PairContinuity],
    synopsis_beats: SynopsisBeats,
) -> BookReview:
    """Assemble the book-level review with **computed** scores (no LLM number).

    ``verdict`` is left empty here; an LLM fills it later from these findings only.
    """
    reviews = sorted(chapter_reviews, key=lambda r: r.number)

    breaks: list[str] = []
    for pair in pair_continuities:
        breaks.extend(pair.breaks)
    continuity = ContinuityReport(score=_continuity_score(len(breaks)), breaks=breaks)

    delivery = SynopsisDelivery(
        score=_synopsis_score(
            len(synopsis_beats.promised), len(synopsis_beats.undelivered)
        ),
        promised=synopsis_beats.promised,
        undelivered=synopsis_beats.undelivered,
    )

    criteria = _book_criteria(reviews)
    components = [c.score for c in criteria] + [continuity.score, delivery.score]
    overall = round(statistics.fmean(components)) if components else 3

    return BookReview(
        overall=max(1, min(5, overall)),
        verdict="",
        criteria=criteria,
        continuity=continuity,
        synopsis_delivery=delivery,
        chapters=reviews,
    )


def findings_summary(review: BookReview) -> str:
    """Compact, manuscript-free digest for the verdict prompt (K4)."""
    lines = [f"overall (computed): {review.overall}/5"]
    for crit in review.criteria:
        lines.append(f"- {crit.name}: {crit.score}/5")
    lines.append(
        f"- continuity: {review.continuity.score}/5 "
        f"({len(review.continuity.breaks)} breaks)"
    )
    lines.append(
        f"- synopsis delivery: {review.synopsis_delivery.score}/5 "
        f"({len(review.synopsis_delivery.undelivered)} undelivered beats)"
    )
    if review.synopsis_delivery.undelivered:
        lines.append(
            "undelivered beats: " + "; ".join(review.synopsis_delivery.undelivered)
        )
    return "\n".join(lines)


def render_review_md(review: BookReview) -> str:
    """Human-readable review.md sidecar."""
    out = ["# Book Review", "", f"**Overall:** {review.overall}/5", ""]
    if review.verdict:
        out += [f"> {review.verdict}", ""]
    out += ["## Criteria", ""]
    for crit in review.criteria:
        out.append(f"- **{crit.name}** — {crit.score}/5: {crit.justification}")
    out += ["", "## Continuity", "", f"Score: {review.continuity.score}/5"]
    for brk in review.continuity.breaks:
        out.append(f"- {brk}")
    out += [
        "",
        "## Synopsis delivery",
        "",
        f"Score: {review.synopsis_delivery.score}/5",
    ]
    for beat in review.synopsis_delivery.undelivered:
        out.append(f"- undelivered: {beat}")
    out += ["", "## Per-chapter", ""]
    for chap in review.chapters:
        out.append(f"### Chapter {chap.number}")
        if chap.summary:
            out.append(chap.summary)
        for crit in chap.criteria:
            out.append(f"- {crit.name}: {crit.score}/5")
        for issue in chap.issues:
            out.append(f"- issue: {issue}")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


# ---------------------------------------------------------------------------
# Graph-node wrappers (state dict in, state-update dict out)
# ---------------------------------------------------------------------------


def load_manuscript(state: dict) -> dict:
    """Read the manuscript file (or ``story.md`` inside a directory)."""
    raw = state.get("manuscript_path", "")
    path = Path(raw)
    if path.is_dir():
        path = path / "story.md"
    if not path.is_file():
        raise FileNotFoundError(f"manuscript not found: {raw}")
    return {
        "manuscript": path.read_text(encoding="utf-8"),
        "manuscript_path": str(path),
    }


def parse_node(state: dict) -> dict:
    """Parse the manuscript; raise on zero chapters (J5 — no empty review)."""
    parsed = parse_manuscript(state.get("manuscript", ""))
    if not parsed.chapters:
        raise ValueError(
            "manuscript has no parseable chapters — refusing to emit an empty review"
        )
    return {
        "parsed": parsed.model_dump(),
        "chapters": [c.model_dump() for c in parsed.chapters],
        "synopsis": parsed.synopsis,
        "cast": parsed.cast,
    }


def lint_node(state: dict) -> dict:
    """Run the deterministic lint over the parsed structure."""
    parsed = ParsedBook.model_validate(state["parsed"])
    return {"lint": lint_manuscript(parsed).model_dump()}


def pairs_node(state: dict) -> dict:
    """Emit self-contained adjacent-seam items for the continuity map."""
    parsed = ParsedBook.model_validate(state["parsed"])
    return {"chapter_pairs": make_chapter_pairs(parsed)}


def _as_dict(value: object) -> dict:
    """Normalise an LLM-node output to a plain dict (FR-059 boundary).

    An ``llm`` node stores the executor's *dynamically built* schema instance —
    a class distinct from our own models despite sharing a name — so
    ``OurModel.model_validate(that_instance)`` would reject it. Collapse to a dict
    first; map nodes already emit dicts.
    """
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return {}


def compute_node(state: dict) -> dict:
    """Deterministic reduce: compute every numeric score (verdict left empty)."""
    reviews = [
        ChapterReview.model_validate(_as_dict(r))
        for r in state.get("chapter_reviews", [])
    ]
    pairs = [
        PairContinuity.model_validate(_as_dict(p))
        for p in state.get("pair_continuities", [])
    ]
    beats = SynopsisBeats.model_validate(_as_dict(state.get("synopsis_beats", {})))
    review = compute_review(reviews, pairs, beats)
    return {
        "review_draft": review.model_dump(),
        "findings": findings_summary(review),
    }


def finalize_node(state: dict) -> dict:
    """Attach the LLM verdict, build the final BookReview, write ``review.md``."""
    review = BookReview.model_validate(state["review_draft"])
    verdict = state.get("verdict")
    if hasattr(verdict, "verdict"):
        verdict = verdict.verdict
    elif isinstance(verdict, dict):
        verdict = verdict.get("verdict", "")
    review.verdict = (verdict or "").strip()

    out_path = Path(state["manuscript_path"]).with_name("review.md")
    out_path.write_text(render_review_md(review), encoding="utf-8")
    return {"review": review.model_dump(), "report_path": str(out_path)}
