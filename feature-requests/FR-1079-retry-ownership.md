# Feature Request: Retry ownership — one retry layer per failure class for every LLM call

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Effort:** 1.5 days
**Requested:** 2026-09-25
**First consumer / first event:** the next `innovation_matrix` run on haiku
(`examples/demos/innovation_matrix/pipeline.yaml`). On 2026-09-24 four of 25
branches timed out after about 91 s each, which is 3 × the 30 s request
timeout. Nobody can say which layers produced those three attempts, or how
many a single request can reach.
**Research:** FR-890 research route not run. This applies the operator's
2026-09-25 decision for the FR-1064 refiles ("refile. skip research —
document as skipped"). The substitute is the in-body solution classes below,
in the form FR-1076's judgement accepted, plus
[docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §4 (failure model)
and §7 A.
**Prior art:**
[FR-1064](FR-1064-map-branch-contract.md) (SPLIT). This is its retry half.
Judgement R-1 requires a separate FR because the SDK change touches every LLM
call. R-4 requires attempt counts witnessed on real provider exception types
before any mapping is chosen.
[FR-1073](FR-1073-map-result-contract.md) (authority active). It owns the map
result and failure channel and never changes retries (its C-7). Its map
`MapFailure` record carries no `error_class`. This FR adds none either: the
field waits for a consumer.
[FR-957](FR-957-map-branch-native-retry-policy.md) (APPROVED WITH REVISIONS,
not enforced). It proposes LangGraph `RetryPolicy` on map branches. Plan §4.1
witnesses that `error_handler` does not fire for concurrent branches. FR-1064
judgement R-1 forbids transferring FR-957's status until this FR is judged.
[031-native-retry-policy.md](031-native-retry-policy.md) (Proposed). A
graph-wide `RetryPolicy`, which would add a fourth layer.
[FR-708](FR-708-llm-client-request-timeout.md) and
[FR-710](FR-710-provider-deadline-floors.md). The request timeout and the
provider deadline floors. The knob this FR's timeout rule depends on.
[FR-408](FR-408-runtime-repair-metadata.md) (Rejected). It rejected a repair
registry; this FR adds no repair actions.

## Summary

Every LLM call in yamlgraph can be retried by three stacked layers: the
provider SDK, the executor loop, and the node's `on_error: retry`. Measure
what each layer does today on the real provider exception types. Then give
each failure class exactly one owner.

## Value Statement

A graph author can predict the worst-case number of requests and the
wall-clock time of a failing LLM node from its configuration. A provider
error is either retried with backoff by one layer or fails once. It is never
multiplied.

## Problem

- **Layer 1, SDK.** `yamlgraph/utils/llm_bounds.py#L18` and `#L73` set
  `max_retries=2` on every provider client. That is up to 3 requests, with the
  SDK's own backoff and its own idea of what is retryable.
- **Layer 2, executor loop.** `yamlgraph/executor.py#L161-L176` and
  `yamlgraph/utils/llm_factory_async.py#L99-L115` make `MAX_RETRIES=3`
  attempts (`yamlgraph/config.py#L84`, env `LLM_MAX_RETRIES`). They back off
  exponentially and retry when `is_retryable` says so.
- **Layer 3, node handler.** `on_error: retry` calls `handle_retry`
  (`yamlgraph/error_handlers.py#L108-L135`) up to `max_retries` times (default
  3, `yamlgraph/node_factory/llm_nodes.py#L165`). Each call re-enters layer 2.
  There is no backoff, and every error class is retried, including
  permanent ones.
- **Classifier.** `is_retryable` (`yamlgraph/executor_base.py#L77-L87`)
  matches class names. `APITimeoutError` counts as transient, so a stuck
  request is repeated. Any class whose name contains `"rate"` is transient;
  `GenerateError` contains it.
- **Arithmetic from source reading, not witnessed.** A failing request under
  `on_error: retry` can reach 3 (SDK) × 3 (executor) on the first attempt,
  plus 3 more handler attempts of 3 × 3 each, for up to 36 requests. The
  observed 2026-09-24 branch took about 3 × 30 s. Source reading and
  observation disagree, so the count must be witnessed first (FR-1064
  judgement R-4).

## Ideal Result

For every supported provider there is a committed witness: one row per
exception class, giving the requests made per layer today and after the
change. After the change:
- a transient error (connection failure, HTTP 5xx, HTTP 429) is retried by
  exactly one layer with backoff, and 429 honours `Retry-After`;
- a permanent error (other 4xx, authentication, a non-streaming timeout) is
  made once;
- a validation error is re-asked with feedback by exactly the node handler;
- worst-case requests per node are a product the reference documents.

## Proposed Solution

1. **Witness first (RED).** Build a local HTTP stub that fakes one provider
   endpoint. It returns 500, 429 with `Retry-After`, 400 and 401, hangs past
   the timeout, drops the connection, or returns schema-invalid JSON. Drive
   the real `create_llm()` clients (Anthropic, OpenAI, Mistral; others as the
   factory supports a `base_url`) through the executor and through a node
   with each `on_error` value. Count requests at the stub per case. Commit the
   table. The rest of this section is a candidate: the witness may change the
   mapping, and any change is recorded in the FR before GREEN.
2. **SDK layer off.** Set `max_retries=0` in `llm_bounds.py` for every client
   the factory builds. The executor loop becomes the only transport retry
   layer.
3. **Explicit classifier.** Replace name matching with a per-provider mapping
   from exception type and HTTP status to `transient` or `permanent`:
   - transient: connection errors, 5xx, 429;
   - permanent: other 4xx, authentication, non-streaming timeouts. A timeout
     cannot tell slow from stuck, so repeating it multiplies the wait (plan
     D7).
   An exception with no mapping is permanent and logged with its type.
   `"rate"` substring matching is removed.
4. **Retry-After.** On a 429, the executor loop waits
   `max(backoff, Retry-After)`, capped at `RETRY_MAX_DELAY`. A `Retry-After`
   above the cap fails as permanent and names the value.
5. **Node handler.** `on_error: retry` re-asks only after output validation
   failures, with feedback, as `_feedback_aware_attempt` already does. For an
   error the executor classified, it does not re-run and returns the error.
6. **Documentation.** `reference/graph-yaml.md` (`on_error: retry`) and
   `reference/development-operations.md` (`LLM_MAX_RETRIES`,
   `LLM_REQUEST_TIMEOUT`) state the owner of each failure class and the
   worst-case request count.

Consequence stated up front: a response that is slow but would have
succeeded now fails once, where today it is retried. The knob is
`LLM_REQUEST_TIMEOUT` (FR-708). The 2026-09-24 run had a 27 s median against
the 30 s default, so the `innovation_matrix` acceptance run sets it
explicitly. Streaming, where the timeout bounds the gap between chunks, is
the real cure. This FR refuses it: its only named consumer is this demo.

## Acceptance Criteria

- [ ] AC-01 (RED, witness): the committed stub table records, per provider
  and per case (500, 429 with and without `Retry-After`, 400, 401, hang past
  the timeout, connection drop, schema-invalid output), the requests made per
  layer on current code, for `on_error` absent, `retry`, and `skip`.
- [ ] AC-02: after the change, the same table shows the SDK making 0
  retries, one transport layer retrying transient cases, and permanent cases
  making exactly one request.
- [ ] AC-03: 429 with `Retry-After: 2` waits at least 2 s before the next
  request (clock injected, no real sleep). A `Retry-After` above
  `RETRY_MAX_DELAY` fails without a retry and names the value.
- [ ] AC-04: a class named `GenerateError` is not retryable. An unmapped
  exception is permanent and logged with its type.
- [ ] AC-05: `on_error: retry` on a schema-invalid response re-asks with
  feedback up to `max_retries`. On a permanent transport error it makes no
  further request.
- [ ] AC-06: the sync and async executor loops produce identical tables.
- [ ] AC-07: the documented worst-case request count for a node equals the
  witnessed maximum from AC-02.
- [ ] AC-08: an `innovation_matrix` run on haiku with `LLM_REQUEST_TIMEOUT`
  set explicitly records, per branch, the request count and elapsed time. It
  is non-gating and needs human spend approval.
- [ ] AC-09: new REQ in a capability file, tests tagged,
  `python scripts/req_coverage.py --strict` passes, changelog fragment, FR
  implementation record, diary entry.
- [ ] AC-10: on judgement, FR-957's status is set to Superseded by this FR
  (FR-1064 judgement R-1).

## Alternatives Considered

Solution classes (chosen: 1):

1. **Executor loop owns transport retries, SDK off, handler owns
   validation.** Chosen. yamlgraph code already owns the loop, the backoff
   constants and the env knob, and it sees every provider through one
   factory.
2. **SDK owns transport retries, executor loop removed.** Preserved dissent:
   the SDKs already honour `Retry-After` and know their own error types, and
   this deletes yamlgraph code. It loses because each SDK decides differently
   what is retryable and how long to wait, and the async and sync paths
   differ per SDK. One classifier in our code can be witnessed once.
3. **LangGraph `RetryPolicy` on nodes (FR-957, FR-031).** Rejected: on a map
   with two or more branches, `error_handler` does not fire (plan §4.1). It
   also adds a layer rather than removing one.
4. **Keep three layers, lower each to 1 retry.** Rejected: still multiplies
   (2 × 2 × 2), still retries permanent errors, and keeps the `"rate"`
   substring match.
5. **Per-node `retry:` configuration.** Rejected for now: no consumer asks
   for per-node transport policy. The failure is the default's overlap, not a
   missing knob.

`is_this_a_graph`: no. Retry classification is a deterministic mapping at the
provider boundary (`the_one_law`), not a model decision.

## Out of scope

Map result and failure channel (FR-1073). Streaming requests. Per-node
retry configuration. Cross-run failure memory (FR-1065, FR-1076). An
`error_class` field on FR-1073's `MapFailure`, which waits for a consumer.
LangGraph `RetryPolicy`.

## Related

- Split from: [FR-1064](FR-1064-map-branch-contract.md)
- Composes with: [FR-1073](FR-1073-map-result-contract.md), [FR-708](FR-708-llm-client-request-timeout.md), [FR-710](FR-710-provider-deadline-floors.md)
- Plan: [docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §4, §7 A.5
