# Feature Request: Map Branch Native Retry — one owner, LangGraph `RetryPolicy`, exceptions the orchestrator can see

**Priority:** HIGH
**Type:** Enhancement
**Status:** Proposed
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
style, sanctioned by `TEMPLATE.md`). The FR-890 route was run on
2026-09-02 against `feature-requests/research-briefs/fr957-map-native-retry-brief.md`
(preflight passed, five personas executed) and failed in the reducer:
`precedent names nonexistent FR-030`. FR-030 exists as
`feature-requests/030-map-concurrency-control.md`; the checker at
`examples/demos/research-route/nodes/research_tools.py:391-395` globs
only `FR-{number}` filenames (see FR-936 adjacent findings). No persona
output was persisted.
**Prior art:** [031-native-retry-policy.md](031-native-retry-policy.md)
(Proposed, 2026-02-13) — proposed replacing `on_error: retry` graph-wide
with LangGraph `RetryPolicy` for backoff, jitter and conditional retry;
never judged. **This FR supersedes FR-031 within the map-branch fence
only**: same mechanism, one node registration, and it resolves the
exception-visibility problem FR-031 never saw. FR-031 keeps its status
for the graph-wide scope, which is not authorized here.
[030-map-concurrency-control.md](030-map-concurrency-control.md) (Won't
Fix) — "concurrency control belongs in LLM provider (RetryPolicy), not
orchestration"; this FR is the RetryPolicy half that closure pointed at
and never wired. [FR-936-map-node-hardening.md](FR-936-map-node-hardening.md)
— SPLIT parent, deliverable **D-4**; its judgement R-6 found the
parent's `retry=` spelling wrong and the wrapper's exception swallowing
fatal; C-4/C-5 and the rejudgement R-5/AC-07/AC-10/C-5/C-6 fence this
FR. [FR-672-extract-shared-retry-policy.md](FR-672-extract-shared-retry-policy.md)
(Rejected), [FR-676](FR-676-async-invoke-retry-fallback-parity.md) and
[FR-679](FR-679-consolidate-retry-fallback-post-676.md) (Enforced) —
the *prompt-executor* retry loop and its sync/async consolidation into
`executor_base`; a different layer, untouched here, but it is one of the
owners this FR must reconcile against. [FR-933-retry-cannot-recover-deterministic-rejection.md](FR-933-retry-cannot-recover-deterministic-rejection.md)
(Implemented) — node-level `on_error: retry` now carries validation
feedback; this FR composes with it (validation errors stay outside the
native retryable vocabulary). [FR-708-llm-client-request-timeout.md](FR-708-llm-client-request-timeout.md)
(Completed) — sets `max_retries=2` on every provider client: a fourth,
SDK-level retry layer that this FR's ownership table must name.
[FR-943-census-row-failure-containment.md](FR-943-census-row-failure-containment.md)
— consumes `_error` rows downstream; composes, no overlap (its
judgement says so). Vocabulary-only hits dismissed: FR-311/314/330
(watcher retries), FR-454 (eval timeout). No REJECTED FR governs
branch-level retry.

## Summary

Give map branches one retry owner: a typed `retry:` block on the map
node compiles to a LangGraph `RetryPolicy` on the sub-node registration,
the branch wrapper stops swallowing exceptions in the closed retryable
vocabulary so LangGraph can retry them with backoff and jitter, and the
final failure is disposed exactly once — as today's `_error` row — via
LangGraph's per-node `error_handler`.

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
| 2. Prompt executor | `executor_base` shared attempt policy (FR-676/679), `is_retryable()` at `yamlgraph/executor_base.py:70-84` | fixed attempts + backoff, structured-output fallback | exception *name* in `RETRYABLE_EXCEPTIONS` or containing "rate" |
| 3. Node `on_error: retry` | `handle_retry` (`yamlgraph/error_handlers.py:108-136`) from `llm_execution.py:150-156`, `NodeConfig.max_retries` | fixed count, **no backoff, no jitter**, FR-933 validation feedback | everything the node raised |
| 4. Map branch | `wrap_for_reducer` (`yamlgraph/compile/map_compiler.py:139-173`) | **none** — catches `TimeoutError` then bare `Exception`, returns a *successful* update `{collect: [_error row], errors: [...]}` | n/a |

