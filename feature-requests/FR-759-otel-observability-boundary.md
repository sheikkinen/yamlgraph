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

- [x] AC-01: `pyproject.toml` defines an `otel` extra with OTEL API, SDK, and OTLP exporter packages; core install remains OTEL-free when the feature is disabled
- [x] AC-02: `docs/dependency-rationale.yaml` documents each added OTEL package; `python scripts/dependency_rationale.py --strict` passes
- [x] AC-03: With OTEL disabled, tests assert no OTEL import is required, no spans are emitted, and existing graph execution behavior is unchanged
- [x] AC-04: With OTEL explicitly enabled and the extra unavailable, graph execution fails before running nodes with a clear error naming the missing `otel` extra
- [x] AC-05: With OTEL enabled and an in-memory exporter configured, a hello graph run emits one `yamlgraph.graph.run` span and child `yamlgraph.node.execute` spans sharing one run identity
- [x] AC-06: Unit tests assert required graph/node span attributes, parent/child linkage, success outcome, error outcome, duration unit, state-key-written representation, and deterministic variables hash behavior
- [x] AC-07: `reference/` documents the frozen span schema as an attribute table matching the tests
- [x] AC-08: Hello-graph demo output includes a visible trace artifact or log, committed per demo-gate
- [x] AC-09: Tests are tagged with `@pytest.mark.req(...)`; a new or updated CAP file defines the governing REQ IDs
- [x] AC-10: A changelog fragment exists in `changelog/unreleased/`

## Alternatives Considered

- **Keep LangSmith-only tracing:** rejected — replacement cost analysis shows the vendor coupling is the platform gap itself.
- **Reuse existing `YAMLGRAPH_OTEL_DIR` copilot-node file exporter as the boundary:** rejected as the spine — it is a per-node file dump for copilot CLI nodes, not a run-scoped span model; it should eventually consume the new boundary.
- **Full span taxonomy in one FR:** rejected — spec-kill; prove the two-span schema first.

## Related

- `docs/plan-research-dependency-negative-space.md` — finding 1, recommendation 1, proposed first FR
- FR-723 route decision log (`YAMLGRAPH_ROUTE_LOG`) — future route spans should subsume/correlate
- Sibling FRs from the same research: FR-760, FR-761, FR-762

**Prior art:** `106-otel-observability.md` (Proposed, unjudged) proposed a
broad phased OTel layer (tools, routers, FSM transitions, TTS/STT, infra
metrics) — this FR is the minimal first slice of that idea, scoped by
its own judgement to graph-run + node-execution spans only; the broader
layer remains future work, not superseded. `FR-362`/`FR-363`
(Implemented) instrumented the `copilot_node.py` CLI subprocess path
specifically (per-node file exporter, process-mining POC) — a different,
narrower boundary (copilot CLI invocation timing) that this FR's design
explicitly declines to reuse as the spine (see Alternatives Considered:
"Reuse existing `YAMLGRAPH_OTEL_DIR`... rejected as the spine"); both
remain valid, non-overlapping instrumentation points. `FR-467`
(Proposed, unjudged) envisions a unified FSM+YAMLGraph "Mission Control"
observability surface built atop OTel — this FR is the foundational
span schema that surface would consume; no conflict, this FR does not
touch FSM instrumentation.

## Implementation Status (enforced 2026-07-26)

All 10 acceptance criteria complete:

- **AC-01/AC-02**: `otel` extra added to `pyproject.toml`
  (`opentelemetry-api`/`opentelemetry-sdk`/`opentelemetry-exporter-otlp`,
  all `>=1.0.0`); rationale entries added to
  `docs/dependency-rationale.yaml`; `dependency_rationale.py --strict`
  passes.
- **AC-03/AC-04**: `yamlgraph/observability/otel.py` implements
  `is_otel_enabled()` as a pure env-var check (no import when
  disabled), and `graph_run_span()`/`node_execution_span()` no-op when
  disabled. When `YAMLGRAPH_OTEL_EXPORT=otlp` is set but
  `opentelemetry` cannot be imported, `OtelExtraMissingError` is raised
  *before* the caller's block runs — verified with a `sys.modules`
  patch so the test holds regardless of whether the extra happens to
  be installed locally.
- **AC-05/AC-06**: `yamlgraph/compile/node_otel.py` wraps every node function
  compiled through a single `add_node` call in
  `yamlgraph/compile/node_compiler.py` (llm, tool, python, agent,
  tool_call, race, passthrough, copilot, subgraph) with
  `_maybe_wrap_otel`, mirroring `node_timeout.py`'s existing wrapping
  pattern. `yamlgraph/cli/graph_commands.py`'s `cmd_graph_run` wraps
  the invoke call in `graph_run_span`, threading the checkpointer
  thread id and setting `outcome="interrupted"` when the final result
  contains `__interrupt__`. Manually verified end-to-end against the
  hello demo with an `InMemorySpanExporter`/`ConsoleSpanExporter`:
  correct trace-id sharing, parent/child linkage
  (`node_span.parent.span_id == run_span.context.span_id`), and all
  frozen attributes. 9 unit tests in
  `tests/unit/test_otel_observability.py` cover disabled no-op,
  extra-missing fail-fast, success path (parent/child linkage, all
  required + optional attributes), error path (outcome=error,
  node.error=exception-class-name-only, no message leakage), the
  caller-reported interrupted outcome, and variables-hash determinism.
