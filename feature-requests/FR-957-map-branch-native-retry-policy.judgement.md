# Judgement: FR-957 Map Branch Native Retry — one owner, LangGraph `RetryPolicy`, exceptions the orchestrator can see

**Verdict:** APPROVED WITH REVISIONS — the branch-level native retry direction is sound, but authority activates only after R-1 through R-6 are folded into the FR and human-reviewed.

**Reviewed against:** `feature-requests/FR-957-map-branch-native-retry-policy.md`; `feature-requests/research-briefs/fr957-map-native-retry-brief.md`; `feature-requests/FR-936-map-node-hardening.md`; `feature-requests/FR-936-map-node-hardening.judgement.md`; `feature-requests/031-native-retry-policy.md`; `feature-requests/030-map-concurrency-control.md`; `feature-requests/FR-672-extract-shared-retry-policy.md`; `feature-requests/FR-676-async-invoke-retry-fallback-parity.md`; `feature-requests/FR-679-consolidate-retry-fallback-post-676.md`; `feature-requests/FR-708-llm-client-request-timeout.md`; `feature-requests/FR-933-retry-cannot-recover-deterministic-rejection.md`; `feature-requests/FR-943-census-row-failure-containment.md`; `feature-requests/TEMPLATE.md`; `docs/plan-web-toolkit.md`; `yamlgraph/compile/map_compiler.py`; `yamlgraph/models/node_schema.py`; `yamlgraph/node_factory/llm_execution.py`; `yamlgraph/executor_base.py`; `yamlgraph/utils/llm_providers.py`; `yamlgraph/utils/route_log.py`; `yamlgraph/constants.py`; `reference/graph-yaml.md`; `reference/map-nodes.md`; `capabilities/CAP-11-subgraph-map.yaml`; `pyproject.toml`; installed LangGraph 1.2.11 `langgraph/graph/state.py`, `langgraph/types.py`, `langgraph/errors.py`, `langgraph/_internal/_constants.py`, `langgraph/_internal/_retry.py`, `langgraph/_internal/_runnable.py`, `langgraph/pregel/_algo.py`, and `langgraph/pregel/_retry.py`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The defect is evidenced at the exact seam this FR proposes to change. `wrap_for_reducer` converts both timeout and general exceptions into successful reducer updates, and the map sub-node is then registered without a retry policy (`yamlgraph/compile/map_compiler.py:142-173,332`). LangGraph 1.2.11 exposes both `retry_policy` and `error_handler` on `StateGraph.add_node`, so repairing exception visibility and attaching the native policy at that registration is feasible. The FR also preserves the FR-936 fence: overflow, payload projection, timeout lifecycle, executor retry, SDK retry, and non-map retry remain separately owned (`feature-requests/FR-957-map-branch-native-retry-policy.md:24-53,251-254`).

The research record is substantive despite the documented reducer failure. The in-body table compares six genuine solution classes, dispositions the relevant proposed, rejected, enforced, and won't-fix precedents, preserves the subtractionist disagreement, and answers `is_this_a_graph` (`feature-requests/FR-957-map-branch-native-retry-policy.md:256-270`). That satisfies the prospective research substance gate without pretending that uncaptured persona output exists.

