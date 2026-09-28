"""FR-1134 — the stale FR knowledge graph is retired (REQ-YG-720, CAP-297).

RED on the pre-removal tree, GREEN after the removal commit.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
PRIOR_ART = REPO / ".github/hooks/scripts/checks/prior_art.py"

# process: reads scripts/, reference/, capabilities/ (FR-756)
pytestmark = pytest.mark.process

DELETED = [
    "scripts/extract_fr_graph.py",
    "reference/fr-knowledge-graph.yaml",
    "reference/fr-knowledge-graph.md",
    "tests/fixtures/fr_graph_validation.yaml",
    "tests/unit/test_fr_graph.py",
    "capabilities/CAP-240-fr-knowledge-graph.yaml",
]


@pytest.mark.req("REQ-YG-720")
@pytest.mark.parametrize("rel", DELETED)
def test_graph_artifact_deleted(rel: str) -> None:
    assert not (REPO / rel).exists()


@pytest.mark.req("REQ-YG-720")
@pytest.mark.parametrize(
    "token", ["fr-knowledge-graph", "_graph_prior_art", "graph:cluster", "import yaml"]
)
def test_prior_art_hook_has_no_graph_code(token: str) -> None:
    assert token not in PRIOR_ART.read_text(encoding="utf-8")
