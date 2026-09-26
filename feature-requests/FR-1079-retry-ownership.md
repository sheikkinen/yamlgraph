# Feature Request: Retry ownership — one retry layer per failure class for every LLM call

**Priority:** HIGH
**Type:** Bug
**Status:** Judged — APPROVED WITH REVISIONS ([judgement](FR-1079-retry-ownership.judgement.md)); R-1–R-6 folded 2026-09-26. Authority: active for D-1 (baseline witness) only; D-2–D-6 gated on the committed provider-complete baseline `FR-1079.retry-witness.md` (open item O-1 below, judgement C-1).
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

## Human decisions

- **2026-09-25 (operator; judgement C-1, C-8):** judgement review is
  delegated: where the implementing agent and the judge agree, authority
  stands without an operator read. The agent's check on main is corrected
  here by the R-1 matrix: `race_node.py` and `tools/agent.py` call the
  provider outside the executor loop, so they have no framework retry at all,
  only the SDK's.
- **2026-09-26 (operator):** reviewed the advisory judgement and instructed
  "proceed with all fr changes". This is the human review C-1 requires.
- **2026-09-26 (operator; R-6, C-8):** the optional D-7 `innovation_matrix`
  haiku run is authorized within the session budget of USD 10, only after
  deterministic acceptance is green. It never gates completion.

## Summary

A yamlgraph LLM request can be retried by up to three stacked layers: the
provider SDK, the executor loop, and the node's `on_error: retry`. Some call
paths (race, agent, streaming) have only the SDK layer. Measure what each
layer does today on the real provider exception types. Then give each
failure class exactly one owner on every call path.

## Value Statement

A graph author can predict the worst-case number of requests and the
wall-clock time of a failing LLM node from its configuration. A provider
error is either retried with backoff by one layer or fails once. It is never
multiplied.

## Problem

The layers today:

- **SDK.** `_bounded()` sets `max_retries=2` on every client the factory
  builds (`yamlgraph/utils/llm_bounds.py:18`, `:73`). What that means differs
  per SDK (baseline below).
- **Executor loop.** Sync `yamlgraph/executor.py:161-176` and async
  `yamlgraph/utils/llm_factory_async.py:99-118` make up to `MAX_RETRIES=3`
  attempts (`yamlgraph/config.py:84`, env `LLM_MAX_RETRIES`) with backoff
  `min(RETRY_BASE_DELAY·2^n, RETRY_MAX_DELAY)` (`config.py:85-86`).
- **Node handler.** `on_error: retry` calls `handle_retry`
  (`yamlgraph/error_handlers.py:108-135`): the initial attempt plus
  `max_retries` more (default 3, `yamlgraph/node_factory/llm_nodes.py:165`),
  no backoff, every error class. Each attempt re-enters the executor loop.
- **Classifier.** `is_retryable` (`yamlgraph/executor_base.py:68-87`) matches
  class names: `APITimeoutError` is transient, and any name containing
  `"rate"` is transient, including `GenerateError`.

### Call-path ownership matrix (R-1)

Verified on this branch by reading the cited lines. "Framework" means
yamlgraph's executor loop.