| Rubric criterion | Finding |
|---|---|
| Scope | The production seam is minimal: typed map configuration, wrapper exception visibility, native node registration, and final branch disposition. The claimed three-file surface is inconsistent with AC-11 and AC-13, which also require tests, capability, reference, changelog, prior-FR, FR-status, and diary artifacts (`feature-requests/FR-957-map-branch-native-retry-policy.md:119-120,243-250`); R-4 corrects the delivery record rather than expanding behavior. |
| Consistency | The ownership order and non-map fence are coherent, but the proposal leaves two policy decisions open after already assuming answers, calls provider exceptions type-evaluated although `RETRYABLE_EXCEPTIONS` contains strings, excludes timeout while that tuple includes `APITimeoutError`, and offers both a native error channel and a speculative side table (`feature-requests/FR-957-map-branch-native-retry-policy.md:145-150,171-196,281-290`). R-1 through R-3 remove those contradictions. |
| Measurability | Attempt counts, final row counts, schema rejection, registration policy, ordering, and diff fences are mechanical (`feature-requests/FR-957-map-branch-native-retry-policy.md:211-254`). AC-10 is not: the route log records route decisions and fan-out, not retry attempts (`yamlgraph/utils/route_log.py:1-24,217-230`). R-5 replaces that claim with an existing LangGraph retry-logger witness. |
| Feasibility | `StateGraph.add_node(..., retry_policy=..., error_handler=...)` and `RetryPolicy` have the stated 1.2.11 signatures. The error handler need not infer `__error__` or use shared mutable state: LangGraph injects `NodeError` into a handler parameter typed `NodeError` (`langgraph/errors.py:149-153`; `langgraph/pregel/_algo.py:1236-1238`). R-2 freezes this supported path. |
| Architecture alignment | The change extends the existing CAP-11 map compiler and Pydantic `NodeConfig` surfaces (`capabilities/CAP-11-subgraph-map.yaml:1-16`; `yamlgraph/models/node_schema.py:61-94,339-347`) and uses LangGraph's native orchestration primitive rather than adding a hidden retry loop. |
| Single responsibility | This is FR-936 D-4 only: branch retry registration, exception visibility, and final disposition are one causal contract. The adjacent map defects are explicitly excluded (`feature-requests/FR-936-map-node-hardening.md:32-40`; `feature-requests/FR-936-map-node-hardening.judgement.md:143-145`). |
| Strategic classification | **Framework primitive.** The fi-catalog pilot, ICPC RFE, CWE classifier, and corpus-census consumers establish more than three use cases, while the existing map abstraction cannot expose failures to LangGraph (`feature-requests/FR-957-map-branch-native-retry-policy.md:8-14,72-105`). |
| Testability | Direct RED tests can fail on attempt count, registration metadata, classification, and exactly-once disposition rather than imports or fixtures. The speculative side table and route-log criterion would make tests implementation-dependent; R-2 and R-5 remove them. |

## Required revisions

### R-1: Freeze the public defaults and limit the `on_error` repair

Replace the two unresolved questions with binding decisions already implied by the example and ownership model:

1. A present `retry:` block with omitted `retry_on` means `[provider_transient]`; an absent `retry:` block installs neither `RetryPolicy` nor `error_handler`.
2. Map `on_error` defaults to `skip`. With `retry:` present, `skip` converts the final exhausted or non-retryable exception exactly once and `fail` re-raises it. Without `retry:`, preserve current runtime behavior; correcting map-wide `on_error: fail` independently of native retry is not authorized.

Update the `reference/graph-yaml.md:623` correction accordingly: it must stop claiming that `fail` is the current map default, but it must not claim that FR-957 repaired non-retry map execution.

### R-2: Use LangGraph's typed `NodeError` injection and delete the side-table fallback

Replace §4's unresolved `__error__`/side-table design with a handler whose signature requests `error: NodeError`. Read the final exception from `error.error` and the failed node from `error.node`; read `_map_index` from the branch state passed as the first argument. LangGraph 1.2.11 explicitly injects this value for `error_handler` callables (`langgraph/errors.py:149-153`; `langgraph/_internal/_runnable.py:401-403`; `langgraph/pregel/_algo.py:1236-1238`).

Delete the thread-safe side-table alternative. Shared mutable exception storage is unnecessary, creates cross-branch cleanup and collision obligations, and is not authorized.

### R-3: Make the closed retry classifier implementable and keep timeout excluded

Replace the claim that imported provider exceptions are evaluated by type. `executor_base.RETRYABLE_EXCEPTIONS` is a tuple of class-name strings, not exception classes (`yamlgraph/executor_base.py:63-75`). Freeze these exact predicates:

