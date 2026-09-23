"""Shared unit-test fixtures.

The OpenTelemetry provider fixture lives here because the global
``TracerProvider`` can only be set **once per process**. When two test
modules each kept a private exporter and installed the provider
themselves, whichever ran first won: the second module's
``isinstance(get_tracer_provider(), TracerProvider)`` check short-circuited,
its exporter was never attached to the live provider, and it observed zero
spans. The failure was order-dependent and invisible under ``-n auto``,
which scattered the two modules across different workers (FR-1058).

One exporter per process, owned here, is the fix.
"""

import pytest

from yamlgraph.observability import otel

_SHARED_EXPORTER = None


def _install_shared_provider_once():
    """Install one process-wide provider backed by a shared exporter.

    Spans are cleared between tests rather than the provider replaced,
    because replacing it is not possible.
    """
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


@pytest.fixture
def in_memory_exporter(monkeypatch):
    """Enable OTEL export and yield the shared in-memory exporter, cleared."""
    exporter = _install_shared_provider_once()
    otel._provider_configured = True
    exporter.clear()
    monkeypatch.setenv(otel.ENV_VAR, otel.ENABLED_VALUE)
    return exporter
