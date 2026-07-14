"""FR-730 RED witness: chapter-code inflation discipline (REQ-YG-556).

Judged pins condemned here:
- F2: chapter cap = {Z10} only — a Z10 match demotes to partial and
  never reaches primary/secondary; A13/A23/A29 stay uncapped.
- F3: same-chapter symptom-over-diagnosis — a component-7 match demotes
  to partial when a component-1 match exists in the SAME chapter
  (P03 → P76 demoted); no demotion across chapters or without a
  competing symptom.
- F4: composition context eligibility (non-process, non-capped,
  non-Z-chapter) with component-7 diseases preferred over component-1
  symptoms — the opposite of RFE primacy, deliberately.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "icpc-2-rfe"

TRANSCRIPT = (
    "Caller asks to renew her mother's blood pressure medication "
    "prescription. She mentions feeling sad and worried lately."
)


def _load_reducer():
    path = EXAMPLE / "nodes" / "reduce.py"
    spec = importlib.util.spec_from_file_location("fr730_reduce", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["fr730_reduce"] = mod
    spec.loader.exec_module(mod)
    return mod


def _cand(code, title, verdict, conf, spans=None):
    return {
        "code": code,
        "title": title,
        "verdict": verdict,
        "confidence": conf,
        "reasoning_short": f"{title} indicated.",
        "evidence_spans": spans if spans is not None else ["renew"],
        "missing_signals": [],
    }


def _reduce(reducer, candidates):
    return reducer.reduce_best_rfe(
        {"map_results": [{"candidates": candidates}], "transcript": TRANSCRIPT}
    )


class TestZ10Cap:
    @pytest.mark.req("REQ-YG-556")
    def test_z10_match_demoted_never_secondary(self):
        """F2: Z10 is the Z-side twin of -48 (empty inclusion list)."""
        reducer = _load_reducer()
        out = _reduce(
            reducer,
            [
                _cand("Z10", "Health care system problem", "match", 0.99),
                _cand("R05", "Cough", "match", 0.8),
            ],
        )
        classification = out["classification"]
        assert classification["primary"]["code"] == "R05"
        assert all(e["code"] != "Z10" for e in classification["secondary"])
        assert any(e["code"] == "Z10" for e in classification["best_partial"])

    @pytest.mark.req("REQ-YG-556")
    def test_a13_stays_uncapped(self):
        """F2/F5: A13 is genuinely stateable — accepted residual."""
        reducer = _load_reducer()
        out = _reduce(
            reducer,
            [_cand("A13", "Concern about/fear of medical treatment", "match", 0.9)],
        )
        assert out["classification"]["primary"]["code"] == "A13"


class TestSymptomOverDiagnosis:
    @pytest.mark.req("REQ-YG-556")
    def test_same_chapter_c7_demoted_when_c1_matches(self):
        """F3: P03 (feeling depressed) match → P76 (depressive
        disorder) demotes; ICPC practical rule 3 mechanized."""
        reducer = _load_reducer()
        out = _reduce(
            reducer,
            [
                _cand("P76", "Depressive disorder", "match", 0.95),
                _cand("P03", "Feeling depressed", "match", 0.8),
            ],
        )
        classification = out["classification"]
        assert classification["primary"]["code"] == "P03"
        assert all(e["code"] != "P76" for e in classification["secondary"])
        assert any(e["code"] == "P76" for e in classification["best_partial"])

    @pytest.mark.req("REQ-YG-556")
    def test_c7_kept_without_competing_symptom(self):
        """Guard: K86 alone (renewal call) stays primary-capable."""
        reducer = _load_reducer()
        out = _reduce(
            reducer,
            [_cand("K86", "Hypertension uncomplicated", "match", 0.9)],
        )
        assert out["classification"]["primary"]["code"] == "K86"

    @pytest.mark.req("REQ-YG-556")
    def test_no_demotion_across_chapters(self):
        """Guard: R05 (R-chapter symptom) does not demote K86."""
        reducer = _load_reducer()
        out = _reduce(
            reducer,
            [
                _cand("R05", "Cough", "match", 0.9),
                _cand("K86", "Hypertension uncomplicated", "match", 0.8),
            ],
        )
        codes = {out["classification"]["primary"]["code"]} | {
            e["code"] for e in out["classification"]["secondary"]
        }
        assert codes == {"R05", "K86"}


class TestCompositionContext:
    @pytest.mark.req("REQ-YG-556")
    def test_context_prefers_disease_over_symptom(self):
        """F4: K86 (C7) wins the context slot over A13 (C1) even at
        lower confidence — composition anchors to the problem managed."""
        reducer = _load_reducer()
        out = _reduce(
            reducer,
            [
                _cand("-50", "Medication/prescription/renewal", "match", 0.9),
                _cand("A13", "Concern about treatment", "partial_match", 0.99),
                _cand("K86", "Hypertension uncomplicated", "partial_match", 0.7),
            ],
        )
        primary = out["classification"]["primary"]
        assert primary["chapter_context"]["code"] == "K86"
        assert primary["combined_code"] == "K50"

    @pytest.mark.req("REQ-YG-556")
    def test_z_chapter_ineligible_as_context(self):
        """F4: a renewal is never social-chapter business — Z candidates
        never compose; chapter A default applies."""
        reducer = _load_reducer()
        out = _reduce(
            reducer,
            [
                _cand("-50", "Medication/prescription/renewal", "match", 0.9),
                _cand("Z05", "Work problem", "partial_match", 0.95),
            ],
        )
        primary = out["classification"]["primary"]
        assert primary["combined_code"] == "A50"
        assert "chapter_context" not in primary

    @pytest.mark.req("REQ-YG-556")
    def test_genuine_z_rfe_still_classifiable(self):
        """AC-03: a genuinely social transcript keeps its Z primary
        (Z05 is uncapped; only Z10 is the descriptor twin)."""
        reducer = _load_reducer()
        out = _reduce(
            reducer,
            [_cand("Z05", "Work problem", "match", 0.9)],
        )
        assert out["classification"]["primary"]["code"] == "Z05"