| Class | Binding predicate |
|---|---|
| `provider_transient` | Built-in `ConnectionError`; `httpx.HTTPStatusError` or `requests.HTTPError` with status 429 or 500–599; or exact `type(exc).__name__` membership in `RETRYABLE_EXCEPTIONS` **excluding** `APITimeoutError` |
| `provider_server_error` | HTTP status 500–599; or exact class name `InternalServerError` or `ServiceUnavailableError` |
| `rate_limited` | HTTP status 429; or exact class name `RateLimitError` |

Use one predicate builder shared by wrapper re-raise selection and `RetryPolicy.retry_on`; do not call the fuzzy `is_retryable()` predicate, duplicate the retry loop, import optional provider SDKs, or accept YAML import strings/callables. Built-in `TimeoutError`, `concurrent.futures.TimeoutError`, and provider `APITimeoutError` must all remain non-retryable at this branch layer. Reject an empty `retry_on` list at graph load.

### R-4: Replace the false three-file claim with an exact delivery surface

Replace “All changes inside” with the frozen deliverables below. Name one focused test module, preferably `tests/unit/test_fr957_map_native_retry.py`. Record that CAP-11 receives one new requirement entry; do not create a new capability file. Include the FR implementation record because repo doctrine makes the FR the source of truth.

### R-5: Replace the route-log witness with native retry evidence

Remove the claim that each attempt appears in the route decision log and do not modify `yamlgraph/utils/route_log.py`; that public log emits route and fan-out records, not task-attempt records (`yamlgraph/utils/route_log.py:1-24,217-230`). Replace AC-10 with a deterministic `caplog` witness against LangGraph's retry logger: two failed attempts followed by success must produce two native `Retrying task _map_<name>_sub ...` records from `langgraph.pregel._retry` and zero YAMLGraph node-level retry records. Keep LangSmith visibility as an operational consequence of executing the sub-node through LangGraph, not as an acceptance criterion requiring a live external service.

### R-6: Tighten configuration and ownership witnesses

