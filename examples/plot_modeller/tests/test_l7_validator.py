"""FR-578 — L7 validator tests: validate_affects contract (RED first).

Judgement conditions exercised:
  J1   — on failure, ``affects`` is never written (only ``validation``).
  C1   — the validator checks STRUCTURE only; open/close balance is NOT
         enforced here (it belongs to the merge node, FR-579).
  C4   — ``kind`` is the closed 6-value ``AffectKind`` enum; an unknown kind
         is a structural failure (no tolerance).
"""

from __future__ import annotations

from nodes.tools import validate_affects

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
        "gloss": "Mara resolves to expose ARIA, wracked by guilt.",
        "chapter": 2,
        "kind": "mediation",
        "subject": "Mara",
    },
    {
        "id": "F3",
        "gloss": "Mara confronts ARIA; ARIA's betrayal lands.",
        "chapter": 3,
        "kind": "victory",
        "subject": "Mara",
    },
]
AGENTS = ["Mara", "ARIA", "Jonas"]

VALID_RAW = (
    "- id: F1\n"
    "  eff_affect: []\n"
    "- id: F2\n"
    "  eff_affect:\n"
    "    - op: open\n"
    "      char: Mara\n"
    "      kind: guilt\n"
    "- id: F3\n"
    "  eff_affect:\n"
    "    - op: close\n"
    "      char: Mara\n"
    "      kind: guilt\n"
    "    - op: open\n"
    "      char: ARIA\n"
    "      kind: betrayal\n"
    "      toward: Mara\n"
)


class TestValidateAffectsSuccess:
    def test_golden_success(self):
        out = validate_affects(
            {"affects_raw": VALID_RAW, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is True
        assert out["validation"]["flaws"] == []
        assert len(out["affects"]) == 3

    def test_empty_eff_affect_ok(self):
        out = validate_affects(
            {"affects_raw": VALID_RAW, "glosses": GLOSSES, "agents": AGENTS}
        )
        f1 = next(item for item in out["affects"] if item["id"] == "F1")
        assert f1["eff_affect"] == []

    def test_toward_present_and_valid(self):
        out = validate_affects(
            {"affects_raw": VALID_RAW, "glosses": GLOSSES, "agents": AGENTS}
        )
        f3 = next(item for item in out["affects"] if item["id"] == "F3")
        betrayal = next(d for d in f3["eff_affect"] if d["kind"] == "betrayal")
        assert betrayal["toward"] == "Mara"

    def test_absent_eff_affect_key_defaults_to_empty(self):
        raw = "- id: F1\n- id: F2\n- id: F3\n"
        out = validate_affects(
            {"affects_raw": raw, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is True
        assert all(item["eff_affect"] == [] for item in out["affects"])

    def test_unbalanced_open_without_close_still_valid(self):
        """C1 — balance is NOT a validator concern; an unclosed open is OK here."""
        raw = (
            "- id: F1\n  eff_affect:\n    - op: open\n      char: Mara\n"
            "      kind: hope\n"
            "- id: F2\n  eff_affect: []\n"
            "- id: F3\n  eff_affect: []\n"
        )
        out = validate_affects(
            {"affects_raw": raw, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is True

    def test_code_fenced_output_is_parsed(self):
        fenced = f"```yaml\n{VALID_RAW}```\n"
        out = validate_affects(
            {"affects_raw": fenced, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is True
        assert len(out["affects"]) == 3

    def test_bare_code_fence_is_parsed(self):
        fenced = f"```\n{VALID_RAW}```"
        out = validate_affects(
            {"affects_raw": fenced, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is True


class TestValidateAffectsFailure:
    def test_empty_raw(self):
        out = validate_affects(
            {"affects_raw": "", "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False
        assert "affects" not in out

    def test_invalid_yaml(self):
        out = validate_affects(
            {"affects_raw": "- id: : :\n", "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False
        assert "affects" not in out

    def test_non_list(self):
        out = validate_affects(
            {"affects_raw": "id: F1\n", "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False
        assert "affects" not in out

    def test_orphan_id(self):
        raw = (
            "- id: F1\n  eff_affect: []\n"
            "- id: F2\n  eff_affect: []\n"
            "- id: F3\n  eff_affect: []\n"
            "- id: F99\n  eff_affect: []\n"
        )
        out = validate_affects(
            {"affects_raw": raw, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False
        assert any("F99" in f for f in out["validation"]["flaws"])
        assert "affects" not in out

    def test_missing_id(self):
        raw = "- id: F1\n  eff_affect: []\n- id: F2\n  eff_affect: []\n"
        out = validate_affects(
            {"affects_raw": raw, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False
        assert any("F3" in f for f in out["validation"]["flaws"])
        assert "affects" not in out

    def test_unknown_kind_rejected(self):
        """C4 — closed enum; 'anger' is not an AffectKind."""
        raw = (
            "- id: F1\n  eff_affect:\n    - op: open\n      char: Mara\n"
            "      kind: anger\n"
            "- id: F2\n  eff_affect: []\n"
            "- id: F3\n  eff_affect: []\n"
        )
        out = validate_affects(
            {"affects_raw": raw, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False
        assert "affects" not in out

    def test_invalid_op_rejected(self):
        raw = (
            "- id: F1\n  eff_affect:\n    - op: begin\n      char: Mara\n"
            "      kind: guilt\n"
            "- id: F2\n  eff_affect: []\n"
            "- id: F3\n  eff_affect: []\n"
        )
        out = validate_affects(
            {"affects_raw": raw, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False
        assert "affects" not in out

    def test_extra_key_rejected(self):
        """AffectDelta has extra='forbid'."""
        raw = (
            "- id: F1\n  eff_affect:\n    - op: open\n      char: Mara\n"
            "      kind: guilt\n      intensity: high\n"
            "- id: F2\n  eff_affect: []\n"
            "- id: F3\n  eff_affect: []\n"
        )
        out = validate_affects(
            {"affects_raw": raw, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False
        assert "affects" not in out

    def test_char_not_in_agents(self):
        raw = (
            "- id: F1\n  eff_affect:\n    - op: open\n      char: Ghost\n"
            "      kind: guilt\n"
            "- id: F2\n  eff_affect: []\n"
            "- id: F3\n  eff_affect: []\n"
        )
        out = validate_affects(
            {"affects_raw": raw, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False
        assert any("Ghost" in f for f in out["validation"]["flaws"])

    def test_toward_not_in_agents(self):
        raw = (
            "- id: F1\n  eff_affect:\n    - op: open\n      char: Mara\n"
            "      kind: betrayal\n      toward: Phantom\n"
            "- id: F2\n  eff_affect: []\n"
            "- id: F3\n  eff_affect: []\n"
        )
        out = validate_affects(
            {"affects_raw": raw, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False
        assert any("Phantom" in f for f in out["validation"]["flaws"])

    def test_eff_affect_not_a_list(self):
        raw = (
            "- id: F1\n  eff_affect: open\n"
            "- id: F2\n  eff_affect: []\n"
            "- id: F3\n  eff_affect: []\n"
        )
        out = validate_affects(
            {"affects_raw": raw, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False
        assert "affects" not in out

    def test_unknown_top_level_key_rejected(self):
        raw = (
            "- id: F1\n  eff_affect: []\n  bogus: nope\n"
            "- id: F2\n  eff_affect: []\n"
            "- id: F3\n  eff_affect: []\n"
        )
        out = validate_affects(
            {"affects_raw": raw, "glosses": GLOSSES, "agents": AGENTS}
        )
        assert out["validation"]["ok"] is False
        assert any("bogus" in f for f in out["validation"]["flaws"])
