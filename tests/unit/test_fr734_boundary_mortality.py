"""FR-734 RED witness: boundary run-mortality — off-catalog claims and
interior-omission spans (REQ-YG-561).

Two defect classes from the FR-733 baseline (19/33 runs killed),
recounted at judgement (8 catalog kills / 11 span kills — the span
class dominates):

- Off-population claims: real catalog rows without view-699 membership
  (the model volunteers famous MITRE-Discouraged Classes from prior
  knowledge) divert to meta.off_population_claims; classification slots
  stay population-only (F3: FR-733's AC-02 pin preserved verbatim);
  nonexistent codes still raise.
- Interior-omission spans: claims whose characters are 100% present in
  ≤2 contiguous blocks (elided enumeration markers, list segments,
  tense drift) REPAIR to the true contiguous window (F2); scattered
  fabrications still die (window cap is the load-bearing guard).
"""

import importlib.util
import sys
from pathlib import Path

import pytest

EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "cwe-classifier"


def _load(module_filename: str):
    path = EXAMPLE / "nodes" / module_filename
    assert path.exists(), f"FR-734 module missing: {path}"
    name = f"fr734_{module_filename.removesuffix('.py')}"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


DESCRIPTION = (
    "The (1) TLS and (2) DTLS implementations in OpenSSL do not properly "
    "handle Heartbeat Extension packets via a crafted Content-Type, "
    "Content-Disposition, or Content-Length HTTP header, allowing "
    "attackers to inject arbitrary JavaScript into the page."
)

_ROWS = [
    {"code": "CWE-79", "mapping_usage": "Allowed", "parents": ["CWE-707"]},
    {"code": "CWE-707", "mapping_usage": "Allowed", "parents": []},
]

_CLUSTERS = [
    {
        "cluster_id": "CAT-137",
        "catalog_version": "cwec_v4.20",
        "coverage": {
            "view": 699,
            "candidates": 2,
            "excluded_prohibited": 1,
            "catalog_total": 5,
        },
        "codes": _ROWS,
    }
]

# F4: full-catalog usage lookup shipped by the loader as a state key.
_USAGE_INDEX = {
    "CWE-79": "Allowed",
    "CWE-707": "Allowed",
    "CWE-119": "Discouraged",  # famous junk drawer, no view-699 membership
    "CWE-122": "Allowed",  # real row, off-view
    "CWE-441": "Prohibited",  # stripped at build, still a catalog row
}


def _cand(code, title, verdict, conf, spans=None):
    return {
        "code": code,
        "title": title,
        "verdict": verdict,
        "confidence": conf,
        "reasoning_short": f"{title} indicated.",
        "evidence_spans": spans
        if spans is not None
        else ["inject arbitrary JavaScript"],
        "missing_signals": [],
    }


def _reduce(reducer, candidates, description=DESCRIPTION):
    state = {
        "map_results": [{"candidates": candidates}],
        "description": description,
        "cwe_clusters": _CLUSTERS,
        "usage_index": _USAGE_INDEX,
    }
    return reducer.reduce_best_cwe(state)


# ---------------------------------------------------------------------------
# Off-population claims → meta, never slots (F3)
# ---------------------------------------------------------------------------


class TestOffPopulationClaims:
    @pytest.mark.req("REQ-YG-561")
    def test_off_population_claim_diverted_to_meta(self):
        """AC-01: a volunteered CWE-119 no longer kills the run — it is
        recorded in meta.off_population_claims with its usage; the
        classification carries only population members."""
        reducer = _load("reduce.py")
        out = _reduce(
            reducer,
            [
                _cand("CWE-79", "XSS", "match", 0.9),
                _cand("CWE-119", "Buffer Bounds", "match", 0.95),
            ],
        )
        cls = out["classification"]
        assert cls["primary"]["code"] == "CWE-79"
        slot_codes = (
            {cls["primary"]["code"]}
            | {c["code"] for c in cls["secondary"]}
            | {c["code"] for c in cls["best_partial"]}
        )
        assert "CWE-119" not in slot_codes
        claims = out["meta"]["off_population_claims"]
        assert len(claims) == 1
        assert claims[0]["code"] == "CWE-119"
        assert claims[0]["usage"] == "Discouraged"
        assert claims[0]["verdict"] == "match"

    @pytest.mark.req("REQ-YG-561")
    def test_prohibited_claim_never_in_slots_even_alone(self):
        """AC-03: a lone volunteered Prohibited code yields an honest
        low_confidence result with the claim in meta only."""
        reducer = _load("reduce.py")
        out = _reduce(
            reducer,
            [_cand("CWE-441", "Confused Deputy", "match", 0.9)],
        )
        cls = out["classification"]
        assert cls["primary"] is None
        assert cls["low_confidence"] is True
        assert cls["best_partial"] == []
        claims = out["meta"]["off_population_claims"]
        assert claims[0]["code"] == "CWE-441"
        assert claims[0]["usage"] == "Prohibited"

    @pytest.mark.req("REQ-YG-561")
    def test_nonexistent_code_still_raises(self):
        """AC-02: fabricated codes (no catalog row anywhere) stay fatal."""
        reducer = _load("reduce.py")
        with pytest.raises(ValueError, match="not in catalog"):
            _reduce(reducer, [_cand("CWE-99999", "Invented", "match", 0.9)])

    @pytest.mark.req("REQ-YG-561")
    def test_off_population_span_best_effort_never_fatal(self):
        """F3: an unalignable span on a meta-tier claim is recorded raw
        with span_unverified — the run completes."""
        reducer = _load("reduce.py")
        out = _reduce(
            reducer,
            [
                _cand("CWE-79", "XSS", "match", 0.9),
                _cand(
                    "CWE-122",
                    "Heap Overflow",
                    "match",
                    0.8,
                    ["a completely invented quotation about heap metadata"],
                ),
            ],
        )
        claims = out["meta"]["off_population_claims"]
        assert claims[0]["code"] == "CWE-122"
        assert claims[0]["span_unverified"] is True

    @pytest.mark.req("REQ-YG-561")
    def test_empty_off_population_list_when_all_in_population(self):
        """The audit key is always present — empty is honest."""
        reducer = _load("reduce.py")
        out = _reduce(reducer, [_cand("CWE-79", "XSS", "match", 0.9)])
        assert out["meta"]["off_population_claims"] == []


