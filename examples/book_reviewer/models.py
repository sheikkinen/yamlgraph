"""Pydantic models for the book_reviewer example.

Two tiers, per FR-497 Judgment K2/K3:

- **Parse / lint** structures recovered deterministically from the manuscript.
- **LLM-stage outputs** (one item at a time): ``ChapterReview`` (per chapter),
  ``PairContinuity`` (per adjacent seam), ``SynopsisBeats`` (the synopsis alone).
- **Reduced book-level** report: ``ContinuityReport``, ``SynopsisDelivery``, and
  the final ``BookReview`` — whose numeric scores are *computed* by a deterministic
  reduce node, never invented by an LLM (Commandment 6 / K3).
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Stage 0 — parsed structure
# ---------------------------------------------------------------------------


class ChapterSection(BaseModel):
    """One chapter recovered from the manuscript."""

    number: int = Field(description="Heading ordinal, e.g. '# Chapter 3: …' -> 3")
    title: str = Field(default="", description="Cleaned heading title (may be empty)")
    body: str = Field(default="", description="Chapter prose, up to the next H1")


class ParsedBook(BaseModel):
    """The whole manuscript recovered into structure (no DM import, no JSON)."""

    tagline: str = Field(default="", description="Leading blockquote ('> …')")
    synopsis: str = Field(default="", description="The '# Synopsis' section body")
    cast: list[str] = Field(
        default_factory=list, description="'# Cast' bullet lines (name — gloss)"
    )
    chapters: list[ChapterSection] = Field(
        default_factory=list, description="Chapters in document order"
    )


# ---------------------------------------------------------------------------
# Stage 1 — lint
# ---------------------------------------------------------------------------


class LintIssue(BaseModel):
    """A single mechanical defect found in the manuscript."""

    code: str = Field(description="leaked-label | doubled-heading | …")
    detail: str = Field(description="The offending line or a short description")


class LintReport(BaseModel):
    """Result of the deterministic manuscript lint."""

    ok: bool = Field(description="True when no issues were found")
    issues: list[LintIssue] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Stage 2 — per-chapter review (LLM map item output)
# ---------------------------------------------------------------------------


class CriterionScore(BaseModel):
    """One craft criterion scored on a chapter."""

    name: str = Field(description="coherence | engagement | prose | character")
    score: int = Field(description="1–5", ge=1, le=5)
    justification: str = Field(default="")


class ChapterReview(BaseModel):
    """The LLM's review of a single chapter (one map item)."""

    number: int
    summary: str = Field(
        default="", description="One-sentence digest of what happens (no body leak)"
    )
    criteria: list[CriterionScore] = Field(default_factory=list)
    issues: list[str] = Field(
        default_factory=list, description="Specific, quotable problems in this chapter"
    )

    @field_validator("criteria", mode="before")
    @classmethod
    def _coerce_criteria(cls, v: object) -> list:
        """Coerce criteria to a list; if LLM returns a non-list, return empty.

        Accepts both dicts and CriterionScore objects; Pydantic will convert as needed.
        """
        if not isinstance(v, list):
            return []
        # Return the list as-is; Pydantic will convert items to CriterionScore
        return v

    @field_validator("issues", mode="before")
    @classmethod
    def _coerce_issues(cls, v: object) -> list[str]:
        return v if isinstance(v, list) else []


# ---------------------------------------------------------------------------
# Stage 3 — pairwise continuity
# ---------------------------------------------------------------------------


class PairContinuity(BaseModel):
    """The LLM's continuity check for one adjacent seam (one map item).

    ``breaks`` is a list of plain prose sentences: the boundary with the LLM is
    kept flat on purpose (FR-059 — trust no provider's key naming).
    """

    between: tuple[int, int] = Field(description="(N, N+1)")
    breaks: list[str] = Field(default_factory=list)

    @field_validator("breaks", mode="before")
    @classmethod
    def _coerce_breaks(cls, v: object) -> list[str]:
        """Coerce breaks to a list of strings; if LLM returns non-list, return empty."""
        if not isinstance(v, list):
            return []
        # Convert items to strings, skip empty ones
        return [str(item).strip() for item in v if item and str(item).strip()]


class ContinuityReport(BaseModel):
    """Book-level continuity, reduced from all PairContinuity items."""

    score: int = Field(description="1–5, computed from break count", ge=1, le=5)
    breaks: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Stage 4 — synopsis delivery
# ---------------------------------------------------------------------------


class SynopsisBeats(BaseModel):
    """The LLM decomposition of the synopsis + per-beat coverage verdict."""

    promised: list[str] = Field(
        default_factory=list, description="Discrete beats extracted from the synopsis"
    )
    undelivered: list[str] = Field(
        default_factory=list, description="Promised beats with no chapter coverage"
    )

    @field_validator("promised", "undelivered", mode="before")
    @classmethod
    def _coerce_beat_lists(cls, v: object) -> list[str]:
        """Coerce beat lists to strings; if non-list, return empty."""
        if not isinstance(v, list):
            return []
        return [str(item).strip() for item in v if item and str(item).strip()]


class SynopsisDelivery(BaseModel):
    """Book-level synopsis delivery (score computed = covered / promised)."""

    score: int = Field(description="1–5, computed from coverage", ge=1, le=5)
    promised: list[str] = Field(default_factory=list)
    undelivered: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Stage 5 — reduced book review
# ---------------------------------------------------------------------------


class BookReview(BaseModel):
    """The final, computed review of the manuscript."""

    overall: int = Field(description="1–5 holistic, computed", ge=1, le=5)
    verdict: str = Field(default="", description="One-line judgment (LLM prose)")
    criteria: list[CriterionScore] = Field(
        default_factory=list, description="Book-level, HANNA-derived"
    )
    continuity: ContinuityReport
    synopsis_delivery: SynopsisDelivery
    chapters: list[ChapterReview] = Field(
        default_factory=list, description="Per-chapter detail, retained"
    )
