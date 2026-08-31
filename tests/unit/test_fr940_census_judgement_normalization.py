"""FR-940: judgement label normalization at the ledger boundary.

RED-first witnesses for the frozen normalization algorithm in
examples/demos/corpus_census/tools.py — witnessed repair rows from the
2026-08-31 spark census (committed fixture), grammar/vocabulary
demotion, vocabulary validation, model-abstention canonicalization,
audit fields, frozen summary line, and effective-model plumbing.
"""

import json
from pathlib import Path

import pytest

from examples.demos.corpus_census.tools import reduce_ledger

# References examples/ (process boundary, FR-756)
pytestmark = pytest.mark.process

FIXTURE = json.loads(
    (
        Path(__file__).resolve().parents[1]
        / "fixtures"
        / "fr940_witnessed_judgements.json"
    ).read_text(encoding="utf-8")
)
LABELS = FIXTURE["labels"]
WITNESSED = FIXTURE["witnessed"]


def _finding(judgement, index=0, **overrides):
    finding = {
        "source_index": index,
        "judgement": judgement,
        "confidence": 0.8,
        "evidence_span": "some cited span",
        "abstained": False,
        "abstain_reason": "",
    }
    finding.update(overrides)
    return finding


def _run(tmp_path, findings, labels=None, model=None):
    state = {
        "items": [f"corpus/{i:03d}.txt" for i in range(len(findings))],
        "findings": findings,
        "output_path": str(tmp_path / "ledger.md"),
    }
    if labels is not None:
        state["labels"] = labels
    if model is not None:
        state["model"] = model
    return reduce_ledger(state)


def _rows(tmp_path):
    return [
        json.loads(line)
        for line in (tmp_path / "ledger.jsonl").read_text().splitlines()
    ]


class TestWitnessedRepairs:
    @pytest.mark.req("REQ-YG-633")
    @pytest.mark.parametrize(
        "witness", WITNESSED, ids=[w["expected_judgement"] for w in WITNESSED]
    )
    def test_witnessed_row_repairs_to_vocabulary_label(self, tmp_path, witness):
        """AC-2: every witnessed census shape repairs, none demote."""
        _run(tmp_path, [_finding(witness["raw"])], labels=LABELS)
        row = _rows(tmp_path)[0]
        assert row["judgement"] == witness["expected_judgement"]
        assert row["repaired"] is True
        assert row["raw_judgement"] == witness["raw"]
        assert row["abstained"] is False

    @pytest.mark.req("REQ-YG-633")
    def test_all_witnessed_rows_in_one_run_zero_demotions(self, tmp_path):
        findings = [_finding(w["raw"], index=i) for i, w in enumerate(WITNESSED)]
        _run(tmp_path, findings, labels=LABELS)
        rows = _rows(tmp_path)
        assert len(rows) == len(WITNESSED)
        assert all(not r["abstained"] for r in rows)
        md = (tmp_path / "ledger.md").read_text()
        assert (
            f"Normalization: {len(WITNESSED)} repaired, 0 demoted, "
            f"0 model-abstained, 0 row-failed of {len(WITNESSED)} rows." in md
        )


class TestUntouchedAndCase:
    @pytest.mark.req("REQ-YG-633")
    def test_valid_label_untouched(self, tmp_path):
        _run(tmp_path, [_finding("steering")], labels=LABELS)
        row = _rows(tmp_path)[0]
        assert row["judgement"] == "steering"
        assert row["repaired"] is False
        assert row["raw_judgement"] == ""

    @pytest.mark.req("REQ-YG-633")
    def test_case_collision_emits_canonical_vocab_spelling(self, tmp_path):
        """AC-3: case-only difference canonicalizes, not counted repaired."""
        _run(tmp_path, [_finding("Steering")], labels=LABELS)
        row = _rows(tmp_path)[0]
        assert row["judgement"] == "steering"
        assert row["repaired"] is False
        assert row["raw_judgement"] == "Steering"

    @pytest.mark.req("REQ-YG-633")
    def test_quoted_head_unwrapped(self, tmp_path):
        _run(tmp_path, [_finding('"steering" | theme: cleanup')], labels=LABELS)
        row = _rows(tmp_path)[0]
        assert row["judgement"] == "steering"
        assert row["repaired"] is True