Add schema witnesses for an empty `retry_on` list and `max_interval < initial_interval`. The conflict test must identify the map node and reject only the nested sub-node `on_error: retry` plus map-level `retry:` combination; nested `skip`, `fail`, and `fallback` remain outside this conflict unless existing node validation rejects them. Add a classifier matrix covering every row in R-3, including 429, 503, `RateLimitError`, `APITimeoutError`, `ValueError`, and `ConnectionError`.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/models/node_schema.py`: `RetryClass`, `MapRetryConfig`, map-only validation, conflict validation |
| D-2 | `yamlgraph/compile/map_compiler.py`: one classifier builder, selective exception re-raise, native `RetryPolicy` registration, typed `NodeError` final handler |
| D-3 | `tests/unit/test_fr957_map_native_retry.py`: RED/GREEN witnesses for schema, classifier, registration, attempts, disposition, ordering, and native retry logging |
| D-4 | `capabilities/CAP-11-subgraph-map.yaml` and `ARCHITECTURE.md`: one branch-retry ownership requirement and traceability entry |
| D-5 | `reference/map-nodes.md` and the map property statement at `reference/graph-yaml.md:623` |
| D-6 | `feature-requests/031-native-retry-policy.md`: map-branch supersession note only |
| D-7 | One FR-957 changelog fragment, one diary reflection with `Seed:`, and the FR-957 implementation-status/decision record |

Not authorized: changes to `yamlgraph/executor_base.py`, `yamlgraph/executor.py`, `yamlgraph/executor_async.py`, `yamlgraph/error_handlers.py`, `yamlgraph/node_factory/llm_execution.py`, `yamlgraph/utils/llm_providers.py`, `yamlgraph/utils/route_log.py`, provider SDK configuration, non-map retry, map execution without a `retry:` block, timeout lifecycle or attribution, overflow, payload projection, durability, scheduling, caching, checkpoint format, progress logging, graph/prompt artifacts, or the remaining graph-wide FR-031 proposal.

## Revised acceptance criteria

- [ ] AC-01: `MapRetryConfig` validates `max_attempts >= 1`, positive intervals, `backoff_factor >= 1`, `max_interval >= initial_interval`, and a non-empty list of declared `RetryClass` values.
- [ ] AC-02: `load_graph_config` rejects map `retry:` on non-map nodes, unknown or empty `retry_on`, invalid numeric bounds, and map-level `retry:` combined with nested `node.on_error: retry`; every message names the node and offending field/value.
- [ ] AC-03: A map without `retry:` registers neither `RetryPolicy` nor `error_handler` and preserves its current exception-conversion behavior.
- [ ] AC-04: A 503 `httpx.HTTPStatusError` raised twice then followed by success under `max_attempts: 3` produces exactly three calls, one collected success, no `_error` row, and no `errors` entry.
- [ ] AC-05: A 503 raised through all three attempts under default/explicit `on_error: skip` produces exactly three calls, one row containing `_map_index` and `_error_type == "HTTPStatusError"`, and one `PipelineError`.
- [ ] AC-06: `ValueError`, built-in `TimeoutError`, `concurrent.futures.TimeoutError`, and a class named `APITimeoutError` each execute once and follow the existing converted-row path.
- [ ] AC-07: Exhausted retry with `on_error: fail` raises from the graph; `on_error: skip` and omitted `on_error` each dispose the final failure exactly once.
- [ ] AC-08: Classifier tests cover `ConnectionError`, HTTP 429, HTTP 503, exact-name `RateLimitError`, `InternalServerError`, `ServiceUnavailableError`, `APITimeoutError`, and `ValueError` for all three declared retry classes.
- [ ] AC-09: The compiled `_map_<name>_sub` node carries the configured `RetryPolicy` and a non-`None` error handler only when `retry:` is present; configured values equal the YAML values.
- [ ] AC-10: The final handler receives LangGraph `NodeError`, uses its exception without shared mutable storage, and emits exactly one row and one error for one exhausted branch.
- [ ] AC-11: `_map_index`, `sorted_add` ordering, chained-map behavior, and `flatten_output` remain unchanged after retry.
- [ ] AC-12: `caplog` records exactly two native LangGraph retry messages for a fail/fail/succeed branch and no YAMLGraph node-level retry message.
- [ ] AC-13: CAP-11 and `ARCHITECTURE.md` define one new requirement for map-branch retry ownership; every new test carries its `@pytest.mark.req` marker and `python scripts/req_coverage.py --strict` passes.
- [ ] AC-14: `reference/map-nodes.md` documents fields, defaults, classifier semantics, layered ownership, final disposition, and timeout exclusion; `reference/graph-yaml.md` no longer claims `fail` is the existing map default; FR-031 records map-branch supersession only.
- [ ] AC-15: RED and GREEN are separate commits; RED fails on policy, attempt, classifier, or disposition assertions rather than imports or fixtures.
- [ ] AC-16: The implementation diff touches only D-1 through D-7 and none of the explicitly unauthorized surfaces.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not begin implementation until R-1 through R-6 are folded into FR-957 and this advisory judgement is human-reviewed. | GATE |
| C-2 | Do not store branch exceptions in a side table; consume LangGraph's typed `NodeError` injection. | GATE |
| C-3 | Do not let built-in, futures, or provider API timeout exceptions enter branch-level native retry. | GATE |
| C-4 | Do not expose Python imports/callables through YAML or add another retry loop/classifier owner. | GATE |
| C-5 | Do not modify the route-log public contract to manufacture retry evidence; use LangGraph's native retry logger witness. | GATE |
| C-6 | Do not alter execution for maps lacking `retry:` or cross the FR-936 D-4 fence. | GATE |
| C-7 | Preserve RED then GREEN commits, requirement traceability, focused docs, changelog, FR implementation record, and diary reflection. | GATE |

Authority granted: after R-1 through R-6 are folded and human-reviewed, implementation is limited to D-1 through D-7 under C-1 through C-7.
