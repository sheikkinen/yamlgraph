"""Tests for FR-176: Concurrency Safety Map.

Validates that docs/concurrency-safety.md exists and covers all 6 audited
concurrency areas with the required structure: concurrency model, shared state,
safety invariant, evidence (file:line), and verdict.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.process

DOC_PATH = Path(__file__).resolve().parents[2] / "docs" / "concurrency-safety.md"

# The 6 areas from the FR acceptance criteria
REQUIRED_SECTIONS = [
    "Map Node Fan-Out",
    "Checkpoint Writes",
    "Graph Cache",
    "Inquisitor Diary Writes",
    "MCP Server",
    "Async Executor",
]

REQUIRED_EVIDENCE_MARKERS = [
    "yamlgraph/map_compiler.py",
    "yamlgraph/storage/",
    "yamlgraph/graph_cache.py",
    ".chaplain/inquisitor.sh",
    "yamlgraph/export/mcp.py",
    "yamlgraph/executor_async.py",
]


@pytest.mark.req("REQ-YG-160")
def test_concurrency_safety_doc_exists():
    """AC: docs/concurrency-safety.md exists."""
    assert DOC_PATH.is_file(), f"Missing: {DOC_PATH}"


@pytest.mark.req("REQ-YG-160")
def test_concurrency_safety_doc_not_stub():
    """AC: Genuine content, not a placeholder."""
    content = DOC_PATH.read_text()
    assert len(content.strip()) > 1000, "Document is too short to be a real audit"


@pytest.mark.req("REQ-YG-160")
@pytest.mark.parametrize("section", REQUIRED_SECTIONS)
def test_concurrency_safety_has_section(section: str):
    """AC: Each of the 6 candidates has a dedicated section."""
    content = DOC_PATH.read_text()
    assert f"## {section}" in content, f"Missing section: ## {section}"


@pytest.mark.req("REQ-YG-160")
@pytest.mark.parametrize("marker", REQUIRED_EVIDENCE_MARKERS)
def test_concurrency_safety_has_evidence(marker: str):
    """AC: Each entry documents file:line evidence."""
    content = DOC_PATH.read_text()
    assert marker in content, f"Missing evidence reference: {marker}"


@pytest.mark.req("REQ-YG-160")
def test_concurrency_safety_has_verdicts():
    """AC: Each entry has a verdict classification."""
    content = DOC_PATH.read_text()
    verdict_count = content.count("**Verdict:**")
    assert verdict_count >= 6, f"Expected >= 6 verdict entries, found {verdict_count}"


@pytest.mark.req("REQ-YG-160")
def test_concurrency_safety_has_summary_table():
    """AC: Summary table classifies all 6 areas."""
    content = DOC_PATH.read_text()
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
    """AC: Safe patterns (MCP, async executor) document why they are safe."""
    content = DOC_PATH.read_text()
    assert (
        "max_workers=1" in content
    ), "MCP safety invariant (max_workers=1) not documented"
    assert (
        "asyncio.gather" in content
    ), "Async executor concurrency model not documented"
