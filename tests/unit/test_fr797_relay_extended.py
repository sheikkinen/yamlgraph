"""FR-797 extended relay witnesses: AC-06..AC-10 (rejudgement scope).

Fixture graphs are written to tmp_path — test-local artifacts, not governed
demo graphs (C-4). Each test names the seam it exercises.
"""

from pathlib import Path
from textwrap import dedent

import pytest

pytestmark = pytest.mark.process

CHILD_MULTI_INTERRUPT = dedent(
    """
    version: "1.0"
    name: multi-interrupt-child
    state:
      input_message: str
      phase: str
      first_answer: str
      second_answer: str
    nodes:
      stage_one:
        type: passthrough
        output:
          phase: "one"
      ask_first:
        type: interrupt
        message: "first?"
        state_key: q1
        resume_key: first_answer
      stage_two:
        type: passthrough
        output:
          phase: "two"
      ask_second:
        type: interrupt
        message: "second?"
        state_key: q2
        resume_key: second_answer
      finalize:
        type: passthrough
        output:
          phase: "complete"
    edges:
      - from: START
        to: stage_one
      - from: stage_one
        to: ask_first
      - from: ask_first
        to: stage_two
      - from: stage_two
        to: ask_second
      - from: ask_second
        to: finalize
      - from: finalize
        to: END
    """
)

CHILD_NO_INTERRUPT = dedent(
    """
    version: "1.0"
    name: plain-child
    state:
      input_message: str
      result: str
    nodes:
      work:
        type: passthrough
        output:
          result: "done by child"
    edges:
      - from: START
        to: work
      - from: work
        to: END
    """
)

CHILD_SINGLE_INTERRUPT = dedent(
    """
    version: "1.0"
    name: single-interrupt-child
    state:
      input_message: str
      phase: str
      user_answer: str
    nodes:
      process:
        type: passthrough
        output:
          phase: "processing"
      ask_user:
        type: interrupt
        message: "answer?"
        state_key: question
        resume_key: user_answer
      finalize:
        type: passthrough
        output:
          phase: "complete"
    edges:
      - from: START
        to: process
      - from: process
        to: ask_user
      - from: ask_user
        to: finalize
      - from: finalize
        to: END
    """
)


def _parent_yaml(
    child_file: str, node_extra: str = "", edges: str | None = None
) -> str:
    edges_block = edges or (
        "edges:\n"
        "  - from: START\n"
        "    to: run_child\n"
        "  - from: run_child\n"
        "    to: done\n"
        "  - from: done\n"
        "    to: END\n"
    )
    return (
        'version: "1.0"\n'
        "name: relay-parent\n"
        "checkpointer:\n"
        "  type: memory\n"
        "state:\n"
        "  user_input: str\n"
        "  child_phase: str\n"
        "  final_result: str\n"
        "nodes:\n"
        "  run_child:\n"
        "    type: subgraph\n"
        f"    graph: {child_file}\n"
        "    input_mapping:\n"
        "      user_input: input_message\n"
        "    output_mapping:\n"
        "      final_result: phase\n"
        f"{node_extra}"
        "  done:\n"
        "    type: passthrough\n"
        "    output:\n"
        '      final_result: "all done"\n' + edges_block
    )


def _compile(tmp_path: Path, parent_yaml: str, children: dict[str, str]):
    from langgraph.checkpoint.memory import MemorySaver

    from yamlgraph.compile.graph_loader import compile_graph, load_graph_config

    for name, content in children.items():
        (tmp_path / name).write_text(content)
    parent = tmp_path / "parent.yaml"
    parent.write_text(parent_yaml)
    config = load_graph_config(parent)
    return compile_graph(config).compile(checkpointer=MemorySaver())


MAPPING_EXTRA = "    interrupt_output_mapping:\n" "      child_phase: phase\n"


class TestMultiInterruptChild:
    @pytest.mark.req("REQ-YG-042")
    def test_two_pause_resume_cycles_commit_at_both_boundaries(self, tmp_path):
        """AC-06: two child interrupts → two parent pauses, mapped state
        committed at each boundary, replay-safe resume across both."""
        from langgraph.types import Command

        app = _compile(
            tmp_path,
            _parent_yaml("child.yaml", node_extra=MAPPING_EXTRA),
            {"child.yaml": CHILD_MULTI_INTERRUPT},
        )
        config = {"configurable": {"thread_id": "fr797-multi"}}

        first = app.invoke({"user_input": "go"}, config)
        assert "__interrupt__" in first
        snap1 = app.get_state(config)
        assert snap1.next
        assert snap1.values.get("child_phase") == "one"

        second = app.invoke(Command(resume="answer-1"), config)
        assert "__interrupt__" in second, "second child interrupt must pause again"
        snap2 = app.get_state(config)
        assert snap2.next
        assert snap2.values.get("child_phase") == "two"

        final = app.invoke(Command(resume="answer-2"), config)
        assert "__interrupt__" not in final
        assert final.get("final_result") == "all done"


