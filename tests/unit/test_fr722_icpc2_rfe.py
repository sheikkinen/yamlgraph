"""FR-722 RED witness: ICPC-2 RFE classifier — catalog, contracts, reducer.

The example lives in examples/icpc-2-rfe/ (hyphenated dir → file-path
loading, judged pin); test imports use importlib file loading.

Three contracts condemned here:
- REQ-YG-548 catalog builder + provenance (ClaML parse, component from
  SuperClass, sha256 pin, verified-vs-provisional mechanics)
- REQ-YG-549 catalog loader (provisional exclusion default, actionable
  error when the generated catalog is absent)
- REQ-YG-550 reducer determinism (verdict rank → confidence → code total
  order, multi-label, low_confidence threshold on verdict, candidate
  validation at the boundary, evidence-span substring check)
"""

import importlib.util
import sys
from pathlib import Path

import pytest

EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "icpc-2-rfe"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _load(module_filename: str):
    path = EXAMPLE / "nodes" / module_filename
    assert path.exists(), f"FR-722 module missing: {path}"
    name = f"fr722_{module_filename.removesuffix('.py')}"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# REQ-YG-548 — builder: ClaML parse + provenance
# ---------------------------------------------------------------------------


class TestCatalogBuilder:
    @pytest.mark.req("REQ-YG-548")
    def test_parse_claml_excerpt(self):
        """3-row committed excerpt parses into catalog rows with all
        judged fields; component derived from SuperClass suffix."""
        builder = _load("build_catalog.py")
        xml_text = (FIXTURES / "icpc2_claml_excerpt.xml").read_text()
        rows = builder.parse_claml(xml_text)
        by_code = {r["code"]: r for r in rows}
        assert set(by_code) == {"R05", "R74", "A97"}

        r05 = by_code["R05"]
        assert r05["title"] == "Cough"
        assert r05["chapter"] == "R"
        assert r05["component"] == 1
        assert r05["cluster_id"] == "R-C1"
        assert "dry or moist" in r05["inclusion_terms"][0]
        assert any("R25" in x for x in r05["exclusion_terms"])
        assert r05["source_tier"] == 1
        assert r05["source_reference"] == "ICPC-2e-v7.0/R05"
        assert r05["provenance_status"] == "verified"

        assert by_code["R74"]["component"] == 7
        assert by_code["R74"]["cluster_id"] == "R-C7"

    @pytest.mark.req("REQ-YG-548")
    def test_chapters_and_process_codes_excluded(self):
        """Chapter headers and process codes (components 2–6) are not
        catalog rows — phase-1 purge list."""
        builder = _load("build_catalog.py")
        xml_text = (FIXTURES / "icpc2_claml_excerpt.xml").read_text()
        rows = builder.parse_claml(xml_text)
        codes = {r["code"] for r in rows}
        assert "R" not in codes, "chapter header leaked into catalog"
        assert "-30" not in codes, "process code leaked into catalog (phase 2)"

    @pytest.mark.req("REQ-YG-548")
    def test_sha256_mismatch_raises(self, tmp_path):
        """A tampered source zip must be refused, not parsed."""
        builder = _load("build_catalog.py")
        bad = tmp_path / "ICPC-2e-v7.0.zip"
        bad.write_bytes(b"not the source")
        with pytest.raises(ValueError, match="sha256"):
            builder.verify_source(bad)


# ---------------------------------------------------------------------------
# REQ-YG-549 — loader: provisional exclusion + actionable absence
# ---------------------------------------------------------------------------


