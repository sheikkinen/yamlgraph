# Feature Request: OpenTelemetry Observability Layer

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 5 days (phased)
**Requested:** 2026-03-04

## Summary

Add OpenTelemetry (OTel) instrumentation alongside the existing LangSmith
integration. LangSmith owns LLM-level tracing (already integrated); OTel owns
everything else — Python tool execution, router decisions, graph compilation,
FSM transitions, TTS/STT latency, and infrastructure metrics.

## Value Statement

Operators get end-to-end distributed traces across all node types (not just LLM
calls), per-node latency histograms, token usage breakdowns by model, and
correlated structured logs — answering "why was this call slow?" without grep.

## Problem

### What We Have

- **126 logging calls** across `yamlgraph/` (25 info, 21 debug, 25 warning, 9 error)
- **LangSmith tracing** via `LangChainTracer` callback — auto-traces all LLM
  invocations with token counts, prompts, completions
- **Token tracking** via `TokenUsageCallbackHandler` — aggregate-only, no per-node breakdown
- **`StructuredFormatter`** — JSON or human-readable, no span context correlation
- **LangSmith tools** — programmatic run querying (`get_run_details`, `get_run_errors`)

### What We're Missing

| Gap | Impact |
|-----|--------|
| No traces for Python tool nodes | "Which tool is slow?" requires manual timing |
| No per-node latency metrics | No P50/P95/P99 per node type |
| No per-node token breakdown | Aggregate total hides expensive nodes |
| No correlation across graph + HTTP + WebSocket | ninchat_voice: can't trace call → TTS → STT → graph → Ninchat |
| No infrastructure metrics | No graph run counts, error rates, compilation times |
| Logs lack span context | Can't filter logs for a specific graph execution |
| LangSmith vendor lock-in | Only backend for observability data |

### Commandment 9

> *Thou shalt define and observe operational truth — Establish measurable
> service objectives; instrument and trace execution; treat performance
> degradation, failure rates, and evaluation drift as production defects.*

Current instrumentation violates this: we trace LLM calls but not the
surrounding orchestration. A graph with 12 nodes has visibility into 3 (the LLM
ones) and none into the other 9 (Python tools, routers).

## Research: OTel vs Extended LangSmith

| Dimension | OpenTelemetry | LangSmith (Extended) |
|-----------|--------------|---------------------|
| **Scope** | Universal: traces, metrics, logs for *any* code | LLM-specific: auto-traces LangChain/LangGraph |
| **GenAI Semantics** | `gen_ai.*` conventions (experimental) for model, agent, MCP | Native LLM understanding: tokens, prompts, evals |
| **Non-LLM nodes** | Full control — wrap any function in a span | Invisible unless `@traceable` per function |
| **Metrics** | First-class: counters, histograms, gauges | Dashboard analytics only, no custom metrics API |
| **Logs** | Bridges Python `logging` → span-correlated export | No log ingestion |
| **Backends** | Open: Jaeger, Grafana Tempo, Datadog, Honeycomb, OTLP | Vendor lock-in to LangSmith SaaS |
| **Cost** | Self-hosted: $0. Cloud: varies | Free tier → paid per trace |
| **Evaluation** | None built-in | Core strength: datasets, evaluators, A/B testing |
| **Context propagation** | W3C trace context across services | LangGraph execution chain only |

**Verdict:** Complementary, not competing. Keep LangSmith for LLM tracing +
evaluation. Add OTel for everything else.

```
┌──────────────────────────────────────────────────┐
│  OTel: Infrastructure + Application traces       │
│  ┌──────────────────────────────────────────────┐│
│  │  LangSmith: LLM calls, evals, prompt eng    ││
│  │  (already integrated, keep as-is)            ││
│  └──────────────────────────────────────────────┘│
│  Python tools, routers, map nodes, FSM states,   │
│  HTTP endpoints, WebSocket, TTS/STT latency      │
└──────────────────────────────────────────────────┘
```

## Proposed Solution

### Phase 0: Foundation (1 day, no behavior change)

**Dependencies:**
```toml
# pyproject.toml [project.optional-dependencies]
otel = [
    "opentelemetry-api>=1.25",
    "opentelemetry-sdk>=1.25",
    "opentelemetry-exporter-otlp>=1.25",
    "opentelemetry-semantic-conventions>=0.46b0",
]
```

