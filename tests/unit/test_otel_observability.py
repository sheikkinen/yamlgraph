"""OpenTelemetry observability boundary tests (FR-759).

Covers the graph-run / node-execution span schema: disabled no-op
behavior (AC-03), fail-fast when OTEL is requested but the ``otel``
extra is unavailable (AC-04), and — with an in-memory exporter — span
names, parent/child linkage, required attributes, success/error
outcomes, and the deterministic variables hash (AC-05/AC-06).
"""

from __future__ import annotations

import sys

import pytest

# Guard: opentelemetry is an optional extra ("otel")
otel_sdk = pytest.importorskip("opentelemetry.sdk")

from opentelemetry import trace  # noqa: E402
from opentelemetry.sdk.trace import TracerProvider  # noqa: E402
from opentelemetry.sdk.trace.export import SimpleSpanProcessor  # noqa: E402
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (  # noqa: E402
    InMemorySpanExporter,
)

from yamlgraph.observability import otel  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_otel_env(monkeypatch):
    """Ensure OTEL is disabled by default and the module's provider-configured
    latch is reset between tests, since it is process-global state."""
    monkeypatch.delenv(otel.ENV_VAR, raising=False)
    otel._provider_configured = False
    yield
    otel._provider_configured = False


_SHARED_EXPORTER = InMemorySpanExporter()


def _install_shared_provider_once():
    """OpenTelemetry's global TracerProvider can only be set once per
    process — install a single provider backed by a shared in-memory
    exporter and clear its captured spans between tests instead of
    replacing the provider."""
    if isinstance(trace.get_tracer_provider(), TracerProvider):
        return
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(_SHARED_EXPORTER))
    trace.set_tracer_provider(provider)


@pytest.fixture
def in_memory_exporter(monkeypatch):
    """Enable OTEL export and yield the shared in-memory exporter, cleared."""
    _install_shared_provider_once()
    otel._provider_configured = True
    _SHARED_EXPORTER.clear()
    monkeypatch.setenv(otel.ENV_VAR, otel.ENABLED_VALUE)
    return _SHARED_EXPORTER


@pytest.mark.req("REQ-YG-570")
def test_disabled_is_true_no_op():
    """AC-03: disabled by default; graph_run_span yields a None run id."""
    assert otel.is_otel_enabled() is False
    with otel.graph_run_span("g", {"a": 1}) as run_ctx:
        assert run_ctx.run_id is None
        assert run_ctx.outcome == "success"


@pytest.mark.req("REQ-YG-570")
def test_disabled_node_span_is_no_op():
    """AC-03: node_execution_span no-ops when disabled — no attributes set,
    no OpenTelemetry import triggered by the check itself."""
    assert otel.is_otel_enabled() is False
    with otel.node_execution_span("greet", "llm") as node_ctx:
        node_ctx.keys_written = ["greeting"]  # caller may still mutate freely


@pytest.mark.req("REQ-YG-570")
def test_disabled_unchanged_behavior_node_wrapper():
    """AC-03: the node wrapper calls node_fn directly when OTEL is disabled —
    identical return value, no span machinery involved."""
    from yamlgraph.compile.node_otel import _maybe_wrap_otel

    def node_fn(state):
        return {"out": state["in"] * 2}

    wrapped = _maybe_wrap_otel(node_fn, "double", "python")
    assert wrapped({"in": 21}) == {"out": 42}


@pytest.mark.req("REQ-YG-570")
def test_enabled_but_extra_missing_fails_before_execution(monkeypatch):
    """AC-04: OTEL explicitly enabled, package import unavailable → fails
    before any node runs, with a clear error naming the 'otel' extra."""
    monkeypatch.setenv(otel.ENV_VAR, otel.ENABLED_VALUE)
    # Simulate the extra being absent: force `import opentelemetry` to fail.
    monkeypatch.setitem(sys.modules, "opentelemetry", None)

    executed = False
    with (
        pytest.raises(otel.OtelExtraMissingError, match="otel"),
        otel.graph_run_span("g", {}),
    ):
        executed = True  # pragma: no cover - must not run
    assert executed is False