| # | Call path | Entry and request sites | Transport retry today | Semantic layer on top | Transport owner after |
|---|---|---|---|---|---|
| 1 | Sync prompt | `execute_prompt` `executor.py:45` → `_invoke_with_retry` `executor.py:143-178`; callers `llm_nodes.py:348`, `control_nodes.py:59`, `copilot_node.py:405` | SDK × framework (`executor.py:161-176`) | rows 5, 6 | shared policy (D-2) |
| 2 | Async prompt | `execute_prompt_async` `executor_async.py:32` → `invoke_async` `executor_async.py:87` → `llm_factory_async.py:99-118`; sync invoke in a thread (`:105`), `asyncio.sleep` (`:118`) | SDK × framework | row 5 | shared policy, native async sleep and cancellation (D-2) |
| 3 | Race candidate | `_invoke_candidate_async` `race_node.py:118`; `ainvoke_structured` `:150-156`; FR-464 fallback `llm.ainvoke` `:173`; plain `llm.ainvoke` `:180`; clients built `:203`; router race imports it (`router_race_node.py:18`) | SDK only | row 5 (inline copy) | shared policy (D-3) |
| 4 | Agent loop and finalization | client `agent.py:311`; `llm.invoke` per iteration `agent.py:328` (up to `max_iterations`, default 10, `agent.py:202`); finalization `_try_structured_output` `agent.py:62` (called `:344`, `:400`) with sends at `:100`, `:118`, `:134` | SDK only | agent iterations; finalization tiers | shared policy (D-3) |
| 5 | Structured-output protocol | `attempt_structured_invoke` `executor_base.py:402-445`: FR-998 forced-tool-call second attempt (`structured_output.py:84-100` sync, `:103-130` async), FR-464 `response_format` fallback `executor_base.py:428-443` | inherits row 1/2 (runs inside each attempt) | ≤ 2 sends per attempt | unchanged policy; each send under the shared owner |
| 6 | Node semantic re-execution | `attempt_execute` `llm_nodes.py:344-366` → row 1. `on_error: retry` `llm_execution.py:150-156` with feedback `:103-123`; verification retry `llm_execution.py:58-72` (default 1, `llm_nodes.py:138-147`); post-guard retry `llm_nodes.py:236-270`; `on_error: fallback` `llm_execution.py:158-160` → `error_handlers.py:139-162` (one call) | each re-execution re-enters row 1 | `on_error: retry` repeats every error class today | node re-asks only on Pydantic validation feedback (D-4) |
| 7 | Streaming start | `execute_prompt_streaming` `executor_async.py:133` → `llm.astream` `:185`. No sync `.stream(` call exists under `yamlgraph/` (grep, 2026-09-26) | SDK only | none | start of stream under the shared owner; chunk semantics unchanged (D-3) |

### Provider baseline (R-2) — what is known today

Obtained 2026-09-26 without network or spend. Dummy API keys in the
environment; each `_PROVIDER_FACTORIES` entry
(`yamlgraph/utils/llm_providers.py:336-348`) constructed through
`create_llm(provider=name)`, then `llm.max_retries` and the inner SDK client's
`max_retries` read. Command:
`source .venv/bin/activate && PYTHONPATH=$PWD python <probe>` (probe: construct
each provider, print wrapper type and retry fields, print
`anthropic.DEFAULT_MAX_RETRIES` and `openai.DEFAULT_MAX_RETRIES`), then
read-only `grep`/`sed` of the installed SDK sources. Versions: anthropic 1.5.0,
openai 2.54.0, google-genai 2.23.0, litellm 1.102.0, langchain-anthropic
1.7.2, langchain-openai 1.6.2, langchain-mistralai 1.1.6,
langchain-google-genai 4.4.0.

| Provider(s) | Wrapper | Constructed `max_retries` | What the SDK does with it (installed source) |
|---|---|---|---|
| anthropic | `ChatAnthropic` | field 2; `_client` 2; `_async_client` 2 | 2 retries = 3 sends. Retries 408, 409, 429, ≥ 500 and `x-should-retry` (`anthropic/_base_client.py:835-863`); exceptions via `_should_retry_exception` (`:870`, body not read); `retry-after-ms`, `retry-after` seconds and HTTP-date parsed (`:786-804`), honoured if 0 < v ≤ 60 (`:821`); backoff 0.5–8 s (`anthropic/_constants.py:11-12`) |
| openai, deepseek, inception, lmstudio, runpod, xai | `ChatOpenAI` | field 2; `root_client` 2 | 2 retries = 3 sends. Same status set and header forms (`_should_retry`, `_parse_retry_after_header`); **timeouts retried** (`openai/_base_client.py:1085-1098`); header honoured up to `MAX_RETRY_AFTER_DELAY` (`:807`); backoff 0.5–8 s (`openai/_constants.py:13-14`) |
| google, vertex | `ChatGoogleGenerativeAI` | field 2; inner not exposed | Passed as `HttpRetryOptions(attempts=2)` (`langchain_google_genai/chat_models.py:4090-4091`). `attempts` counts the original request, so 2 = **2 sends, 1 retry**; 0 is coerced to 1 (`google/genai/_api_client.py:574-575`). Retries 408, 429, 500, 502, 503, 504 and httpx transients (`:552-583`), backoff 1–60 s with jitter (`:547-551`); `Retry-After` handling not read |
| mistral | `ChatMistralAI` | field 2 (class default 5 overridden) | langchain tenacity `stop_after_attempt(2)` = **2 sends** (`langchain_core/language_models/llms.py:128`), only on `httpx.RequestError` / `httpx.StreamError` (`langchain_mistralai/chat_models.py:107-114`). HTTP 429/5xx are not in that list (inferred: not SDK-retried) |
| azure | `AzureAIOpenAIApiChatModel` | **not obtained**: `langchain_azure_ai` not installed in `.venv` | — |
| replicate | `ChatLiteLLM` | **not obtained**: `langchain_litellm` not installed in `.venv` | — |

