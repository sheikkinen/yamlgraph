"""FR-733 RED witness: CWE vulnerability classifier — second instance of
reference/patterns/coded-classification.md.

Four contracts condemned here:
- REQ-YG-557 catalog builder (cwec_v4.20 parse, versioned pin + sha256,
  Deprecated skip, view-699 clustering with multi-membership
  duplication, Prohibited stripped from candidacy at BUILD time (F3),
  two-level usage-count pins (F5))
- REQ-YG-558 catalog loader (category clusters, Description-only
  briefs, actionable error when the generated catalog is absent)
- REQ-YG-559 reducer (span-alignment boundary, CWE- prefix repair,
  Discouraged demote-not-drop, Allowed-with-Review flag, lowest-
  abstraction guard both directions (F2), Prohibited rejection,
  dedup, low_confidence, coverage meta)
- REQ-YG-560 crosscheck harness (NVD gold labels, usage-partitioned
  disagreements: our_miss vs label_questionable; gold_unscoreable when
  every gold code is MITRE-Discouraged/Prohibited)
"""

import importlib.util
import sys
from pathlib import Path

import pytest

EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "cwe-classifier"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _load(module_filename: str):
    path = EXAMPLE / "nodes" / module_filename
    assert path.exists(), f"FR-733 module missing: {path}"
    name = f"fr733_{module_filename.removesuffix('.py')}"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# REQ-YG-557 — builder: cwec parse + provenance + candidacy
# ---------------------------------------------------------------------------


class TestCatalogBuilder:
    @pytest.mark.req("REQ-YG-557")
    def test_parse_cwec_excerpt(self):
        """Committed excerpt parses into catalog rows with all judged
        fields; Deprecated rows are skipped entirely."""
        builder = _load("build_catalog.py")
        payload = builder.parse_cwec((FIXTURES / "cwe_excerpt.xml").read_text())
        by_code = {r["code"]: r for r in payload["rows"]}
        assert set(by_code) == {
            "CWE-79",
            "CWE-89",
            "CWE-20",
            "CWE-707",
            "CWE-94",
            "CWE-441",
        }, "Deprecated CWE-365 must be skipped"

        xss = by_code["CWE-79"]
        assert "Cross-site Scripting" in xss["title"]
        assert xss["abstraction"] == "Base"
        assert xss["mapping_usage"] == "Allowed"
        assert "user-controllable input" in xss["description"]
        assert xss["parents"] == ["CWE-707"]
        assert xss["source_tier"] == 1
        assert xss["source_reference"] == "cwec_v4.20/CWE-79"

    @pytest.mark.req("REQ-YG-557")
    def test_multi_membership_duplicated_view_1000_ignored(self):
        """Judged pin: a code in N view-699 categories appears in each
        cluster list; Has_Member rows from other views never count."""
        builder = _load("build_catalog.py")
        payload = builder.parse_cwec((FIXTURES / "cwe_excerpt.xml").read_text())
        by_code = {r["code"]: r for r in payload["rows"]}
        assert by_code["CWE-79"]["cluster_ids"] == ["CAT-137", "CAT-1019"]
        # CWE-89's CAT-1019 membership is View_ID=1000 — must not count.
        assert by_code["CWE-89"]["cluster_ids"] == ["CAT-137"]

    @pytest.mark.req("REQ-YG-557")
    def test_prohibited_stripped_from_candidacy_at_build(self):
        """F3: Prohibited codes stay catalog rows (completeness) but
        get NO cluster membership — never shown to the model."""
        builder = _load("build_catalog.py")
        payload = builder.parse_cwec((FIXTURES / "cwe_excerpt.xml").read_text())
        by_code = {r["code"]: r for r in payload["rows"]}
        assert by_code["CWE-441"]["mapping_usage"] == "Prohibited"
        assert by_code["CWE-441"]["cluster_ids"] == []
        # Discouraged keeps candidacy (cap happens in the reducer).
        assert by_code["CWE-20"]["cluster_ids"] == ["CAT-137"]

    @pytest.mark.req("REQ-YG-557")
    def test_coverage_meta_declares_candidate_population(self):
        """F1: coverage declares view, candidates, excluded_prohibited,
        catalog_total — a no-match is interpretable."""
        builder = _load("build_catalog.py")
        payload = builder.parse_cwec((FIXTURES / "cwe_excerpt.xml").read_text())
        assert payload["catalog_version"] == "cwec_v4.20"
        assert payload["coverage"] == {
            "view": 699,
            "candidates": 5,  # 6 view-699 members minus 1 Prohibited
            "excluded_prohibited": 1,
            "catalog_total": 6,  # live rows (Deprecated skipped)
        }

    @pytest.mark.req("REQ-YG-557")
    def test_usage_pins_loud_on_mismatch(self):
        """F5: two-level count pins — a catalog bump that shifts
        MITRE's curation raises, never drifts silently."""
        builder = _load("build_catalog.py")
        payload = builder.parse_cwec((FIXTURES / "cwe_excerpt.xml").read_text())
        with pytest.raises(ValueError, match="pin"):
            builder.check_pins(payload)

    @pytest.mark.req("REQ-YG-557")
    def test_sha256_mismatch_raises(self, tmp_path):
        """A tampered/moved source zip must be refused, not parsed
        (cwec_latest is a moving pointer — versioned pin only)."""
        builder = _load("build_catalog.py")
        bad = tmp_path / "cwec_v4.20.xml.zip"
        bad.write_bytes(b"not the source")
        with pytest.raises(ValueError, match="sha256"):
            builder.verify_source(bad)