The sub-node is registered with `builder.add_node(sub_node_name,
wrapped_node)` (`map_compiler.py:332`) and no `retry_policy`. LangGraph
1.2.11 exposes `add_node(..., retry_policy=RetryPolicy | Sequence[RetryPolicy]
| None, error_handler=StateNode | None)` (signature verified 2026-09-02;
`RetryPolicy` fields `initial_interval, backoff_factor, max_interval,
max_attempts, jitter, retry_on`, default `retry_on=default_retry_on` in
`langgraph/_internal/_retry.py`: retries `ConnectionError`, HTTP 5xx from
`httpx`/`requests`, and anything not in a fixed non-retryable list).
None of it is reachable from YAML, and attaching it at line 332 today
would never fire — the wrapper has already swallowed the exception one
frame below (judgement C-4).

Two adjacent drifts this FR must pin, because they are about exception
ownership at the same boundary:

- `reference/graph-yaml.md:623` documents map-level `on_error: skip |
  fail` ("`fail` (default) raises"), but `compile_map_node` never reads
  `config["on_error"]` (`map_compiler.py:255-262,335-366`): a map branch
  today always behaves as `skip`. The documented default does not exist.
- The timeout error row names the node `"map_subnode"`
  (`map_compiler.py:156`) — attribution is FR-956's deliverable and is
  not repeated here; this FR must not regress it.

## Ideal Result

A graph author writes one `retry:` block on a map node and gets
LangGraph's backoff-and-jitter retry on every branch for a declared,
closed set of transient failures; after the last attempt the branch is
disposed exactly once according to `on_error`, producing the same
`_error` row shape consumers already parse; every retry attempt is
visible in the LangSmith trace and the route log as LangGraph's own
retry, not as a hidden loop inside the node.

## Proposed Solution

All changes inside `yamlgraph/compile/map_compiler.py`,
`yamlgraph/models/node_schema.py`, and `reference/map-nodes.md`.

### 1. Typed `retry:` on map nodes

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
      retry_on: [provider_transient]   # closed vocabulary, see §3
    on_error: skip             # final disposition after retries (default today's behaviour)
    node:
      type: llm
      prompt: classify_domain
      state_key: label
    collect: labels
