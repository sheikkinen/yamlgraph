"""FR-1058: RunnableConfig propagation and native direct-mode subgraphs.

Two defects reported in issue #474, both caused by the unconditional OTel
node wrapper introduced in FR-759:

1. ``mode: direct`` is dead on arrival. ``create_subgraph_node`` returns a
   ``CompiledStateGraph``, which LangGraph knows how to register natively,
   but the wrapper closes over it and calls it as a function —
   ``TypeError: 'CompiledStateGraph' object is not callable``.
2. The wrapper declares ``otel_wrapped(state)``. LangGraph decides whether to
   inject ``RunnableConfig`` by inspecting the callable's arity, so a
   one-parameter wrapper permanently suppresses injection. Subgraph nodes
   then see ``config=None`` and every parent thread's child collapses onto a
   single child thread id.

These tests are the condemning witnesses. They must fail before the fix.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import TypedDict

import pytest
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.pregel import Pregel

from yamlgraph.compile.graph_loader import compile_graph, load_graph_config
from yamlgraph.compile.node_otel import _maybe_wrap_otel
from yamlgraph.node_factory.subgraph_nodes import _build_child_config
from yamlgraph.observability import otel

FIXTURES = Path(__file__).parent.parent / "fixtures" / "subgraph_direct_fr1058"

try:
    import opentelemetry.sdk as otel_sdk
except ImportError:  # pragma: no cover - exercised only without the extra
    otel_sdk = None

requires_otel_sdk = pytest.mark.skipif(
    otel_sdk is None, reason="requires the 'otel' extra (opentelemetry-sdk)"
)

_SHARED_EXPORTER = None


def _install_shared_provider_once():
    """The global TracerProvider can only be set once per process."""
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
        InMemorySpanExporter,
    )

    global _SHARED_EXPORTER
    if _SHARED_EXPORTER is None:
        _SHARED_EXPORTER = InMemorySpanExporter()
    if not isinstance(trace.get_tracer_provider(), TracerProvider):
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(_SHARED_EXPORTER))
        trace.set_tracer_provider(provider)
    return _SHARED_EXPORTER


@pytest.fixture(autouse=True)
def _reset_otel_env(monkeypatch):
    monkeypatch.delenv(otel.ENV_VAR, raising=False)
    otel._provider_configured = False
    yield
    otel._provider_configured = False


@pytest.fixture
def otel_spans(monkeypatch):
    """Enable OTEL export and yield the cleared in-memory exporter."""
    exporter = _install_shared_provider_once()
    exporter.clear()
    monkeypatch.setenv(otel.ENV_VAR, otel.ENABLED_VALUE)
    otel._provider_configured = True
    return exporter


def _node_spans(exporter):
    """(node_name, node_type) for every yamlgraph.node.execute span."""
    return [
        (
            s.attributes.get("yamlgraph.node.name"),
            s.attributes.get("yamlgraph.node.type"),
        )
        for s in exporter.get_finished_spans()
        if s.name == otel.NODE_EXECUTE_SPAN
    ]


def _compile_fixture(name: str, checkpointer=None):
    config = load_graph_config(FIXTURES / name)
    builder = compile_graph(config)
    return builder, builder.compile(checkpointer=checkpointer)


@pytest.mark.req("REQ-YG-042")
class TestDirectModeRuns:
    """AC-02: a mode: direct child compiles and runs, OTEL off and on."""

    def test_direct_subgraph_runs_with_otel_disabled(self):
        _, app = _compile_fixture("fr-1058-test.yaml")
        assert app.invoke({})["phase"] == "complete"

    @requires_otel_sdk
    def test_direct_subgraph_runs_with_otel_enabled(self, otel_spans):
        _, app = _compile_fixture("fr-1058-test.yaml")
        assert app.invoke({})["phase"] == "complete"

    def test_direct_child_registered_as_native_compiled_graph(self):
        """C-2: the child stays a Pregel. A RunnableLambda or any other
        callable adapter would restore invocability while destroying the
        native checkpoint-namespace inheritance that mode: direct exists for.
        """
        builder, _ = _compile_fixture("fr-1058-test.yaml")
        assert isinstance(builder.nodes["child"].runnable, Pregel)


@pytest.mark.req("REQ-YG-570")
class TestDirectModeSpans:
    """AC-03: no synthetic outer span; child nodes stay instrumented."""

    @requires_otel_sdk
    def test_direct_subgraph_emits_no_outer_subgraph_span(self, otel_spans):
        _, app = _compile_fixture("fr-1058-test.yaml")
        app.invoke({})
        spans = _node_spans(otel_spans)
        assert ("child", "subgraph") not in spans
        assert not [n for n, t in spans if t == "subgraph"]

    @requires_otel_sdk
    def test_direct_subgraph_child_nodes_remain_instrumented(self, otel_spans):
        _, app = _compile_fixture("fr-1058-test.yaml")
        app.invoke({})
        assert "prepare" in [n for n, _ in _node_spans(otel_spans)]


class _S(TypedDict, total=False):
    x: str


def _run_wrapped(node_fn):
    """Compile a one-node graph around the OTel-wrapped fn and invoke it."""
    wrapped = _maybe_wrap_otel(node_fn, "n", "python")
    g = StateGraph(_S)
    g.add_node("n", wrapped)
    g.add_edge(START, "n")
    g.add_edge("n", END)
    app = g.compile(checkpointer=MemorySaver())
    return app.invoke({}, {"configurable": {"thread_id": "T", "tenant": "acme"}})


@pytest.mark.req("REQ-YG-570")
class TestOtelWrapperConfigTransparency:
    """AC-05: all four wrapper cases, asserted on the received payload."""

    def _config_aware(self, seen):
        def node(state, config=None):
            seen["config"] = config
            return {"x": "done"}

        return node

    def _state_only(self, seen):
        # Strict arity: a config= leak raises TypeError rather than passing.
        def node(state):
            seen["called"] = True
            return {"x": "done"}

        return node

    def test_a_config_aware_otel_off_receives_config(self):
        seen = {}
        _run_wrapped(self._config_aware(seen))
        assert seen["config"] is not None
        assert seen["config"]["configurable"]["thread_id"] == "T"

    @requires_otel_sdk
    def test_b_config_aware_otel_on_receives_config_and_emits_span(self, otel_spans):
        seen = {}
        _run_wrapped(self._config_aware(seen))
        assert seen["config"] is not None
        assert seen["config"]["configurable"]["thread_id"] == "T"
        assert ("n", "python") in _node_spans(otel_spans)

    def test_c_state_only_otel_off_called_with_state_only(self):
        """FR-759's disabled no-op contract: no config= leak."""
        seen = {}
        _run_wrapped(self._state_only(seen))
        assert seen.get("called") is True

    @requires_otel_sdk
    def test_d_state_only_otel_on_called_with_state_only(self, otel_spans):
        seen = {}
        _run_wrapped(self._state_only(seen))
        assert seen.get("called") is True
        assert ("n", "python") in _node_spans(otel_spans)