# ---------------------------------------------------------------------------
# Interior-omission span repair (F2)
# ---------------------------------------------------------------------------


class TestInteriorOmissionRepair:
    @pytest.mark.req("REQ-YG-561")
    def test_enumeration_marker_omission_repaired(self):
        """Heartbleed shape: '(1) TLS and (2) DTLS' claimed without the
        markers — repairs to the true contiguous window."""
        reducer = _load("reduce.py")
        out = _reduce(
            reducer,
            [_cand("CWE-79", "XSS", "match", 0.9, ["TLS and DTLS implementations"])],
        )
        span = out["classification"]["primary"]["evidence_spans"][0]
        assert span in DESCRIPTION
        assert "(2)" in span, "repair must restore the elided text verbatim"

    @pytest.mark.req("REQ-YG-561")
    def test_list_segment_omission_repaired(self):
        """Struts shape: 'crafted Content-Length HTTP header' claimed,
        eliding 'Content-Type, Content-Disposition, or' — repairs to
        the full verbatim list."""
        reducer = _load("reduce.py")
        out = _reduce(
            reducer,
            [
                _cand(
                    "CWE-79",
                    "XSS",
                    "match",
                    0.9,
                    ["crafted Content-Length HTTP header"],
                )
            ],
        )
        span = out["classification"]["primary"]["evidence_spans"][0]
        assert span in DESCRIPTION
        assert "Content-Disposition" in span

    @pytest.mark.req("REQ-YG-561")
    def test_scattered_fabrication_still_raises(self):
        """The window cap is the load-bearing guard: characters present
        but scattered across the description are a fabrication."""
        reducer = _load("reduce.py")
        with pytest.raises(ValueError, match="evidence_span"):
            _reduce(
                reducer,
                [
                    _cand(
                        "CWE-79",
                        "XSS",
                        "match",
                        0.9,
                        ["TLS implementations inject arbitrary headers"],
                    )
                ],
            )

    @pytest.mark.req("REQ-YG-561")
    def test_one_char_drift_still_repaired(self):
        """FR-733 regression guard: the pre-existing single-block shapes
        keep repairing under the multi-block mechanism."""
        reducer = _load("reduce.py")
        out = _reduce(
            reducer,
            [_cand("CWE-79", "XSS", "match", 0.9, ["inject arbitary JavaScript"])],
        )
        span = out["classification"]["primary"]["evidence_spans"][0]
        assert span in DESCRIPTION
        assert "arbitrary" in span

    @pytest.mark.req("REQ-YG-561")
    def test_decoy_occurrence_does_not_steal_the_anchor(self):
        """AC-05 residual (re-baseline read): Spring4Shell's 'running on
        JDK 9+' stole the 'running' block from 'to run on Tomcat as a
        WAR deployment' 137 chars away, blowing the window cap on a
        claim that repairs perfectly around its largest block. Matching
        must re-anchor LOCALLY around the longest block."""
        reducer = _load("reduce.py")
        description = (
            "A Spring application running on JDK 9+ may be vulnerable to "
            "remote code execution via data binding. The specific exploit "
            "requires the application to run on Tomcat as a WAR deployment "
            "with attackers able to inject arbitrary JavaScript."
        )
        out = _reduce(
            reducer,
            [
                _cand(
                    "CWE-79",
                    "XSS",
                    "match",
                    0.9,
                    ["running on Tomcat as a WAR deployment"],
                )
            ],
            description=description,
        )
        span = out["classification"]["primary"]["evidence_spans"][0]
        assert span in description
        assert "Tomcat as a WAR deployment" in span
        assert "JDK" not in span


# ---------------------------------------------------------------------------
# Loader ships usage_index (F4)
# ---------------------------------------------------------------------------


class TestLoaderUsageIndex:
    @pytest.mark.req("REQ-YG-561")
    def test_loader_returns_merged_dict_with_usage_index(self):
        """The loader returns {cwe_clusters, usage_index} (merged-dict
        node precedent); the index covers ALL catalog rows including
        the Prohibited row that has no cluster membership."""
        catalog = _load("catalog.py")
        state = {"catalog_path": str(EXAMPLE / "data" / "fixture_catalog.yaml")}
        out = catalog.load_cwe_clusters(state)
        assert set(out) == {"cwe_clusters", "usage_index"}
        assert out["usage_index"]["CWE-441"] == "Prohibited"
        assert out["usage_index"]["CWE-79"] == "Allowed"
        assert {c["cluster_id"] for c in out["cwe_clusters"]} == {
            "CAT-137",
            "CAT-1019",
        }