class TestCatalogLoader:
    @pytest.mark.req("REQ-YG-549")
    def test_fixture_catalog_loads_clusters(self):
        """Committed paraphrased fixture groups into chapter×component
        clusters, each carrying its code list."""
        catalog = _load("catalog.py")
        state = {"catalog_path": str(EXAMPLE / "data" / "fixture_catalog.yaml")}
        clusters = catalog.load_rfe_catalog(state)
        ids = {c["cluster_id"] for c in clusters}
        assert "R-C1" in ids
        r_c1 = next(c for c in clusters if c["cluster_id"] == "R-C1")
        assert any(row["code"] == "R05" for row in r_c1["codes"])

    @pytest.mark.req("REQ-YG-549")
    def test_provisional_excluded_by_default(self):
        """F6: provisional rows are out unless include_provisional."""
        catalog = _load("catalog.py")
        path = str(EXAMPLE / "data" / "fixture_catalog.yaml")
        default_rows = [
            row
            for c in catalog.load_rfe_catalog({"catalog_path": path})
            for row in c["codes"]
        ]
        assert all(r["provenance_status"] == "verified" for r in default_rows)

        with_prov = [
            row
            for c in catalog.load_rfe_catalog(
                {"catalog_path": path, "include_provisional": True}
            )
            for row in c["codes"]
        ]
        assert any(r["provenance_status"] == "provisional" for r in with_prov)

    @pytest.mark.req("REQ-YG-549")
    def test_missing_catalog_actionable_error(self, tmp_path):
        """A1: absent generated catalog names the build step."""
        catalog = _load("catalog.py")
        with pytest.raises(FileNotFoundError, match="build_catalog"):
            catalog.load_rfe_catalog({"catalog_path": str(tmp_path / "missing.yaml")})


# ---------------------------------------------------------------------------
# REQ-YG-550 — reducer: deterministic policy
# ---------------------------------------------------------------------------

TRANSCRIPT = (
    "Patient calls because of a dry cough for two weeks, worse at night. "
    "Also asks about mild fever earlier this week."
)


def _cand(code, title, verdict, conf, spans=None):
    return {
        "code": code,
        "title": title,
        "verdict": verdict,
        "confidence": conf,
        "reasoning_short": f"{title} indicated.",
        "evidence_spans": spans if spans is not None else ["dry cough"],
        "missing_signals": [],
    }


def _reduce(reducer, candidates, transcript=TRANSCRIPT):
    state = {
        "map_results": [{"candidates": candidates}],
        "transcript": transcript,
    }
    return reducer.reduce_best_rfe(state)