So "SDK retries = 2" means 3 sends on Anthropic and OpenAI-compatible
clients, 2 on Google/Vertex and Mistral, and different retryable sets per SDK.
Source-read worst case for an Anthropic or OpenAI-family timeout under
`on_error: retry`: 3 (SDK) × 3 (executor) × 4 (node) = 36 sends. The
2026-09-24 branch took about 3 × 30 s, which matches the SDK layer alone. Why
the outer layers did not show is unwitnessed; D-1 answers it.

**Open item O-1 (gates D-2–D-6).** Still missing for AC-01: (a) azure and
replicate rows, obtainable at no cost by installing the optional extras and
re-running the probe; (b) the qualified exception module/type, status and
header shape that reaches yamlgraph per provider and injected case, sync and
async, obtainable at no cost by intercepting each SDK's transport in tests
(D-1); (c) Anthropic timeout retry, Google/Vertex `Retry-After` handling and
Mistral 429/5xx behaviour, which this read did not settle. No item needs a
paid call. If any constructor cannot be driven through a wrapper-supported
transport seam without credentials, enforcement stays blocked (judgement
R-2, C-4).

## Ideal Result

For every supported provider there is a committed witness: one row per
exception class, giving the requests made per layer today and after the
change. After the change:
- a transient error (connection failure, HTTP 5xx, HTTP 429) is retried by
  exactly one layer with backoff, and 429 honours a valid `Retry-After` up to
  the cap, otherwise it fails loudly naming the value;
- a permanent error (other 4xx, authentication, a non-streaming timeout) is
  made once;
- a validation error is re-asked with feedback by exactly the node handler;
- worst-case requests per node are a product the reference documents.

## Proposed Solution

1. **Baseline, then RED (R-2; D-1).** Close O-1. Commit
   `feature-requests/FR-1079.retry-witness.md` with columns provider, wrapper
   family, call path (rows 1–7), injected failure, exception module/type,
   status/header shape, SDK sends, framework sends, elapsed/scheduled delay.
   Cases: 500, 429 without header, 429 delay-seconds, 429 HTTP-date, 400, 401,
   request timeout, connection drop, schema-invalid output; sync and async;
   all twelve providers. Failures are injected at each SDK's own transport
   seam in tests (for example an httpx transport for the OpenAI and
   Anthropic clients). No public `base_url`, credential or production test
   hook is added (C-4); no provider's contract is inferred from another's.
   This characterization passes on current code and is not RED. Separate
   desired-state tests are the RED commit: they fail on current code because
   SDK retries are on, rows 3, 4 and 7 have no shared owner, classification
   is by name, or node retry repeats transport errors. Then fold the
   witnessed provider-qualified mapping into this FR. If it changes the owner,
   the solution class or the transient/permanent split, the FR returns to
   judgement before GREEN (C-2).
2. **One shared transport policy (R-1; D-2, D-3).** One typed module under
   `yamlgraph/utils/` takes a provider identity and an invocation callable and
   has sync and async entry points sharing one classifier and one delay
   calculator; the async one keeps native `asyncio.sleep` and cancellation.
   It replaces both executor loops (rows 1, 2) and wraps every transport send
   in rows 3, 4, 5 and 7, including stream start. Protocol negotiation (row
   5), Pydantic correction, verification, post-guards, fallback provider and
   agent iterations keep their semantics and stay separate owners (C-7).
   Only after every row routes through the policy does `_bounded()` set
   `max_retries=0` for every `_PROVIDER_FACTORIES` constructor (C-3); a
   caller cannot reintroduce SDK retries through the factory.
