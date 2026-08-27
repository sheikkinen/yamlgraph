"""FR-895 RED: census brief citation boundary — fail-closed witnesses.

The synthesis LLM emits structured claim blocks; the LLM-free boundary
validates every citation against the source artifact BEFORE any markdown
is rendered (R-1). On failure: no brief, a .REJECTED.md failure artifact
with the deterministic summary head and reasons (R-2). Synthesis input is
bounded and column-allowlisted before the call (R-4/R-5).
"""

import pytest

# References examples/ (process boundary, FR-756)
pytestmark = pytest.mark.process

SOURCE_ROWS = [
    {"label": "downstream_fix", "entries": 118, "citations": ["a.md", "b.md"]},
    {"label": "plausible_wrong_answer", "entries": 104, "citations": ["c.md"]},
    {"label": "audit_as_ritual", "entries": 104, "citations": ["d.md"]},
    {"label": "quick_confidence", "entries": 42, "citations": ["e.md"]},
]

GOOD_CLAIMS = [
    {
        "claim_id": "c1",
        "text": "The most recurrent trap is fixing at the symptom site.",
        "citations": ["label:downstream_fix"],
        "confidence": 0.9,
    },
    {
        "claim_id": "c2",
        "text": "Plausible wrong answers and audit ritual recur equally.",
        "citations": ["label:plausible_wrong_answer", "label:audit_as_ritual"],
        "confidence": 0.8,
    },
]


def _boundary(claims, rows=None):
    from examples.demos.corpus_census.adapters.census_brief import (
        validate_claims,
    )

    return validate_claims(claims, rows if rows is not None else SOURCE_ROWS)


class TestCitationBoundary:
    @pytest.mark.req("REQ-YG-625")
    def test_valid_claims_pass(self):
        assert _boundary(GOOD_CLAIMS) == []

    @pytest.mark.req("REQ-YG-625")
    def test_fabricated_label_citation_rejected(self):
        bad = GOOD_CLAIMS + [
            {
                "claim_id": "c3",
                "text": "Ghost trap dominates.",
                "citations": ["label:ghost_trap_never_seen"],
            }
        ]
        errors = _boundary(bad)
        assert errors and "ghost_trap_never_seen" in str(errors)

    @pytest.mark.req("REQ-YG-625")
    def test_claim_without_citation_rejected(self):
        bad = GOOD_CLAIMS + [
            {"claim_id": "c3", "text": "Everything is fine.", "citations": []}
        ]
        errors = _boundary(bad)
        assert errors and "c3" in str(errors)

    @pytest.mark.req("REQ-YG-625")
    def test_citation_outside_source_rejected(self):
        bad = [
            {
                "claim_id": "c1",
                "text": "Row citation to a foreign artifact.",
                "citations": ["row:docs/other/thing.md"],
            }
        ]
        errors = _boundary(bad)
        assert errors

    @pytest.mark.req("REQ-YG-625")
    def test_malformed_claim_rejected(self):
        errors = _boundary([{"text": "no id, no citations"}])
        assert errors


class TestBriefEmission:
    def _emit(self, tmp_path, claims, rows=None):
        from examples.demos.corpus_census.adapters.census_brief import (
            emit_brief,
        )

        return emit_brief(
            claims,
            rows if rows is not None else SOURCE_ROWS,
            str(tmp_path / "brief-2026-08-27.md"),
            run_meta={"model": "test-model", "source_hash": "abc123"},
        )

    @pytest.mark.req("REQ-YG-625")
    def test_accepted_brief_contains_head_narrative_and_meta(self, tmp_path):
        result = self._emit(tmp_path, GOOD_CLAIMS)
        assert result["accepted"] is True
        text = (tmp_path / "brief-2026-08-27.md").read_text()
        assert "downstream_fix" in text  # deterministic summary head
        assert "symptom site" in text  # rendered narrative
        assert "test-model" in text and "abc123" in text  # provenance

    @pytest.mark.req("REQ-YG-625")
    def test_rejected_narrative_emits_no_brief_only_failure_artifact(self, tmp_path):
        bad = [
            {
                "claim_id": "c1",
                "text": "Ghost claim.",
                "citations": ["label:ghost"],
            }
        ]
        result = self._emit(tmp_path, bad)
        assert result["accepted"] is False
        assert not (tmp_path / "brief-2026-08-27.md").exists()
        rejected = tmp_path / "brief-2026-08-27.REJECTED.md"
        assert rejected.exists()
        text = rejected.read_text()
        assert "downstream_fix" in text  # summary head still present
        assert "ghost" in text  # rejection reason cited


class TestBoundedPublicSafeInput:
    @pytest.mark.req("REQ-YG-625")
    def test_input_bounded_by_ceiling_top_n(self):
        from examples.demos.corpus_census.adapters.census_brief import (
            build_synthesis_input,
        )

        out = build_synthesis_input(SOURCE_ROWS, max_rows=2)
        assert len(out) == 2
        assert out[0]["label"] == "downstream_fix"  # top-N by entries

    @pytest.mark.req("REQ-YG-625")
    def test_disallowed_columns_stripped(self):
        from examples.demos.corpus_census.adapters.census_brief import (
            build_synthesis_input,
        )

        rows = [
            {
                "label": "x",
                "entries": 5,
                "evidence_span": "RAW SECRET SPAN",
                "citations": ["a.md"],
            }
        ]
        out = build_synthesis_input(rows, max_rows=10)
        assert "evidence_span" not in out[0]  # public-safe allowlist (R-5)