# ---------------------------------------------------------------------------
# REQ-YG-558 — loader: category clusters + actionable absence
# ---------------------------------------------------------------------------


class TestCatalogLoader:
    @pytest.mark.req("REQ-YG-558")
    def test_fixture_catalog_loads_clusters(self):
        """Committed fixture groups into view-699 category clusters;
        multi-membership codes appear in every member cluster."""
        catalog = _load("catalog.py")
        state = {"catalog_path": str(EXAMPLE / "data" / "fixture_catalog.yaml")}
        clusters = catalog.load_cwe_clusters(state)
        by_id = {c["cluster_id"]: c for c in clusters}
        assert set(by_id) == {"CAT-137", "CAT-1019"}
        cat137 = {row["code"] for row in by_id["CAT-137"]["codes"]}
        assert cat137 == {
            "CWE-79",
            "CWE-89",
            "CWE-20",
        }, "Prohibited CWE-441 must never reach a cluster brief"
        assert "CWE-79" in {r["code"] for r in by_id["CAT-1019"]["codes"]}

    @pytest.mark.req("REQ-YG-558")
    def test_brief_is_description_only(self):
        """F4: briefs render code — title | description; no usage or
        abstraction noise (caps are code-side, not the model's job)."""
        catalog = _load("catalog.py")
        state = {"catalog_path": str(EXAMPLE / "data" / "fixture_catalog.yaml")}
        clusters = catalog.load_cwe_clusters(state)
        brief = next(c for c in clusters if c["cluster_id"] == "CAT-137")["brief"]
        assert "CWE-79" in brief
        assert "user-controllable input" in brief
        assert "Discouraged" not in brief
        assert "Base" not in brief.split("|")[0]

    @pytest.mark.req("REQ-YG-558")
    def test_missing_catalog_actionable_error(self, tmp_path):
        """Absent generated catalog names the build step."""
        catalog = _load("catalog.py")
        with pytest.raises(FileNotFoundError, match="build_catalog"):
            catalog.load_cwe_clusters({"catalog_path": str(tmp_path / "nope.yaml")})


# ---------------------------------------------------------------------------
# REQ-YG-559 — reducer: deterministic policy
# ---------------------------------------------------------------------------

DESCRIPTION = (
    "The application fails to sanitize user input in the search field, "
    "allowing attackers to inject arbitrary JavaScript that executes in "
    "the victim's browser session."
)

_ROWS = [
    {"code": "CWE-79", "mapping_usage": "Allowed", "parents": ["CWE-707"]},
    {"code": "CWE-89", "mapping_usage": "Allowed", "parents": ["CWE-707"]},
    {"code": "CWE-20", "mapping_usage": "Discouraged", "parents": []},
    {"code": "CWE-707", "mapping_usage": "Allowed", "parents": []},
    {"code": "CWE-94", "mapping_usage": "Allowed-with-Review", "parents": ["CWE-707"]},
]

_CLUSTERS = [
    {
        "cluster_id": "CAT-137",
        "catalog_version": "cwec_v4.20",
        "coverage": {
            "view": 699,
            "candidates": 5,
            "excluded_prohibited": 1,
            "catalog_total": 6,
        },
        "codes": _ROWS,
    }
]