@pytest.mark.req("REQ-YG-042")
class TestInvokeModeThreadIdentity:
    """AC-06: two parent threads must not share one child identity."""

    def test_two_parent_threads_get_distinct_child_threads(self, monkeypatch):
        import yamlgraph.node_factory.subgraph_nodes as sn

        seen = []
        real = sn._build_child_config

        def spy(parent_config, node_name):
            child = real(parent_config, node_name)
            seen.append(child["configurable"])
            return child

        monkeypatch.setattr(sn, "_build_child_config", spy)

        _, app = _compile_fixture("invoke_parent.yaml", checkpointer=MemorySaver())
        for thread in ("parent-a", "parent-b"):
            app.invoke({"phase": "start"}, {"configurable": {"thread_id": thread}})

        assert [c["thread_id"] for c in seen] == ["parent-a:child", "parent-b:child"]

        # Distinct ids are only half the claim. The defect was the child
        # RESUMING INTO the parent's checkpoint, so assert end-to-end that
        # no parent checkpoint coordinate reaches the child on a live run.
        # The forbidden set is spelled out here rather than imported from
        # the implementation, so the test states the contract on its own.
        forbidden = {"checkpoint_id", "checkpoint_ns", "checkpoint_map"}
        for child_configurable in seen:
            leaked = [
                key
                for key in child_configurable
                if key in forbidden or key.startswith("__pregel_")
            ]
            assert not leaked, f"parent routing keys reached the child: {leaked}"


