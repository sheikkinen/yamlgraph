"""FR-532 -- tests for the continuity-axis calibration harness.

Example-scoped (FR-474 J3): NO ``@pytest.mark.req``; these guard the deterministic
study tool, not a framework requirement.
"""

from __future__ import annotations

from pathlib import Path

from examples.dungeon_master.scripts import calibrate_continuity_axis as cal

_REVIEW_MD = """# Book Review

**Overall:** 4/5

## Continuity

Score: 1/5
- Arnulf declared dead then reappears alive -- lifecycle contradiction.
- Rope single line then a second handline knot -- rope micro-state.
- Food pouch hand-off churn -- which-hand-holds-the-prop.

## Synopsis delivery

Score: 5/5
- this bullet is NOT a continuity break and must be ignored.
"""


def test_parse_continuity_breaks_reads_score_and_bullets() -> None:
    score, breaks = cal.parse_continuity_breaks(_REVIEW_MD)
    assert score == 1
    assert len(breaks) == 3
    assert breaks[0].startswith("Arnulf declared dead")
    # The synopsis-section bullet must not leak into the continuity breaks.
    assert all("NOT a continuity break" not in b for b in breaks)


def test_recalibrated_score_mirrors_reviewer_formula() -> None:
    assert cal.recalibrated_score(0) == 5
    assert cal.recalibrated_score(2) == 3
    # Floors at 1 -- matches book_reviewer's max(1, 5 - n).
    assert cal.recalibrated_score(7) == 1


def test_tabulate_counts_real_vs_micro_and_recalibrates() -> None:
    sample = {
        "BK-1": {"critic_score": 1, "breaks": ["a", "b", "c"]},
    }
    labels = {
        "BK-1": {
            "breaks": [
                {"label": "real"},
                {"label": "micro"},
                {"label": "micro"},
            ]
        }
    }
    rows = cal.tabulate(sample, labels)
    assert len(rows) == 1
    row = rows[0]
    assert row["critic_breaks"] == 3
    assert row["real"] == 1
    assert row["micro"] == 2
    assert row["critic_score"] == 1
    # One reader-real break -> recalibrated 5 - 1 = 4.
    assert row["recalibrated_score"] == 4


def test_tabulate_rejects_label_count_mismatch() -> None:
    sample = {"BK-1": {"critic_score": 1, "breaks": ["a", "b"]}}
    labels = {"BK-1": {"breaks": [{"label": "real"}]}}
    try:
        cal.tabulate(sample, labels)
    except ValueError as exc:
        assert "re-align the labels" in str(exc)
    else:  # pragma: no cover - guard must raise
        raise AssertionError("expected a count-mismatch ValueError")


def test_committed_labels_align_with_the_recorded_corpus() -> None:
    """The committed labels classify exactly the breaks the critic recorded -- the
    calibration is reproducible against the real review.md artifacts."""
    repo = Path(__file__).resolve().parents[3]
    labels_path = (
        repo
        / "examples"
        / "dungeon_master"
        / "docs"
        / "continuity-calibration-labels.yaml"
    )
    out_dir = repo / "outputs" / "dungeon-master"
    if not out_dir.exists():
        return  # corpus not present in this checkout -- harness still unit-tested above

    labels = cal.load_labels(labels_path)
    sample = cal.load_sample(out_dir, sorted(labels))
    # Must not raise: every book's label count matches its recorded break count.
    rows = cal.tabulate(sample, labels)
    total_micro = sum(r["micro"] for r in rows)
    total = sum(r["critic_breaks"] for r in rows)
    # The load-bearing finding: physical micro-state dominates the critic's breaks.
    assert total_micro > total / 2
