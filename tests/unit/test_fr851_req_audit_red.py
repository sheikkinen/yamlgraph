"""FR-851 requirement-witness audit: constructor + reconciliation (RED).

Deterministic constructor (scripts/req_audit_questions.py) emits one
frozen-schema question file per registry REQ; reconciliation
(scripts/req_audit_report.py) verifies model verdicts against batch
inputs at the boundary (two_strike_split).
"""

from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

import pytest

pytestmark = pytest.mark.process

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from req_audit_questions import (  # noqa: E402
    FIXED_QUESTION,
    RESOLUTION_CLASSES,
    build_batches,
    build_question,
    build_stage2_question,
    derive_resolution,
    estimate_tokens,
    write_questions,
)
from req_audit_report import (  # noqa: E402
    reconcile,
    reconcile_batch,
    render_report,
)


def _question(req_id: str, req_text: str = "Some requirement text.") -> dict:
    return build_question(
        req_id=req_id,
        req_text=req_text,
        cap_id="CAP-999",
        cap_name="Test Capability",
        declared_modules=["scripts"],
        tests=[{"test_id": "test_x::test_y", "resolution": "coverage"}],
        resolved_files=["yamlgraph/config.py"],
    )


@pytest.mark.req("REQ-YG-606")
class TestQuestionSchema:
    def test_frozen_schema_keys(self) -> None:
        q = _question("REQ-YG-001")
        assert set(q.keys()) == {
            "req_id",
            "req_text",
            "cap_id",
            "cap_name",
            "declared_modules",
            "tests",
            "resolved_files",
            "evidence_depth",
            "question",
        }

    def test_fixed_question_and_names_depth(self) -> None:
        q = _question("REQ-YG-001")
        assert q["question"] == FIXED_QUESTION
        assert q["evidence_depth"] == "names"

    def test_resolution_enum_frozen(self) -> None:
        assert RESOLUTION_CLASSES == (
            "coverage",
            "ast",
            "no-link-ran",
            "no-link-unrecorded",
            "doc-witness",
        )


@pytest.mark.req("REQ-YG-606")
class TestDeriveResolution:
    def test_coverage_resolved(self, tmp_path: Path) -> None:
        cls, files = derive_resolution(
            "test_a::test_b",
            coverage_map={"test_a::test_b": {"yamlgraph/config.py"}},
            recorded_contexts={"test_a::test_b"},
            test_file=None,
        )
        assert cls == "coverage"
        assert files == ["yamlgraph/config.py"]

    def test_ast_fallback(self, tmp_path: Path) -> None:
        f = tmp_path / "test_ast.py"
        f.write_text(
            "from yamlgraph.config import PACKAGE_ROOT\n\n"
            "def test_thing():\n    assert PACKAGE_ROOT\n"
        )
        cls, files = derive_resolution(
            "test_ast::test_thing",
            coverage_map={},
            recorded_contexts=set(),
            test_file=f,
        )
        assert cls == "ast"
        assert "yamlgraph/config.py" in files

    def test_doc_witness(self, tmp_path: Path) -> None:
        # Mimics test_race_pipeline_docs: no yamlgraph imports, reads .md docs
        f = tmp_path / "test_docs.py"
        f.write_text(
            textwrap.dedent("""\
                from pathlib import Path

                def test_doc_has_section():
                    text = Path("reference/graph-yaml.md").read_text()
                    assert "race" in text
            """)
        )
        cls, files = derive_resolution(
            "test_docs::test_doc_has_section",
            coverage_map={},
            recorded_contexts={"test_docs::test_doc_has_section"},
            test_file=f,
        )
        assert cls == "doc-witness"
        assert files == []

    def test_no_link_ran(self, tmp_path: Path) -> None:
        f = tmp_path / "test_ran.py"
        f.write_text("def test_pure():\n    assert 1 + 1 == 2\n")
        cls, _ = derive_resolution(
            "test_ran::test_pure",
            coverage_map={},
            recorded_contexts={"test_ran::test_pure"},
            test_file=f,
        )
        assert cls == "no-link-ran"

    def test_no_link_unrecorded(self, tmp_path: Path) -> None:
        f = tmp_path / "test_unrec.py"
        f.write_text("def test_pure():\n    assert True\n")
        cls, _ = derive_resolution(
            "test_unrec::test_pure",
            coverage_map={},
            recorded_contexts=set(),
            test_file=f,
        )
        assert cls == "no-link-unrecorded"


@pytest.mark.req("REQ-YG-606")
class TestBatching:
    def test_estimator_chars_over_four(self) -> None:
        assert estimate_tokens("x" * 400) == 100

    def test_batches_ordered_by_req_id_and_capped(self) -> None:
        questions = [_question(f"REQ-YG-{n:03d}") for n in (3, 1, 2)]
        batches = build_batches(questions, max_tokens=8000)
        flat = [q["req_id"] for b in batches for q in b]
        assert flat == ["REQ-YG-001", "REQ-YG-002", "REQ-YG-003"]
        for batch in batches:
            total = sum(estimate_tokens(json.dumps(q)) for q in batch)
            assert total <= 8000

    def test_oversized_req_isolated_untruncated(self) -> None:
        # REQ-YG-566-sized fixture: single question exceeding the budget
        long_text = "collector chunker coverage render " * 2000
        big = _question("REQ-YG-002", req_text=long_text)
        small = _question("REQ-YG-001")
        batches = build_batches([big, small], max_tokens=100)
        assert [len(b) for b in batches] == [1, 1]
        isolated = next(b[0] for b in batches if b[0]["req_id"] == "REQ-YG-002")
        assert isolated["req_text"] == long_text  # never truncated


