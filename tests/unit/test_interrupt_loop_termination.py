"""Condemning test for the FR-466 turn-loop non-termination bug.

Hypothesis: when an ``interrupt`` node sits inside a cycle and a downstream
conditional edge routes one branch to a ``map`` node (and another to ``END``),
the compiled graph fails to terminate. A conditional edge whose target is a map
node registers an *unconditional* fan-out router on the source node, so the map
branch fires on every turn regardless of the condition — ``END`` is never
reached and the loop runs forever.

Observed in the dungeon-master turn loop: resuming ``dm_window`` with ``end``
correctly parses ``dm_action == 'end'`` and the expression router returns
``__end__``, yet ``get_state(...).next`` remains ``('dm_window',)`` because the
``retry`` branch points at the ``plan_all`` map node.

These tests reproduce the structure with passthrough nodes (no LLM) so they are
deterministic and fast.
"""

import uuid
from pathlib import Path

import pytest
from langgraph.types import Command

from yamlgraph.compile.graph_loader import (
    compile_graph,
    get_checkpointer_for_graph,
    load_graph_config,
)

FIXTURE = Path(__file__).parent.parent / "fixtures" / "interrupt_loop_end.yaml"


def _compile_app():
    config = load_graph_config(FIXTURE)
    graph = compile_graph(config)
    checkpointer = get_checkpointer_for_graph(config)
    return graph.compile(checkpointer=checkpointer)


@pytest.mark.req("REQ-YG-434")
def test_resume_with_terminating_token_ends_graph():
    """Resuming the interrupt with 'stop' must terminate the graph."""
    app = _compile_app()
    run_config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    app.invoke({"items": ["a", "b"]}, run_config)
    # We are paused at the interrupt.
    assert app.get_state(run_config).next == ("ask",)

    app.invoke(Command(resume="stop"), run_config)

    state = app.get_state(run_config)
    assert state.values.get("action") == "stop"
    # The condemning assertion: the graph must have terminated.
    assert state.next == (), (
        f"Graph did not terminate after 'stop'; next={state.next}. "
        "The map-node branch fired unconditionally instead of routing to END."
    )


@pytest.mark.req("REQ-YG-434")
def test_resume_with_loop_token_returns_to_interrupt():
    """Resuming with a non-terminating token loops back to the interrupt."""
    app = _compile_app()
    run_config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    app.invoke({"items": ["a", "b"]}, run_config)
    app.invoke(Command(resume="go"), run_config)

    # After one loop iteration we should be paused at the interrupt again.
    assert app.get_state(run_config).next == ("ask",)
