"""FR-570 — Plot Modeller L4 spike tests.

Covers the validator (AC#2, AC#5 incl. the J1 crash regression) and the
evaluator scoring of absent/unparseable output (AC#6, J6).
"""

from __future__ import annotations

from evaluate import compare, score_genre, summarise
from nodes.tools import validate_kinds

GLOSSES = [
    {"id": "F1", "gloss": "Hagen's men abduct Pell.", "chapter": 1},
    {"id": "F2", "gloss": "Marren finds the witness gone.", "chapter": 1},
]


class TestValidateKinds:
    """AC#2 / AC#5 — validator contract."""

    def test_golden_success_writes_kinds(self):
        """Valid YAML list → kinds written, validation ok (golden)."""
        raw = (
            "- id: F1\n  kind: villainy\n  subject: Hagen\n"
            "- id: F2\n  kind: lack\n  subject: Marren\n"
        )
        out = validate_kinds({"kinds_raw": raw, "glosses": GLOSSES})
        assert out["validation"]["ok"] is True
        assert out["validation"]["flaws"] == []
        assert [item["kind"] for item in out["kinds"]] == ["villainy", "lack"]

    def test_empty_raw_does_not_crash(self):
        """J1 regression: empty kinds_raw (yaml→None) must not raise TypeError.

        The pre-fix validator did `for item in items` where items=None, crashing
        the graph on the first validation. The fix guards with isinstance(list).
        """
        out = validate_kinds({"kinds_raw": "", "glosses": GLOSSES})
        assert out["validation"]["ok"] is False
        assert "kinds" not in out  # J1: never write kinds on failure

    def test_scalar_raw_is_invalid(self):
        """Non-list YAML (a scalar) → invalid, no crash."""
        out = validate_kinds({"kinds_raw": "just a string", "glosses": GLOSSES})
        assert out["validation"]["ok"] is False
        assert "kinds" not in out

    def test_rejects_unknown_kind(self):
        """Unknown kind label → flaw, kinds absent."""
        raw = "- id: F1\n  kind: betrayal\n  subject: Hagen\n"
        out = validate_kinds({"kinds_raw": raw, "glosses": [GLOSSES[0]]})
        assert out["validation"]["ok"] is False
        assert any("betrayal" in f for f in out["validation"]["flaws"])
        assert "kinds" not in out

    def test_rejects_missing_subject(self):
        """Missing subject → flaw."""
        raw = "- id: F1\n  kind: villainy\n"
        out = validate_kinds({"kinds_raw": raw, "glosses": [GLOSSES[0]]})
        assert out["validation"]["ok"] is False
        assert any("subject" in f for f in out["validation"]["flaws"])

    def test_rejects_missing_glosses(self):
        """A gloss left unclassified → 'missing' flaw."""
        raw = "- id: F1\n  kind: villainy\n  subject: Hagen\n"
        out = validate_kinds({"kinds_raw": raw, "glosses": GLOSSES})
        assert out["validation"]["ok"] is False
        assert any("missing" in f for f in out["validation"]["flaws"])

    def test_invalid_yaml_syntax(self):
        """Unparseable YAML → caught, reported, no crash."""
        out = validate_kinds(
            {"kinds_raw": "- id: F1\n  kind: : :\n", "glosses": GLOSSES}
        )
        assert out["validation"]["ok"] is False
        assert "kinds" not in out


TRUTH = [
    {"id": "F1", "kind": "villainy", "subject": "Hagen"},
    {"id": "F2", "kind": "lack", "subject": "Marren"},
]


class TestEvaluate:
    """AC#6 / J6 — evaluator scoring of absent/unparseable predictions."""

    def test_golden_all_correct(self):
        """Perfect prediction → full marks, valid YAML true."""
        predicted = [
            {"id": "F1", "kind": "villainy", "subject": "Hagen"},
            {"id": "F2", "kind": "lack", "subject": "Marren"},
        ]
        ev = score_genre("detective", predicted, TRUTH, "anthropic", "haiku")
        assert ev["summary"]["kind_correct"] == 2
        assert ev["summary"]["kind_accuracy"] == "2/2 (1.00)"
        assert ev["summary"]["subject_correct"] == 2
        assert ev["summary"]["produced_valid_yaml"] is True
        assert ev["confusions"] == []
        assert ev["meta"]["corpus"] == "self-derived (upper-bound)"  # J2

    def test_absent_prediction_scores_all_wrong(self):
        """J6: predicted=None → every function wrong, no crash."""
        ev = score_genre("horror", None, TRUTH, "anthropic", "haiku")
        assert ev["summary"]["kind_correct"] == 0
        assert ev["summary"]["kind_accuracy"] == "0/2 (0.00)"
        assert ev["summary"]["produced_valid_yaml"] is False
        assert len(ev["confusions"]) == 2

    def test_non_list_prediction_scores_all_wrong(self):
        """J6: a scalar prediction is treated as all-wrong, never crashes."""
        ev = score_genre("scifi", "garbage", TRUTH, "anthropic", "haiku")
        assert ev["summary"]["kind_correct"] == 0
        assert ev["summary"]["produced_valid_yaml"] is False

    def test_confusion_recorded(self):
        """A misclassification is recorded as expected-vs-predicted."""
        predicted = [
            {"id": "F1", "kind": "villainy", "subject": "Hagen"},
            {"id": "F2", "kind": "pursuit", "subject": "Marren"},  # wrong kind
        ]
        per_function, confusions = compare(predicted, TRUTH)
        assert per_function[1]["kind_match"] is False
        assert confusions == [
            {"expected": "lack", "predicted": "pursuit", "function": "F2"}
        ]

    def test_subject_match_is_tolerant(self):
        """Subject comparison ignores case and surrounding whitespace."""
        predicted = [
            {"id": "F1", "kind": "villainy", "subject": "  hagen "},
            {"id": "F2", "kind": "lack", "subject": "MARREN"},
        ]
        ev = score_genre("detective", predicted, TRUTH, "anthropic", "haiku")
        assert ev["summary"]["subject_correct"] == 2

    def test_summarise_stamps_corpus_ceiling(self):
        """Aggregate summary carries the self-derived ceiling (J2)."""
        ev = score_genre("detective", None, TRUTH, "anthropic", "haiku")
        summary = summarise([ev])
        assert summary["corpus"] == "self-derived (upper-bound)"
        assert summary["total_functions"] == 2
        assert summary["kind_accuracy"] == "0/2 (0.00)"
