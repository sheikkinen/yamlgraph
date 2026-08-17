# Judgement: FR-813 run_graph_async None initial_state checkpoint regression

**Verdict:** APPROVED - the FR identifies a real FR-811 regression at the supported async runner boundary, proposes the smallest semantics-preserving fix, and freezes the `None` evidence identity without widening the OTel span schema.

**Reviewed against:** `feature-requests/FR-813-run-graph-async-none-input-regression.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/FR-811-otel-programmatic-run-export.md`; `feature-requests/FR-811-otel-programmatic-run-export.judgement.md`; `capabilities/CAP-212-otel-observability-boundary.yaml`; `ARCHITECTURE.md`; `reference/otel-observability.md`; `yamlgraph/observability/otel.py`; `yamlgraph/executor_async.py`; `tests/unit/test_otel_observability.py`; `tests/unit/test_async_executor.py`.

**Prior art:** FR-813 is the governing proposal judged here; FR-811 / CAP-212
/ REQ-YG-570 is the existing OTel runner boundary that this regression fix
repairs. No other FR provides the `run_graph_async(..., None, config)` fix.

## What is sound

The problem is real and source-true. FR-813 cites the exact unconditional normalization that now evaluates `asdict(initial_state)` for every non-dict input (`feature-requests/FR-813-run-graph-async-none-input-regression.md` L21-L35), and the current implementation matches it: `run_graph_async` computes `variables = initial_state if isinstance(initial_state, dict) else asdict(initial_state)` before entering `graph_run_span` or calling `app.ainvoke` (`yamlgraph/observability/otel.py` L267-L313). Because `None` is neither a dict nor a dataclass, the cited `TypeError` is the direct result of the committed code, not a speculative host failure.

The scope is narrow and minimal. FR-813 does not reopen FR-811's exporter, route identity, graph metadata, direct-invocation, or native-streaming decisions; it only restores the already-supported `run_graph_async` invocation path for the `None` input shape (`feature-requests/FR-813-run-graph-async-none-input-regression.md` L13-L17, L151-L153). That aligns with FR-811's frozen boundary: `run_graph_async` is the supported programmatic non-streaming seam, while direct `app.ainvoke`, `app.invoke`, and native streaming remain outside scope (`feature-requests/FR-811-otel-programmatic-run-export.md` L89-L91; `reference/otel-observability.md` L49-L76).

The semantic distinction is correctly preserved. FR-813 explicitly forbids converting `None` to `{}` and freezes different hashes for canonical JSON `null` and `{}` (`feature-requests/FR-813-run-graph-async-none-input-regression.md` L92-L102). That follows the existing privacy/evidence contract: `variables_hash` hashes canonical JSON and exports no raw values (`yamlgraph/observability/otel.py` L105-L112; `reference/otel-observability.md` L80-L95). The cited SHA-256 values for `null` and `{}` are correct.

The implementation approach is feasible with existing tools. The OTel tests already use an in-memory exporter and assert root span attributes without network export (`tests/unit/test_otel_observability.py` L78-L85, L317-L350), and existing async-runner tests already mock `app.ainvoke` and assert call-through behavior (`tests/unit/test_async_executor.py` L124-L144, L187-L205). FR-813's two required witnesses can be added at these same seams.

The architecture classification is **Framework primitive**. The affected function is the public programmatic runner re-exported from `yamlgraph.executor_async` (`yamlgraph/executor_async.py` L351-L360), and CAP-212/REQ-YG-570 already defines `run_graph_async` as part of the OTel observability boundary (`capabilities/CAP-212-otel-observability-boundary.yaml` L20-L22, L43-L50; `ARCHITECTURE.md` L2657-L2665). Fixing the runner boundary is preferable to a host workaround because the runner itself introduced the regression.

## Required revisions