@pytest.mark.req("REQ-YG-606")
class TestWriteQuestions:
    def test_one_file_per_req_and_deterministic(self, tmp_path: Path) -> None:
        questions = [_question(f"REQ-YG-{n:03d}") for n in (1, 2)]
        out1 = tmp_path / "run1"
        out2 = tmp_path / "run2"
        write_questions(questions, out1)
        write_questions(questions, out2)
        files1 = sorted(p.name for p in (out1 / "questions").glob("*.json"))
        assert files1 == ["REQ-YG-001.json", "REQ-YG-002.json"]
        for name in files1:
            a = (out1 / "questions" / name).read_bytes()
            b = (out2 / "questions" / name).read_bytes()
            assert a == b
        assert (out1 / "batches").is_dir()
        b1 = sorted((out1 / "batches").glob("batch-*.json"))
        assert b1, "batches must be emitted"


@pytest.mark.req("REQ-YG-606")
class TestStage2:
    def test_stage2_includes_test_body(self, tmp_path: Path) -> None:
        f = tmp_path / "test_body.py"
        f.write_text("def test_specific_seam():\n    assert compute() == 42\n")
        q = _question("REQ-YG-001")
        q2 = build_stage2_question(
            q, test_files={"test_x::test_y": f}, repo_root=tmp_path
        )
        assert q2["evidence_depth"] == "bodies"
        assert "test_specific_seam" in json.dumps(q2) or "test_bodies" in q2


@pytest.mark.req("REQ-YG-607")
class TestReconcileBatch:
    def test_hallucinated_id_rejects_batch(self) -> None:
        result = reconcile_batch(
            input_ids=["REQ-YG-001", "REQ-YG-002"],
            verdicts=[
                {
                    "req_id": "REQ-YG-001",
                    "witnessed": "yes",
                    "gap": "",
                    "suggestion": "",
                },
                {
                    "req_id": "REQ-YG-999",
                    "witnessed": "no",
                    "gap": "x",
                    "suggestion": "y",
                },
            ],
        )
        assert result.rejected is True
        assert result.requeue == ["REQ-YG-001", "REQ-YG-002"]
        assert result.audited == {}

    def test_duplicate_keeps_first(self) -> None:
        result = reconcile_batch(
            input_ids=["REQ-YG-001"],
            verdicts=[
                {
                    "req_id": "REQ-YG-001",
                    "witnessed": "yes",
                    "gap": "",
                    "suggestion": "",
                },
                {
                    "req_id": "REQ-YG-001",
                    "witnessed": "no",
                    "gap": "late",
                    "suggestion": "",
                },
            ],
        )
        assert result.rejected is False
        assert result.audited["REQ-YG-001"]["witnessed"] == "yes"
        assert result.duplicates == ["REQ-YG-001"]

    def test_missing_id_requeues(self) -> None:
        result = reconcile_batch(
            input_ids=["REQ-YG-001", "REQ-YG-002"],
            verdicts=[
                {
                    "req_id": "REQ-YG-001",
                    "witnessed": "yes",
                    "gap": "",
                    "suggestion": "",
                },
            ],
        )
        assert result.rejected is False
        assert result.requeue == ["REQ-YG-002"]


@pytest.mark.req("REQ-YG-607")
class TestReconcileAll:
    def test_missing_after_retry_is_unaudited_nothing_lost(self) -> None:
        batches = {"batch-000": ["REQ-YG-001", "REQ-YG-002"]}
        responses = {
            "batch-000": [
                {
                    "req_id": "REQ-YG-001",
                    "witnessed": "yes",
                    "gap": "",
                    "suggestion": "",
                },
            ]
        }
        retry_responses: dict[str, list[dict]] = {}  # retry returned nothing
        result = reconcile(batches, responses, retry_responses)
        assert set(result.audited) == {"REQ-YG-001"}
        assert result.unaudited == ["REQ-YG-002"]
        all_inputs = {r for ids in batches.values() for r in ids}
        assert set(result.audited) | set(result.unaudited) == all_inputs


@pytest.mark.req("REQ-YG-607")
class TestRenderReport:
    def _result(self):
        batches = {
            "batch-000": ["REQ-YG-001", "REQ-YG-002", "REQ-YG-003", "REQ-YG-004"]
        }
        responses = {
            "batch-000": [
                {
                    "req_id": "REQ-YG-001",
                    "witnessed": "yes",
                    "gap": "",
                    "suggestion": "",
                },
                {
                    "req_id": "REQ-YG-002",
                    "witnessed": "no",
                    "gap": "no assertion",
                    "suggestion": "add test",
                },
                {
                    "req_id": "REQ-YG-003",
                    "witnessed": "partial",
                    "gap": "one seam",
                    "suggestion": "widen",
                },
            ]
        }
        return reconcile(batches, responses, {})

    def test_ranks_no_partial_unaudited_before_yes(self) -> None:
        report = render_report(
            self._result(),
            metadata={
                "model": "claude-haiku",
                "provider": "anthropic",
                "tree_sha": "abc1234",
                "batch_count": 1,
                "stage": "1 (witness plausibility from names and declared links)",
            },
        )
        assert report.index("REQ-YG-002") < report.index("REQ-YG-003")
        assert "REQ-YG-004" in report  # unaudited listed
        # yes collapses to a count, not a listed row
        assert "REQ-YG-001" not in report
        assert "1" in report

    def test_metadata_and_stage_label_present(self) -> None:
        report = render_report(
            self._result(),
            metadata={
                "model": "claude-haiku",
                "provider": "anthropic",
                "tree_sha": "abc1234",
                "batch_count": 1,
                "stage": "1 (witness plausibility from names and declared links)",
            },
        )
        assert "claude-haiku" in report
        assert "abc1234" in report
        assert "plausibility" in report
