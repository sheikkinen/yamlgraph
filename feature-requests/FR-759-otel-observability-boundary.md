# Feature Request: OpenTelemetry Observability Boundary

**Priority:** HIGH
**Type:** Feature
**Status:** Judged
**Effort:** 3 days
**Requested:** 2026-07-26
**First consumer / first event:** An agent diagnosing a failed graph run in an environment without LangSmith access, at the moment it needs the run's node/LLM/route timeline without rerunning the graph.

## Summary

Add a vendor-neutral OpenTelemetry boundary to YAMLGraph: a small, stable span schema for graph and node execution, an optional `otel` extra (API/SDK/OTLP exporter), and one opt-in exporter path validated on a hello graph. LangSmith remains supported but stops being the only operational truth surface.

## Value Statement

Operators and agents get YAMLGraph-shaped traces (graph run, node, LLM call, route decision) exportable to any OTLP backend, so observability survives a LangSmith replacement and works in CI/local environments.

## Problem

From `docs/plan-research-dependency-negative-space.md` (finding 1, ranked recommendation 1):

- Tracing today is LangSmith/LangChain-shaped, not YAMLGraph-shaped. There is no stable span/event model for graph run, node execution, LLM invocation, tool call, routing decision, retry, interrupt, checkpoint, or verification gate outcomes.
- If LangSmith is replaced, tracing and callback integration must be redesigned simultaneously — the observability spine is a vendor integration, not a YAMLGraph contract.
- Route logs (`YAMLGRAPH_ROUTE_LOG`), LangSmith traces, and CLI output share no common run identity.

Commandment 9 requires operational truth to be YAMLGraph-owned; today it is ecosystem-borrowed.

## Ideal Result

Every graph run can emit a stable YAMLGraph OTEL trace with graph-run and node-execution spans (LLM, tool, route, checkpoint, interrupt, verification spans as later increments), correlated under one run identity, exported via OTLP behind an opt-in env/config switch. LangSmith becomes one exporter among several, not the spine.

## Proposed Solution