class TestGrammarDemotion:
    @pytest.mark.req("REQ-YG-633")
    def test_ambiguous_prose_demotes(self, tmp_path):
        raw = "consider splitting the core framework from the examples tree"
        _run(tmp_path, [_finding(raw)])
        row = _rows(tmp_path)[0]
        assert row["judgement"] == "abstain"
        assert row["abstained"] is True
        assert row["confidence"] == 0.0
        assert row["evidence_span"] == ""
        assert row["abstain_reason"] == "unparseable judgement shape"
        assert row["raw_judgement"] == raw
        assert row["repaired"] is False

    @pytest.mark.req("REQ-YG-633")
    def test_over_64_chars_demotes(self, tmp_path):
        _run(tmp_path, [_finding("x" * 70)])
        row = _rows(tmp_path)[0]
        assert row["judgement"] == "abstain"
        assert row["abstain_reason"] == "unparseable judgement shape"

    @pytest.mark.req("REQ-YG-633")
    def test_syntactic_guarantee_without_labels(self, tmp_path):
        """AC-4: no vocabulary — heads repair by grammar, prose demotes."""
        _run(
            tmp_path,
            [
                _finding("new-spark | some theme | some text", index=0),
                _finding("this is definitely not a category label", index=1),
            ],
        )
        judged = sorted(r["judgement"] for r in _rows(tmp_path))
        assert judged == ["abstain", "new-spark"]


class TestVocabulary:
    @pytest.mark.req("REQ-YG-633")
    def test_out_of_vocabulary_demotes(self, tmp_path):
        _run(tmp_path, [_finding("architecture")], labels=LABELS)
        row = _rows(tmp_path)[0]
        assert row["judgement"] == "abstain"
        assert row["abstain_reason"] == "label not in vocabulary"
        assert row["raw_judgement"] == "architecture"

    @pytest.mark.req("REQ-YG-633")
    @pytest.mark.parametrize(
        "bad_labels",
        [[], [""], ["Ops", "ops"], ["steering", "abstain"]],
        ids=["empty", "empty-member", "casefold-duplicate", "reserved-abstain"],
    )
    def test_invalid_vocabulary_raises(self, tmp_path, bad_labels):
        with pytest.raises(ValueError):
            _run(tmp_path, [_finding("steering")], labels=bad_labels)


class TestModelAbstention:
    @pytest.mark.req("REQ-YG-633")
    def test_model_abstention_canonicalized_not_demoted(self, tmp_path):
        _run(
            tmp_path,
            [
                _finding(
                    "unknown",
                    abstained=True,
                    evidence_span="",
                    abstain_reason="document empty",
                )
            ],
            labels=LABELS,
        )
        row = _rows(tmp_path)[0]
        assert row["judgement"] == "abstain"
        assert row["abstained"] is True
        assert row["raw_judgement"] == "unknown"
        assert row["abstain_reason"] == "document empty"
        md = (tmp_path / "ledger.md").read_text()
        assert (
            "Normalization: 0 repaired, 0 demoted, "
            "1 model-abstained, 0 row-failed of 1 rows." in md
        )


class TestArtifacts:
    @pytest.mark.req("REQ-YG-633")
    def test_jsonl_schema_carries_audit_fields(self, tmp_path):
        """AC-5: revised key set includes raw_judgement and repaired."""
        _run(tmp_path, [_finding("steering")], labels=LABELS)
        assert set(_rows(tmp_path)[0]) == {
            "item_ref",
            "judgement",
            "confidence",
            "evidence_span",
            "model",
            "prompt_version",
            "abstained",
            "abstain_reason",
            "disagreement",
            "raw_judgement",
            "repaired",
        }

    @pytest.mark.req("REQ-YG-633")
    def test_summary_line_exact(self, tmp_path):
        findings = [
            _finding("steering", index=0),
            _finding("(a) type: reframe; (b) theme: x", index=1),
            _finding("utterly unclassifiable free form prose here", index=2),
        ]
        _run(tmp_path, findings, labels=LABELS)
        md = (tmp_path / "ledger.md").read_text()
        assert (
            "Normalization: 1 repaired, 1 demoted, "
            "0 model-abstained, 0 row-failed of 3 rows." in md
        )


class TestEffectiveModel:
    @pytest.mark.req("REQ-YG-633")
    def test_model_var_reaches_provenance(self, tmp_path):
        _run(tmp_path, [_finding("steering")], labels=LABELS, model="mercury-2")
        assert _rows(tmp_path)[0]["model"] == "mercury-2"

    @pytest.mark.req("REQ-YG-633")
    def test_model_defaults_to_pinned_haiku(self, tmp_path):
        _run(tmp_path, [_finding("steering")], labels=LABELS)
        assert _rows(tmp_path)[0]["model"] == "claude-haiku-4-5"
