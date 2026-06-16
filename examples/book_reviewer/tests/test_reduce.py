"""Reduce-stage tests for book_reviewer (pure, deterministic — K3)."""

from examples.book_reviewer.models import (
    ChapterReview,
    CriterionScore,
    PairContinuity,
    SynopsisBeats,
)
from examples.book_reviewer.nodes.tools import (
    compute_review,
    make_chapter_pairs,
    parse_manuscript,
)


def _chapter_review(number: int, score: int, summary: str = "s") -> ChapterReview:
    return ChapterReview(
        number=number,
        summary=summary,
        criteria=[
            CriterionScore(name=n, score=score, justification="j")
            for n in ("coherence", "engagement", "prose", "character")
        ],
        issues=[],
    )


class TestComputedScores:
    def test_criteria_are_means_over_chapters(self):
        reviews = [_chapter_review(1, 4), _chapter_review(2, 2)]
        review = compute_review(
            reviews, [], SynopsisBeats(promised=["a"], undelivered=[])
        )
        coherence = next(c for c in review.criteria if c.name == "coherence")
        assert coherence.score == 3  # mean(4, 2)
        assert "weakest is chapter 2" in coherence.justification

    def test_continuity_score_drops_with_breaks(self):
        clean = compute_review(
            [_chapter_review(1, 5)], [], SynopsisBeats(promised=["a"], undelivered=[])
        )
        assert clean.continuity.score == 5

        broken_pairs = [PairContinuity(between=(1, 2), breaks=["x", "y"])]
        broken = compute_review(
            [_chapter_review(1, 5)],
            broken_pairs,
            SynopsisBeats(promised=["a"], undelivered=[]),
        )
        assert broken.continuity.score == 3  # 5 - 2 breaks
        assert len(broken.continuity.breaks) == 2

    def test_synopsis_delivery_is_coverage_ratio(self):
        review = compute_review(
            [_chapter_review(1, 5)],
            [],
            SynopsisBeats(promised=["a", "b", "c", "d"], undelivered=["d"]),
        )
        assert review.synopsis_delivery.score == 4  # round(5 * 3/4)

    def test_verdict_is_empty_after_compute(self):
        review = compute_review(
            [_chapter_review(1, 5)], [], SynopsisBeats(promised=["a"], undelivered=[])
        )
        assert review.verdict == ""  # only the LLM fills this, later

    def test_chapters_sorted_by_number(self):
        """Map collection order is non-deterministic; reduce must re-sort."""
        reviews = [_chapter_review(2, 3), _chapter_review(1, 4)]
        review = compute_review(
            reviews, [], SynopsisBeats(promised=["a"], undelivered=[])
        )
        assert [c.number for c in review.chapters] == [1, 2]


class TestComputeNodeBoundary:
    def test_compute_node_normalizes_model_instances(self):
        """FR-059: an llm node stores a (foreign) model instance, not a dict.

        ``compute_node`` must coerce model-or-dict inputs before validating against
        our own models — regression for the live run where the executor returned a
        dynamically built ``SynopsisBeats`` distinct from ours.
        """
        from examples.book_reviewer.models import BookReview
        from examples.book_reviewer.nodes.tools import compute_node

        state = {
            "chapter_reviews": [
                _chapter_review(1, 4).model_dump(),
                _chapter_review(2, 3).model_dump(),
            ],
            "pair_continuities": [
                PairContinuity(between=(1, 2), breaks=[]).model_dump()
            ],
            # A model INSTANCE, not a dict — the case that broke the live run.
            "synopsis_beats": SynopsisBeats(promised=["a", "b"], undelivered=["b"]),
        }
        out = compute_node(state)
        review = BookReview.model_validate(out["review_draft"])
        assert 1 <= review.overall <= 5
        assert review.synopsis_delivery.score >= 1


class TestChapterPairs:
    def test_pairs_are_self_contained(self):
        """K2: each pair item carries both bodies, not indices."""
        parsed = parse_manuscript(
            "> t\n\n# Synopsis\n\ns\n\n# Chapter 1: A\n\nbody one\n\n# Chapter 2: B\n\nbody two\n"
        )
        pairs = make_chapter_pairs(parsed)
        assert len(pairs) == 1
        assert pairs[0]["between"] == [1, 2]
        assert pairs[0]["body_n"] == "body one"
        assert pairs[0]["body_n1"] == "body two"