3. **Closed classifier (R-3).** A typed result (not a dict) carries provider,
   qualified exception type, optional status, failure class, attempt number
   and parsed retry delay. Predicates are frozen from the witness:
   transient = connection failure, 429, 500–599; permanent = other 4xx,
   authentication, non-streaming request timeout (a timeout cannot tell slow
   from stuck, so repeating it multiplies the wait; plan D7). An unmapped
   exception is attempted once and logged with provider and qualified type.
   A name containing `"rate"` is never sufficient.
4. **Attempts and delays (R-3).** `LLM_MAX_RETRIES` means **total transport
   attempts**, an integer ≥ 1. `LLM_RETRY_DELAY` and `LLM_RETRY_MAX_DELAY` are
   non-negative with max ≥ base. Invalid values raise at the configuration
   boundary. No new env knob. Tests inject wall clock, monotonic clock,
   sleeper and any jitter source.
5. **Retry-After (R-3).** On 429, delay-seconds and HTTP-date are parsed
   against the injected wall clock. No header: capped exponential backoff.
   A valid delay ≤ `RETRY_MAX_DELAY` waits `max(backoff, retry_after)`. A
   negative, malformed or over-cap value makes no retry and raises and logs
   naming the raw value and the cap. The response stays classified as a
   transient rate limit that exceeded the local budget, not as permanent.
6. **Node semantic retry (R-4; D-4).** `on_error: retry` on an LLM node
   re-asks only when `build_validation_feedback(error)` returns non-empty
   feedback, i.e. a Pydantic `ValidationError`. `max_retries` stays the number
   of additional semantic re-asks after the initial invocation. Malformed or
   unextractable JSON that is not a `ValidationError` is **not** eligible: it
   fails once unless an existing structured-output fallback (row 5) handles
   it. A permanent, timeout, unmapped or transient-exhausted transport error
   makes no node re-ask and produces exactly one existing `PipelineError`
   state update with no output. `skip`, `fail` and fallback-provider keep
   their disposition; each provider call inside them uses the shared owner.
   No coercion or repair registry (FR-408 stays rejected).
7. **Request budgets (R-5).** Variables: `T` transport attempts
   (`LLM_MAX_RETRIES`, default 3); `P` protocol sends per attempt (1, or 2
   with the FR-998 second attempt or FR-464 fallback); `V` validation re-asks
   (`max_retries`, default 3); `Q` verification re-executions (default 1);
   `G` sum of post-guard retry budgets (default 1 per rule); `F` fallback
   provider call (0 or 1); `I` agent iterations (≤ `max_iterations`, default
   10); `C` race candidates. Candidate formulas: ordinary call `T·P`; LLM node
   `T·P·(1 + V + Q + G)` under `on_error: retry`, `T·P·(2 + Q + G)` under
   `fallback`; race `Σ_C T·P`; agent `T·(I + 4)` (finalization has at most
   four sends, `agent.py:100`, `:118`, `:134`, with `:100` able to send twice).
   Each formula is proven by a deterministic mixed-path fixture (AC-10); a
   fixture that disagrees corrects the formula here before GREEN.
8. **Documentation (R-5; D-5).** `reference/graph-yaml.md` and
   `reference/development-operations.md` name each failure-class owner,
   separate SDK retry count from framework total attempts, give the formulas
   with defaults, describe malformed and over-cap `Retry-After`, and state
   that `LLM_REQUEST_TIMEOUT` bounds one non-streaming request, not a node.
   The RunPod guidance that recommends stacking `on_error: retry` for cold
   starts (`reference/development-operations.md:119`) is removed.