@pytest.mark.req("REQ-YG-042")
class TestBuildChildConfig:
    """AC-07: one table-driven witness for the child-config contract."""

    PARENT = {
        "tags": ["t1"],
        "metadata": {"m": 1},
        "callbacks": None,
        "configurable": {
            "thread_id": "parent-a",
            "tenant": "acme",
            "checkpoint_id": "ck-1",
            "checkpoint_ns": "ns-1",
            "checkpoint_map": {"a": 1},
            "__pregel_task_id": "task-1",
            "__pregel_send": object(),
            "__pregel_read": object(),
            "__pregel_scratchpad": {},
        },
    }

    @pytest.fixture
    def child(self):
        return _build_child_config(dict(self.PARENT), "child")

    @pytest.mark.parametrize("key", ["tags", "metadata", "callbacks"])
    def test_outer_keys_retained(self, child, key):
        assert child[key] == self.PARENT[key]

    def test_ordinary_configurable_keys_retained(self, child):
        assert child["configurable"]["tenant"] == "acme"

    def test_thread_id_derived_from_parent(self, child):
        assert child["configurable"]["thread_id"] == "parent-a:child"

    @pytest.mark.parametrize(
        "key",
        [
            "checkpoint_id",
            "checkpoint_ns",
            "checkpoint_map",
            "__pregel_task_id",
            "__pregel_send",
            "__pregel_read",
            "__pregel_scratchpad",
        ],
    )
    def test_routing_keys_removed(self, child, key):
        """Forwarding these makes the child resume into the parent's
        checkpoint rather than its own."""
        assert key not in child["configurable"]

    def test_parent_config_not_mutated(self):
        parent = {"configurable": {"thread_id": "parent-a", "checkpoint_id": "ck-1"}}
        _build_child_config(parent, "child")
        assert parent["configurable"] == {
            "thread_id": "parent-a",
            "checkpoint_id": "ck-1",
        }


@pytest.mark.req("REQ-YG-042")
class TestDirectModeInterruptDurability:
    """AC-04: a direct child's pause survives a closed SqliteSaver."""

    def test_direct_child_interrupt_resumes_after_reopen(self, tmp_path):
        from langgraph.checkpoint.sqlite import SqliteSaver
        from langgraph.types import Command

        db = tmp_path / "fr1058.sqlite"
        cfg = {"configurable": {"thread_id": "durable-1"}}

        conn = sqlite3.connect(db, check_same_thread=False)
        try:
            _, app = _compile_fixture(
                "direct_interrupt_parent.yaml", checkpointer=SqliteSaver(conn)
            )
            paused = app.invoke({}, cfg)
            assert "__interrupt__" in paused
        finally:
            conn.close()

        conn = sqlite3.connect(db, check_same_thread=False)
        try:
            _, app = _compile_fixture(
                "direct_interrupt_parent.yaml", checkpointer=SqliteSaver(conn)
            )
            resumed = app.invoke(Command(resume="the answer"), cfg)
        finally:
            conn.close()

        assert resumed["phase"] == "complete"
        assert resumed["user_answer"] == "the answer"
