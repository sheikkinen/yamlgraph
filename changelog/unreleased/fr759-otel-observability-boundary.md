---
type: feat
scope: observability
req: REQ-YG-570
---
- **FR-759 OpenTelemetry Observability Boundary**: a vendor-neutral,
  opt-in OTEL span schema for graph runs and node executions. Disabled
  by default (no OpenTelemetry import, no spans, no behavior change);
  enabled via `YAMLGRAPH_OTEL_EXPORT=otlp`, which fails fast before any
  node executes when the new `otel` extra is not installed. Emits one
  `yamlgraph.graph.run` span per invocation (UUIDv7 run identity, sha256
  variables hash, `success|error|interrupted` outcome) with child
  `yamlgraph.node.execute` spans (node name/type — including `router`,
  distinct from `llm` — state keys-written, optional error-class-name)
  sharing one trace id with correct parent/child linkage across all 9
  wrapped node types (`llm`, `router`, `tool`, `python`, `agent`,
  `tool_call`, `race`, `passthrough`, `copilot`, `subgraph`). The
  disabled/missing-extra tests run without the `otel` extra installed;
  CI's `core-test` job validates this no-extra path directly. LangSmith
  tracing is unaffected — this is a parallel exporter path. Round 2 fix:
  `_configure_exporter_if_needed()`'s own SDK/exporter imports now raise
  `OtelExtraMissingError` on a partial install instead of a raw
  `ImportError` (previously only the top-level `opentelemetry` import
  was guarded); 2 new regression tests.
  (REQ-YG-570, CAP-212)