9. **Sequencing FR-957 (R-6; D-7).** After R-1–R-6 are folded (done
   2026-09-26), the baseline is committed, the judgement is human-reviewed
   (done 2026-09-26) and D-2 authority activates, FR-957 is set to
   `Superseded by FR-1079` with a note that its concurrent `error_handler`
   design was disproved. FR-031 keeps only its non-LLM graph-wide proposal.
   This FR does not set that status yet.
10. **Optional live observation (R-6; D-7).** After deterministic acceptance
    is green, one `innovation_matrix` haiku run with `LLM_REQUEST_TIMEOUT` set
    explicitly, within the operator's USD 10 session budget (Human
    decisions). Record provider/model, exact command, timeout, per-branch
    request count, elapsed time, final map verdict and raw log path. It
    cannot override deterministic acceptance and never gates completion.

Consequence stated up front: a response that is slow but would have
succeeded now fails once, where today it is retried. The knob is
`LLM_REQUEST_TIMEOUT` (FR-708). The 2026-09-24 run had a 27 s median against
the 30 s default, so the optional live run sets it explicitly. Token
streaming, where the timeout bounds the gap between chunks, is the real
cure. This FR refuses it: its only named consumer is this demo.

## Acceptance Criteria

Replaced by the judgement's revised criteria.

- [ ] AC-01: `feature-requests/FR-1079.retry-witness.md` records every supported provider constructor, wrapper family, sync/async call path, injected case, qualified real exception/status/header shape, SDK sends, framework sends, and elapsed/scheduled delay for 500, 429 with no header, 429 delay-seconds, 429 HTTP-date, 400, 401, timeout, connection drop, and schema-invalid output.
- [ ] AC-02: Desired-state RED tests are committed separately from the passing characterization witness and fail on request ownership/count, classification, delay, or node-disposition assertions rather than missing dependencies, credentials, imports, or fixtures.
- [ ] AC-03: Every `_PROVIDER_FACTORIES` constructor receives `max_retries=0`; no supported provider silently retains SDK retries, and caller-supplied production behavior cannot reintroduce a second retry owner through the factory.
- [ ] AC-04: Sync prompt, async prompt, race candidate, and agent transport failures all use the same provider-qualified classifier and total-attempt budget; transient/transient/success makes exactly three sends with `LLM_MAX_RETRIES=3`, while 400, 401, non-streaming timeout, and unmapped exceptions each make one.
- [ ] AC-05: Classifier tests cover every witnessed provider exception type plus `GenerateError`; only connection failures, 429, and 500-599 are transport-transient, and each unmapped qualified type is logged with provider identity.
- [ ] AC-06: `LLM_MAX_RETRIES`, base delay, and max delay reject invalid values at the configuration boundary; sync and async calculate identical attempt schedules and differ only in injected blocking versus async sleep.
- [ ] AC-07: 429 delay-seconds and HTTP-date values produce the exact injected-clock delay; absent headers use backoff; malformed, negative, or over-cap values make no retry and name the raw value and cap without reclassifying the provider response as permanent.
- [ ] AC-08: `on_error: retry` re-asks a Pydantic-invalid output with non-empty sanitized feedback for exactly `max_retries` additional semantic attempts; a permanent, timeout, unmapped, or transient-exhausted transport error makes no node re-ask and emits exactly one existing `PipelineError`.
- [ ] AC-09: Structured-output negotiation, fallback-provider invocation, verification retry, post-guard retry, race candidates, and agent iterations retain their existing semantic behavior while every transport send inside them uses the one transport owner; focused regressions assert no hidden SDK or executor multiplication.
- [ ] AC-10: Deterministic mixed-sequence fixtures prove the documented request-budget formulas for ordinary, structured-output, validation, verification/guard, fallback, race, and agent paths, including validation re-ask plus transient transport failures.
- [ ] AC-11: `invoke`, `ainvoke`, `stream`, and `astream` startup failures have one transport owner and bounded witnessed counts; no token-streaming/chunk-gap behavior or public factory API is added.
- [ ] AC-12: The implementation diff is limited to D-1 through D-7 and does not touch any explicitly unauthorized surface.
- [ ] AC-13: `reference/graph-yaml.md` and `reference/development-operations.md` name every failure-class owner, attempt semantics, defaults, formulas, timeout behavior, and `Retry-After` failure behavior; the stale stacked-retry RunPod guidance is removed.
- [ ] AC-14: CAP-03 gains one new retry-ownership requirement, every changed test carries its requirement marker, `python scripts/req_coverage.py --strict` passes, and the changelog fragment, FR implementation record, and diary entry are present.
- [ ] AC-15: After authority activation, FR-957 records supersession by FR-1079 while FR-031 retains only its non-LLM graph-wide proposal. The optional live run is absent unless human spend approval is recorded and never gates completion.

