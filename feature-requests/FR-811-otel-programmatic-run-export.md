# Feature Request: OTel exporter configuration and root span for programmatic (non-CLI) graph runs

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Enforced 2026-08-17
**Effort:** 1 day
**Requested:** 2026-08-17
**First consumer / first event:** ninchat_voice (csap) GKE deployment, NC-434 —
the moment its FSM `yamlgraph_async` action runs a graph via
`load_and_compile_async` + `run_graph_async` with
`YAMLGRAPH_OTEL_EXPORT=otlp` set and expects spans in Cloud Trace.

## Summary

FR-759's OTel boundary only exports telemetry for CLI runs. Both the root
`yamlgraph.graph.run` span and — critically — the one-time OTLP exporter
installation (`_configure_exporter_if_needed`) are invoked solely from
`cli/graph_commands.py` via `graph_run_span`. Embedded hosts that use the
documented non-streaming runner (`load_and_compile_async` + `run_graph_async`)
get node spans created against the default no-op ProxyTracerProvider:
`YAMLGRAPH_OTEL_EXPORT=otlp` is set, the `otel` extra is installed, no error is
raised, and **zero telemetry leaves the process**.

## Value Statement

Embedded hosts (ninchat_voice FSM actions, any service importing
`executor_async.run_graph_async`) get the same opt-in span export as CLI users
without copy-pasting `graph_run_span` boilerplate around every invocation.

## Problem

Verified 2026-08-17 against 0.5.20: `node_execution_span` calls
`_ensure_otel_available()` but never `_configure_exporter_if_needed(trace)`.
Only `graph_run_span` configures the provider, and its sole caller is the CLI
(`graph_commands.py:190`). A programmatic run therefore:

1. emits no root span (no run id, no variables hash, no outcome), and
2. exports nothing at all — node spans go to the ProxyTracerProvider.

This violates the FR-759 judgement's own C-3 spirit: "silent success with
missing requested telemetry is never authorized." The missing-extra case
fails fast; the missing-*wiring* case fails silent.

There is no universal invocation seam after compilation: callers may bypass
YAMLGraph and call the returned LangGraph object's `ainvoke` directly. The
supported framework seam is therefore `run_graph_async`, already used by the
first consumer in `yamlgraph/utils/fsm/graph_runner.py`. Direct `ainvoke` and
native streaming are explicitly outside this increment.

## Ideal Result

Any non-streaming graph invocation made through YAMLGraph's documented runners
— CLI or `run_graph_async` — with `YAMLGRAPH_OTEL_EXPORT=otlp` set exports one
`yamlgraph.graph.run` root span with correctly parented
`yamlgraph.node.execute` children and no host-side boilerplate. CLI and async
runners each own their invocation boundary while consuming the same
`graph_run_span` primitive. When the switch is unset, nothing changes (AC-03
of FR-759 preserved).

## Proposed Solution

1. At `load_and_compile_async`, attach the validated YAML graph name as
      `_yamlgraph_graph_name` to every newly compiled graph before caching,
      alongside the existing `_yamlgraph_source_path`. This is immutable execution
      metadata, not state. Cached graph objects expose both attributes.
2. Wrap `run_graph_async`'s `app.ainvoke` call in `graph_run_span`, using that
      graph name and the optional checkpointer `thread_id`. Entering the root span
      configures the exporter and fails before `ainvoke` when the requested OTel
      extra is unavailable. When OTel is enabled and the supplied app lacks a
      non-empty `_yamlgraph_graph_name`, raise `ValueError` before `app.ainvoke`
      with a message that names the missing metadata and directs the caller to
      `load_and_compile_async`; never emit `unknown`, a class name, or a raw path
      as `yamlgraph.graph.name`. OTel-disabled foreign app-like objects retain
      their current behavior.
3. Generate one UUIDv7 at the runner boundary and pass it to both
      `graph_run_span` and the existing `route_run_context`, preserving FR-807's
      one-run/one-identity contract without changing route-log semantics.
4. Treat every call to `run_graph_async` as one invocation and therefore one
      root span. An initial-state dict is hashed through the existing canonical
      `variables_hash` contract. A `Command` resume is normalized with
      `dataclasses.asdict` before hashing; only the resulting SHA-256 is exported.
      A returned `__interrupt__` sets `outcome=interrupted`; an exception sets
      `outcome=error`; all other returns set `outcome=success`. A later resume is
      a separate invocation/root span under the same optional thread id.
5. Keep the CLI wrapper where it is. There is no common post-compilation seam,
      and moving CLI behavior into the async runner would not cover synchronous
      CLI invocation.

`graph_run_span` remains public for hosts that intentionally invoke compiled
LangGraph objects directly. Direct `app.ainvoke`, `app.invoke`, and
`run_graph_streaming_native` are not instrumented by this FR.

## Acceptance Criteria

- [x] AC-01: `load_and_compile_async` attaches `_yamlgraph_graph_name` and
      `_yamlgraph_source_path` to newly compiled graphs before caching; cached
      graph objects expose the same validated graph name and source path.
- [x] AC-02: A `run_graph_async` invocation with OTel enabled and an in-memory
      exporter installed emits exactly one `yamlgraph.graph.run` root span and
      correctly parented `yamlgraph.node.execute` children sharing one trace id.
- [x] AC-03: The programmatic root span carries the frozen FR-759 attributes:
      YAML graph name, UUIDv7 run id, optional thread id, deterministic input
      hash, and `success|error|interrupted` outcome; no raw input/state value is
      exported.
- [x] AC-04: Tests cover success, exception, interrupt, and `Command` resume.
      Each `run_graph_async` call emits one root span; a resume call emits a new
      root span and retains the supplied checkpointer thread id.
