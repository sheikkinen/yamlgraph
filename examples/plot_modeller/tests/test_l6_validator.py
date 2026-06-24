"""FR-577 — L6 validator tests: validate_causality contract (RED first).

Judgement conditions exercised:
  J1   — on failure, ``causality`` is never written (only ``validation``).
  J:C2 — ``enables`` links are forward-only; a backward link is a validation
         failure (not merely an evaluator miss).
"""

from __future__ import annotations

from nodes.tools import validate_causality

# Three ordered beats. Narrative order is the glosses list order (F1 < F2 < F3).
GLOSSES = [
    {
        "id": "F1",
        "gloss": "Mara discovers the anomaly in the loom.",
        "chapter": 1,
        "kind": "villainy",
        "subject": "ARIA",
    },
    {
        "id": "F2",
        "gloss": "Mara resolves to expose ARIA to the council.",
        "chapter": 2,
        "kind": "mediation",
        "subject": "Mara",
    },
    {
        "id": "F3",
        "gloss": "Mara confronts ARIA at the phase lock.",
        "chapter": 3,
        "kind": "victory",
        "subject": "Mara",
    },
]
AGENTS = ["Mara", "ARIA", "Jonas"]

VALID_RAW = (
    "- id: F1\n"
    "  enables: [F2]\n"
    "  motivation: null\n"
    "  threatens: null\n"
    "- id: F2\n"
    "  enables: [F3]\n"
    "  motivation:\n"
    "    agent: Mara\n"
    "    goal: expose_ARIA\n"
    "  threatens:\n"
    "    agent: ARIA\n"
    "    goal: expand_coherence\n"
    "- id: F3\n"
    "  enables: []\n"
    "  motivation:\n"
    "    agent: Mara\n"
    "    goal: stop_ARIA\n"
    "  threatens: null\n"
)


