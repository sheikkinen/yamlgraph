"""OpenTelemetry observability boundary (FR-759).

A vendor-neutral, opt-in span schema for graph-run and node-execution
tracing. **Disabled by default**: when ``YAMLGRAPH_OTEL_EXPORT`` is
unset, no OpenTelemetry package is imported and no spans are created —
a true no-op (AC-03).

Enable with::

    YAMLGRAPH_OTEL_EXPORT=otlp yamlgraph graph run examples/demos/hello/graph.yaml \\
        --var name=World --var style=formal

When enabled and the ``otel`` extra is not installed, the run fails
before any node executes with a clear installation error (AC-04,
judgement C-3) — silent success with missing requested telemetry is
never authorized.

Span schema (frozen, judgement R-2; see ``reference/otel-span-schema.md``)::

    yamlgraph.graph.run
        yamlgraph.run.id            str (uuid), required — run identity,
                                     shared by all child spans
        yamlgraph.graph.name        str, required
        yamlgraph.thread.id         str, optional
        yamlgraph.variables.hash    str (sha256 of canonical JSON), required
        yamlgraph.run.outcome       str enum success|error|interrupted, required

    yamlgraph.node.execute
        yamlgraph.node.name           str, required
        yamlgraph.node.type           str, required
        yamlgraph.state.keys_written  list[str], required (key names only)
        yamlgraph.node.error          str, optional (exception class name only)

    both: duration via native OTEL span start/end timestamps.

Privacy rule (judgement C-4, binding): metadata and deterministic
hashes only — never raw variable values, state contents, prompts,
completions, or tool payloads.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

ENV_VAR = "YAMLGRAPH_OTEL_EXPORT"
ENABLED_VALUE = "otlp"

GRAPH_RUN_SPAN = "yamlgraph.graph.run"
NODE_EXECUTE_SPAN = "yamlgraph.node.execute"

# Set once a TracerProvider has been installed by this module or found
# already configured (e.g. by a test's in-memory exporter setup).
_provider_configured = False


class OtelExtraMissingError(ImportError):
    """Raised when OTEL export is requested but the ``otel`` extra is absent."""


@dataclass
class GraphRunContext:
    """Mutable handle yielded by :func:`graph_run_span`.

    ``run_id`` is ``None`` when OTEL is disabled. Callers set
    ``outcome`` to ``"interrupted"`` when a run pauses on an
    interrupt — the span itself cannot see that state.
    """

    run_id: str | None
    outcome: str = "success"


@dataclass
class NodeExecutionContext:
    """Mutable handle yielded by :func:`node_execution_span`."""

    keys_written: list[str] = field(default_factory=list)


def is_otel_enabled() -> bool:
    """Return True when the opt-in OTEL export switch is set (AC-03/04).

    A pure environment-variable check — imports nothing, so checking
    this when disabled costs nothing and touches no OpenTelemetry
    package.
    """
    return os.environ.get(ENV_VAR) == ENABLED_VALUE


def variables_hash(variables: dict[str, Any]) -> str:
    """SHA-256 hex digest of canonical (sorted-key) JSON of ``variables``.

    Never emits raw values (judgement C-4) — only this deterministic
    digest is placed on the span.
    """
    canonical = json.dumps(variables, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _ensure_otel_available() -> Any:
    """Import OpenTelemetry, raising a clear error if the extra is missing.

    Returns the ``opentelemetry.trace`` module on success.
    """
    try:
        from opentelemetry import trace
    except ImportError as e:
        raise OtelExtraMissingError(
            f"{ENV_VAR}={ENABLED_VALUE} requested OTEL export, but the "
            "'otel' extra is not installed. Install it with: "
            'pip install "yamlgraph[otel]"'
        ) from e
    return trace


def _configure_exporter_if_needed(trace: Any) -> None:
    """Configure an OTLP exporter on the global TracerProvider, once.

    Idempotent, and defers to any TracerProvider a test or host
    application has already installed (e.g. one wired to an in-memory
    exporter) rather than overwriting it.
    """
    global _provider_configured
    if _provider_configured:
        return

    from opentelemetry.sdk.trace import TracerProvider

    if isinstance(trace.get_tracer_provider(), TracerProvider):
        # Already configured by the host process/test — respect it.
        _provider_configured = True
        return

    from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
        OTLPSpanExporter,
    )
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)
    _provider_configured = True


@contextmanager
def graph_run_span(
    graph_name: str,
    variables: dict[str, Any],
    thread_id: str | None = None,
) -> Iterator[GraphRunContext]:
    """Start the ``yamlgraph.graph.run`` span (no-op when OTEL is disabled).

    Raises :class:`OtelExtraMissingError` before yielding when OTEL
    export is requested but the extra is unavailable (AC-04) — the
    caller's block, and therefore every node, never runs in that case.
    """
    if not is_otel_enabled():
        yield GraphRunContext(run_id=None)
        return

    trace = _ensure_otel_available()
    _configure_exporter_if_needed(trace)

    run_id = str(uuid.uuid4())
    tracer = trace.get_tracer("yamlgraph")
    with tracer.start_as_current_span(GRAPH_RUN_SPAN) as span:
        span.set_attribute("yamlgraph.run.id", run_id)
        span.set_attribute("yamlgraph.graph.name", graph_name)
        if thread_id:
            span.set_attribute("yamlgraph.thread.id", thread_id)
        span.set_attribute("yamlgraph.variables.hash", variables_hash(variables))

        run_ctx = GraphRunContext(run_id=run_id)
        try:
            yield run_ctx
        except BaseException:
            run_ctx.outcome = "error"
            raise
        finally:
            span.set_attribute("yamlgraph.run.outcome", run_ctx.outcome)


@contextmanager
def node_execution_span(
    node_name: str,
    node_type: str,
) -> Iterator[NodeExecutionContext]:
    """Start the ``yamlgraph.node.execute`` span (no-op when OTEL is disabled).

    Nests under the currently active ``yamlgraph.graph.run`` span via
    OpenTelemetry's own context propagation — no explicit parent
    linkage is threaded by this module.
    """
    if not is_otel_enabled():
        yield NodeExecutionContext()
        return

    trace = _ensure_otel_available()
    tracer = trace.get_tracer("yamlgraph")
    with tracer.start_as_current_span(NODE_EXECUTE_SPAN) as span:
        span.set_attribute("yamlgraph.node.name", node_name)
        span.set_attribute("yamlgraph.node.type", node_type)

        node_ctx = NodeExecutionContext()
        try:
            yield node_ctx
        except BaseException as e:
            span.set_attribute("yamlgraph.node.error", type(e).__name__)
            raise
        finally:
            span.set_attribute("yamlgraph.state.keys_written", node_ctx.keys_written)


__all__ = [
    "ENV_VAR",
    "ENABLED_VALUE",
    "GRAPH_RUN_SPAN",
    "NODE_EXECUTE_SPAN",
    "GraphRunContext",
    "NodeExecutionContext",
    "OtelExtraMissingError",
    "is_otel_enabled",
    "variables_hash",
    "graph_run_span",
    "node_execution_span",
]