- [x] AC-05: When route logging and OTel are both enabled, one caller-generated
      UUIDv7 is shared by `route_run_context` and `graph_run_span`, preserving
      FR-807's identity contract.
- [x] AC-06: With `YAMLGRAPH_OTEL_EXPORT` unset, `run_graph_async` imports no
      OpenTelemetry package and retains its current return, interrupt, route-log,
      and exception behavior.
- [x] AC-07: With OTel requested but the extra unavailable, `run_graph_async`
      raises `OtelExtraMissingError` before calling `app.ainvoke`.
- [x] AC-08: With OTel enabled and `_yamlgraph_graph_name` absent or empty,
      `run_graph_async` raises `ValueError` before `app.ainvoke`; its message
      names `_yamlgraph_graph_name` and `load_and_compile_async`. No fabricated
      graph name or path fallback is authorized.
- [x] AC-09: Exporter configuration remains idempotent and defers to a
      host-installed `TracerProvider`; concurrent `run_graph_async` calls keep
      independent parent contexts and run ids.
- [x] AC-10: Existing CLI OTel tests remain green with the same span schema and
      hello-demo trace artifact. Direct compiled-object invocation and native
      streaming remain explicitly outside this FR.
- [x] AC-11: `reference/otel-observability.md` documents programmatic usage,
      the supported `run_graph_async` boundary, per-invocation resume semantics,
      metadata requirement/failure, and the direct-invocation/streaming
      exclusions.
- [x] AC-12: CAP-212 / REQ-YG-570 and `ARCHITECTURE.md` are updated to include
      the programmatic runner; all new tests carry `@pytest.mark.req` and
      `python scripts/req_coverage.py --strict` passes.
- [x] AC-13: A changelog fragment and `docs/diary/` reflection are included.

## Alternatives Considered

- **Host-side wrapping only (status quo, documented):** ninchat_voice wraps
  its invocation in `graph_run_span` itself. Works today (NC-434 does this
  as interim), but every embedded host must rediscover the silent-no-export
  trap; the framework owns the boundary, so the framework should wire it.
- **Configure exporter in `node_execution_span` only:** exports orphan node
      spans without run identity/outcome — half the schema and still silently
      abandons the requested run contract; rejected.
- **Wrap every object returned by `load_and_compile_async`:** would intercept
      direct `ainvoke`, but changes the documented return type and must proxy the
      full LangGraph runnable API (`ainvoke`, `astream`, state/history methods,
      configuration). Rejected as disproportionate to the first consumer, which
      already uses `run_graph_async`.
- **Instrument native streaming in the same FR:** stream cancellation,
      generator close, timeout, yielded error events, and interrupts require a
      distinct root-span lifecycle contract. Deferred to a separate FR.

## Related

- FR-759 / REQ-YG-570 / CAP-212 — the OTel observability boundary
- `yamlgraph/observability/otel.py` (`_configure_exporter_if_needed`,
  `graph_run_span`), `yamlgraph/compile/node_otel.py`,
  `yamlgraph/cli/graph_commands.py:177-197`
- ninchat_voice NC-434 (first consumer; carries the interim host-side wrap)
- FR-807 / REQ-YG-552 — route evidence record and shared run identity

**Prior art:** FR-759 / CAP-212 / REQ-YG-570 is the governing frozen span
schema and exporter boundary extended here. FR-807 is consumed only for its
shared run-identity and route-context coordination contract; this FR does not
change route-record grammar. `106-otel-observability.md` is the superseded
broad OTel-layer proposal; its metrics, logging, tool/router/FSM phases remain
out of scope. FR-363's `YAMLGRAPH_OTEL_DIR` is a separate copilot-subprocess
file-exporter path and is not modified. FR-467's proposed Mission Control
UI/LangSmith/FSM surface may consume these traces later but is not implemented
here.

## Decisions (2026-08-17)

- The supported programmatic boundary is `run_graph_async`, not arbitrary
      calls on a compiled LangGraph object.
- Each initial or resume call is one invocation and one root span.
- Direct invocation and native streaming are deferred explicitly.
- CAP-212 / REQ-YG-570 are extended rather than creating a second capability
      for the same graph-run/node-execution span schema.

## Judgement (2026-08-17)

**Verdict:** APPROVED — authority active within the scope frozen in
`FR-811-otel-programmatic-run-export.judgement.md`.

Rendered via the sole judge route (`scripts/judge.sh`, model `gpt-5.5`);
R-1 through R-3 from the first judgement were folded before the approved
rejudgement. No human decisions remain open.

## Implementation Status (enforced 2026-08-17)

All acceptance criteria are complete. `load_and_compile_async` attaches graph
metadata before caching. The public `run_graph_async` API now owns one root span
per non-streaming invocation, hashes `Command` resumes without exposing values,
records success/error/interrupted outcomes, shares one UUIDv7 with route
evidence, and fails before invocation when requested telemetry lacks its extra
or required graph metadata. Disabled execution remains a true no-op.

The invocation lifecycle was moved into the existing
`yamlgraph/observability/otel.py` boundary after the broad suite fired the
existing `<400` line gate on `executor_async.py`. This is a narrow structural
deviation from the frozen single-file listing: the public import, behavior, and
authorized scope remain unchanged, while the repository's module-size,
root-module, and generated-map constraints are restored without raising gates.

Validation evidence:

- Focused OTel, async executor, and route-evidence suites: 56 passed.
- Structural witnesses plus affected suites in the final module shape: 64 passed.
- Full fast unit suite: 5,799 passed, 97 skipped, 1 xfailed.
- Strict requirement coverage passed for all registered requirements.
- Ruff format/check and Radon grade-D scans passed on touched Python modules.