R-4's mixed sequences are part of AC-08–AC-10: transient/transient/success;
permanent once; timeout once; validation rejection then corrected output;
validation rejection whose re-ask meets transient faults; exhausted
transient under `on_error: retry`; fallback provider after a primary
permanent error. Each asserts transport sends, semantic invocations,
scheduled delays, emitted error count and feedback presence.

## Scope (frozen by judgement)

| Deliverable | Surface |
|---|---|
| D-1 — baseline evidence | `feature-requests/FR-1079.retry-witness.md`; deterministic provider transport fixtures |
| D-2 — shared transport owner | `yamlgraph/utils/llm_bounds.py`; one typed retry-policy module under `yamlgraph/utils/`; `yamlgraph/executor.py`; `yamlgraph/utils/llm_factory_async.py`; only directly required classifier/config helpers |
| D-3 — complete caller routing | `yamlgraph/node_factory/race_node.py`; `yamlgraph/tools/agent.py`; `yamlgraph/node_factory/llm_execution.py`; directly required structured-output call wrapping without changing protocol-fallback policy |
| D-4 — witnesses | `tests/unit/test_fr1079_retry_ownership.py`; directly affected executor, async-factory, provider-bound, race, agent, validation-feedback, verification and guard regression suites |
| D-5 — contract and traceability | `reference/graph-yaml.md`; `reference/development-operations.md`; one new requirement in `capabilities/CAP-03-node-execution.yaml`; regenerated `ARCHITECTURE.md` traceability |
| D-6 — repository record | this FR's implementation record; one fix changelog fragment; one diary entry with `Seed:` |
| D-7 — planning and optional observation | FR-957 supersession note after authority activates; optional `innovation_matrix` haiku run record (spend approved, Human decisions) |

Not authorized: map result/failure-channel changes; LangGraph `RetryPolicy`;
generic Python/tool-node retry; FR-1073 record or schema changes; an
`error_class` field on `MapFailure`; per-node transport configuration; new
retry env knobs; a public provider endpoint/base-URL test hook;
repair/coercion registries; token-streaming or chunk-gap redesign; graph or
prompt edits; map timeout-thread lifecycle; cross-run memory; provider
credentials in tests; CI/hook/judge/review changes; implementation of the
remaining FR-031 proposal.

Enforcement conditions C-1–C-10 in the
[judgement](FR-1079-retry-ownership.judgement.md#conditions-for-enforcement)
apply unchanged. C-1 status: R-1–R-6 folded and human review recorded
(2026-09-26); baseline commit outstanding (O-1).

## Alternatives Considered

Solution classes (chosen: 1):

1. **One shared yamlgraph transport policy owns transport retries on every
   call path, SDK off, handler owns validation.** Chosen. yamlgraph code
   already owns the loops, the backoff constants and the env knob, and it
   sees every provider through one factory. The policy replaces the two
   executor loops rather than adding a layer.
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

Map result and failure channel (FR-1073). Token-streaming and chunk-gap
redesign (stream and astream start-up request counts are in scope, AC-11).
Per-node retry configuration. Cross-run failure memory (FR-1065, FR-1076). An
`error_class` field on FR-1073's `MapFailure`, which waits for a consumer.
LangGraph `RetryPolicy`.

## Related

- Split from: [FR-1064](FR-1064-map-branch-contract.md)
- Composes with: [FR-1073](FR-1073-map-result-contract.md), [FR-708](FR-708-llm-client-request-timeout.md), [FR-710](FR-710-provider-deadline-floors.md)
- Plan: [docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §4, §7 A.5
