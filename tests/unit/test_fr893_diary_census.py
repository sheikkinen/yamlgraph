"""FR-893 RED: diary trap recurrence aggregator — fail-closed witnesses.

LLM-free aggregator over corpus_census JSONL ledgers: canonical-label
grouping, DISTINCT-ENTRY counting (R-4), citation preservation,
threshold filtering, abstention exclusion, public-safe committed output
(no evidence-span column, R-3), and the hidden-canary run gate.
"""

import json
from pathlib import Path

import pytest

# References examples/ (process boundary, FR-756)
pytestmark = pytest.mark.process


def _row(item_ref, judgement, abstained=False, reason=""):
    return {
        "item_ref": item_ref,
        "judgement": judgement,
        "confidence": 0.9 if not abstained else 0.1,
        "evidence_span": "" if abstained else f"span from {item_ref}",
        "model": "claude-haiku-4-5",
        "prompt_version": "judge_item.v1",
        "abstained": abstained,
        "abstain_reason": reason,
        "disagreement": False,
    }


def _ledger(tmp_path, name, rows):
    p = tmp_path / name
    with p.open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    return p


ROWS = [
    _row("docs/diary/2026-08-25-a.md", "stale_msg_file, heading_consumption"),
    _row("docs/diary/2026-08-26-b.md", "stale_msg_file"),
    _row("docs/diary/2026-08-26-c.md", "stale_msg_file, line_pinned_gates"),
    _row("docs/diary/2026-08-24-d.md", "line_pinned_gates"),
    _row("docs/diary/2026-08-23-e.md", "line_pinned_gates"),
    _row("docs/diary/2026-08-22-f.md", "none", abstained=True, reason="no traps"),
]

CANARIES = {"msg_file|msg_txt": 3, "line_pin": 3}


def _aggregate(tmp_path, rows=None, canaries=None, threshold=3):
    from examples.demos.corpus_census.adapters.diary_recurrence import aggregate

    ledger = _ledger(tmp_path, "ledger.jsonl", rows if rows is not None else ROWS)
    out = tmp_path / "census"
    return aggregate(
        [str(ledger)],
        str(out),
        threshold=threshold,
        canaries=canaries if canaries is not None else CANARIES,
        inbox_dir=str(tmp_path / "inbox"),
    )


class TestAggregation:
    @pytest.mark.req("REQ-YG-624")
    def test_distinct_entry_counting_and_grouping(self, tmp_path):
        result = _aggregate(tmp_path)
        counts = {c["label"]: c["entries"] for c in result["candidates"]}
        assert counts["stale_msg_file"] == 3
        assert counts["line_pinned_gates"] == 3
        assert counts["heading_consumption"] == 1

    @pytest.mark.req("REQ-YG-624")
    def test_same_entry_counts_once(self, tmp_path):
        rows = ROWS + [_row("docs/diary/2026-08-25-a.md", "stale_msg_file")]
        result = _aggregate(tmp_path, rows=rows)
        counts = {c["label"]: c["entries"] for c in result["candidates"]}
        assert counts["stale_msg_file"] == 3  # duplicate entry not recounted

    @pytest.mark.req("REQ-YG-624")
    def test_citations_and_first_last_seen(self, tmp_path):
        result = _aggregate(tmp_path)
        smf = next(c for c in result["candidates"] if c["label"] == "stale_msg_file")
        assert len(smf["citations"]) == 3
        assert smf["first_seen"] == "2026-08-25"
        assert smf["last_seen"] == "2026-08-26"

    @pytest.mark.req("REQ-YG-624")
    def test_abstentions_excluded_but_counted(self, tmp_path):
        result = _aggregate(tmp_path)
        labels = {c["label"] for c in result["candidates"]}
        assert "none" not in labels
        assert result["abstentions"] == 1

    @pytest.mark.req("REQ-YG-624")
    def test_label_without_citation_rejected(self, tmp_path):
        rows = ROWS + [_row("", "orphan_label")]
        with pytest.raises(ValueError, match="citation|item_ref"):
            _aggregate(tmp_path, rows=rows)


class TestPublicSafeArtifact:
    @pytest.mark.req("REQ-YG-624")
    def test_committed_table_has_no_evidence_spans(self, tmp_path):
        result = _aggregate(tmp_path)
        table = (tmp_path / "census" / result["table_name"]).read_text(encoding="utf-8")
        assert "span from" not in table  # raw spans never committed (R-3)
        assert "stale_msg_file" in table
        assert "2026-08-25-a.md" in table  # citations are paths only

    @pytest.mark.req("REQ-YG-624")
    def test_inbox_draft_written_at_threshold(self, tmp_path):
        result = _aggregate(tmp_path)
        drafts = result["inbox_drafts"]
        assert len(drafts) == 2  # two labels at >=3 distinct entries
        from pathlib import Path

        text = Path(drafts[0]).read_text(encoding="utf-8")
        assert "graduation" in text.lower()
        assert "span from" not in text

    @pytest.mark.req("REQ-YG-624")
    def test_graduated_labels_excluded_from_drafts(self, tmp_path):
        """Scripture-graduated labels are measured but not re-proposed."""
        from examples.demos.corpus_census.adapters.diary_recurrence import (
            aggregate,
        )

        ledger = _ledger(tmp_path, "ledger.jsonl", ROWS)
        result = aggregate(
            [str(ledger)],
            str(tmp_path / "census"),
            threshold=3,
            canaries=CANARIES,
            inbox_dir=str(tmp_path / "inbox"),
            graduated={"stale_msg_file"},
        )
        drafted = {Path(d).stem for d in result["inbox_drafts"]}
        assert "diary-census-stale_msg_file" not in drafted
        assert "diary-census-line_pinned_gates" in drafted
        # still measured in the table
        labels = {c["label"] for c in result["candidates"]}
        assert "stale_msg_file" in labels


class TestCanaryGate:
    @pytest.mark.req("REQ-YG-624")
    def test_missing_canary_fails_loudly(self, tmp_path):
        rows = [r for r in ROWS if "line_pinned_gates" not in r["judgement"]]
        with pytest.raises(ValueError, match="[Cc]anary"):
            _aggregate(tmp_path, rows=rows)

    @pytest.mark.req("REQ-YG-624")
    def test_canary_below_threshold_fails(self, tmp_path):
        canaries = {"msg_file": 5}
        with pytest.raises(ValueError, match="[Cc]anary"):
            _aggregate(tmp_path, canaries=canaries)

    @pytest.mark.req("REQ-YG-624")
    def test_canary_family_matches_drifted_labels(self, tmp_path):
        """Vocabulary drift: family substring matches label variants."""
        rows = [
            _row("docs/diary/2026-03-07-a.md", "tmp_msg_txt"),
            _row("docs/diary/2026-03-07-b.md", "stale_tmp_msg_file"),
            _row("docs/diary/2026-07-15-c.md", "tmp_msg_file_loss"),
        ]
        result = _aggregate(
            tmp_path, rows=rows, canaries={"msg_txt|msg_file": 3}, threshold=5
        )
        assert result["rows"] == 3  # gate passed on family match

    @pytest.mark.req("REQ-YG-624")
    def test_no_inbox_drafts_when_canary_fails(self, tmp_path):
        rows = [r for r in ROWS if "line_pinned_gates" not in r["judgement"]]
        with pytest.raises(ValueError):
            _aggregate(tmp_path, rows=rows)
        assert not (tmp_path / "inbox").exists()  # fail before emission