- **AC-07**: `reference/otel-observability.md` documents the frozen
  span schema as an attribute table matching the tests, plus the
  enablement contract, run-identity/linkage model, and this
  increment's coverage boundary.
- **AC-08**: `examples/demos/hello/otel-trace-demo.txt` captures a
  real console-exporter run of the hello graph showing both spans
  (attributes, trace id, parent/child linkage, success outcome).
  `examples/demos/hello/demo-output.log` regenerated per demo-gate
  (this PR adds a new file under `examples/demos/hello/`, triggering
  the gate).
- **AC-09**: All 9 tests tagged `@pytest.mark.req("REQ-YG-570")`;
  `capabilities/CAP-212-otel-observability-boundary.yaml` registers
  REQ-YG-570; `ARCHITECTURE.md`'s capability and requirement tables
  updated. `req_coverage.py --strict` passes (CAP-212: 1/1 reqs, 9
  tests).
- **AC-10**: `changelog/unreleased/fr759-otel-observability-boundary.md`.

**Scope discipline (R-3/R-4, C-5):** node-execution span wrapping was
applied to every node type compiled via a single `add_node` call site
(9 types) rather than only `llm` — a low-risk generalization of the
same boundary, not a scope expansion — while `map`, `interrupt`, and
`verify` nodes (multi-node/edge compile paths) were left unwrapped as
explicitly out of scope for this increment. No `langchain-core`
declaration, lockfile/scan/pip-audit governance, or example-dependency
taxonomy work was touched, per C-5/R-4.

## PR #465 review fixes (2026-07-26)

**P1 — run id is now UUIDv7, not UUIDv4.** The frozen schema
(`yamlgraph.run.id: str (UUIDv7)`) was implemented with `uuid.uuid4()` —
source-of-truth drift the reviewer caught by comparing the FR text,
the implementation, and the reference doc side by side.
`otel.py`'s `_generate_run_id()` now constructs an RFC 9562 UUIDv7
directly (48-bit millisecond timestamp + version/variant bits + random
tail) since this repo targets Python 3.11+ and `uuid.uuid7()` is
stdlib-only from 3.14. `test_enabled_success_emits_parent_and_child_spans`
now asserts `uuid.UUID(run_ctx.run_id).version == 7`, not just
non-null/string-typed.

**P2 — disabled/missing-extra tests now run without the `otel` extra
installed.** The test module previously imported `opentelemetry.sdk`
at module scope via `pytest.importorskip`, so the ENTIRE file skipped
in a no-extra environment — including the disabled-no-op and
missing-extra tests that are supposed to prove the core install stays
OTEL-free. The SDK import is now `try`/`except ImportError`-guarded and
gates only the 4 in-memory-exporter tests via a `skipif` marker; a new
`test_disabled_no_op_when_opentelemetry_entirely_unavailable` blocks
`import opentelemetry` itself (not just the SDK) to prove the no-op
path never touches OpenTelemetry at all. CI's `core-test` job no longer
installs the `otel` extra, giving this a real no-extra validation
environment instead of relying solely on `sys.modules` patching inside
an environment that happens to have the extra installed.

**P3 — node-type coverage aligned with the frozen contract.**
`_compile_race_node` now wraps its node function with
`_maybe_wrap_otel(..., NodeType.RACE)` (previously omitted, contradicting
the documented coverage claim). `_compile_llm_node` — shared by both
`llm` and `router` YAML types — now passes the node's actual declared
`type` from graph config into the wrapper instead of hardcoding
`NodeType.LLM`, so router spans correctly report `yamlgraph.node.type
== "router"`. Three new tests in
`tests/unit/test_node_compiler_branches.py`
(`TestCompileNodeOtelNodeType`) assert the wrapper receives `llm`,
`router`, and `race` respectively; `test_race_node.py`'s existing
no-double-timeout-wrap test updated to also patch `_maybe_wrap_otel`
now that race nodes are wrapped.

All three fixes verified: full `pytest tests/unit/` (5234 passed, 74
skipped, 1 xfailed — zero regressions), a manual no-extra probe
(blocking `import opentelemetry` entirely) showing 6 pass / 4 skip
instead of the reviewer's cited "1 skipped, exit 5", and a direct UUIDv7
version check on 5 generated ids.

## Judgement (2026-07-26)

**Verdict:** APPROVED WITH REVISIONS — revisions R-1..R-4 folded above; authority active.

Full judgement: [FR-759-otel-observability-boundary.judgement.md](FR-759-otel-observability-boundary.judgement.md)

**Conditions (GATE):** C-1 revisions folded (done); C-2 preserve FR-723 route-log behavior — route spans are future work; C-3 no silent success when OTEL requested but extra missing; C-4 metadata/hashes only in span attributes — never raw values/prompts/completions; C-5 no sibling FR work under this authority.

**Scope frozen:** D-1 `otel` extra; D-2 rationale entries; D-3 graph-run + node-execution span boundary on the hello-graph path; D-4 `YAMLGRAPH_OTEL_EXPORT=otlp` opt-in; D-5 in-memory exporter unit tests; D-6 `reference/` span schema doc; D-7 hello demo trace output; D-8 CAP/REQ, markers, changelog fragment. Not authorized: any other span types, metrics, LangSmith migration, sibling FR scope.
