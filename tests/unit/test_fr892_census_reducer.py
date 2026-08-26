"""FR-892 AC-06/AC-07: corpus_census reducer — fail-closed ledger witnesses.

Deterministic tests against examples/demos/corpus_census/tools.py:
frozen columns, abstention as first-class rows, empty-cell rejection,
error-string rejection, missing/duplicate finding rejection.
"""

import json

import pytest

from examples.demos.corpus_census.tools import reduce_ledger

# References examples/ (process boundary, FR-756)
pytestmark = pytest.mark.process

ITEMS = ["corpus/a.txt", "corpus/b.txt"]

GOOD_A = {
    "source_index": 0,
    "judgement": "Architecture",
    "confidence": 0.9,
    "evidence_span": "describes boundaries",
    "abstained": False,
    "abstain_reason": "",
}
ABSTAIN_B = {
    "source_index": 1,
    "judgement": "unknown",
    "confidence": 0.1,
    "evidence_span": "",
    "abstained": True,
    "abstain_reason": "document empty",
}


def _run(tmp_path, findings, items=ITEMS):
    out = str(tmp_path / "ledger.md")
    return reduce_ledger(
        {"items": list(items), "findings": findings, "output_path": out}
    )


class TestLedgerContract:
    @pytest.mark.req("REQ-YG-624")
    def test_frozen_columns_in_md_and_jsonl(self, tmp_path):
        result = _run(tmp_path, [GOOD_A, ABSTAIN_B])["ledger"]
        md = (tmp_path / "ledger.md").read_text()
        for col in (
            "item_ref",
            "judgement",
            "confidence",
            "evidence_span",
            "model",
            "prompt_version",
            "abstained",
            "abstain_reason",
            "disagreement",
        ):
            assert col in md
        rows = [
            json.loads(line)
            for line in (tmp_path / "ledger.jsonl").read_text().splitlines()
        ]
        assert result["rows"] == 2 and len(rows) == 2
        assert set(rows[0]) == {
            "item_ref",
            "judgement",
            "confidence",
            "evidence_span",
            "model",
            "prompt_version",
            "abstained",
            "abstain_reason",
            "disagreement",
        }

    @pytest.mark.req("REQ-YG-624")
    def test_abstention_becomes_ledger_row(self, tmp_path):
        """AC-06: abstentions are rows, never omissions."""
        _run(tmp_path, [GOOD_A, ABSTAIN_B])
        rows = [
            json.loads(line)
            for line in (tmp_path / "ledger.jsonl").read_text().splitlines()
        ]
        abstained = [r for r in rows if r["abstained"]]
        assert len(abstained) == 1
        assert abstained[0]["abstain_reason"] == "document empty"

    @pytest.mark.req("REQ-YG-624")
    def test_dropped_finding_rejected(self, tmp_path):
        """A missing per-item finding fails the whole reduce (fail closed)."""
        with pytest.raises(ValueError, match="missing findings"):
            _run(tmp_path, [GOOD_A])

    @pytest.mark.req("REQ-YG-624")
    def test_duplicate_finding_rejected(self, tmp_path):
        with pytest.raises(ValueError, match="duplicate"):
            _run(tmp_path, [GOOD_A, {**GOOD_A}, ABSTAIN_B])

    @pytest.mark.req("REQ-YG-624")
    def test_error_string_judgement_rejected(self, tmp_path):
        bad = {**GOOD_A, "judgement": "Error: search failed"}
        with pytest.raises(ValueError, match="error string"):
            _run(tmp_path, [bad, ABSTAIN_B])

    @pytest.mark.req("REQ-YG-624")
    def test_empty_required_cell_rejected(self, tmp_path):
        bad = {**GOOD_A, "evidence_span": "   "}
        with pytest.raises(ValueError, match="evidence_span|invalid ledger row"):
            _run(tmp_path, [bad, ABSTAIN_B])

    @pytest.mark.req("REQ-YG-624")
    def test_abstained_with_evidence_rejected(self, tmp_path):
        """Abstention cross-validation: no evidence smuggling."""
        bad = {**ABSTAIN_B, "evidence_span": "actually has evidence"}
        with pytest.raises(ValueError, match="invalid ledger row"):
            _run(tmp_path, [GOOD_A, bad])

    @pytest.mark.req("REQ-YG-624")
    def test_map_error_row_rejected(self, tmp_path):
        bad = {"_error": "boom", "source_index": 1}
        with pytest.raises(ValueError, match="map error"):
            _run(tmp_path, [GOOD_A, bad])


class TestSecurityWitness:
    """AC-10: hostile variable through the shlex-quoted shell path."""

    @pytest.mark.req("REQ-YG-624")
    def test_hostile_shell_variable_no_injection(self, tmp_path):
        from yamlgraph.tools.shell import ShellToolConfig, execute_shell_tool

        marker = tmp_path / "pwned"
        config = ShellToolConfig(
            command="echo {payload}", description="echo user input"
        )
        hostile = f"hi; touch {marker}; echo owned"
        result = execute_shell_tool(config, {"payload": hostile})
        assert not marker.exists(), "shell injection succeeded — quoting broken"
        assert "owned" in str(result.output)  # payload echoed as DATA