def _cand(code, title, verdict, conf, spans=None):
    return {
        "code": code,
        "title": title,
        "verdict": verdict,
        "confidence": conf,
        "reasoning_short": f"{title} indicated.",
        "evidence_spans": spans if spans is not None else ["sanitize user input"],
        "missing_signals": [],
    }


def _reduce(reducer, candidates, description=DESCRIPTION):
    state = {
        "map_results": [{"candidates": candidates}],
        "description": description,
        "cwe_clusters": _CLUSTERS,
    }
    return reducer.reduce_best_cwe(state)


class TestReducerPolicy:
    @pytest.mark.req("REQ-YG-559")
    def test_match_beats_partial_and_span_boundary_holds(self):
        """Copy-adapted icpc discipline: rank order + verbatim spans."""
        reducer = _load("reduce.py")
        out = _reduce(
            reducer,
            [
                _cand("CWE-89", "SQL Injection", "partial_match", 0.99),
                _cand("CWE-79", "XSS", "match", 0.6, ["inject arbitrary JavaScript"]),
            ],
        )
        assert out["classification"]["primary"]["code"] == "CWE-79"

    @pytest.mark.req("REQ-YG-559")
    def test_near_miss_span_repaired_fabrication_rejected(self):
        """Same _align_span floor as icpc (two-strike-split boundary)."""
        reducer = _load("reduce.py")
        out = _reduce(
            reducer,
            [_cand("CWE-79", "XSS", "match", 0.9, ["sanitze user input"])],
        )
        assert out["classification"]["primary"]["evidence_spans"][0] in DESCRIPTION
        with pytest.raises(ValueError, match="evidence_span"):
            _reduce(
                reducer,
                [_cand("CWE-79", "XSS", "match", 0.9, ["heap buffer overflow in"])],
            )

    @pytest.mark.req("REQ-YG-559")
    def test_bare_numeric_code_repaired_to_cwe_prefix(self):
        """Sigil analog (FR-724 field finding): models emit '79' for
        'CWE-79' — repair mechanically when the prefixed form IS in
        the catalog; anything else is an invention and raises."""
        reducer = _load("reduce.py")
        out = _reduce(reducer, [_cand("79", "XSS", "match", 0.9)])
        assert out["classification"]["primary"]["code"] == "CWE-79"

    @pytest.mark.req("REQ-YG-559")
    def test_prohibited_or_invented_code_rejected(self):
        """AC-02: Prohibited codes are never candidates — they are not
        in any cluster, so a model that invents one is refused."""
        reducer = _load("reduce.py")
        with pytest.raises(ValueError, match="not in catalog"):
            _reduce(reducer, [_cand("CWE-441", "Confused Deputy", "match", 0.9)])

    @pytest.mark.req("REQ-YG-559")
    def test_discouraged_match_demoted_not_dropped(self):
        """F3 / FR-727 mechanism: a Discouraged match demotes to
        partial with evidence preserved; primary is unreachable."""
        reducer = _load("reduce.py")
        out = _reduce(
            reducer,
            [_cand("CWE-20", "Improper Input Validation", "match", 0.95)],
        )
        cls = out["classification"]
        assert cls["primary"] is None
        assert cls["low_confidence"] is True
        assert cls["best_partial"][0]["code"] == "CWE-20"

    @pytest.mark.req("REQ-YG-559")
    def test_review_flagged_match_stays_primary_capable(self):
        """F3: Allowed-with-Review is flagged, NOT demoted — review is
        a first-class outcome in the analyst-assistance posture."""
        reducer = _load("reduce.py")
        out = _reduce(reducer, [_cand("CWE-94", "Code Injection", "match", 0.9)])
        primary = out["classification"]["primary"]
        assert primary["code"] == "CWE-94"
        assert primary["review"] is True

    @pytest.mark.req("REQ-YG-559")
    def test_base_match_demotes_matched_class_parent(self):
        """F2 direction 1: CWE-79 (Base) match demotes its matched
        ChildOf ancestor CWE-707 (Class) to partial."""
        reducer = _load("reduce.py")
        out = _reduce(
            reducer,
            [
                _cand("CWE-707", "Improper Neutralization", "match", 0.95),
                _cand("CWE-79", "XSS", "match", 0.8),
            ],
        )
        cls = out["classification"]
        assert cls["primary"]["code"] == "CWE-79"
        assert [c["code"] for c in cls["secondary"]] == []
        assert "CWE-707" in {c["code"] for c in cls["best_partial"]}

    @pytest.mark.req("REQ-YG-559")
    def test_lone_class_match_survives(self):
        """F2 direction 2: a Class match with no matched descendant
        stays primary — the rule never fires alone."""
        reducer = _load("reduce.py")
        out = _reduce(
            reducer,
            [_cand("CWE-707", "Improper Neutralization", "match", 0.7)],
        )
        assert out["classification"]["primary"]["code"] == "CWE-707"

    @pytest.mark.req("REQ-YG-559")
    def test_dedup_and_coverage_meta(self):
        """Per-code dedup keeps best-ranked; meta carries the builder's
        coverage block plus fan-out accounting."""
        reducer = _load("reduce.py")
        out = _reduce(
            reducer,
            [
                _cand("CWE-79", "XSS", "match", 0.9),
                _cand("CWE-79", "XSS", "partial_match", 0.6),
            ],
        )
        assert out["meta"]["candidates_total"] == 1
        assert out["meta"]["catalog_version"] == "cwec_v4.20"
        assert out["meta"]["catalog_coverage"]["view"] == 699
        assert out["meta"]["catalog_coverage"]["candidates"] == 5