class TestValidateCausalitySuccess:
    """Golden path — valid causality assignment."""

    def test_golden_success(self):
        out = validate_causality(
            {"causality_raw": VALID_RAW, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is True
        assert out["validation"]["flaws"] == []
        assert len(out["causality"]) == 3

    def test_terminal_beat_empty_enables_ok(self):
        out = validate_causality(
            {"causality_raw": VALID_RAW, "glosses": GLOSSES, "agents": AGENTS}
        )
        f3 = next(item for item in out["causality"] if item["id"] == "F3")
        assert f3["enables"] == []

    def test_null_motivation_and_threatens_ok(self):
        out = validate_causality(
            {"causality_raw": VALID_RAW, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is True
        f1 = next(item for item in out["causality"] if item["id"] == "F1")
        assert f1["motivation"] is None
        assert f1["threatens"] is None

    def test_code_fenced_output_is_parsed(self):
        """Boundary: LLM sometimes wraps YAML in ```yaml ... ``` fences."""
        fenced = f"```yaml\n{VALID_RAW}```\n"
        out = validate_causality(
            {"causality_raw": fenced, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is True
        assert len(out["causality"]) == 3

    def test_bare_code_fence_is_parsed(self):
        fenced = f"```\n{VALID_RAW}```"
        out = validate_causality(
            {"causality_raw": fenced, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is True

    def test_absent_optional_keys_default_gracefully(self):
        """Missing motivation/threatens keys are treated as null (not a flaw)."""
        raw = (
            "- id: F1\n  enables: [F2]\n"
            "- id: F2\n  enables: [F3]\n"
            "- id: F3\n  enables: []\n"
        )
        out = validate_causality(
            {"causality_raw": raw, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is True
        assert len(out["causality"]) == 3


class TestValidateCausalityFailure:
    """Each flaw -> validation fails, causality not written (J1)."""

    def test_empty_raw(self):
        out = validate_causality(
            {"causality_raw": "", "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False
        assert "causality" not in out

    def test_invalid_yaml(self):
        out = validate_causality(
            {"causality_raw": "- id: : :\n", "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False
        assert "causality" not in out

    def test_non_list(self):
        out = validate_causality(
            {"causality_raw": "id: F1\n", "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False
        assert "causality" not in out

    def test_orphan_id(self):
        raw = (
            "- id: F1\n  enables: [F2]\n"
            "- id: F2\n  enables: [F3]\n"
            "- id: F3\n  enables: []\n"
            "- id: F99\n  enables: []\n"
        )
        out = validate_causality(
            {"causality_raw": raw, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False
        assert any("F99" in f for f in out["validation"]["flaws"])
        assert "causality" not in out

    def test_missing_id(self):
        raw = "- id: F1\n  enables: [F2]\n- id: F2\n  enables: [F3]\n"
        out = validate_causality(
            {"causality_raw": raw, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False
        assert any("F3" in f for f in out["validation"]["flaws"])
        assert "causality" not in out

    def test_invalid_enables_target(self):
        raw = (
            "- id: F1\n  enables: [F2]\n"
            "- id: F2\n  enables: [F77]\n"
            "- id: F3\n  enables: []\n"
        )
        out = validate_causality(
            {"causality_raw": raw, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False
        assert any("F77" in f for f in out["validation"]["flaws"])
        assert "causality" not in out

    def test_backward_enables_link_rejected(self):
        """J:C2 — a beat may only enable a LATER beat; F2 -> F1 is a failure."""
        raw = (
            "- id: F1\n  enables: [F2]\n"
            "- id: F2\n  enables: [F1]\n"
            "- id: F3\n  enables: []\n"
        )
        out = validate_causality(
            {"causality_raw": raw, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False
        assert any("backward" in f.lower() for f in out["validation"]["flaws"])
        assert "causality" not in out

    def test_self_enables_link_rejected(self):
        """A beat enabling itself is a backward (non-forward) link."""
        raw = (
            "- id: F1\n  enables: [F2]\n"
            "- id: F2\n  enables: [F2]\n"
            "- id: F3\n  enables: []\n"
        )
        out = validate_causality(
            {"causality_raw": raw, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False
        assert "causality" not in out

    def test_enables_not_a_list(self):
        raw = (
            "- id: F1\n  enables: F2\n"
            "- id: F2\n  enables: [F3]\n"
            "- id: F3\n  enables: []\n"
        )
        out = validate_causality(
            {"causality_raw": raw, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False
        assert "causality" not in out

    def test_motivation_agent_not_in_agents(self):
        raw = (
            "- id: F1\n  enables: [F2]\n"
            "- id: F2\n  enables: [F3]\n"
            "  motivation:\n    agent: Ghost\n    goal: haunt\n"
            "- id: F3\n  enables: []\n"
        )
        out = validate_causality(
            {"causality_raw": raw, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False
        assert any("Ghost" in f for f in out["validation"]["flaws"])

    def test_threatens_agent_not_in_agents(self):
        raw = (
            "- id: F1\n  enables: [F2]\n"
            "- id: F2\n  enables: [F3]\n"
            "  threatens:\n    agent: Phantom\n    goal: lurk\n"
            "- id: F3\n  enables: []\n"
        )
        out = validate_causality(
            {"causality_raw": raw, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False
        assert any("Phantom" in f for f in out["validation"]["flaws"])

    def test_motivation_missing_goal_rejected(self):
        raw = (
            "- id: F1\n  enables: [F2]\n"
            "- id: F2\n  enables: [F3]\n"
            "  motivation:\n    agent: Mara\n"
            "- id: F3\n  enables: []\n"
        )
        out = validate_causality(
            {"causality_raw": raw, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False

    def test_unknown_key_rejected(self):
        raw = (
            "- id: F1\n  enables: [F2]\n  bogus: nope\n"
            "- id: F2\n  enables: [F3]\n"
            "- id: F3\n  enables: []\n"
        )
        out = validate_causality(
            {"causality_raw": raw, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False
        assert any("bogus" in f for f in out["validation"]["flaws"])
