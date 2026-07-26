# OpenTelemetry Observability Boundary (FR-759)

YAMLGraph emits a small, stable, vendor-neutral OpenTelemetry span
schema for graph runs and node executions. It is opt-in and disabled
by default: with no configuration, YAMLGraph imports no OpenTelemetry
package and creates no spans.

LangSmith tracing (`yamlgraph/utils/tracing.py`) is unaffected and
continues to work independently — this boundary is a parallel exporter
path, not a replacement.

## Enabling

```bash
pip install "yamlgraph[otel]"

YAMLGRAPH_OTEL_EXPORT=otlp yamlgraph graph run examples/demos/hello/graph.yaml \
    --var name=World --var style=formal
```

- **Disabled** (`YAMLGRAPH_OTEL_EXPORT` unset or any other value): no
  OpenTelemetry import, no spans, no behavior change.
- **Enabled but the `otel` extra is not installed**: the run fails
  *before any node executes* with a clear installation error naming
  the `otel` extra. Silent success with missing requested telemetry is
  never authorized.
- **Enabled with the extra installed**: spans are exported via OTLP.
  If a host process or test has already installed a `TracerProvider`
  (e.g. wired to an in-memory or console exporter), that provider is
  respected rather than overwritten.

### Where spans go

The exporter is the stock OTLP/HTTP `OTLPSpanExporter()` — destination
and headers are controlled by the standard OpenTelemetry environment
variables, e.g.:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318   # default
export OTEL_EXPORTER_OTLP_HEADERS="authorization=Bearer <token>"
export OTEL_SERVICE_NAME=yamlgraph
```

With no `OTEL_*` variables set, spans are POSTed to
`http://localhost:4318/v1/traces` (the OTLP/HTTP default) — run a local
collector (e.g. Jaeger all-in-one, `grafana/otel-lgtm`, or an
OpenTelemetry Collector) to receive them.

## Span schema (frozen)

| Span | Attribute | Type | Required | Source / rule |
|---|---|---|---|---|
| `yamlgraph.graph.run` | `yamlgraph.run.id` | str (UUIDv7) | required | generated at run start; shared by all child spans (run identity) |
| `yamlgraph.graph.run` | `yamlgraph.graph.name` | str | required | graph YAML `name` (or file stem) |
| `yamlgraph.graph.run` | `yamlgraph.thread.id` | str | optional | checkpointer thread id when present; omitted otherwise |
| `yamlgraph.graph.run` | `yamlgraph.variables.hash` | str | required | sha256 of canonical JSON (sorted keys) of input variables; raw values never emitted |
| `yamlgraph.graph.run` | `yamlgraph.run.outcome` | str enum `success\|error\|interrupted` | required | terminal state |
| `yamlgraph.node.execute` | `yamlgraph.node.name` | str | required | node id from graph YAML |
| `yamlgraph.node.execute` | `yamlgraph.node.type` | str | required | node factory type — the YAML `type` value (`llm`, `router`, `tool`, `python`, `agent`, `tool_call`, `race`, `passthrough`, `copilot`, `subgraph`, …) |
| `yamlgraph.node.execute` | `yamlgraph.state.keys_written` | list[str] | required | key names only, never values |
| `yamlgraph.node.execute` | `yamlgraph.node.error` | str | optional | exception class name only, on failure |
| both | duration | — | required | native OTEL span start/end timestamps (nanoseconds) — no custom attribute |

**Privacy rule (binding):** no raw variable values, state contents,
prompts, completions, or tool payloads ever appear in span attributes —
metadata and deterministic hashes only.

## Run identity and parent/child linkage

Every `yamlgraph graph run` invocation starts one `yamlgraph.graph.run`
span with a fresh `yamlgraph.run.id`. Every node executed during that
run emits a child `yamlgraph.node.execute` span, nested under the
graph-run span via OpenTelemetry's own context propagation (same trace
id, `parent_id` equal to the graph-run span's id) — no explicit linkage
threading is required.

## Coverage (first increment, R-3)

The graph-run span wraps the CLI's `yamlgraph graph run` entry point.
Node-execution spans wrap the `llm`, `router`, `tool`, `python`, `agent`,
`tool_call`, `race`, `passthrough`, `copilot`, and `subgraph` node
types — the set compiled through a single `add_node` call in
`yamlgraph/compile/node_compiler.py`. `map`, `interrupt`, and `verify`
nodes are out of scope for this increment.

Out of scope for this FR (later increments): LLM/tool/route/checkpoint
/interrupt/verification span types, metrics, LangSmith-as-exporter
migration, async/streaming execution paths, and the MCP server /
programmatic (non-CLI) entry points.

## Testing

Unit tests use OpenTelemetry's `InMemorySpanExporter`
(`tests/unit/test_otel_observability.py`) to assert span names,
parent/child linkage, required attributes, success/error/interrupted
outcomes, and the deterministic variables hash — without any network
export. The "extra missing" failure path is exercised by forcing
`import opentelemetry` to fail via `sys.modules` patching, so the test
runs correctly whether or not the `otel` extra happens to be installed
in the current environment. Only the in-memory-exporter tests import
`opentelemetry.sdk` at module scope; that import is optional
(`try`/`except ImportError`) and gates just those tests via a
`skipif` marker, so the disabled and missing-extra tests always
collect and run. CI's `core-test` job deliberately does not install
the `otel` extra, giving the disabled/no-op path a real no-extra
validation environment rather than relying solely on `sys.modules`
patching within an environment that has it installed.

## Related

- `yamlgraph/observability/otel.py` — span creation, enablement check,
  fail-fast guard, variables hash.
- `yamlgraph/compile/node_otel.py` — generic node-execution span wrapper,
  mirroring `yamlgraph/node_timeout.py`'s wrapping pattern.
- `yamlgraph/utils/tracing.py` — the existing LangSmith integration
  (separate, unaffected).
- `YAMLGRAPH_ROUTE_LOG` (FR-723) — route decision log; future route
  spans should correlate with this boundary's run identity.
- `feature-requests/FR-759-otel-observability-boundary.md` — governing FR.
