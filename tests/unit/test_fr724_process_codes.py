"""FR-724 RED witness: ICPC-2 process codes (phase 2).

Judged pins condemned here (REQ-YG-551):
- Builder includes process rubrics (components 2–6, chapter "-") as
  ``PROC-C<n>`` clusters; chapter headers still excluded.
- Reducer F4: a process-code match outranks a chapter-code match for
  RFE primacy — explicit rule, never asciibetical accident.
- Reducer F1: ``chapter_context`` is reducer-derived — best-ranked
  non-process candidate attached when the primary is a process code.
- Coverage meta declares components [1..7].
"""

import importlib.util
import sys
from pathlib import Path

import pytest

EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "icpc-2-rfe"
FIXTURES = Path(__file__).resolve().parent / "fixtures"

TRANSCRIPT = (
    "Caller asks to renew her mother's blood pressure medication "
    "prescription. The medication has worked well with no problems."
)


def _load(module_filename: str):
    path = EXAMPLE / "nodes" / module_filename
    name = f"fr724_{module_filename.removesuffix('.py')}"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
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


class TestBuilderProcessCodes:
    @pytest.mark.req("REQ-YG-551")
    def test_process_codes_included_as_proc_clusters(self):
        builder = _load("build_catalog.py")
        xml_text = (FIXTURES / "icpc2_claml_excerpt.xml").read_text()
        rows = builder.parse_claml(xml_text)
        by_code = {r["code"]: r for r in rows}
        assert "-30" in by_code, "process code excluded (phase-1 rule leaked)"
        p30 = by_code["-30"]
        assert p30["component"] == 2
        assert p30["cluster_id"] == "PROC-C2"
        assert p30["chapter"] == "-"
        assert p30["provenance_status"] == "verified"
        # chapter headers still excluded
        assert "R" not in by_code

    @pytest.mark.req("REQ-YG-551")
    def test_chapter_code_clusters_unchanged(self):
        builder = _load("build_catalog.py")
        xml_text = (FIXTURES / "icpc2_claml_excerpt.xml").read_text()
        rows = builder.parse_claml(xml_text)
        by_code = {r["code"]: r for r in rows}
        assert by_code["R05"]["cluster_id"] == "R-C1"
        assert by_code["R74"]["cluster_id"] == "R-C7"


class TestReducerProcessPrimacy:
    @pytest.mark.req("REQ-YG-551")
    def test_process_match_outranks_chapter_match(self):
        """F4: deliberate rule — even at LOWER confidence the process
        match takes primary (the stated reason IS the process)."""
        reducer = _load("reduce.py")
        out = _reduce(
            reducer,
            [
                _cand("K86", "Hypertension uncomplicated", "match", 0.99),
                _cand("-50", "Medication/prescription/renewal", "match", 0.60),
            ],
        )
        assert out["classification"]["primary"]["code"] == "-50"

    @pytest.mark.req("REQ-YG-551")
    def test_chapter_context_attached_to_process_primary(self):
        """F1: chapter_context is reducer-derived — best non-process
        candidate (match or partial), attached mechanically."""
        reducer = _load("reduce.py")
        out = _reduce(
            reducer,
            [
                _cand("-50", "Medication/prescription/renewal", "match", 0.9),
                _cand("K86", "Hypertension uncomplicated", "partial_match", 0.95),
                _cand("A97", "No disease", "partial_match", 0.5),
            ],
        )
        primary = out["classification"]["primary"]
        assert primary["code"] == "-50"
        assert primary["chapter_context"]["code"] == "K86"

    @pytest.mark.req("REQ-YG-551")
    def test_no_chapter_context_on_chapter_primary(self):
        reducer = _load("reduce.py")
        out = _reduce(
            reducer,
            [_cand("K86", "Hypertension uncomplicated", "match", 0.9)],
        )
        assert "chapter_context" not in out["classification"]["primary"]

    @pytest.mark.req("REQ-YG-551")
    def test_coverage_meta_declares_all_components(self):
        reducer = _load("reduce.py")
        out = _reduce(reducer, [_cand("-50", "Medication renewal", "match", 0.9)])
        assert out["meta"]["catalog_coverage"]["components"] == [
            1,
            2,
            3,
            4,
            5,
            6,
            7,
        ]
