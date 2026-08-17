# Judgement: FR-811 OTel exporter configuration and root span for programmatic (non-CLI) graph runs

**Verdict:** APPROVED — the FR extends the existing FR-759 OTel boundary at the documented async runner seam, with narrow scope, mechanically checkable criteria, and explicit exclusions.

**Reviewed against:** `feature-requests/FR-811-otel-programmatic-run-export.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `reference/otel-observability.md`; `ARCHITECTURE.md`; `capabilities/CAP-212-otel-observability-boundary.yaml`; `feature-requests/FR-759-otel-observability-boundary.md`; `feature-requests/FR-759-otel-observability-boundary.judgement.md`; `feature-requests/FR-807-route-evidence-record-hardening.md`; `feature-requests/FR-807-route-evidence-record-hardening.judgement.md`; `feature-requests/106-otel-observability.md`; `feature-requests/FR-363-per-node-otel-scoping-in-copilot-node.md`; `feature-requests/FR-467-mission-control-unified-observability.md`; `yamlgraph/observability/otel.py`; `yamlgraph/compile/node_otel.py`; `yamlgraph/cli/graph_commands.py`; `yamlgraph/executor_async.py`; `yamlgraph/compile/graph_loader.py`; `yamlgraph/utils/fsm/graph_runner.py`; `yamlgraph/utils/route_log.py`; `tests/unit/test_otel_observability.py`; `tests/unit/test_async_executor.py`; `tests/unit/test_fr807_route_evidence_record.py`.

**Prior art:** FR-811 is the governing proposal judged here;
`106-otel-observability.md` is its superseded broad OTel precedent. FR-424,
FR-735, and FR-448 use “programmatic” or “run” in unrelated session-timeline,
WebLLM evidence, and structured-output contexts and do not provide this
`run_graph_async` observability boundary.

## What is sound

The problem is real and source-true. FR-811 identifies that the exporter is configured only by `graph_run_span`, and the current CLI path is the only cited caller around graph invocation (`feature-requests/FR-811-otel-programmatic-run-export.md` L15-L22; `yamlgraph/cli/graph_commands.py` L177-L194). Node spans do not configure the exporter; they only call `node_execution_span`, whose enabled path imports OTEL but does not call `_configure_exporter_if_needed()` (`yamlgraph/observability/otel.py` L233-L261). That makes the stated silent no-export programmatic failure plausible and directly contrary to FR-759's documented "silent success with missing requested telemetry is never authorized" contract (`reference/otel-observability.md` L21-L30).

The proposed seam is the right framework boundary. `run_graph_async` is the documented async convenience wrapper around `app.ainvoke`, including interrupt and `Command(resume=...)` behavior (`yamlgraph/executor_async.py` L195-L232), and the first consumer actually flows through `load_and_compile_async` plus `run_graph_async` (`yamlgraph/utils/fsm/graph_runner.py` L214-L239). The FR explicitly excludes arbitrary direct `ainvoke` and native streaming, avoiding the overbroad wrapper rejected in its alternatives (`feature-requests/FR-811-otel-programmatic-run-export.md` L44-L48, L89-L91, L144-L151).

The implementation approach conforms to existing primitives rather than inventing a second observability path. `graph_run_span` already owns exporter configuration, UUIDv7 run identity, variables hashing, thread id, and outcome attributes (`yamlgraph/observability/otel.py` L194-L230); CLI and route logging already share caller-generated run IDs (`yamlgraph/cli/graph_commands.py` L179-L194; `yamlgraph/utils/route_log.py` L147-L156). FR-811 correctly asks the async runner to consume those primitives and to preserve FR-807's one-run/one-identity route context (`feature-requests/FR-811-otel-programmatic-run-export.md` L75-L77; `feature-requests/FR-807-route-evidence-record-hardening.md` L40-L50).

The scope is clear and minimal. The FR extends CAP-212 / REQ-YG-570 instead of creating a new capability for the same graph-run/node-execution span schema (`feature-requests/FR-811-otel-programmatic-run-export.md` L130-L132, L172-L179), matching the current capability description and requirement surface (`capabilities/CAP-212-otel-observability-boundary.yaml` L6-L20, L27-L47; `ARCHITECTURE.md` L2656-L2664). It also dispositions prior art: FR-759 as the governing schema, FR-807 as route identity coordination, `106-otel-observability.md` as superseded broad scope, FR-363 as separate copilot-subprocess file export, and FR-467 as future consumer (`feature-requests/FR-811-otel-programmatic-run-export.md` L153-L170).

The acceptance criteria are mechanically testable. Existing tests already cover the base span schema, no-op behavior, missing-extra failure, parent/child linkage, supplied route run ID, thread id, interrupted outcome, and deterministic hash (`tests/unit/test_otel_observability.py` L85-L311). Existing async-runner tests cover success, checkpointer config, interrupt, resume, concurrency, and error propagation surfaces (`tests/unit/test_async_executor.py` L123-L204), and FR-807 already has an async route-envelope regression seam for `run_graph_async` (`tests/unit/test_fr807_route_evidence_record.py` L124-L148). FR-811's ACs can be written directly against these seams.

Strategic classification: **Framework primitive**. Programmatic graph execution is a documented YAMLGraph runner, not a single host workaround, and the same opt-in OTel export contract is useful to ninchat_voice, web/API hosts, FSM actions, and any service importing `executor_async.run_graph_async` (`feature-requests/FR-811-otel-programmatic-run-export.md` L24-L29, L50-L58; `ARCHITECTURE.md` L72-L109).

## Required revisions

None. Authority is active as written.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/executor_async.py`: `load_and_compile_async` attaches `_yamlgraph_graph_name` alongside `_yamlgraph_source_path` before caching; cached compiled graphs expose both values. |
| D-2 | `yamlgraph/executor_async.py`: `run_graph_async` wraps exactly one `app.ainvoke` call in `graph_run_span` when OTel is enabled or disabled, preserving disabled behavior and current error propagation. |
| D-3 | `yamlgraph/executor_async.py`: one caller-generated UUIDv7 is shared between `graph_run_span` and `route_run_context` for a single `run_graph_async` invocation. |
| D-4 | `yamlgraph/executor_async.py`: OTel-enabled foreign app-like objects without a non-empty `_yamlgraph_graph_name` raise `ValueError` before `app.ainvoke`, naming `_yamlgraph_graph_name` and `load_and_compile_async`. |
| D-5 | `yamlgraph/executor_async.py`: initial dict inputs and `Command` resume inputs are hashed without exporting raw values; success, error, and interrupted outcomes are assigned per invocation. |
| D-6 | Unit tests for programmatic OTel success, exception, interrupt, `Command` resume, missing extra, missing metadata, disabled no-op, route/OTel run-id sharing, and concurrent invocation isolation. |
| D-7 | `reference/otel-observability.md`, `ARCHITECTURE.md`, and `capabilities/CAP-212-otel-observability-boundary.yaml` / REQ-YG-570 updated to name the programmatic `run_graph_async` boundary. |
| D-8 | Changelog fragment and `docs/diary/` reflection. |

