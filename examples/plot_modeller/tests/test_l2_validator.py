"""FR-574 — L2 validator tests: validate_goals contract (RED first)."""

from __future__ import annotations

from nodes.tools import validate_goals

AGENTS = ["Marren", "Hagen", "Witness Pell"]

VALID_RAW = (
    "- pred: alive\n"
    "  args: [Witness Pell]\n"
    "  value: true\n"
    "- pred: holds\n"
    "  args: [Marren, ledger]\n"
    "  value: true\n"
)


class TestValidateGoalsSuccess:
    """Golden path — valid goals extraction."""

    def test_golden_success(self):
        out = validate_goals({"goals_raw": VALID_RAW, "agents": AGENTS})
        assert out["validation"]["ok"] is True
        assert out["validation"]["flaws"] == []
        assert len(out["goals"]) == 2

    def test_single_goal(self):
        raw = "- pred: alive\n  args: [Marren]\n  value: true\n"
        out = validate_goals({"goals_raw": raw, "agents": AGENTS})
        assert out["validation"]["ok"] is True
        assert len(out["goals"]) == 1

    def test_rel_goal(self):
        raw = "- pred: rel\n  args: [Marren, Hagen]\n  value: reconciled\n"
        out = validate_goals({"goals_raw": raw, "agents": AGENTS})
        assert out["validation"]["ok"] is True


class TestValidateGoalsFailure:
    """Each flaw → validation fails, goals not written (J1)."""

    def test_empty_raw(self):
        out = validate_goals({"goals_raw": "", "agents": AGENTS})
        assert out["validation"]["ok"] is False
        assert "goals" not in out

    def test_invalid_yaml(self):
        out = validate_goals({"goals_raw": "- pred: : :\n", "agents": AGENTS})
        assert out["validation"]["ok"] is False

    def test_non_list(self):
        out = validate_goals({"goals_raw": "just a string\n", "agents": AGENTS})
        assert out["validation"]["ok"] is False

    def test_empty_list(self):
        out = validate_goals({"goals_raw": "[]\n", "agents": AGENTS})
        assert out["validation"]["ok"] is False
        assert any("empty" in f or "at least" in f for f in out["validation"]["flaws"])

    def test_invalid_fluent(self):
        raw = "- bad_key: nope\n"
        out = validate_goals({"goals_raw": raw, "agents": AGENTS})
        assert out["validation"]["ok"] is False

    def test_unknown_predicate(self):
        raw = "- pred: loves\n  args: [Marren, Hagen]\n  value: true\n"
        out = validate_goals({"goals_raw": raw, "agents": AGENTS})
        assert out["validation"]["ok"] is False
        assert any("loves" in f for f in out["validation"]["flaws"])

    def test_agent_not_in_agents_list(self):
        raw = "- pred: alive\n  args: [Unknown]\n  value: true\n"
        out = validate_goals({"goals_raw": raw, "agents": AGENTS})
        assert out["validation"]["ok"] is False
        assert any("Unknown" in f for f in out["validation"]["flaws"])

    def test_duplicate_goals(self):
        raw = (
            "- pred: alive\n  args: [Marren]\n  value: true\n"
            "- pred: alive\n  args: [Marren]\n  value: true\n"
        )
        out = validate_goals({"goals_raw": raw, "agents": AGENTS})
        assert out["validation"]["ok"] is False
        assert any("duplicate" in f.lower() for f in out["validation"]["flaws"])

    def test_failure_does_not_write_goals(self):
        out = validate_goals({"goals_raw": "garbage", "agents": AGENTS})
        assert "goals" not in out
        assert "validation" in out