# ---------------------------------------------------------------------------
# REQ-YG-560 — crosscheck harness: NVD gold + usage partition
# ---------------------------------------------------------------------------

_USAGE = {
    "CWE-79": "Allowed",
    "CWE-917": "Allowed",
    "CWE-20": "Discouraged",
    "CWE-755": "Discouraged",
}


def _result(primary=None, secondary=(), low_confidence=False):
    return {
        "classification": {
            "primary": {"code": primary} if primary else None,
            "secondary": [{"code": c} for c in secondary],
            "low_confidence": low_confidence,
            "best_partial": [],
        },
        "meta": {"catalog_version": "cwec_v4.20"},
    }


class TestCrosscheckHarness:
    @pytest.mark.req("REQ-YG-560")
    def test_labels_load_with_rationale_and_nvd_gold(self):
        """The 11 committed fixtures load; every label carries cve_id,
        nvd_cwes and a provenance rationale comment."""
        crosscheck = _load("crosscheck.py")
        labels = crosscheck.load_labels()
        assert len(labels) >= 10
        log4shell = labels["cve-2021-44228"]
        assert log4shell["cve_id"] == "CVE-2021-44228"
        assert set(log4shell["nvd_cwes"]) == {"CWE-20", "CWE-917"}
        assert "nvd.nist.gov" in log4shell["rationale"]

    @pytest.mark.req("REQ-YG-560")
    def test_discouraged_gold_miss_is_label_questionable(self):
        """Addendum protocol: Log4Shell result surfacing CWE-917 but
        not the Discouraged CWE-20 PASSES; the CWE-20 miss is
        partitioned as label_questionable, never our_miss."""
        crosscheck = _load("crosscheck.py")
        label = {"cve_id": "CVE-2021-44228", "nvd_cwes": ["CWE-20", "CWE-917"]}
        ev = crosscheck.evaluate_result(label, _result("CWE-917"), _USAGE)
        assert ev["passed"] is True
        assert ev["label_questionable"] == ["CWE-20"]
        assert ev["our_miss"] == []

    @pytest.mark.req("REQ-YG-560")
    def test_allowed_gold_miss_is_our_miss(self):
        """A miss on an Allowed gold code fails the fixture."""
        crosscheck = _load("crosscheck.py")
        label = {"cve_id": "CVE-2024-49038", "nvd_cwes": ["CWE-79"]}
        ev = crosscheck.evaluate_result(label, _result("CWE-89"), _USAGE)
        assert ev["passed"] is False
        assert ev["our_miss"] == ["CWE-79"]

    @pytest.mark.req("REQ-YG-560")
    def test_all_discouraged_gold_is_unscoreable_not_failed(self):
        """Drupalgeddon2/Struts: every gold code violates MITRE
        guidance → gold_unscoreable (reported for human read), never a
        mechanical pass or fail."""
        crosscheck = _load("crosscheck.py")
        label = {"cve_id": "CVE-2018-7600", "nvd_cwes": ["CWE-20"]}
        ev = crosscheck.evaluate_result(label, _result("CWE-94"), _USAGE)
        assert ev["passed"] is None
        assert ev["gold_unscoreable"] is True
        assert ev["our_primary"] == "CWE-94"