class TestCheckpointerContract:
    @pytest.mark.req("REQ-YG-042")
    def test_child_without_checkpointer_gets_default_relay_saver(self, tmp_path):
        """AC-07: child YAML declares no checkpointer → in-process default
        enables pause/resume (non-durable relay)."""
        from langgraph.types import Command

        app = _compile(
            tmp_path,
            _parent_yaml("child.yaml", node_extra=MAPPING_EXTRA),
            {"child.yaml": CHILD_SINGLE_INTERRUPT},
        )
        config = {"configurable": {"thread_id": "fr797-defaultsaver"}}
        assert "__interrupt__" in app.invoke({"user_input": "hi"}, config)
        result = app.invoke(Command(resume="ok"), config)
        assert result.get("final_result") == "all done"

    @pytest.mark.req("REQ-YG-042")
    def test_child_declared_checkpointer_honored(self, tmp_path):
        """AC-07: child-declared memory checkpointer is honored and relays."""
        from langgraph.types import Command

        child = CHILD_SINGLE_INTERRUPT.replace(
            "name: single-interrupt-child",
            "name: single-interrupt-child\ncheckpointer:\n  type: memory",
        )
        app = _compile(
            tmp_path,
            _parent_yaml("child.yaml", node_extra=MAPPING_EXTRA),
            {"child.yaml": child},
        )
        config = {"configurable": {"thread_id": "fr797-declared"}}
        assert "__interrupt__" in app.invoke({"user_input": "hi"}, config)
        result = app.invoke(Command(resume="ok"), config)
        assert result.get("final_result") == "all done"

    @pytest.mark.req("REQ-YG-042")
    def test_non_relay_child_interrupt_fails_loud(self):
        """AC-07: an interrupt surfacing from a child that is not
        relay-capable by detection raises ValueError naming the child."""
        from yamlgraph.node_factory.subgraph_nodes import (
            _guard_unrelayed_interrupt,
        )

        with pytest.raises(ValueError, match="child.yaml"):
            _guard_unrelayed_interrupt(
                {"__interrupt__": [object()]},
                "run_child",
                Path("subgraphs/child.yaml"),
            )
        # Clean output passes through untouched.
        _guard_unrelayed_interrupt({"ok": 1}, "run_child", Path("c.yaml"))


class TestStateFieldSynthesis:
    PARENT_CONFIG = {
        "name": "relay-parent",
        "nodes": {
            "run_child": {
                "type": "subgraph",
                "graph": "child.yaml",
                "interrupt_output_mapping": {"child_phase": "phase"},
            },
            "plain_child": {
                "type": "subgraph",
                "graph": "plain.yaml",
                "output_mapping": {"x": "y"},
            },
        },
    }

    @pytest.mark.req("REQ-YG-042")
    def test_runtime_state_includes_relay_fields_for_relay_nodes_only(self):
        """AC-08: build_state_class synthesizes relay internals for
        relay-capable subgraph nodes and excludes them otherwise."""
        from yamlgraph.models.state_builder import build_state_class

        state_cls = build_state_class(self.PARENT_CONFIG)
        keys = state_cls.__annotations__.keys()
        assert "__run_child_paused__" in keys
        assert "__run_child_payload__" in keys
        assert "__run_child_resume__" in keys
        assert "__plain_child_paused__" not in keys

    @pytest.mark.req("REQ-YG-042")
    def test_codegen_includes_relay_fields_for_relay_nodes_only(self):
        """AC-08: generated TypedDict code has the same include/exclude."""
        from yamlgraph.models.state_builder import generate_typeddict_code

        code = generate_typeddict_code(self.PARENT_CONFIG)
        assert "__run_child_paused__" in code
        assert "__run_child_payload__" in code
        assert "__run_child_resume__" in code
        assert "__plain_child_paused__" not in code


class TestRelayScopeBoundaries:
    @pytest.mark.req("REQ-YG-042")
    def test_interrupt_child_without_mapping_still_relays(self, tmp_path):
        """AC-09: child CAN interrupt, no interrupt_output_mapping → parent
        still pauses and resumes (broadened relay scope, R-1)."""
        from langgraph.types import Command

        app = _compile(
            tmp_path,
            _parent_yaml("child.yaml"),
            {"child.yaml": CHILD_SINGLE_INTERRUPT},
        )
        config = {"configurable": {"thread_id": "fr797-nomap"}}
        result = app.invoke({"user_input": "hi"}, config)
        assert "__interrupt__" in result, "no-mapping interrupt child must relay"
        done = app.invoke(Command(resume="ok"), config)
        assert done.get("final_result") == "all done"

    @pytest.mark.req("REQ-YG-042")
    def test_non_interrupt_child_keeps_single_node_compilation(self, tmp_path):
        """AC-09: invoke-mode child that cannot interrupt compiles as one
        node — no __run/__pause split, behavior unchanged."""
        app = _compile(
            tmp_path,
            _parent_yaml("child.yaml"),
            {"child.yaml": CHILD_NO_INTERRUPT},
        )
        node_names = set(app.get_graph().nodes)
        assert "run_child" in node_names
        assert "run_child__run" not in node_names
        assert "run_child__pause" not in node_names
        result = app.invoke(
            {"user_input": "hi"}, {"configurable": {"thread_id": "fr797-plain"}}
        )
        assert result.get("final_result") == "all done"


class TestConditionalOutgoingRejected:
    @pytest.mark.req("REQ-YG-042")
    def test_conditional_outgoing_edge_from_relay_node_fails_compile(self, tmp_path):
        """AC-10: condition on the relay node's outgoing edge is a
        compile-time error (Phase-1 scope, J-13/J-15)."""
        edges = dedent(
            """
            edges:
              - from: START
                to: run_child
              - from: run_child
                to: done
                condition: "child_phase == 'processing'"
              - from: run_child
                to: END
              - from: done
                to: END
            """
        )
        with pytest.raises(Exception, match="run_child"):
            _compile(
                tmp_path,
                _parent_yaml("child.yaml", node_extra=MAPPING_EXTRA, edges=edges),
                {"child.yaml": CHILD_SINGLE_INTERRUPT},
            )
