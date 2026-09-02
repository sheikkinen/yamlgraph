"""FR-725 RED witness: labeled crosscheck harness (REQ-YG-554).

Judged pins condemned here:
- Labels parse from ``data/labeled/`` (file-based only — F2); every
  label carries rationale + valid_for_components (F4).
- ``evaluate_result``: primary_any_of / must_include (any surfaced
  slot) / must_not_include (primary+secondary) / low_confidence_expected
  (tri-state: true/false/null=either).
- Attribution: archives join on fixture basename; "stdin" archives are
  never attributed (F2).
- Agreement: raw k-of-n counts, NO significance fields (F3).
- Component skip: label whose valid_for_components mismatches the
  result's declared coverage is skipped loudly by name (F4).
"""

import importlib.util
import sys
from pathlib import Path

import pytest

EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "icpc-2-rfe"
LABELED = EXAMPLE / "data" / "labeled"


def _load_harness():
    path = EXAMPLE / "nodes" / "crosscheck.py"
    assert path.exists(), f"FR-725 module missing: {path}"
    spec = importlib.util.spec_from_file_location("fr725_crosscheck", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["fr725_crosscheck"] = mod
    spec.loader.exec_module(mod)
    return mod


def _result(
    primary_code=None,
    secondary=(),
    partials=(),
    low_conf=False,
    components=(1, 2, 3, 4, 5, 6, 7),
    context=None,
):
    primary = None
    if primary_code:
        primary = {"code": primary_code, "title": primary_code}
        if context:
            primary["chapter_context"] = {"code": context, "title": context}
    return {
        "classification": {
            "primary": primary,
            "secondary": [{"code": c, "title": c} for c in secondary],
            "low_confidence": low_conf,
            "best_partial": [{"code": c, "title": c} for c in partials],
        },
        "meta": {
            "catalog_version": "ICPC-2e-v7.0",
            "catalog_coverage": {"components": list(components)},
        },
    }


class TestLabels:
    @pytest.mark.req("REQ-YG-554")
    def test_labeled_fixtures_parse_complete(self):
        harness = _load_harness()
        labels = harness.load_labels(LABELED)
        # 6 originals + hp36 en/de translations (language invariance)
        assert len(labels) >= 8
        for name, label in labels.items():
            assert (LABELED / f"{name}.md").exists(), f"{name}: transcript missing"
            assert label["rationale"], f"{name}: rationale required"
            assert label["valid_for_components"], name
            assert label["primary_any_of"] or label["low_confidence_expected"] in (
                True,
                None,
            ), f"{name}: no acceptance shape"


class TestEvaluate:
    @pytest.mark.req("REQ-YG-554")
    def test_primary_any_of_pass_and_fail(self):
        harness = _load_harness()
        label = {
            "primary_any_of": ["R05"],
            "must_include": [],
            "must_not_include": [],
            "low_confidence_expected": False,
            "valid_for_components": [1, 2, 3, 4, 5, 6, 7],
            "rationale": "r",
        }
        ok = harness.evaluate_result(label, _result("R05"))
        assert ok["passed"] is True
        bad = harness.evaluate_result(label, _result("Z10"))
        assert bad["passed"] is False
        assert any("primary" in f for f in bad["failures"])

    @pytest.mark.req("REQ-YG-554")
    def test_must_include_any_surfaced_slot(self):
        harness = _load_harness()
        label = {
            "primary_any_of": ["-50"],
            "must_include": ["K86"],
            "must_not_include": [],
            "low_confidence_expected": False,
            "valid_for_components": [1, 2, 3, 4, 5, 6, 7],
            "rationale": "r",
        }
        # K86 surfaced via chapter_context counts
        ok = harness.evaluate_result(label, _result("-50", context="K86"))
        assert ok["passed"] is True
        # K86 surfaced via best_partial counts
        ok2 = harness.evaluate_result(label, _result("-50", partials=["K86"]))
        assert ok2["passed"] is True
        missing = harness.evaluate_result(label, _result("-50"))
        assert missing["passed"] is False

    @pytest.mark.req("REQ-YG-554")
    def test_must_not_include_blocks_primary_and_secondary_only(self):
        harness = _load_harness()
        label = {
            "primary_any_of": ["R05"],
            "must_include": [],
            "must_not_include": ["Z10"],
            "low_confidence_expected": False,
            "valid_for_components": [1, 2, 3, 4, 5, 6, 7],
            "rationale": "r",
        }
        bad = harness.evaluate_result(label, _result("R05", secondary=["Z10"]))
        assert bad["passed"] is False
        # allowed in best_partial (informational)
        ok = harness.evaluate_result(label, _result("R05", partials=["Z10"]))
        assert ok["passed"] is True

    @pytest.mark.req("REQ-YG-554")
    def test_low_confidence_tristate(self):
        harness = _load_harness()
        base = {
            "primary_any_of": ["A97"],
            "must_include": [],
            "must_not_include": [],
            "valid_for_components": [1, 2, 3, 4, 5, 6, 7],
            "rationale": "r",
        }
        either = harness.evaluate_result(
            {**base, "low_confidence_expected": None},
            _result(None, low_conf=True),
        )
        assert either["passed"] is True

    @pytest.mark.req("REQ-YG-554")
    def test_component_mismatch_skips_loudly(self):
        harness = _load_harness()
        label = {
            "primary_any_of": ["-50"],
            "must_include": [],
            "must_not_include": [],
            "low_confidence_expected": False,
            "valid_for_components": [1, 2, 3, 4, 5, 6, 7],
            "rationale": "r",
        }
        out = harness.evaluate_result(label, _result("R05", components=(1, 7)))
        assert out["skipped"] is True
        assert "components" in out["reason"]


class TestAttributionAndAgreement:
    @pytest.mark.req("REQ-YG-554")
    def test_stdin_archives_never_attributed(self, tmp_path):
        harness = _load_harness()
        (tmp_path / "stdin-20260714_120000.result.json").write_text("{}", encoding="utf-8")
        (tmp_path / "cough-fever-20260714_120000.result.json").write_text("{}", encoding="utf-8")
        (tmp_path / "unknown-run-20260714_120000.result.json").write_text("{}", encoding="utf-8")
        attributed = harness.attribute_archives(tmp_path, {"cough-fever"})
        assert set(attributed) == {"cough-fever"}
        assert len(attributed["cough-fever"]) == 1

    @pytest.mark.req("REQ-YG-554")
    def test_prefix_fixture_names_not_confused(self, tmp_path):
        """Language-invariance finding: hp36-renewal-behalf-en archives
        must NOT attribute to hp36-renewal-behalf (prefix collision) —
        attribution is exact name + timestamp."""
        (tmp_path / "hp36-20260715_080000.result.json").write_text("{}", encoding="utf-8")
        (tmp_path / "hp36-en-20260715_080001.result.json").write_text("{}", encoding="utf-8")
        attributed = _load_harness().attribute_archives(tmp_path, {"hp36", "hp36-en"})
        assert len(attributed["hp36"]) == 1
        assert len(attributed["hp36-en"]) == 1

    @pytest.mark.req("REQ-YG-554")
    def test_agreement_raw_counts_no_significance(self):
        harness = _load_harness()
        results = [_result("R05"), _result("R05"), _result("A03")]
        agr = harness.agreement(results)
        assert agr == {"n": 3, "primary_mode": "R05", "k": 2}
