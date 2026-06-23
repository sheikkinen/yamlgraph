"""FR-570 — Plot Modeller L4 spike tests.

Covers the validator (AC#2, AC#5 incl. the J1 crash regression) and the
evaluator scoring of absent/unparseable output (AC#6, J6).
"""

from __future__ import annotations

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