@pytest.mark.req("REQ-YG-570")
def test_enabled_success_emits_parent_and_child_spans(in_memory_exporter):
    """AC-05/AC-06: enabled + in-memory exporter → one graph-run span, one
    child node-execution span, sharing a trace id (run identity), correct
    parent/child linkage, and success outcome."""
    from yamlgraph.compile.node_otel import _maybe_wrap_otel

    def node_fn(state):
        return {"greeting": "hi", "current_step": "greet"}

    wrapped = _maybe_wrap_otel(node_fn, "greet", "llm")

    variables = {"name": "World", "style": "formal"}
    with otel.graph_run_span("hello-world", variables) as run_ctx:
        assert run_ctx.run_id is not None
        wrapped({})

    spans = in_memory_exporter.get_finished_spans()
    by_name = {s.name: s for s in spans}
    assert set(by_name) == {otel.GRAPH_RUN_SPAN, otel.NODE_EXECUTE_SPAN}

    run_span = by_name[otel.GRAPH_RUN_SPAN]
    node_span = by_name[otel.NODE_EXECUTE_SPAN]

    # Shared run identity: same trace, node span parented by the run span.
    assert node_span.context.trace_id == run_span.context.trace_id
    assert node_span.parent.span_id == run_span.context.span_id

    # Required graph-run attributes (frozen schema).
    assert run_span.attributes["yamlgraph.run.id"] == run_ctx.run_id
    assert run_span.attributes["yamlgraph.graph.name"] == "hello-world"
    assert run_span.attributes["yamlgraph.variables.hash"] == otel.variables_hash(
        variables
    )
    assert run_span.attributes["yamlgraph.run.outcome"] == "success"
    assert "yamlgraph.thread.id" not in run_span.attributes  # optional, omitted

    # Required node-execution attributes.
    assert node_span.attributes["yamlgraph.node.name"] == "greet"
    assert node_span.attributes["yamlgraph.node.type"] == "llm"
    assert list(node_span.attributes["yamlgraph.state.keys_written"]) == [
        "greeting",
        "current_step",
    ]
    assert "yamlgraph.node.error" not in node_span.attributes  # optional, omitted

    # Duration: native OTEL span timestamps, not a custom attribute.
    assert run_span.end_time > run_span.start_time
    assert node_span.end_time > node_span.start_time


@pytest.mark.req("REQ-YG-570")
def test_enabled_with_thread_id_sets_optional_attribute(in_memory_exporter):
    """AC-06: yamlgraph.thread.id is set when a checkpointer thread id is
    supplied, and omitted otherwise (already covered above)."""
    with otel.graph_run_span("g", {}, thread_id="thread-42"):
        pass

    spans = in_memory_exporter.get_finished_spans()
    run_span = next(s for s in spans if s.name == otel.GRAPH_RUN_SPAN)
    assert run_span.attributes["yamlgraph.thread.id"] == "thread-42"


@pytest.mark.req("REQ-YG-570")
def test_graph_run_error_outcome_and_node_error_attribute(in_memory_exporter):
    """AC-06: an exception inside the run sets outcome=error on the graph-run
    span and yamlgraph.node.error (exception class name only) on the node
    span — never the exception message or a traceback."""
    from yamlgraph.compile.node_otel import _maybe_wrap_otel

    def failing_node(state):
        raise ValueError("do not leak this message onto the span")

    wrapped = _maybe_wrap_otel(failing_node, "boom", "python")

    with pytest.raises(ValueError), otel.graph_run_span("g", {}):
        wrapped({})

    spans = in_memory_exporter.get_finished_spans()
    by_name = {s.name: s for s in spans}
    run_span = by_name[otel.GRAPH_RUN_SPAN]
    node_span = by_name[otel.NODE_EXECUTE_SPAN]

    assert run_span.attributes["yamlgraph.run.outcome"] == "error"
    assert node_span.attributes["yamlgraph.node.error"] == "ValueError"
    for span in (run_span, node_span):
        for value in span.attributes.values():
            assert "do not leak this message" not in str(value)


@pytest.mark.req("REQ-YG-570")
def test_graph_run_interrupted_outcome(in_memory_exporter):
    """AC-06: caller-reported interrupted outcome (the CLI sets this when the
    result contains __interrupt__, which the span itself cannot observe)."""
    with otel.graph_run_span("g", {}) as run_ctx:
        run_ctx.outcome = "interrupted"

    spans = in_memory_exporter.get_finished_spans()
    run_span = next(s for s in spans if s.name == otel.GRAPH_RUN_SPAN)
    assert run_span.attributes["yamlgraph.run.outcome"] == "interrupted"


@pytest.mark.req("REQ-YG-570")
def test_variables_hash_is_deterministic_and_key_order_independent():
    """AC-06: sha256 of canonical (sorted-key) JSON — order independent,
    never the raw values themselves."""
    h1 = otel.variables_hash({"name": "World", "style": "formal"})
    h2 = otel.variables_hash({"style": "formal", "name": "World"})
    h3 = otel.variables_hash({"name": "Other", "style": "formal"})

    assert h1 == h2
    assert h1 != h3
    assert "World" not in h1
    assert len(h1) == 64  # sha256 hex digest length