**New module:** `yamlgraph/utils/otel.py`
```python
"""OpenTelemetry integration (FR-106).

Gracefully degrades: if opentelemetry-sdk is not installed,
all functions return no-ops. Zero impact on existing behavior.
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)

try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    HAS_OTEL = True
except ImportError:
    HAS_OTEL = False

_initialized = False

def init_otel(service_name: str = "yamlgraph") -> None:
    """Initialize OTel TracerProvider + MeterProvider.

    Reads standard OTEL_* env vars for exporter configuration.
    Safe to call multiple times (idempotent).
    """
    global _initialized
    if not HAS_OTEL or _initialized:
        return
    # ... TracerProvider + OTLP exporter setup
    _initialized = True

def get_tracer(name: str) -> trace.Tracer | None:
    """Get a tracer, or None if OTel not available."""
    if not HAS_OTEL:
        return None
    return trace.get_tracer(name)

def get_meter(name: str) -> metrics.Meter | None:
    """Get a meter, or None if OTel not available."""
    if not HAS_OTEL:
        return None
    return metrics.get_meter(name)
```

**Log bridge:** Extend `setup_logging()` in `utils/logging.py` to attach
OTel `LoggingHandler` when available — existing Python logs get span context
(trace_id, span_id) for free.

### Phase 1: Graph Execution Spans (1 day)

Wrap key execution points in spans:

| Location | Span Name | Attributes |
|----------|-----------|------------|
| `graph_loader.compile_graph()` | `yamlgraph.compile` | `graph.name`, `graph.version`, `node_count`, `edge_count` |
| `llm_nodes.node_fn()` | `yamlgraph.node.{name}` | `node.type`, `node.state_key`, `llm.provider`, `llm.model` |
| `python_tool.execute_python_tool()` | `yamlgraph.tool.{name}` | `tool.module`, `tool.function` |
| `agent.run_agent_loop()` | `yamlgraph.agent.{name}` | `agent.max_iterations`, `agent.tools` |

Pattern (non-invasive):
```python
from yamlgraph.utils.otel import get_tracer

tracer = get_tracer(__name__)

def node_fn(state: dict) -> dict:
    span_ctx = tracer.start_as_current_span(
        f"yamlgraph.node.{node_name}",
        attributes={"node.type": str(node_type), "node.state_key": state_key},
    ) if tracer else nullcontext()

    with span_ctx as span:
        # ... existing node logic ...
        if span:
            span.set_attribute("node.duration_ms", duration_ms)
        return update
```

### Phase 2: GenAI Semantic Conventions (1 day)

Follow OTel GenAI semconv (`gen_ai.*`) for LLM spans:

| Attribute | Value |
|-----------|-------|
| `gen_ai.system` | `anthropic` / `openai` / `google` |
| `gen_ai.request.model` | `claude-3-5-sonnet-20241022` |
| `gen_ai.usage.input_tokens` | from TokenUsageCallbackHandler |
| `gen_ai.usage.output_tokens` | from TokenUsageCallbackHandler |

Extend `TokenUsageCallbackHandler.on_llm_end()` to also set attributes on the
current OTel span (per-node token breakdown, not just aggregate).

Router decisions as span events:
```python
span.add_event("gen_ai.choice", attributes={
    "route_key": route_key,
    "target_node": update["_route"],
    "matched": route_key in routes,
})
```

### Phase 3: Metrics (1 day)

| Metric | Type | Labels |
|--------|------|--------|
| `yamlgraph.node.duration` | Histogram | `node_name`, `node_type`, `graph_name` |
| `yamlgraph.node.error_count` | Counter | `node_name`, `error_type` |
| `yamlgraph.llm.token_usage` | Counter | `direction` (input/output), `model`, `provider` |
| `yamlgraph.graph.run_count` | Counter | `graph_name`, `status` (success/failure) |

### Phase 4: ninchat_voice + FSM (1 day)

| Span | Attributes |
|------|------------|
| `ninchat.tts.speak` | `text_length`, `audio_duration_ms` |
| `ninchat.stt.listen` | `transcript_length`, `silence_timeout` |
| `ninchat.telephony.call` | Root span for entire call lifetime |
| `ninchat.fsm.transition` | `from_state`, `to_state`, `trigger` |

### Phase 5: LangSmith ↔ OTel Bridge (future, optional)

