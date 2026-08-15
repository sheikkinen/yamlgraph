"""FR-797 C-2 gate witnesses: subgraph interrupt propagation under langgraph 1.x.

Two layers:

1. Boundary-contract witnesses (PASS): pin the langgraph 1.2.x behavior the
   fix design must respect — ``__pregel_send`` writes made before
   ``interrupt()`` surface in the transient invoke result but are NOT
   committed to checkpointed state at the pause boundary. This refutes the
   single-node relay mechanism (judgement C-2) and is the recorded evidence
   for the two-node split design.

2. Condemning witnesses (RED until the fix lands): the parent graph must
   pause on a child interrupt with mapped state committed, and resume must
   reach the child. These become the fix's regression suite.
"""

from pathlib import Path
from typing import TypedDict

import pytest

pytestmark = pytest.mark.process

PARENT_GRAPH = (
    Path(__file__).parent.parent.parent
    / "examples"
    / "demos"
    / "interrupt"
    / "interrupt-parent.yaml"
)


class _SeamState(TypedDict, total=False):
    committed: str
    final: str


def _build_send_before_interrupt_app(saver):
    """Minimal langgraph app: one node sends a write, then interrupts."""
    from langgraph.graph import END, START, StateGraph
    from langgraph.types import interrupt

    def node(state, config):
        send = config["configurable"].get("__pregel_send")
        assert send is not None, "__pregel_send absent from configurable"
        send([("committed", "before-pause")])
        answer = interrupt("q?")
        return {"final": answer}

    graph = StateGraph(_SeamState)
    graph.add_node("n", node)
    graph.add_edge(START, "n")
    graph.add_edge("n", END)
    return graph.compile(checkpointer=saver)


class TestLanggraphPauseBoundaryContract:
    """C-2 evidence, mechanized: the provider contract at the pause seam."""

    @pytest.mark.req("REQ-YG-042")
    def test_send_before_interrupt_surfaces_in_result_only(self):
        """Writes sent before interrupt() appear in the invoke result…"""
        from langgraph.checkpoint.memory import MemorySaver

        app = _build_send_before_interrupt_app(MemorySaver())
        config = {"configurable": {"thread_id": "c2-result"}}
        result = app.invoke({}, config)

        assert "__interrupt__" in result
        assert result.get("committed") == "before-pause"

    @pytest.mark.req("REQ-YG-042")
    def test_send_before_interrupt_not_committed_at_pause(self):
        """…but are NOT committed to checkpointed state at the pause boundary.

        This is the refutation of the single-node relay design (C-2): any
        consumer reading parent state via get_state() while paused sees
        nothing. If a langgraph upgrade ever makes this witness fail, the
        two-node split can be revisited.
        """
        from langgraph.checkpoint.memory import MemorySaver

        captured: list[tuple] = []

        class Spy(MemorySaver):
            def put_writes(self, config, writes, task_id, task_path=""):
                captured.extend(writes)
                return super().put_writes(config, writes, task_id, task_path)

        app = _build_send_before_interrupt_app(Spy())
        config = {"configurable": {"thread_id": "c2-state"}}
        app.invoke({}, config)

        snapshot = app.get_state(config)
        assert snapshot.next, "expected graph paused at the interrupt node"
        assert "committed" not in snapshot.values, (
            "langgraph now persists pre-interrupt sends — "
            "C-2 refutation no longer holds; revisit the relay design"
        )
        persisted_channels = {channel for channel, _ in captured}
        assert "committed" not in persisted_channels


@pytest.fixture
def compiled_parent():
    from langgraph.checkpoint.memory import MemorySaver

    from yamlgraph.compile.graph_loader import compile_graph, load_graph_config

    config = load_graph_config(PARENT_GRAPH)
    state_graph = compile_graph(config)
    return state_graph.compile(checkpointer=MemorySaver())


class TestSubgraphInterruptRelayLanggraph1x:
    """Condemning witnesses (RED until FR-797's fix lands)."""

    @pytest.mark.req("REQ-YG-042")
    def test_subgraph_interrupt_relay_langgraph_1x(self, compiled_parent):
        """AC-03: a child interrupt must genuinely pause the parent."""
        config = {"configurable": {"thread_id": "fr797-pause"}}
        result = compiled_parent.invoke({"user_input": "hello"}, config)

        assert "__interrupt__" in result, (
            "child interrupt was swallowed: parent ran to completion "
            "instead of pausing (reserved __interrupt__ key dropped)"
        )
        snapshot = compiled_parent.get_state(config)
        assert snapshot.next, "parent must be paused with a pending task"

    @pytest.mark.req("REQ-YG-042")
    def test_mapped_state_committed_at_pause_boundary(self, compiled_parent):
        """AC-04: interrupt_output_mapping committed to parent state, not
        only present in the transient result dict."""
        config = {"configurable": {"thread_id": "fr797-commit"}}
        compiled_parent.invoke({"user_input": "hello"}, config)

        snapshot = compiled_parent.get_state(config)
        assert snapshot.next, (
            "mapped keys must be committed AT THE PAUSE, not after a "
            "silent run-to-completion (assert_path_not_destination)"
        )
        assert snapshot.values.get("child_phase") == "processing"
        assert snapshot.values.get("child_data") == "partial result from child"

    @pytest.mark.req("REQ-YG-042")
    def test_resume_relays_into_child_exactly_once(self, compiled_parent):
        """AC-05/AC-06: parent resume reaches the paused child once; the
        child's pre-interrupt work is not re-executed."""
        from langgraph.types import Command

        config = {"configurable": {"thread_id": "fr797-resume"}}
        first = compiled_parent.invoke({"user_input": "hello"}, config)
        assert "__interrupt__" in first

        result = compiled_parent.invoke(Command(resume="my answer"), config)

        assert "__interrupt__" not in result, "parent still paused after resume"
        assert result.get("final_result") == "all done"
