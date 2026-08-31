"""FR-943 REDs: corpus_census reducer — row-level failure containment.

Attributable model-owned failures (map-error findings, error-string
judgements, model-owned envelope ValidationErrors) become contained
fail-closed rows instead of aborting the batch; structural
impossibilities stay batch-fatal (FR-892 preserved).
"""

import json
from pathlib import Path

import pytest

from examples.demos.corpus_census.tools import reduce_ledger

# References examples/ (process boundary, FR-756)
pytestmark = pytest.mark.process

FIXTURE = Path(__file__).parent.parent / "fixtures" / "fr943_incident_map_errors.json"

ITEMS = ["corpus/a.txt", "corpus/b.txt", "corpus/c.txt"]


def _good(index: int) -> dict:
    return {
        "source_index": index,
        "judgement": "steering",
        "confidence": 0.9,
        "evidence_span": f"evidence {index}",
        "abstained": False,
        "abstain_reason": "",
    }


def _run(tmp_path, findings, items=ITEMS):
    out = str(tmp_path / "ledger.md")
    return reduce_ledger(
        {"items": list(items), "findings": findings, "output_path": out}
    )


def _rows(tmp_path) -> list[dict]:
    return [
        json.loads(line)
        for line in (tmp_path / "ledger.jsonl").read_text().splitlines()
    ]


class TestContainment:
    @pytest.mark.req("REQ-YG-634")
    def test_map_error_finding_contained(self, tmp_path):
        """AC-02: one _error finding yields one failed row, peers unchanged."""
        findings = [_good(0), {"_map_index": 1, "_error": "boom"}, _good(2)]
        result = _run(tmp_path, findings)["ledger"]
        assert result["rows"] == 3
        rows = _rows(tmp_path)
        failed = [r for r in rows if r["abstain_reason"].startswith("row failed: ")]
        assert len(failed) == 1
        row = failed[0]
        assert row["item_ref"] == "corpus/b.txt"
        assert row["judgement"] == "abstain"
        assert row["abstained"] is True
        assert row["confidence"] == 0.0
        assert row["evidence_span"] == ""
        assert row["repaired"] is False
        assert row["abstain_reason"] == "row failed: boom"
        assert row["raw_judgement"] == "boom"
        peers = [r for r in rows if r["item_ref"] != "corpus/b.txt"]
        assert all(r["judgement"] == "steering" for r in peers)

    @pytest.mark.req("REQ-YG-634")
    def test_error_string_judgement_contained(self, tmp_path):
        """AC-03: error-string judgement becomes a failed row, raw preserved."""
        bad = {**_good(1), "judgement": "Error: search failed"}
        _run(tmp_path, [_good(0), bad, _good(2)])
        rows = _rows(tmp_path)
        failed = [r for r in rows if r["abstain_reason"].startswith("row failed: ")]
        assert len(failed) == 1
        assert failed[0]["abstain_reason"] == (
            "row failed: judgement is an error string"
        )
        assert failed[0]["raw_judgement"] == "Error: search failed"

    @pytest.mark.req("REQ-YG-634")
    def test_confidence_none_contained(self, tmp_path):
        """AC-05: model-owned envelope ValidationError becomes a failed row."""
        bad = {**_good(1), "confidence": None}
        _run(tmp_path, [_good(0), bad, _good(2)])
        rows = _rows(tmp_path)
        failed = [r for r in rows if r["abstain_reason"].startswith("row failed: ")]
        assert len(failed) == 1
        assert failed[0]["abstain_reason"].startswith("row failed: confidence:")
        # AC-10: raw_judgement is the deterministic JSON of the whole finding
        assert json.loads(failed[0]["raw_judgement"]) == bad

    @pytest.mark.req("REQ-YG-634")
    def test_out_of_range_confidence_contained(self, tmp_path):
        bad = {**_good(1), "confidence": 7.5}
        _run(tmp_path, [_good(0), bad, _good(2)])
        failed = [
            r for r in _rows(tmp_path) if r["abstain_reason"].startswith("row failed: ")
        ]
        assert len(failed) == 1

    @pytest.mark.req("REQ-YG-634")
    def test_missing_judged_row_evidence_contained(self, tmp_path):
        bad = {**_good(1), "evidence_span": "   "}
        _run(tmp_path, [_good(0), bad, _good(2)])
        failed = [
            r for r in _rows(tmp_path) if r["abstain_reason"].startswith("row failed: ")
        ]
        assert len(failed) == 1

    @pytest.mark.req("REQ-YG-634")
    def test_inconsistent_abstention_cells_contained(self, tmp_path):
        """AC-05: abstained row smuggling evidence is model-owned (loc == ())."""
        bad = {
            "source_index": 1,
            "judgement": "unknown",
            "confidence": 0.1,
            "evidence_span": "smuggled evidence",
            "abstained": True,
            "abstain_reason": "unsure",
        }
        _run(tmp_path, [_good(0), bad, _good(2)])
        failed = [
            r for r in _rows(tmp_path) if r["abstain_reason"].startswith("row failed: ")
        ]
        assert len(failed) == 1
        assert "<model>:" in failed[0]["abstain_reason"]

    @pytest.mark.req("REQ-YG-634")
    def test_summary_line_carries_failed_count(self, tmp_path):
        """AC-11: frozen amended Normalization line."""
        findings = [_good(0), {"_map_index": 1, "_error": "boom"}, _good(2)]
        _run(tmp_path, findings)
        md = (tmp_path / "ledger.md").read_text()
        assert (
            "Normalization: 0 repaired, 0 demoted, 0 model-abstained, "
            "1 row-failed of 3 rows." in md
        )

    @pytest.mark.req("REQ-YG-634")
    def test_public_result_shape_unchanged(self, tmp_path):
        """AC-12: one outer ledger key; three nested keys; 11 JSONL keys."""
        findings = [_good(0), {"_map_index": 1, "_error": "boom"}, _good(2)]
        result = _run(tmp_path, findings)
        assert set(result) == {"ledger"}
        assert set(result["ledger"]) == {"markdown_path", "jsonl_path", "rows"}
        assert all(len(r) == 11 for r in _rows(tmp_path))


