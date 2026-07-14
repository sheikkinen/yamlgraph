"""FR-727 RED witness: process-code discipline + combined-code composition.

Judged pins condemned here (REQ-YG-555):
- F1/F2/F3: META_PROCESS_CODES = {-43, -46, -48, -69} demote
  match → partial_match at validation time — evidence preserved in
  best_partial, never primary/secondary. Genuine process requests
  (-50, -62) are NOT capped.
- F4: process primaries gain combined_code composed from
  chapter_context (K86 + -50 → K50); chapter A when contextless;
  chapter primaries get no combined_code.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "icpc-2-rfe"

TRANSCRIPT = (
    "Caller asks to renew her mother's blood pressure medication "
    "prescription. The medication has worked well with no problems."
)


def _load_reducer():
    path = EXAMPLE / "nodes" / "reduce.py"
    spec = importlib.util.spec_from_file_location("fr727_reduce", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["fr727_reduce"] = mod
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


class TestMetaProcessCap:
    @pytest.mark.req("REQ-YG-555")
    def test_meta_process_match_demoted_to_best_partial(self):
        """F3: a -48 match claim lands in best_partial, never primary
        or secondary — the FR-725 baseline regression condemned."""
        reducer = _load_reducer()
        out = _reduce(
            reducer,
            [
                _cand("-48", "Clarification of RFE/demand", "match", 0.99),
                _cand("R05", "Cough", "match", 0.8),
            ],
        )
        classification = out["classification"]
        assert classification["primary"]["code"] == "R05"
        assert all(e["code"] != "-48" for e in classification["secondary"])
        assert any(e["code"] == "-48" for e in classification["best_partial"])

    @pytest.mark.req("REQ-YG-555")
    def test_all_four_capped_codes(self):
        reducer = _load_reducer()
        capped = ["-43", "-46", "-48", "-69"]
        out = _reduce(
            reducer,
            [_cand(c, f"meta {c}", "match", 0.99) for c in capped],
        )
        assert out["classification"]["primary"] is None
        assert out["classification"]["low_confidence"] is True
        partial_codes = {e["code"] for e in out["classification"]["best_partial"]}
        assert partial_codes <= set(capped) and partial_codes

    @pytest.mark.req("REQ-YG-555")
    def test_genuine_process_requests_not_capped(self):
        """-50 renewal and -62 admin stay primary-capable."""
        reducer = _load_reducer()
        out = _reduce(
            reducer,
            [
                _cand("-50", "Medication/prescription/renewal", "match", 0.9),
                _cand("-62", "Administrative procedure", "match", 0.8),
            ],
        )
        assert out["classification"]["primary"]["code"] == "-50"
        assert out["classification"]["secondary"][0]["code"] == "-62"


class TestCombinedCode:
    @pytest.mark.req("REQ-YG-555")
    def test_composed_from_chapter_context(self):
        """F4: K86 context + -50 → K50."""
        reducer = _load_reducer()
        out = _reduce(
            reducer,
            [
                _cand("-50", "Medication/prescription/renewal", "match", 0.9),
                _cand("K86", "Hypertension uncomplicated", "partial_match", 0.9),
            ],
        )
        primary = out["classification"]["primary"]
        assert primary["code"] == "-50"
        assert primary["combined_code"] == "K50"
        assert primary["chapter_context"]["code"] == "K86"

    @pytest.mark.req("REQ-YG-555")
    def test_chapter_a_default_when_contextless(self):
        reducer = _load_reducer()
        out = _reduce(
            reducer,
            [_cand("-62", "Administrative procedure", "match", 0.9)],
        )
        primary = out["classification"]["primary"]
        assert primary["combined_code"] == "A62"
        assert "chapter_context" not in primary

    @pytest.mark.req("REQ-YG-555")
    def test_chapter_primary_gets_no_combined_code(self):
        reducer = _load_reducer()
        out = _reduce(reducer, [_cand("R05", "Cough", "match", 0.9, ["renew"])])
        assert "combined_code" not in out["classification"]["primary"]
