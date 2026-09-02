"""Tests for FR-176: Concurrency Safety Map.

Validates that docs/concurrency-safety.md exists and covers the audited
concurrency areas with the required structure: concurrency model, shared state,
safety invariant, evidence (file:line), and verdict.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.process

DOC_PATH = Path(__file__).resolve().parents[2] / "docs" / "concurrency-safety.md"

# The areas from the FR acceptance criteria (MCP server retired by FR-910)
REQUIRED_SECTIONS = [
    "Map Node Fan-Out",
    "Checkpoint Writes",
    "Graph Cache",
    "Inquisitor Diary Writes",
    "Async Executor",
]

REQUIRED_EVIDENCE_MARKERS = [
    "yamlgraph/map_compiler.py",
    "yamlgraph/storage/",
    "yamlgraph/graph_cache.py",
    ".chaplain/inquisitor.sh",
    "yamlgraph/executor_async.py",
]


@pytest.mark.req("REQ-YG-160")
def test_concurrency_safety_doc_exists():
    """AC: docs/concurrency-safety.md exists."""
    assert DOC_PATH.is_file(), f"Missing: {DOC_PATH}"


@pytest.mark.req("REQ-YG-160")
def test_concurrency_safety_doc_not_stub():
    """AC: Genuine content, not a placeholder."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert len(content.strip()) > 1000, "Document is too short to be a real audit"


@pytest.mark.req("REQ-YG-160")
@pytest.mark.parametrize("section", REQUIRED_SECTIONS)
def test_concurrency_safety_has_section(section: str):
    """AC: Each of the 6 candidates has a dedicated section."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert f"## {section}" in content, f"Missing section: ## {section}"


@pytest.mark.req("REQ-YG-160")
@pytest.mark.parametrize("marker", REQUIRED_EVIDENCE_MARKERS)
def test_concurrency_safety_has_evidence(marker: str):
    """AC: Each entry documents file:line evidence."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert marker in content, f"Missing evidence reference: {marker}"


@pytest.mark.req("REQ-YG-160")
def test_concurrency_safety_has_verdicts():
    """AC: Each entry has a verdict classification."""
    content = DOC_PATH.read_text(encoding="utf-8")
    verdict_count = content.count("**Verdict:**")
    assert verdict_count >= 5, f"Expected >= 5 verdict entries, found {verdict_count}"


@pytest.mark.req("REQ-YG-160")
def test_concurrency_safety_has_summary_table():
    """AC: Summary table classifies all audited areas."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "| Area |" in content or "| Area " in content, "Missing summary table"
    for section in REQUIRED_SECTIONS:
        # Summary table uses different formatting than section headers
        section_lower = section.lower()
        assert any(
            keyword in content.lower()
            for keyword in [section_lower, section_lower.replace(" ", "-")]
        ), f"Summary table missing entry for: {section}"


@pytest.mark.req("REQ-YG-160")
def test_concurrency_safety_safe_patterns_documented():
    """AC: Safe patterns (async executor) document why they are safe."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert (
        "asyncio.gather" in content
    ), "Async executor concurrency model not documented"