Minimal path back from the ideal (per the research doc's proposed first FR):

1. Add an `otel` optional extra:

```toml
[project.optional-dependencies]
otel = [
    "opentelemetry-api>=1.0.0",
    "opentelemetry-sdk>=1.0.0",
    "opentelemetry-exporter-otlp>=1.0.0",
]
```

2. Define the first small span schema — **graph run** and **node execution only** — frozen as the attribute table below (R-2). Attribute names follow OpenTelemetry GenAI semantic conventions where they apply; exceptions are pinned in the table.

   | Span | Attribute | Type | Req | Source / rule |
   |---|---|---|---|---|
   | `yamlgraph.graph.run` | `yamlgraph.run.id` | str (UUIDv7) | required | generated at run start; shared by all child spans (run identity) |
   | `yamlgraph.graph.run` | `yamlgraph.graph.name` | str | required | graph YAML `name` or file stem |
   | `yamlgraph.graph.run` | `yamlgraph.thread.id` | str | optional | checkpointer thread id when present; omitted otherwise |
   | `yamlgraph.graph.run` | `yamlgraph.variables.hash` | str | required | sha256 of canonical JSON (sorted keys) of input variables; raw values never emitted |
   | `yamlgraph.graph.run` | `yamlgraph.run.outcome` | str enum `success\|error\|interrupted` | required | terminal state |
   | `yamlgraph.node.execute` | `yamlgraph.node.name` | str | required | node id from graph YAML |
   | `yamlgraph.node.execute` | `yamlgraph.node.type` | str | required | node factory type (llm, router, map, …) |
   | `yamlgraph.node.execute` | `yamlgraph.state.keys_written` | list[str] | required | key names only, never values |
   | `yamlgraph.node.execute` | `yamlgraph.node.error` | str | optional | exception class name only on failure |
   | both | duration | — | required | native OTEL span start/end timestamps (nanoseconds) |

   Privacy rule (binding, judgement C-4): no raw variable values, state contents, prompts, completions, or tool payloads in span attributes — metadata and deterministic hashes only.

3. Wire one opt-in exporter path behind `YAMLGRAPH_OTEL_EXPORT=otlp`. Failure contract (R-1):
   - OTEL **not enabled**: core install performs no OTEL import and changes no behavior (no-op).
   - OTEL **explicitly enabled but `otel` extra absent**: the run fails before graph execution with a clear installation error naming the `otel` extra. Silent success with missing requested telemetry is not authorized.
4. First-increment execution surface (R-3): the path exercised by `yamlgraph graph run examples/demos/hello/graph.yaml` must produce one graph-run span and child node-execution spans under one run identity. Unit tests use an in-memory exporter to assert parent/child linkage, span names, key attributes, success outcome, and error outcome.

Out of scope (later FRs): LLM/tool/route/checkpoint/interrupt/verification spans, metrics, LangSmith-as-exporter migration, async/streaming paths. Sibling boundary (R-4): this FR may add only the `otel` optional dependency group and its rationale entries — it must not implement FR-760's `langchain-core` declaration, FR-761's lockfile/direct-import scan/pip-audit governance, or FR-762's example taxonomy.

## Acceptance Criteria (revised per judgement)

- [ ] AC-01: `pyproject.toml` defines an `otel` extra with OTEL API, SDK, and OTLP exporter packages; core install remains OTEL-free when the feature is disabled
- [ ] AC-02: `docs/dependency-rationale.yaml` documents each added OTEL package; `python scripts/dependency_rationale.py --strict` passes
- [ ] AC-03: With OTEL disabled, tests assert no OTEL import is required, no spans are emitted, and existing graph execution behavior is unchanged
- [ ] AC-04: With OTEL explicitly enabled and the extra unavailable, graph execution fails before running nodes with a clear error naming the missing `otel` extra
- [ ] AC-05: With OTEL enabled and an in-memory exporter configured, a hello graph run emits one `yamlgraph.graph.run` span and child `yamlgraph.node.execute` spans sharing one run identity
- [ ] AC-06: Unit tests assert required graph/node span attributes, parent/child linkage, success outcome, error outcome, duration unit, state-key-written representation, and deterministic variables hash behavior
- [ ] AC-07: `reference/` documents the frozen span schema as an attribute table matching the tests
- [ ] AC-08: Hello-graph demo output includes a visible trace artifact or log, committed per demo-gate
- [ ] AC-09: Tests are tagged with `@pytest.mark.req(...)`; a new or updated CAP file defines the governing REQ IDs
- [ ] AC-10: A changelog fragment exists in `changelog/unreleased/`

## Alternatives Considered

- **Keep LangSmith-only tracing:** rejected — replacement cost analysis shows the vendor coupling is the platform gap itself.
- **Reuse existing `YAMLGRAPH_OTEL_DIR` copilot-node file exporter as the boundary:** rejected as the spine — it is a per-node file dump for copilot CLI nodes, not a run-scoped span model; it should eventually consume the new boundary.
- **Full span taxonomy in one FR:** rejected — spec-kill; prove the two-span schema first.

## Related

- `docs/plan-research-dependency-negative-space.md` — finding 1, recommendation 1, proposed first FR
- FR-723 route decision log (`YAMLGRAPH_ROUTE_LOG`) — future route spans should subsume/correlate
- Sibling FRs from the same research: FR-760, FR-761, FR-762

**Prior art:** `106-otel-observability.md` (Proposed) is an earlier, undeveloped proposal on the same topic — superseded by this judged FR's concrete span schema and phased scope; not a duplicate to merge. `FR-363-per-node-otel-scoping-in-copilot-node.md` (Implemented) covers per-node OTEL export for copilot CLI nodes specifically — a narrower, already-shipped mechanism this FR's `YAMLGRAPH_OTEL_DIR` alternative explicitly declines to use as the spine (see Alternatives Considered). `FR-467-mission-control-unified-observability.md` (Proposed) is a higher-level dashboard/UI concern layered on top of a trace source; it consumes spans, it does not define them, so it does not overlap this FR's span-schema scope. `FR-231-model-provider-timing-comparison.md` (Implemented) is a one-off timing comparison tool, not a standing span schema or exporter boundary. None require scope changes here.

## Judgement (2026-07-26)

**Verdict:** APPROVED WITH REVISIONS — revisions R-1..R-4 folded above; authority active.

Full judgement: [FR-759-otel-observability-boundary.judgement.md](FR-759-otel-observability-boundary.judgement.md)

**Conditions (GATE):** C-1 revisions folded (done); C-2 preserve FR-723 route-log behavior — route spans are future work; C-3 no silent success when OTEL requested but extra missing; C-4 metadata/hashes only in span attributes — never raw values/prompts/completions; C-5 no sibling FR work under this authority.

**Scope frozen:** D-1 `otel` extra; D-2 rationale entries; D-3 graph-run + node-execution span boundary on the hello-graph path; D-4 `YAMLGRAPH_OTEL_EXPORT=otlp` opt-in; D-5 in-memory exporter unit tests; D-6 `reference/` span schema doc; D-7 hello demo trace output; D-8 CAP/REQ, markers, changelog fragment. Not authorized: any other span types, metrics, LangSmith migration, sibling FR scope.
