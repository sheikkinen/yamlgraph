"""FR-1087: the safety-guards demo compiles and routes low → revise, high → expand."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from yamlgraph.compile.graph_loader import compile_graph, load_graph_config

pytestmark = pytest.mark.process

GRAPH = Path(__file__).parents[2] / "examples/demos/safety-guards/graph.yaml"


def _run_with_scores(scores: list[float]) -> list[str]:
    """Run the demo with scripted review scores; return the top-level node order."""
    review_scores = iter(scores)

    def fake_execute_prompt(prompt_name: str, **_: object) -> object:
        if prompt_name == "review":
            return SimpleNamespace(score=next(review_scores), feedback="tighten")
        return f"{prompt_name} output"

    graph = compile_graph(load_graph_config(GRAPH)).compile()
    order: list[str] = []
    with patch(
        "yamlgraph.node_factory.llm_nodes.execute_prompt",
        side_effect=fake_execute_prompt,
    ):
        for update in graph.stream(
            {"topic": "quantum computing", "topics": ["physics", "math", "biology"]},
            stream_mode="updates",
        ):
            order.extend(update)
    return order


def _collapse_map(order: list[str]) -> list[str]:
    """Count the map's per-item sub-node updates as one `expand` visit."""
    collapsed: list[str] = []
    for node in order:
        name = "expand" if "expand" in node else node
        if not (name == "expand" and collapsed and collapsed[-1] == "expand"):
            collapsed.append(name)
    return collapsed


@pytest.mark.req("REQ-YG-022")
def test_safety_guards_graph_compiles() -> None:
    assert compile_graph(load_graph_config(GRAPH)).compile() is not None


@pytest.mark.req("REQ-YG-022")
def test_low_then_high_score_loops_once_then_expands_once() -> None:
    order = _collapse_map(_run_with_scores([0.3, 0.9]))

    assert order == ["draft", "review", "revise", "review", "expand"]
    assert order.count("revise") == 1
    assert order.count("expand") == 1
    last_review = len(order) - 1 - order[::-1].index("review")
    assert all(i > last_review for i, n in enumerate(order) if n == "expand")