Not authorized: direct `app.ainvoke` / `app.invoke` instrumentation; `run_graph_streaming_native` or native streaming instrumentation; new span types beyond the existing `yamlgraph.graph.run` and `yamlgraph.node.execute`; changes to the frozen span attribute names or privacy rule; route-record grammar changes; LangSmith changes; `YAMLGRAPH_OTEL_DIR` / copilot-subprocess exporter changes; Mission Control UI work; broad OTel metrics/logging/tool/router/FSM phases from `106-otel-observability.md`.

## Revised acceptance criteria

- [ ] AC-01: `load_and_compile_async` attaches `_yamlgraph_graph_name` and `_yamlgraph_source_path` to newly compiled graphs before caching; cached graph objects expose the same validated graph name and source path.
- [ ] AC-02: A `run_graph_async` invocation with OTel enabled and an in-memory exporter installed emits exactly one `yamlgraph.graph.run` root span and correctly parented `yamlgraph.node.execute` children sharing one trace id.
- [ ] AC-03: The programmatic root span carries the frozen FR-759 attributes: YAML graph name, UUIDv7 run id, optional thread id, deterministic input hash, and `success|error|interrupted` outcome; no raw input or state value is exported.
- [ ] AC-04: Tests cover success, exception, interrupt, and `Command` resume. Each `run_graph_async` call emits one root span; a resume call emits a new root span and retains the supplied checkpointer thread id.
- [ ] AC-05: When route logging and OTel are both enabled, one caller-generated UUIDv7 is shared by `route_run_context` and `graph_run_span`, preserving FR-807's identity contract.
- [ ] AC-06: With `YAMLGRAPH_OTEL_EXPORT` unset, `run_graph_async` imports no OpenTelemetry package and retains its current return, interrupt, route-log, and exception behavior.
- [ ] AC-07: With OTel requested but the extra unavailable, `run_graph_async` raises `OtelExtraMissingError` before calling `app.ainvoke`.
- [ ] AC-08: With OTel enabled and `_yamlgraph_graph_name` absent or empty, `run_graph_async` raises `ValueError` before `app.ainvoke`; its message names `_yamlgraph_graph_name` and `load_and_compile_async`. No fabricated graph name or path fallback is authorized.
- [ ] AC-09: Exporter configuration remains idempotent and defers to a host-installed `TracerProvider`; concurrent `run_graph_async` calls keep independent parent contexts and run ids.
- [ ] AC-10: Existing CLI OTel tests remain green with the same span schema and hello-demo trace artifact. Direct compiled-object invocation and native streaming remain explicitly outside this FR.
- [ ] AC-11: `reference/otel-observability.md` documents programmatic usage, the supported `run_graph_async` boundary, per-invocation resume semantics, metadata requirement/failure, and the direct-invocation/streaming exclusions.
- [ ] AC-12: CAP-212 / REQ-YG-570 and `ARCHITECTURE.md` are updated to include the programmatic runner; all new tests carry `@pytest.mark.req` and `python scripts/req_coverage.py --strict` passes.
- [ ] AC-13: A changelog fragment and `docs/diary/` reflection are included.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Preserve FR-759's no-op-disabled contract: with `YAMLGRAPH_OTEL_EXPORT` unset, `run_graph_async` must not import OpenTelemetry and must preserve existing return, interrupt, route-log, and exception behavior. | GATE |
| C-2 | Preserve FR-759's privacy rule: no raw input, state, prompt, completion, tool payload, exception message, or traceback may appear in OTel span attributes; hashes and metadata only. | GATE |
| C-3 | Do not fabricate `yamlgraph.graph.name` for programmatic runs; OTel-enabled apps without `_yamlgraph_graph_name` must fail before invocation with the specified `ValueError`. | GATE |
| C-4 | Preserve FR-807 route evidence semantics: when route logging and OTel are both enabled for one `run_graph_async` invocation, the route `run_id` and OTel `yamlgraph.run.id` are identical, and route-record grammar is not changed. | GATE |
| C-5 | Do not instrument direct compiled-object invocation, synchronous `app.invoke`, or native streaming under this authority. | GATE |
| C-6 | Keep `graph_run_span` public and unchanged for hosts that intentionally own direct invocation wrapping. | GATE |

Authority granted: the enforcer may implement the programmatic `run_graph_async` OTel root-span/exporter wiring and metadata propagation exactly within the surfaces frozen above.
