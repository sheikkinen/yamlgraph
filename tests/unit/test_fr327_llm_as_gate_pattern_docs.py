"""Acceptance tests for FR-327 LLM-as-gate pattern documentation."""

from pathlib import Path

import pytest

WORKTREE = Path(__file__).resolve().parents[2]
DOC_PATH = WORKTREE / "reference" / "patterns" / "llm-as-gate.md"
REFERENCE_INDEX = WORKTREE / "reference" / "README.md"


def _read_doc() -> str:
    assert DOC_PATH.exists(), f"Missing pattern doc: {DOC_PATH}"
    return DOC_PATH.read_text().lower()


@pytest.mark.req("REQ-YG-271")
class TestFR327LlmAsGatePatternDocs:
    """AC-01..AC-08 documentation contract."""

    def test_ac01_llm_as_gate_doc_exists(self) -> None:
        assert DOC_PATH.exists(), f"Missing pattern doc: {DOC_PATH}"

    def test_ac02_problem_statement_mentions_shape_vs_meaning(self) -> None:
        content = _read_doc()
        assert "shape" in content
        assert "meaning" in content
        assert "semantic" in content

    def test_ac03_graph_example_uses_router_with_verdict_route_field(self) -> None:
        content = _read_doc()
        assert "type: router" in content
        assert "route_field: verdict" in content
        assert "pass:" in content
        assert "fail:" in content

    def test_ac04_schema_example_contains_binary_verdict_and_reason(self) -> None:
        content = _read_doc()
        assert "schema:" in content
        assert "verdict" in content
        assert "reason" in content
        assert any(
            token in content for token in ("pass|fail", "pass/fail", "pass, fail")
        )

    def test_ac05_doc_compares_semantic_and_mechanical_gates(self) -> None:
        content = _read_doc()
        assert "semantic" in content
        assert any(token in content for token in ("mechanical", "deterministic"))
        assert "grep" in content
        assert "file" in content
        assert "exit code" in content

    def test_ac06_doc_describes_chain_fallback_and_retry_composition(self) -> None:
        content = _read_doc()
        assert any(token in content for token in ("chain", "chaining"))
        assert "fallback" in content
        assert "retry" in content

    def test_ac07_doc_states_no_new_framework_primitive_required(self) -> None:
        content = _read_doc()
        assert "no new" in content
        assert any(
            token in content for token in ("node type", "action type", "primitive")
        )

    def test_ac08_reference_readme_links_llm_as_gate_doc(self) -> None:
        assert REFERENCE_INDEX.exists(), f"Missing reference index: {REFERENCE_INDEX}"
        readme = REFERENCE_INDEX.read_text().lower()
        assert "patterns/llm-as-gate.md" in readme
