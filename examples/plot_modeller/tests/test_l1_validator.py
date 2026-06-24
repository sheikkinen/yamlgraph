"""FR-573 — L1 validator tests: validate_agents contract (RED first)."""

from __future__ import annotations

from nodes.tools import validate_agents

# --- Minimal valid extraction ---

VALID_RAW = (
    "agents:\n"
    "  - Marren\n"
    "  - Hagen\n"
    "initial_world:\n"
    "  - pred: alive\n"
    "    args: [Marren]\n"
    "    value: true\n"
    "  - pred: alive\n"
    "    args: [Hagen]\n"
    "    value: true\n"
    "initial_belief: []\n"
)


class TestValidateAgentsSuccess:
    """Golden path — valid extraction writes agents + world + belief."""

    def test_golden_success(self):
        out = validate_agents({"agents_raw": VALID_RAW})
        assert out["validation"]["ok"] is True
        assert out["validation"]["flaws"] == []
        assert out["agents"] == ["Marren", "Hagen"]
        assert len(out["initial_world"]) == 2
        assert out["initial_belief"] == []

    def test_with_beliefs(self):
        raw = (
            "agents:\n"
            "  - A\n"
            "  - B\n"
            "initial_world:\n"
            "  - pred: alive\n"
            "    args: [A]\n"
            "    value: true\n"
            "  - pred: alive\n"
            "    args: [B]\n"
            "    value: true\n"
            "initial_belief:\n"
            "  - observer: A\n"
            "    fluent:\n"
            "      pred: rel\n"
            "      args: [A, B]\n"
            "    held: unknown\n"
        )
        out = validate_agents({"agents_raw": raw})
        assert out["validation"]["ok"] is True
        assert len(out["initial_belief"]) == 1

    def test_with_extra_world_predicates(self):
        """at, holds, rel, faction predicates beyond alive are fine."""
        raw = (
            "agents:\n"
            "  - Naima\n"
            "  - Diallo\n"
            "initial_world:\n"
            "  - pred: alive\n"
            "    args: [Naima]\n"
            "    value: true\n"
            "  - pred: alive\n"
            "    args: [Diallo]\n"
            "    value: true\n"
            "  - pred: at\n"
            "    args: [Naima, Timbuktu]\n"
            "    value: true\n"
            "  - pred: rel\n"
            "    args: [Naima, Diallo]\n"
            "    value: rivals\n"
            "initial_belief: []\n"
        )
        out = validate_agents({"agents_raw": raw})
        assert out["validation"]["ok"] is True
        assert len(out["initial_world"]) == 4


class TestValidateAgentsFailure:
    """Each flaw → validation fails, no agents/world/belief written (J1)."""

    def test_empty_raw_does_not_crash(self):
        out = validate_agents({"agents_raw": ""})
        assert out["validation"]["ok"] is False
        assert "agents" not in out

    def test_invalid_yaml_syntax(self):
        out = validate_agents({"agents_raw": "agents: [\ninvalid: : :\n"})
        assert out["validation"]["ok"] is False
        assert "agents" not in out

    def test_non_dict_top_level(self):
        out = validate_agents({"agents_raw": "- just\n- a\n- list\n"})
        assert out["validation"]["ok"] is False

    def test_missing_agents_key(self):
        raw = "initial_world: []\ninitial_belief: []\n"
        out = validate_agents({"agents_raw": raw})
        assert out["validation"]["ok"] is False
        assert any("agents" in f for f in out["validation"]["flaws"])

    def test_empty_agents_list(self):
        raw = "agents: []\ninitial_world: []\ninitial_belief: []\n"
        out = validate_agents({"agents_raw": raw})
        assert out["validation"]["ok"] is False

    def test_agents_not_strings(self):
        raw = "agents:\n  - 123\n  - true\ninitial_world: []\ninitial_belief: []\n"
        out = validate_agents({"agents_raw": raw})
        assert out["validation"]["ok"] is False

    def test_invalid_fluent_in_world(self):
        raw = (
            "agents:\n"
            "  - A\n"
            "initial_world:\n"
            "  - bad_key: nope\n"
            "initial_belief: []\n"
        )
        out = validate_agents({"agents_raw": raw})
        assert out["validation"]["ok"] is False
        assert any("initial_world" in f for f in out["validation"]["flaws"])

    def test_invalid_belief(self):
        raw = (
            "agents:\n"
            "  - A\n"
            "initial_world:\n"
            "  - pred: alive\n"
            "    args: [A]\n"
            "    value: true\n"
            "initial_belief:\n"
            "  - not_a_belief: true\n"
        )
        out = validate_agents({"agents_raw": raw})
        assert out["validation"]["ok"] is False
        assert any("initial_belief" in f for f in out["validation"]["flaws"])

    def test_agent_referenced_in_world_not_in_agents_list(self):
        raw = (
            "agents:\n"
            "  - A\n"
            "initial_world:\n"
            "  - pred: alive\n"
            "    args: [A]\n"
            "    value: true\n"
            "  - pred: alive\n"
            "    args: [B]\n"
            "    value: true\n"
            "initial_belief: []\n"
        )
        out = validate_agents({"agents_raw": raw})
        assert out["validation"]["ok"] is False
        assert any("B" in f for f in out["validation"]["flaws"])

    def test_agent_missing_alive_predicate(self):
        raw = (
            "agents:\n"
            "  - A\n"
            "  - B\n"
            "initial_world:\n"
            "  - pred: alive\n"
            "    args: [A]\n"
            "    value: true\n"
            "initial_belief: []\n"
        )
        out = validate_agents({"agents_raw": raw})
        assert out["validation"]["ok"] is False
        assert any("B" in f and "alive" in f for f in out["validation"]["flaws"])

    def test_failure_does_not_write_agents(self):
        """J1 pattern: failure writes ONLY validation."""
        out = validate_agents({"agents_raw": "garbage"})
        assert "agents" not in out
        assert "initial_world" not in out
        assert "initial_belief" not in out
        assert "validation" in out
