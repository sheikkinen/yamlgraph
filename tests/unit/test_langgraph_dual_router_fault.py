"""Second-level condemnation: is the FR-466 loop bug LangGraph's or YAMLGraph's?

The first condemnation (test_interrupt_loop_termination.py) proved that a
conditional edge whose target is a map node makes YAMLGraph register TWO
``add_conditional_edges`` routers on the same source node:

  - map_edge        -> _map_<name>_sub   (UNCONDITIONAL — ignores the condition)
  - expr_router_fn  -> __end__ / others  (conditional)

This module isolates the question of fault using *raw LangGraph only* (no
YAMLGraph imports in the graph build). It answers two things:

1. ``test_langgraph_runs_all_conditional_routers``: when a node has two
   ``add_conditional_edges`` calls, LangGraph fans out to the union of every
   router's target every superstep. This is documented LangGraph behavior, not
   a defect — so the bug is NOT in LangGraph.

2. ``test_langgraph_single_router_terminates``: the SAME graph with a single
   router that returns exactly one target per step terminates correctly. This
   confirms the cure: YAMLGraph must emit one router that honors the condition,
   not two.

Conclusion encoded by these tests: the defect is YAMLGraph's
``_handle_to_map_edge`` registering a second, unconditional router — LangGraph
is behaving exactly as specified.
"""

import pytest
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict


class _State(TypedDict, total=False):
    action: str
    visits: list


def _record(node: str):
    def fn(state: _State) -> dict:
        visits = list(state.get("visits") or [])
        visits.append(node)
        return {"visits": visits}

    return fn


@pytest.mark.req("REQ-YG-434")
def test_langgraph_runs_all_conditional_routers():
    """Two routers on one node => LangGraph fans out to BOTH targets.

    This mirrors YAMLGraph's emission: a map_edge router that always returns the
    map sub-node, plus an expression router that returns END on 'stop'. Even
    when the expression router selects END, the map router still drives the
    'plan' branch — proving the duplication, not LangGraph, is at fault.
    """
    graph: StateGraph = StateGraph(_State)
    graph.add_node("parse", _record("parse"))
    graph.add_node("plan", _record("plan"))
    graph.add_edge(START, "parse")

    # Router 1: emulates YAMLGraph's map_edge — ALWAYS routes to the map node.
    graph.add_conditional_edges("parse", lambda s: "plan", {"plan": "plan"})

    # Router 2: emulates YAMLGraph's expr_router_fn — conditional END.
    def _expr(state: _State) -> str:
        return END if state.get("action") == "stop" else "plan"

    graph.add_conditional_edges("parse", _expr, {END: END, "plan": "plan"})
    graph.add_edge("plan", END)

    app = graph.compile(checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": "two-routers"}}

    result = app.invoke({"action": "stop", "visits": []}, config)

    # Despite action=='stop' (expr router -> END), the map router still ran plan.
    assert "plan" in result["visits"], (
        "Expected LangGraph to fan out to 'plan' from the second router even "
        "when the expression router chose END — confirming both routers fire."
    )


@pytest.mark.req("REQ-YG-434")
def test_langgraph_single_router_terminates():
    """A single router that honors the condition terminates correctly.

    This is the cure YAMLGraph must implement: fold the map target into ONE
    router so 'stop' routes to END and nothing else fires.
    """
    graph: StateGraph = StateGraph(_State)
    graph.add_node("parse", _record("parse"))
    graph.add_node("plan", _record("plan"))
    graph.add_edge(START, "parse")

    def _single(state: _State) -> str:
        return END if state.get("action") == "stop" else "plan"

    graph.add_conditional_edges("parse", _single, {END: END, "plan": "plan"})
    graph.add_edge("plan", END)

    app = graph.compile(checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": "one-router"}}

    result = app.invoke({"action": "stop", "visits": []}, config)

    assert "plan" not in result["visits"], (
        "With a single condition-honoring router, 'stop' must route to END "
        "without entering the map branch."
    )
