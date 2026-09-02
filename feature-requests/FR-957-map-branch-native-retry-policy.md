# Feature Request: Map Branch Native Retry — one owner, LangGraph `RetryPolicy`, exceptions the orchestrator can see

**Priority:** HIGH
**Type:** Enhancement
**Status:** Judged — APPROVED WITH REVISIONS
([FR-957-map-branch-native-retry-policy.judgement.md](FR-957-map-branch-native-retry-policy.judgement.md),
2026-09-02, sole route). **R-1–R-6 folded 2026-09-02** into the body
below; the judgement's revised acceptance criteria AC-01–AC-16 and
gates C-1–C-7 are the frozen contract. Authority activates on human
review of the judgement (C-1).
**Effort:** 2 days
**Requested:** 2026-09-02
**First consumer / first event:** the fi-catalog pilot (component D,
`docs/plan-web-toolkit.md`) — the first fan-out large enough that
provider 429/529/5xx bursts across simultaneous branches are routine.
Nearer-term: `examples/icpc-2-rfe` and `examples/cwe-classifier` (38–39
parallel branches per run) and every `examples/demos/corpus_census`
consumer, which today receive transient failures as `_error` rows the
reducer must treat as data.
**Research:** in-body dispositioned alternatives table below (FR-889
style, sanctioned by `TEMPLATE.md`; the judgement accepted this form).
The FR-890 route was run on 2026-09-02 against
`feature-requests/research-briefs/fr957-map-native-retry-brief.md`
(preflight passed, five personas executed) and failed in the reducer:
`precedent names nonexistent FR-030`. FR-030 exists as
`feature-requests/030-map-concurrency-control.md`; the checker at
`examples/demos/research-route/nodes/research_tools.py:391-395` globs
only `FR-{number}` filenames (see FR-936 adjacent findings). No persona
output was persisted and none is claimed.
**Prior art:** [031-native-retry-policy.md](031-native-retry-policy.md)
(Proposed, 2026-02-13) — proposed replacing `on_error: retry` graph-wide
with LangGraph `RetryPolicy`; never judged. **This FR supersedes FR-031
within the map-branch fence only**; FR-031 keeps its status for the
graph-wide scope, which is not authorized here (D-6 adds only a
supersession note). [030-map-concurrency-control.md](030-map-concurrency-control.md)
(Won't Fix) — "concurrency control belongs in LLM provider (RetryPolicy),
not orchestration"; this FR is the RetryPolicy half that closure pointed
at. [FR-936-map-node-hardening.md](FR-936-map-node-hardening.md) — SPLIT
parent, deliverable **D-4**; its judgement R-6/C-4/C-5 and the
rejudgement R-5/AC-07/AC-10/C-5/C-6 fence this FR.
[FR-672-extract-shared-retry-policy.md](FR-672-extract-shared-retry-policy.md)
(Rejected), [FR-676](FR-676-async-invoke-retry-fallback-parity.md) and
[FR-679](FR-679-consolidate-retry-fallback-post-676.md) (Enforced) —
the *prompt-executor* retry loop; a different layer, untouched here.
[FR-933-retry-cannot-recover-deterministic-rejection.md](FR-933-retry-cannot-recover-deterministic-rejection.md)
(Implemented) — node-level `on_error: retry` with validation feedback;
composes (validation errors stay outside the native vocabulary).
[FR-708-llm-client-request-timeout.md](FR-708-llm-client-request-timeout.md)
(Completed) — SDK-level `max_retries=2` on every client: the fourth
retry layer named in the ownership table. [FR-943-census-row-failure-containment.md](FR-943-census-row-failure-containment.md)
— consumes `_error` rows downstream; composes, no overlap.
Vocabulary-only hits dismissed: FR-311/314/330 (watcher retries),
FR-454 (eval timeout). No REJECTED FR governs branch-level retry.

## Summary

Give map branches one retry owner: a typed `retry:` block on the map
node compiles to a LangGraph `RetryPolicy` on the sub-node registration,
the branch wrapper stops swallowing exceptions in the closed retryable
vocabulary so LangGraph can retry them with backoff and jitter, and the
final failure is disposed exactly once — as today's `_error` row — via
LangGraph's per-node `error_handler`, which receives the exception as a
typed `NodeError`. A map without `retry:` is untouched.

## Value Statement

A fan-out of hundreds of branches survives a provider burst with
exponential backoff instead of producing hundreds of `_error` rows or
hammering the API with fixed-count immediate retries, and graph authors
can say in one YAML block which failures are retried, how, and what
happens when retries run out.

## Problem

Retry exists at four layers, none of them owned by the map node and
none visible to the orchestrator:

| Layer | Where | Semantics | Sees which failures |
|---|---|---|---|
| 1. SDK client | `create_llm` clients, `max_retries=2` (FR-708, `yamlgraph/utils/llm_providers.py`) | provider SDK's own retry | transport/5xx as the SDK defines |
| 2. Prompt executor | `executor_base` shared attempt policy (FR-676/679), `is_retryable()` at `yamlgraph/executor_base.py:70-84` | fixed attempts + backoff, structured-output fallback | exception *name* in `RETRYABLE_EXCEPTIONS` (a tuple of class-name strings, `executor_base.py:63-75`) or containing "rate" |
| 3. Node `on_error: retry` | `handle_retry` (`yamlgraph/error_handlers.py:108-136`) from `llm_execution.py:150-156`, `NodeConfig.max_retries` | fixed count, **no backoff, no jitter**, FR-933 validation feedback | everything the node raised |
| 4. Map branch | `wrap_for_reducer` (`yamlgraph/compile/map_compiler.py:139-173`) | **none** — catches `TimeoutError` then bare `Exception`, returns a *successful* update | n/a |

The sub-node is registered with `builder.add_node(sub_node_name,
wrapped_node)` (`map_compiler.py:332`) and no `retry_policy`. LangGraph
1.2.11 exposes `add_node(..., retry_policy=..., error_handler=...)`;
`RetryPolicy` has fields `initial_interval, backoff_factor,
max_interval, max_attempts, jitter, retry_on` (`langgraph/types.py:418-436`),
and LangGraph injects a typed `NodeError` into an `error_handler`
callable whose parameter is annotated `NodeError`
(`langgraph/errors.py:149-153`; `langgraph/_internal/_runnable.py:401-403`;
`langgraph/pregel/_algo.py:1236-1238`). None of it is reachable from
YAML, and attaching a policy at line 332 today would never fire — the
wrapper has already swallowed the exception one frame below (FR-936
judgement C-4).

One adjacent drift is pinned, narrowly (R-1): `reference/graph-yaml.md:623`
documents map-level `on_error: skip | fail` with "`fail` (default)
raises", but `compile_map_node` never reads `config["on_error"]`; a map
branch today always behaves as `skip`. This FR makes `fail` real **only
when a `retry:` block is present**; map execution without `retry:` is
not changed, and the reference stops claiming `fail` is the current
default without claiming this FR repaired non-retry execution.

## Ideal Result

A graph author writes one `retry:` block on a map node and gets
LangGraph's backoff-and-jitter retry on every branch for a declared,
closed set of transient failures; after the last attempt the branch is
disposed exactly once according to `on_error`, producing the same
`_error` row shape consumers already parse; every retry attempt is
LangGraph's own retry, visible in its retry logger and LangSmith trace,
not a hidden loop inside the node.

## Proposed Solution

### 1. Typed `retry:` on map nodes, with frozen defaults (R-1, R-6)

```yaml
nodes:
  classify:
    type: map
    over: "{state.domains}"
    as: domain
    retry:
      max_attempts: 4          # total attempts, LangGraph semantics
      initial_interval: 0.5
      backoff_factor: 2.0
      max_interval: 30.0
      jitter: true
      retry_on: [provider_transient]   # closed vocabulary, §3; default when omitted
    on_error: skip             # final disposition after retries; default
    node:
      type: llm
      prompt: classify_domain
      state_key: label
    collect: labels
```

`MapRetryConfig(BaseModel)`: `max_attempts: int (ge 1) = 3`,
`initial_interval: float (gt 0) = 0.5`, `backoff_factor: float (ge 1)
= 2.0`, `max_interval: float (gt 0) = 128.0` with `max_interval >=
initial_interval`, `jitter: bool = True`, `retry_on: list[RetryClass]`
— **non-empty**, defaulting to `[provider_transient]` when omitted.
`NodeConfig.retry: MapRetryConfig | None`, validated at graph load;
rejected on non-map nodes; rejected when combined with the nested
sub-node's `node.on_error: retry` (two owners), naming the map node.
Nested `skip`, `fail`, `fallback` are not part of this conflict.

Binding defaults: a present `retry:` block with omitted `retry_on`
means `[provider_transient]`; an **absent** `retry:` block installs
neither `RetryPolicy` nor `error_handler` and preserves current
behaviour exactly. Map `on_error` defaults to `skip`.

### 2. Registration and exception visibility

```python
builder.add_node(
    sub_node_name,
    wrapped_node,
    retry_policy=RetryPolicy(**policy.langgraph_kwargs(), retry_on=predicate),
    error_handler=branch_error_handler,   # §4
)
```

`wrap_for_reducer` gains `reraise: Callable[[BaseException], bool] |
None`. With `retry:` configured, exceptions for which `predicate(exc)`
is true are **re-raised** so LangGraph's retry sees them; everything
else keeps today's conversion path. Built-in `TimeoutError`,
`concurrent.futures.TimeoutError` (FR-069/FR-956) and provider
`APITimeoutError` are never re-raised (C-3).

### 3. Closed `retry_on` vocabulary — binding predicates (R-3)

| `RetryClass` | Binding predicate |
|---|---|
| `provider_transient` | built-in `ConnectionError`; `httpx.HTTPStatusError` or `requests.HTTPError` with status 429 or 500–599; or exact `type(exc).__name__` membership in `executor_base.RETRYABLE_EXCEPTIONS` **excluding** `APITimeoutError` |
| `provider_server_error` | HTTP status 500–599; or exact class name `InternalServerError` or `ServiceUnavailableError` |
| `rate_limited` | HTTP status 429; or exact class name `RateLimitError` |

One predicate builder in `map_compiler.py` is shared by wrapper
re-raise selection and `RetryPolicy.retry_on`. It does not call the
fuzzy `is_retryable()`, does not duplicate the executor retry loop,
does not import optional provider SDKs (names are matched as strings,
which is what `RETRYABLE_EXCEPTIONS` holds), and accepts no YAML import
strings or callables (C-4). An empty `retry_on` list is rejected at
load. Not offered: `validation` (FR-933 territory), `timeout`
(FR-956), `any` (Commandment 6).

### 4. Final disposition, exactly once, via typed `NodeError` (R-2)

```python
def branch_error_handler(state: dict, error: NodeError) -> dict:
    exc = error.error                      # the final exception
    index = state.get("_map_index", 0)     # branch payload is the first argument
    ...
```

LangGraph injects the `NodeError` because the parameter is annotated
`NodeError` (`langgraph/errors.py:149-153`; `_runnable.py:401-403`;
`_algo.py:1236-1238`); `error.node` names the failed node. With
`retry:` present: `on_error: skip` (or omitted) emits today's
`{collect_key: [{_map_index, _error, _error_type}], "errors":
[PipelineError]}` update **once**; `on_error: fail` re-raises. No
shared mutable side table exists (C-2). Without `retry:` the handler
is not registered and behaviour is unchanged.

### 5. Ownership table (recorded in `reference/map-nodes.md`)

Layer 1 (SDK) and layer 2 (prompt executor) continue to act *inside* an
attempt; layer 3 (`on_error: retry` on the sub-node) is rejected at load
when a map-level `retry:` block is present; layer 4 (LangGraph
`RetryPolicy` on the branch) is the single owner of cross-attempt retry
for map branches. Without a `retry:` block nothing changes.

### 6. Native retry evidence (R-5)

Retry attempts are witnessed with `caplog` against LangGraph's retry
logger: a fail/fail/succeed branch must produce exactly two native
`Retrying task _map_<name>_sub ...` records from
`langgraph.pregel._retry` and zero YAMLGraph node-level retry records.
`yamlgraph/utils/route_log.py` is not modified — it emits route and
fan-out records, not task-attempt records (C-5). LangSmith visibility
is an operational consequence, not an acceptance criterion.

## Acceptance Criteria

Frozen by the judgement; the enforcer satisfies this list.

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

## Scope (frozen by the judgement; R-4 delivery surface)

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/models/node_schema.py`: `RetryClass`, `MapRetryConfig`, map-only validation, conflict validation |
| D-2 | `yamlgraph/compile/map_compiler.py`: one classifier builder, selective exception re-raise, native `RetryPolicy` registration, typed `NodeError` final handler |
| D-3 | `tests/unit/test_fr957_map_native_retry.py`: RED/GREEN witnesses for schema, classifier, registration, attempts, disposition, ordering, and native retry logging |
| D-4 | `capabilities/CAP-11-subgraph-map.yaml` (one new requirement entry, no new capability file) and `ARCHITECTURE.md` traceability entry |
| D-5 | `reference/map-nodes.md` and the map property statement at `reference/graph-yaml.md:623` |
| D-6 | `feature-requests/031-native-retry-policy.md`: map-branch supersession note only |
| D-7 | One FR-957 changelog fragment, one diary reflection with `Seed:`, and this FR's implementation-status/decision record |

Not authorized: changes to `yamlgraph/executor_base.py`,
`yamlgraph/executor.py`, `yamlgraph/executor_async.py`,
`yamlgraph/error_handlers.py`, `yamlgraph/node_factory/llm_execution.py`,
`yamlgraph/utils/llm_providers.py`, `yamlgraph/utils/route_log.py`,
provider SDK configuration, non-map retry, map execution without a
`retry:` block, timeout lifecycle or attribution (FR-956), overflow
(FR-939), payload projection (FR-955), durability, scheduling, caching,
checkpoint format, progress logging, graph/prompt artifacts, or the
remaining graph-wide FR-031 proposal.

## Alternatives Considered

| class | mechanism | precedent | disposition |
|---|---|---|---|
| 1. LangGraph `RetryPolicy` on the branch + typed `NodeError` `error_handler` for final disposition | §2–§4 above | FR-031 (mechanism), FR-030 closure, LangGraph 1.2.11 `add_node` signature and `NodeError` injection | **CHOSEN** — the only class where the orchestrator both performs and *observes* the retry (judgement C-4) |
| 2. Retry inside `wrap_for_reducer` with a typed backoff policy | keep swallowing, loop with backoff/jitter in the wrapper | `handle_retry` shape; FR-676/679 executor loop | REJECTED — a third hand-rolled loop, invisible to LangGraph; the former "side-table fallback" variant is deleted per R-2 |
| 3. Reuse node-level `on_error: retry` on the sub-node | rely on layer 3 inside `node:` | FR-933 | REJECTED as owner — fixed count, no backoff/jitter; kept as a load-time conflict (AC-02) so two owners cannot coexist |
| 4. Graph-shaped retry: loop edge with `loop_limits` around the map, or a second map over failed rows | YAML only | Pattern 12 quality gate + retry loop in `reference/patterns.md` | REJECTED as the primitive — re-fans out all items or needs manual partitioning; right tool for *semantic* retry (FR-933's territory). `is_this_a_graph`: no for transient faults, yes for quality loops |
| 5. Rely on SDK `max_retries` (FR-708) only | nothing above layer 1 | FR-708 | REJECTED — `llm` sub-nodes only, invisible, uncontrollable per graph |
| 6. Graph-wide native retry now (full FR-031) | replace `on_error: retry` everywhere | FR-031 | REJECTED here — outside the D-4 fence (C-6); FR-031 remains the vehicle if a consumer appears |

Preserved disagreement: the subtractionist position (delete layer 3
for map sub-nodes outright once layer 4 exists) is not taken — AC-02's
load-time conflict achieves single ownership without deleting a
documented feature.

## Related

- [FR-957-map-branch-native-retry-policy.judgement.md](FR-957-map-branch-native-retry-policy.judgement.md)
- `yamlgraph/compile/map_compiler.py:139-173,329-332`
- `yamlgraph/error_handlers.py:108-136`, `yamlgraph/node_factory/llm_execution.py:136-160`
- `yamlgraph/executor_base.py:60-84`, `yamlgraph/utils/llm_providers.py` (FR-708)
- `langgraph/types.py:418-436` (`RetryPolicy`), `langgraph/_internal/_retry.py` (`default_retry_on`), `langgraph/errors.py:149-153` (`NodeError`), `langgraph/pregel/_algo.py:1236-1238`
- `capabilities/CAP-11-subgraph-map.yaml`
- `docs/plan-web-toolkit.md` audit item 4

## Judgement (2026-09-02)

**Verdict:** APPROVED WITH REVISIONS — see
[FR-957-map-branch-native-retry-policy.judgement.md](FR-957-map-branch-native-retry-policy.judgement.md)
for the full rubric, R-1–R-6, AC-01–AC-16 and C-1–C-7. R-1–R-6 are
folded above (§1 frozen defaults and narrowed `on_error` repair; §4
typed `NodeError`, side table deleted; §3 binding predicates with
timeout excluded; §Scope exact delivery surface; §6 `caplog` witness
replacing the route-log claim; §1 extra schema and conflict witnesses).
Authority activates on human review.

### Questions for the human (as options, or 'none')

None. Both earlier questions were resolved by the judgement (R-1):
`retry_on` defaults to `[provider_transient]`; `on_error: fail` becomes
real only with a `retry:` block present.
