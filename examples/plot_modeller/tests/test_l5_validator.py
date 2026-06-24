"""FR-576 — L5 validator tests: validate_pre_eff contract (RED first).

Judgement conditions exercised:
  J1  — on failure, ``pre_eff`` is never written (only ``validation``).
  J:C2 — NO kind->effect structural rule: a ``death`` beat whose effect is a
         ``rel`` change (not ``alive=false``) must validate.
"""

from __future__ import annotations

from nodes.tools import validate_pre_eff

# Two beats: F1 (villainy), F2 (death modelled as a relationship change).
GLOSSES = [
    {
        "id": "F1",
        "gloss": "ARIA seizes the firmware channel.",
        "chapter": 1,
        "kind": "villainy",
        "subject": "ARIA",
    },
    {
        "id": "F2",
        "gloss": "Jonas is assimilated.",
        "chapter": 6,
        "kind": "death",
        "subject": "ARIA",
    },
]
AGENTS = ["ARIA", "Jonas", "Mara", "The Swarm"]

VALID_RAW = (
    "- id: F1\n"
    "  pre_world:\n"
    "    - pred: holds\n"
    "      args: [ARIA, firmware_channel]\n"
    "      value: true\n"
    "  eff_world:\n"
    "    - pred: rel\n"
    "      args: [The Swarm, ARIA]\n"
    "      value: assimilated\n"
    "  pre_belief: []\n"
    "  eff_belief: []\n"
    "- id: F2\n"
    "  pre_world:\n"
    "    - pred: alive\n"
    "      args: [Jonas]\n"
    "      value: true\n"
    "  eff_world:\n"
    "    - pred: rel\n"
    "      args: [Jonas, ARIA]\n"
    "      value: assimilated\n"
    "  pre_belief: []\n"
    "  eff_belief:\n"
    "    - observer: Mara\n"
    "      fluent:\n"
    "        pred: rel\n"
    "        args: [Jonas, ARIA]\n"
    "      held: anomalous\n"
)


class TestValidatePreEffSuccess:
    """Golden path — valid pre/eff assignment."""

    def test_golden_success(self):
        out = validate_pre_eff(
            {"pre_eff_raw": VALID_RAW, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is True
        assert out["validation"]["flaws"] == []
        assert len(out["pre_eff"]) == 2

    def test_death_as_relationship_change_is_valid(self):
        """J:C2 — a death beat need NOT produce alive=false; rel change is valid."""
        out = validate_pre_eff(
            {"pre_eff_raw": VALID_RAW, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is True
        f2 = next(item for item in out["pre_eff"] if item["id"] == "F2")
        # The effect is a relationship change, not alive=false — and that's fine.
        assert f2["eff_world"][0]["pred"] == "rel"

    def test_empty_pre_belief_ok(self):
        out = validate_pre_eff(
            {"pre_eff_raw": VALID_RAW, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is True


class TestValidatePreEffFailure:
    """Each flaw -> validation fails, pre_eff not written (J1)."""

    def test_empty_raw(self):
        out = validate_pre_eff(
            {"pre_eff_raw": "", "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False
        assert "pre_eff" not in out

    def test_invalid_yaml(self):
        out = validate_pre_eff(
            {"pre_eff_raw": "- id: : :\n", "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False
        assert "pre_eff" not in out

    def test_non_list(self):
        out = validate_pre_eff(
            {"pre_eff_raw": "id: F1\n", "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False
        assert "pre_eff" not in out

    def test_orphan_id(self):
        raw = (
            "- id: F1\n  pre_world: []\n  eff_world: []\n  pre_belief: []\n  eff_belief: []\n"
            "- id: F2\n  pre_world: []\n  eff_world: []\n  pre_belief: []\n  eff_belief: []\n"
            "- id: F99\n  pre_world: []\n  eff_world: []\n  pre_belief: []\n  eff_belief: []\n"
        )
        out = validate_pre_eff(
            {"pre_eff_raw": raw, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False
        assert any("F99" in f for f in out["validation"]["flaws"])
        assert "pre_eff" not in out

    def test_missing_id(self):
        raw = "- id: F1\n  pre_world: []\n  eff_world: []\n  pre_belief: []\n  eff_belief: []\n"
        out = validate_pre_eff(
            {"pre_eff_raw": raw, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False
        assert any("F2" in f for f in out["validation"]["flaws"])

    def test_unknown_predicate(self):
        raw = (
            "- id: F1\n  pre_world:\n    - pred: teleports\n      args: [ARIA]\n      value: true\n"
            "  eff_world: []\n  pre_belief: []\n  eff_belief: []\n"
            "- id: F2\n  pre_world: []\n  eff_world: []\n  pre_belief: []\n  eff_belief: []\n"
        )
        out = validate_pre_eff(
            {"pre_eff_raw": raw, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False
        assert any("teleports" in f for f in out["validation"]["flaws"])

    def test_invalid_fluent_structure(self):
        raw = (
            "- id: F1\n  pre_world:\n    - pred: holds\n      extra_key: nope\n      args: [ARIA, x]\n      value: true\n"
            "  eff_world: []\n  pre_belief: []\n  eff_belief: []\n"
            "- id: F2\n  pre_world: []\n  eff_world: []\n  pre_belief: []\n  eff_belief: []\n"
        )
        out = validate_pre_eff(
            {"pre_eff_raw": raw, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False

    def test_unknown_agent_in_alive(self):
        raw = (
            "- id: F1\n  pre_world:\n    - pred: alive\n      args: [Ghost]\n      value: true\n"
            "  eff_world: []\n  pre_belief: []\n  eff_belief: []\n"
            "- id: F2\n  pre_world: []\n  eff_world: []\n  pre_belief: []\n  eff_belief: []\n"
        )
        out = validate_pre_eff(
            {"pre_eff_raw": raw, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False
        assert any("Ghost" in f for f in out["validation"]["flaws"])

    def test_invalid_belief_structure(self):
        raw = (
            "- id: F1\n  pre_world: []\n  eff_world: []\n  pre_belief: []\n"
            "  eff_belief:\n    - observer: Mara\n      held: true\n"  # missing fluent
            "- id: F2\n  pre_world: []\n  eff_world: []\n  pre_belief: []\n  eff_belief: []\n"
        )
        out = validate_pre_eff(
            {"pre_eff_raw": raw, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False