None. Authority is active after human review of this draft.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/observability/otel.py`: `run_graph_async` admits `initial_state=None`, preserves it unchanged for `app.ainvoke`, and uses canonical JSON `null` as the OTel evidence input when hashing is enabled. |
| D-2 | `yamlgraph/observability/otel.py`: type annotations/docstrings for `run_graph_async`, `graph_run_span`, and `variables_hash` are widened only as needed for `None`; runtime serialization remains canonical `json.dumps(..., sort_keys=True, default=str)`. |
| D-3 | `tests/unit/test_otel_observability.py`: disabled-path regression test proves `run_graph_async(app, None, config)` reaches `app.ainvoke(None, config)`, returns its result, and imports no OpenTelemetry package. |
| D-4 | `tests/unit/test_otel_observability.py`: enabled-path test with in-memory exporter proves `yamlgraph.variables.hash` equals the SHA-256 of canonical JSON `null`, does not equal the `{}` hash, and exports no raw values. |
| D-5 | Existing FR-811 dict, `Command`, interrupt, error, missing-extra, missing-metadata, route-id, and concurrency tests remain in force. |
| D-6 | Existing CAP-212 / REQ-YG-570 traceability is retained; changelog fragment and diary reflection are included. |

Not authorized: changing LangGraph checkpoint semantics; converting `None` to `{}`; changing the frozen span names or attribute names; changing route-record grammar; instrumenting direct `app.ainvoke` / `app.invoke`; instrumenting `run_graph_streaming_native` or native streaming; adding a new capability or requirement; changing exporter configuration, graph-name metadata validation, UUIDv7 run identity, or privacy rules except where the `None` evidence identity requires annotation/docstring widening.

## Revised acceptance criteria

- [ ] AC-01: With `YAMLGRAPH_OTEL_EXPORT` unset and `opentelemetry` forced unavailable in `sys.modules`, `await run_graph_async(app, None, config)` returns `app.ainvoke`'s result and awaits `app.ainvoke` exactly once with `(None, config)`.
- [ ] AC-02: The disabled-path RED test fails on v0.5.21/current regression before the fix with `TypeError: asdict() should be called on dataclass instances` and `app.ainvoke` uncalled.
- [ ] AC-03: With OTel enabled and an in-memory exporter installed, `await run_graph_async(app_with_graph_name, None, config)` emits exactly one `yamlgraph.graph.run` root span whose `yamlgraph.variables.hash` is `74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b`.
- [ ] AC-04: The enabled-path test rejects the `{}` hash `44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a` for the `None` input path and asserts no raw values are exported in span attributes.
- [ ] AC-05: Existing dict-input and `Command(resume=...)` FR-811 tests continue to pass without altered expected hashes, call arguments, outcomes, route run IDs, or metadata failures.
- [ ] AC-06: `run_graph_async.initial_state` admits `dict[str, Any] | Command | None`; `graph_run_span` and `variables_hash` annotations admit the `None` hashing path without weakening unrelated public contracts.
- [ ] AC-07: The `run_graph_async` docstring documents `None` as the checkpoint re-run/resume-from-checkpoint input and states that it is passed through to `app.ainvoke` unchanged.
- [ ] AC-08: All new tests are marked with existing `REQ-YG-570`; no new CAP or REQ is created, and strict requirement coverage passes.
- [ ] AC-09: A changelog fragment and `docs/diary/` reflection are included.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | `None` and `{}` must remain distinct LangGraph inputs and distinct evidence identities; substituting either for the other is forbidden. | GATE |
| C-2 | With OTel disabled, the fix must not import OpenTelemetry, require graph metadata, create spans, alter route logging, or change exception/interrupt behavior. | GATE |
| C-3 | With OTel enabled, the fix must preserve FR-811's graph-name metadata validation and missing-extra fail-before-invoke behavior. | GATE |
| C-4 | OTel span attributes must preserve CAP-212's privacy rule: hashes and metadata only, no raw input/state/prompt/completion/tool payloads, exception messages, or tracebacks. | GATE |
| C-5 | Direct compiled-object invocation, native streaming, span schema redesign, exporter configuration changes, and route grammar changes remain outside this authority. | GATE |
| C-6 | The change must be implemented as a focused regression fix in the existing OTel runner boundary; no host-specific ninchat_voice workaround is authorized in this repository. | GATE |

Authority granted: after human review of this draft, the enforcer may implement only the `run_graph_async(..., None, config)` regression fix and its direct tests/documentation within the frozen surfaces above.
