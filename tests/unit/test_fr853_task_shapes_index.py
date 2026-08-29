"""FR-853: Task-shape instrument index visibility (AC-04).

Proves the literal ``Task shapes:`` clause in graph descriptions
survives ``discover_graphs()`` — the agent-visible discovery surface
actually carries the instrument index (judgement R-4).
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# AC-03: the first index set frozen by the judgement.
INDEXED_GRAPHS = {
    "map-demo",
    "fan-out-demo",
    "race-demo",
    "five-whys",
    "innovation-matrix",
}


def _discover_demo_graphs():
    from yamlgraph.discovery import discover_graphs

    pattern = str(REPO_ROOT / "examples" / "demos" / "*" / "graph.yaml")
    return discover_graphs([pattern])


@pytest.mark.req("REQ-YG-206")
def test_task_shapes_clause_survives_discover_graphs():
    """Indexed graphs carry 'Task shapes:' through discover_graphs()."""
    graphs = {g["name"]: g for g in _discover_demo_graphs()}
    missing = INDEXED_GRAPHS - set(graphs)
    assert not missing, f"indexed graphs not discovered: {missing}"
    without_clause = [
        name
        for name in sorted(INDEXED_GRAPHS)
        if "Task shapes:" not in graphs[name]["description"]
    ]
    assert not without_clause, f"missing 'Task shapes:' clause: {without_clause}"