class TestIncidentReplay:
    @pytest.mark.req("REQ-YG-634")
    def test_witnessed_incidents_replay_contained(self, tmp_path):
        """AC-13: the four 2026-08-31 batch-killer findings replay as rows."""
        incidents = json.loads(FIXTURE.read_text())["incidents"]
        for incident in incidents:
            idx = incident["map_index"]
            items = [f"corpus/item-{i:04d}.txt" for i in range(idx + 2)]
            findings = [_good(i) for i in range(len(items))]
            findings[idx] = {"_map_index": idx, "_error": incident["error_text"]}
            out = str(tmp_path / f"{incident['batch']}.md")
            result = reduce_ledger(
                {"items": items, "findings": findings, "output_path": out}
            )["ledger"]
            assert result["rows"] == len(items)
            rows = [
                json.loads(line)
                for line in Path(out).with_suffix(".jsonl").read_text().splitlines()
            ]
            failed = [r for r in rows if r["abstain_reason"].startswith("row failed: ")]
            assert len(failed) == 1
            assert failed[0]["item_ref"] == items[idx]
            assert failed[0]["raw_judgement"] == incident["error_text"]


class TestStructuralStaysFatal:
    @pytest.mark.req("REQ-YG-634")
    def test_error_finding_without_map_index_fatal(self, tmp_path):
        """AC-06: _error attribution uses _map_index ONLY."""
        bad = {"_error": "boom", "source_index": 1}
        with pytest.raises(ValueError):
            _run(tmp_path, [_good(0), bad, _good(2)])

    @pytest.mark.req("REQ-YG-634")
    def test_boolean_index_fatal(self, tmp_path):
        """AC-07: booleans are not usable indexes anywhere."""
        bad = {**_good(1)}
        bad["source_index"] = True
        with pytest.raises(ValueError):
            _run(tmp_path, [_good(0), bad, _good(2)])

    @pytest.mark.req("REQ-YG-634")
    def test_invalid_present_source_index_no_fallback(self, tmp_path):
        """AC-06: invalid present source_index must not fall through."""
        bad = {**_good(1), "source_index": "1", "_map_index": 1}
        with pytest.raises(ValueError):
            _run(tmp_path, [_good(0), bad, _good(2)])

    @pytest.mark.req("REQ-YG-634")
    def test_both_indexes_present_source_selected(self, tmp_path):
        """AC-07: source_index wins; _map_index is not a second input."""
        shifted = {**_good(1), "_map_index": 2}
        _run(tmp_path, [_good(0), shifted, _good(2)])
        rows = _rows(tmp_path)
        assert sorted(r["item_ref"] for r in rows) == sorted(ITEMS)

    @pytest.mark.req("REQ-YG-634")
    def test_reducer_owned_validation_fatal(self, tmp_path):
        """AC-06: item_ref validation is reducer-owned -> batch-fatal."""
        with pytest.raises(ValueError):
            _run(tmp_path, [_good(0)], items=[""])

    @pytest.mark.req("REQ-YG-634")
    def test_non_serializable_finding_fatal(self, tmp_path):
        """AC-06/AC-10: class-3 finding that cannot be JSON-serialized aborts."""
        bad = {**_good(1), "confidence": None, "extra": object()}
        with pytest.raises(ValueError):
            _run(tmp_path, [_good(0), bad, _good(2)])

    @pytest.mark.req("REQ-YG-634")
    def test_missing_findings_still_fatal(self, tmp_path):
        with pytest.raises(ValueError, match="missing findings"):
            _run(tmp_path, [_good(0), _good(1)])

    @pytest.mark.req("REQ-YG-634")
    def test_duplicate_index_still_fatal(self, tmp_path):
        with pytest.raises(ValueError, match="duplicate"):
            _run(tmp_path, [_good(0), _good(1), {**_good(1)}])