```

`MapRetryConfig(BaseModel)`: `max_attempts: int = 3 (ge 1)`,
`initial_interval: float = 0.5 (gt 0)`, `backoff_factor: float = 2.0
(ge 1)`, `max_interval: float = 128.0 (gt 0)`, `jitter: bool = True`,
`retry_on: list[RetryClass] = ["provider_transient"]`. Attached to
`NodeConfig.retry: MapRetryConfig | None`; validated at graph load;
rejected at load on non-map nodes (this FR does not authorize graph-wide
retry — FR-031's territory).

### 2. Registration and exception visibility

```python
builder.add_node(
    sub_node_name,
    wrapped_node,
    retry_policy=RetryPolicy(**policy.langgraph_kwargs(), retry_on=retry_on_pred),
    error_handler=make_branch_error_handler(name, collect_key, on_error),
)
```

`wrap_for_reducer` gains a `reraise: Callable[[BaseException], bool] |
None`. When a `retry:` block is configured, exceptions for which
`reraise(exc)` is true are **re-raised** instead of converted, so
LangGraph's retry sees them; everything else keeps today's conversion
path unchanged. `TimeoutError` from `_execute_node_fn` is never
re-raised (FR-069/FR-956 own it); it stays a converted row.

### 3. Closed `retry_on` vocabulary

| `RetryClass` | Exceptions (evaluated by type, not name) | Default |
|---|---|---|
| `provider_transient` | `ConnectionError`; `httpx.HTTPStatusError`/`requests.HTTPError` with 5xx or 429; provider rate-limit exception types enumerated in `executor_base.RETRYABLE_EXCEPTIONS` (imported, not duplicated) | on |
| `provider_server_error` | 5xx only | off |
| `rate_limited` | 429 / rate-limit types only | off |

Not offered: `validation` (deterministic rejection — FR-933 proves
retry without feedback cannot recover it; the owner stays layer 3),
`timeout` (FR-956), `any` (Commandment 6 — retrying a `TypeError` hides
a defect). No import strings, no callables (judgement C-5).

### 4. Final disposition, exactly once

`make_branch_error_handler` returns a node function that receives the
failed task's input — LangGraph passes the branch payload itself
(`langgraph/pregel/_algo.py`, `prepare_node_error_handler_task` builds
the handler task with `failed_task.input`; verified 2026-09-02) — and
emits today's `{collect_key: [{_map_index, _error, _error_type}],
"errors": [PipelineError]}` update once. How the exception object is
exposed to the handler must be confirmed against LangGraph's `__error__`
channel constant (`langgraph/_internal/_constants.py:13`) at enforcement;
if the handler cannot see the exception, the wrapper records the last
exception per `_map_index` in a thread-safe side table the handler
reads (fallback, still exactly-once). `on_error: fail` on the map node
becomes real: the handler re-raises instead of emitting a row. The
`skip` default preserves every existing consumer.

### 5. Ownership table (recorded in `reference/map-nodes.md`)

Layer 1 (SDK) and layer 2 (prompt executor) continue to act *inside* an
attempt; layer 3 (`on_error: retry` on the sub-node) is rejected at load
when a map-level `retry:` block is present (two owners is the defect);
layer 4 (LangGraph `RetryPolicy` on the branch) is the single owner of
cross-attempt retry for map branches. Without a `retry:` block nothing
changes.

## Acceptance Criteria

- [ ] AC-01 RED: with `retry: {max_attempts: 3, retry_on: [provider_transient]}`
      and a mock sub-node raising a 503 `httpx.HTTPStatusError` twice then
      succeeding, the collected result is the success value, the mock was
      called exactly 3 times, and no `_error` row exists.
- [ ] AC-02 RED: same mock raising 503 four times → exactly 3 calls,
      exactly one `_error` row with `_map_index`, exactly one `errors`
      entry, `_error_type == "HTTPStatusError"`.
- [ ] AC-03: a `ValueError` under the same config → exactly 1 call, one
      `_error` row (non-retryable path unchanged).
- [ ] AC-04: `TimeoutError` under `retry:` → exactly 1 call, today's
      timeout row; FR-069 witnesses in `tests/unit/test_map_node_timeout.py`
      stay green.
- [ ] AC-05: `on_error: fail` with retries exhausted raises out of the
      graph run; `on_error: skip` (and absent) collects the row — pinning
      the documented contract at `reference/graph-yaml.md:623` for the
      first time.
- [ ] AC-06: `load_graph_config` rejects `retry:` on non-map nodes,
      `retry_on` values outside the vocabulary, `max_attempts < 1`, and a
      map node carrying both `retry:` and a sub-node `on_error: retry`,
      each with node name and offending value in the message.
- [ ] AC-07: registration witness — the compiled `StateGraph` node for
      `_map_<name>_sub` carries a `RetryPolicy` with the configured
      fields and a non-None `error_handler` when `retry:` is set, and
      neither when it is not.
- [ ] AC-08: exactly-once witness — under exhausted retries the
      `errors` reducer holds one entry for the branch across the whole
      run (no duplicate from wrapper + handler).
- [ ] AC-09: `_map_index` attribution and `sorted_add` order preserved
      after retries; FR-944 chained maps unchanged; `flatten_output` unchanged.
- [ ] AC-10: LangSmith/route-log witness — each retry attempt appears as
      a LangGraph task retry (attempt metadata), not as a hidden loop;
      asserted via the route decision log line count for the branch.
- [ ] AC-11: one new CAP-11 requirement (branch retry ownership);
      `@pytest.mark.req` on every new test; `req_coverage.py --strict` green.
- [ ] AC-12: RED and GREEN separate commits; RED fails on attempt
      counts, not on import or fixture.
- [ ] AC-13: `reference/map-nodes.md` documents `retry:`, the vocabulary,
      the ownership table, and corrects `graph-yaml.md:623`; FR-031 gets a
      one-line status note ("map-branch scope superseded by FR-957");
      one changelog fragment; one diary reflection.
- [ ] AC-14: diff contains none of: `executor_base` retry changes,
      `handle_retry`/FR-933 changes, `llm_providers.py` (FR-708), non-map
      `retry:`, overflow (FR-939), payload projection (FR-955), executor/
      timeout changes (FR-956).

## Alternatives Considered

| class | mechanism | precedent | disposition |
|---|---|---|---|
| 1. LangGraph `RetryPolicy` on the branch + `error_handler` for final disposition | §2–§4 above | FR-031 (mechanism), FR-030 closure, LangGraph 1.2 `add_node` signature | **CHOSEN** — the only class where the orchestrator both performs and *observes* the retry, satisfying judgement C-4 |
| 2. Retry inside `wrap_for_reducer` with a typed backoff policy | keep swallowing, loop with backoff/jitter in the wrapper | `handle_retry` shape; FR-676/679 executor loop | REJECTED — a third hand-rolled loop; invisible to LangGraph traces; duplicates what `RetryPolicy` already is. Retained only as the fallback *for the disposition step* if `error_handler` cannot see the exception (§4) |
| 3. Reuse node-level `on_error: retry` on the sub-node | rely on layer 3 as configured inside `node:` | FR-933 | REJECTED as owner — fixed count, no backoff/jitter, per-attempt cost identical; kept as a load-time conflict (AC-06) so two owners cannot coexist |
| 4. Graph-shaped retry: loop edge with `loop_limits` around the map, or a second map over failed rows | YAML only | Pattern 12 quality gate + retry loop in `reference/patterns.md` | REJECTED as the primitive — re-fans out *all* items or requires the author to partition failures by hand; per-branch transient retry is a node-registration concern. Remains the right tool for *semantic* retry (quality gates), which is FR-933's territory. `is_this_a_graph`: no for transient faults, yes for quality loops — the split is the point |
| 5. Rely on SDK `max_retries` (FR-708) only | do nothing above layer 1 | FR-708 | REJECTED — covers `llm` sub-nodes only, invisible, uncontrollable per graph; `python`/`tool_call`/`agent` branches get nothing |
| 6. Graph-wide native retry now (full FR-031) | replace `on_error: retry` everywhere | FR-031 | REJECTED here — outside the D-4 fence (judgement C-6); FR-031 remains the vehicle if a consumer appears |

Preserved disagreement: the subtractionist position (delete layer 3
for map sub-nodes outright once layer 4 exists) is not taken — AC-06's
load-time conflict achieves single ownership without deleting a
documented feature.

## Related

- `yamlgraph/compile/map_compiler.py:139-173,329-332`
- `yamlgraph/error_handlers.py:108-136`, `yamlgraph/node_factory/llm_execution.py:136-160`
- `yamlgraph/executor_base.py:60-84`, `yamlgraph/utils/llm_providers.py` (FR-708)
- `langgraph/types.py:418-436` (`RetryPolicy`), `langgraph/_internal/_retry.py` (`default_retry_on`), `langgraph/pregel/_algo.py` (`prepare_node_error_handler_task`)
- `capabilities/CAP-11-subgraph-map.yaml`
- `docs/plan-web-toolkit.md` audit item 4

### Questions for the human (as options, or 'none')

1. Default for `retry:` when the block is present but `retry_on` is
   omitted: **`[provider_transient]`** (recommended — matches what
   FR-030's closure and LangGraph's default intend) vs no default
   (explicit list required).
2. Should `on_error: fail` on a map node — documented since FR-069 but
   never implemented — become real in this FR (**yes**, recommended: it
   is the disposition half of exception ownership) or be corrected in
   the docs only?