Evaluate when LangSmith ships OTLP export. Until then, both pipelines run
in parallel: LangSmith via `LangChainTracer` callback, OTel via manual spans.

## What NOT to Change

- **Keep LangSmith** for LLM tracing, evaluation, prompt engineering
- **Keep `utils/tracing.py`** — LangChainTracer injection, trace URL sharing
- **Keep `TokenUsageCallbackHandler`** — extend it, don't replace
- **Keep `StructuredFormatter`** — bridge to OTel, don't remove

## Environment Variables

```bash
# Existing (keep)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_...
LANGCHAIN_PROJECT=yamlgraph

# New (OTel) — all standard, no custom env vars
OTEL_SERVICE_NAME=yamlgraph
OTEL_TRACES_EXPORTER=otlp          # or "console" for dev
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_METRICS_EXPORTER=otlp
OTEL_LOGS_EXPORTER=otlp
```

## Backend Options

| Option | Cost | Setup | Best For |
|--------|------|-------|----------|
| Jaeger (Docker) | Free | 5 min | Dev trace visualization |
| Grafana + Tempo + Prometheus | Free self-hosted | 30 min | Full stack |
| Grafana Cloud | Free tier generous | 10 min | Production without infra |
| Datadog / Honeycomb | Paid | 10 min | Enterprise |

## Acceptance Criteria

### Phase 0
- [ ] `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-exporter-otlp` in `pyproject.toml[otel]`
- [ ] `yamlgraph/utils/otel.py` with `init_otel()`, `get_tracer()`, `get_meter()`
- [ ] Graceful degradation: no OTel deps → no-op, zero behavior change
- [ ] Python logging bridge: logs get `trace_id`/`span_id` when OTel active
- [ ] Tests: import without OTel deps doesn't crash

### Phase 1
- [ ] `graph_loader.compile_graph()` emits `yamlgraph.compile` span
- [ ] `llm_nodes.node_fn()` emits `yamlgraph.node.{name}` span with `node.type`
- [ ] `python_tool.execute_python_tool()` emits `yamlgraph.tool.{name}` span
- [ ] `agent.run_agent_loop()` emits `yamlgraph.agent.{name}` span
- [ ] Console exporter integration test: graph run produces trace output

### Phase 2
- [ ] LLM spans include `gen_ai.system`, `gen_ai.request.model`
- [ ] `TokenUsageCallbackHandler` writes `gen_ai.usage.*` to current span
- [ ] Router decisions emit span events with `route_key`, `target_node`

### Phase 3
- [ ] `yamlgraph.node.duration` histogram recorded per node execution
- [ ] `yamlgraph.node.error_count` counter incremented on error
- [ ] `yamlgraph.llm.token_usage` counter per model/provider/direction
- [ ] `yamlgraph.graph.run_count` counter per graph/status

### Phase 4
- [ ] ninchat_voice TTS/STT spans with latency attributes
- [ ] FSM state transitions as span events
- [ ] Twilio call as root span enclosing all child operations

## Constraints

- **Optional dependency**: OTel packages in `[otel]` extra, not in base install
- **Zero overhead when disabled**: `if tracer` guards, no performance tax
- **No LangSmith removal**: both systems coexist permanently
- **Standard env vars only**: `OTEL_*` — no custom configuration
- **GenAI semconv version**: pin to stable when available, use experimental with opt-in flag

## Alternatives Considered

1. **LangSmith only (extend with `@traceable`)** — rejected: no metrics, no
   log correlation, no non-LLM node visibility without per-function decoration,
   vendor lock-in
2. **OTel only (replace LangSmith)** — rejected: LangSmith's evaluation,
   annotation queues, and native LLM understanding are irreplaceable
3. **Custom telemetry module** — rejected: reinventing what OTel already
   standardizes; violates "conform before extending" (Commandment 4)

## Related

- `yamlgraph/utils/tracing.py` — existing LangSmith integration (FR-022)
- `yamlgraph/utils/token_tracker.py` — token callback (REQ-YG-064)
- `yamlgraph/utils/logging.py` — StructuredFormatter
- `ARCHITECTURE.md` CAP-13 — LangSmith Tracing (REQ-YG-047)
- OTel GenAI Semantic Conventions: https://opentelemetry.io/docs/specs/semconv/gen-ai/