class TestReducerPolicy:
    @pytest.mark.req("REQ-YG-550")
    def test_match_beats_partial_regardless_of_confidence(self):
        reducer = _load("reduce.py")
        out = _reduce(
            reducer,
            [
                _cand("A03", "Fever", "partial_match", 0.99, ["mild fever"]),
                _cand("R05", "Cough", "match", 0.6),
            ],
        )
        assert out["classification"]["primary"]["code"] == "R05"

    @pytest.mark.req("REQ-YG-550")
    def test_tie_break_confidence_then_code(self):
        reducer = _load("reduce.py")
        out = _reduce(
            reducer,
            [
                _cand("R05", "Cough", "match", 0.8),
                _cand("A03", "Fever", "match", 0.8, ["mild fever"]),
                _cand("R02", "Shortness of breath", "match", 0.9),
            ],
        )
        # 0.9 first; then 0.8 tie broken by code string: A03 < R05
        assert out["classification"]["primary"]["code"] == "R02"
        secondary = [c["code"] for c in out["classification"]["secondary"]]
        assert secondary == ["A03", "R05"]

    @pytest.mark.req("REQ-YG-550")
    def test_no_match_yields_low_confidence(self):
        """AC-06/F6: threshold is on the verdict — no forced match."""
        reducer = _load("reduce.py")
        out = _reduce(
            reducer,
            [
                _cand("A03", "Fever", "partial_match", 0.7, ["mild fever"]),
                _cand("R05", "Cough", "not_applicable", 0.9, []),
            ],
        )
        assert out["classification"]["primary"] is None
        assert out["classification"]["low_confidence"] is True
        best = [c["code"] for c in out["classification"]["best_partial"]]
        assert best == ["A03"]

    @pytest.mark.req("REQ-YG-550")
    def test_evidence_span_must_be_substring_of_transcript(self):
        """F3 guard: spans that don't occur in the input are a
        plausible_wrong_answer — refuse loudly."""
        reducer = _load("reduce.py")
        with pytest.raises(ValueError, match="evidence_span"):
            _reduce(
                reducer,
                [_cand("R05", "Cough", "match", 0.9, ["productive cough"])],
            )

    @pytest.mark.req("REQ-YG-550")
    def test_invalid_candidate_shape_raises(self):
        """Commandment 5: candidates validate at the reducer boundary."""
        reducer = _load("reduce.py")
        bad = {"code": "R05", "verdict": "definitely"}  # bad enum, fields gone
        with pytest.raises(ValueError, match="candidate"):
            _reduce(reducer, [bad])

    @pytest.mark.req("REQ-YG-550")
    def test_evidence_span_case_fold_tolerated(self):
        """Raw-read finding (field runs 3/6): the model lowercases span
        first-letters; case-insensitive containment still catches
        invented spans while tolerating case-folds."""
        reducer = _load("reduce.py")
        out = _reduce(
            reducer,
            [_cand("R05", "Cough", "match", 0.9, ["patient calls"])],
        )
        assert out["classification"]["primary"]["code"] == "R05"

    @pytest.mark.req("REQ-YG-550")
    def test_off_catalog_code_rejected(self):
        """AC-02: verdicts are drawn only from the catalog list."""
        reducer = _load("reduce.py")
        state = {
            "map_results": [{"candidates": [_cand("Q99", "Invented", "match", 0.9)]}],
            "transcript": TRANSCRIPT,
            "rfe_clusters": [{"cluster_id": "R-C1", "codes": [{"code": "R05"}]}],
        }
        with pytest.raises(ValueError, match="not in catalog"):
            reducer.reduce_best_rfe(state)

    @pytest.mark.req("REQ-YG-550")
    def test_duplicate_codes_deduped_keeping_best(self):
        """Raw-read finding (field run 3): a cluster emitted the same
        code twice → duplicate secondary entries. Keep best-ranked."""
        reducer = _load("reduce.py")
        out = _reduce(
            reducer,
            [
                _cand("R05", "Cough", "match", 0.9),
                _cand("R05", "Cough", "partial_match", 0.7),
                _cand("A03", "Fever", "match", 0.8, ["mild fever"]),
            ],
        )
        assert out["classification"]["primary"]["code"] == "R05"
        codes = [c["code"] for c in out["classification"]["secondary"]]
        assert codes == ["A03"], "duplicate R05 must not reappear"
        assert out["meta"]["candidates_total"] == 2

    @pytest.mark.req("REQ-YG-550")
    def test_near_miss_span_repaired_to_transcript_text(self):
        """Field run 8 (HP-36): one-character drift ("äitini" →
        "äitiini") survived two prompt hardenings — token fidelity is
        mechanizable, so the boundary REPAIRS near-miss claims to the
        true transcript substring."""
        reducer = _load("reduce.py")
        # transcript says "dry cough"; the model typed "dryy cough"
        out = _reduce(
            reducer,
            [_cand("R05", "Cough", "match", 0.9, ["a dryy cough for two weeks"])],
        )
        spans = out["classification"]["primary"]["evidence_spans"]
        assert len(spans) == 1
        assert spans[0] in TRANSCRIPT, "output span must be verbatim transcript"
        assert "dry cough" in spans[0]

    @pytest.mark.req("REQ-YG-550")
    def test_fabricated_span_still_rejected(self):
        """The repair floor (0.85) still refuses invented evidence."""
        reducer = _load("reduce.py")
        with pytest.raises(ValueError, match="evidence_span"):
            _reduce(
                reducer,
                [
                    _cand(
                        "R05",
                        "Cough",
                        "match",
                        0.9,
                        ["patient reports severe chest pain radiating to the arm"],
                    )
                ],
            )

    @pytest.mark.req("REQ-YG-550")
    def test_output_meta_declares_coverage(self):
        """Coverage honesty pin: a no-match must be interpretable."""
        reducer = _load("reduce.py")
        out = _reduce(reducer, [_cand("R05", "Cough", "match", 0.9)])
        assert out["meta"]["catalog_version"] == "ICPC-2e-v7.0"
        assert out["meta"]["catalog_coverage"]["components"] == [1, 7]
