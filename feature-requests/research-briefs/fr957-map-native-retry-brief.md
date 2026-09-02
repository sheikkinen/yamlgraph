# Problem brief: transient failures inside a map fan-out have no owner for retry

**Prior art:** FR-936
(`feature-requests/FR-936-map-node-hardening.md`) bundled this concern
with three others and was SPLIT; its judgement
(`feature-requests/FR-936-map-node-hardening.judgement.md`, R-6, C-4,
C-5, AC-09/AC-10) found that the parent's proposal could not work as
written because `wrap_for_reducer` converts every exception into a
successful state update before LangGraph can observe it, and required
a single retry owner, typed configuration, and a closed retryable-error
vocabulary. This brief is deliverable D-4 and inherits the fence:
overflow (D-2, FR-939), payload projection (D-1), timeout lifecycle
(D-3) are out of bounds. FR-030
(`feature-requests/030-map-concurrency-control.md`, Won't Fix) closed
with "concurrency control belongs in LLM provider (RetryPolicy), not
orchestration. See FR-031" — the earliest in-repo statement that retry
is a provider-boundary concern; it must be dispositioned. FR-672
(`feature-requests/FR-672-extract-shared-retry-policy.md`, Rejected)
proposed extracting the sync/async LLM retry loop into `executor_base`;
it concerns the *prompt-executor* retry, not node-level or branch-level
retry, and its rejection rationale must be distinguished from this
scope. FR-933
(`feature-requests/FR-933-retry-cannot-recover-deterministic-rejection.md`,
Implemented 2026-08-31) made `on_error: retry` carry validation
feedback between attempts — it is the current shape of node-level
retry and any change here must compose with it, not fork it. A
REJECTED-FR sweep found no prior proposal on LangGraph-native retry
for map sub-nodes.

## Problem statement

Retry exists at three layers today, none of which is owned by the map
node and none of which LangGraph can see:

1. Prompt-executor retry: `PromptExecutor._invoke_with_retry` with
   `is_retryable()` (`yamlgraph/executor_base.py:70-84`: name-matched
   `RETRYABLE_EXCEPTIONS` or `"rate"` in the exception name), duplicated
   sync/async (the FR-672 finding).
2. Node-level `on_error: retry` → `handle_retry(node_name, execute_fn,
   max_retries)` (`yamlgraph/error_handlers.py:108-136`; dispatched from
   `yamlgraph/node_factory/llm_execution.py:150-156`), with FR-933
   validation feedback. `NodeConfig.max_retries` is the knob
   (`yamlgraph/models/node_schema.py:158-160`).
3. Nothing at the map-branch boundary: `wrap_for_reducer` catches
   `TimeoutError` and then bare `Exception` and returns
   `{collect_key: [error_result], "errors": [...]}` — a *successful*
   state update (`yamlgraph/compile/map_compiler.py:139-173`). The
   sub-node is registered with `builder.add_node(sub_node_name,
   wrapped_node)` (`map_compiler.py:332`) and no `retry_policy`.

LangGraph 1.2.11 (installed) exposes `add_node(..., retry_policy=
RetryPolicy | Sequence[RetryPolicy] | None)` with fields
`initial_interval, backoff_factor, max_interval, max_attempts, jitter,
retry_on` and a `default_retry_on` that retries `ConnectionError`,
HTTP 5xx from `httpx`/`requests`, and any exception not in a fixed
non-retryable list (`langgraph/_internal/_retry.py`). None of it is
reachable from YAML, and even if attached at `map_compiler.py:332` it
would never fire, because the wrapper has already swallowed the
exception one frame below.

Consequences at fan-out scale: a burst of 429/529/5xx responses across
hundreds of simultaneous branches produces hundreds of `_error` rows
that the reducer must then treat as data, or the whole map fails on
`on_error: fail`, or (with `on_error: retry`) every branch retries
inside the node with fixed-count no-backoff semantics that LangGraph's
own policy would have handled with exponential backoff and jitter.
Graph authors cannot express "retry transient provider errors on each
branch, then dispose the final failure" as one declaration; and when
retries do happen, nobody can say which layer performed them.

The problem: retry ownership for a map branch is undefined, the
exception path is opaque to the orchestrator, and the native policy
LangGraph already provides is structurally unreachable.

## Classification

enforcement/latency-critical

## Constraints

- The FR-936 judgement scope fence applies (C-1, C-6): this concern
  ships alone — no overflow, payload, timeout, durability, caching or
  non-map retry refactors ride along; changing `PromptExecutor` retry
  or FR-933 feedback semantics needs its own judged scope.
- One retry owner (judgement R-6; rejudgement R-5, AC-07): the end
  state must name exactly one layer that performs retries for a map
  branch and define the ordering between that layer and the final
  `on_error` disposition — the final disposition must occur exactly
  once (rejudgement AC-10).
- Exceptions the retry owner must act on must actually reach it
  (judgement C-4; rejudgement C-5): a policy attached outside a wrapper
  that already converts the target exception into a state update is
  not acceptable.
- Typed configuration on `NodeConfig` (Pydantic, Commandment 5),
  validated at load (Commandment 3); the retryable-error vocabulary
  must be a closed declarative allowlist — no arbitrary Python import
  strings or callables through YAML (judgement C-5; rejudgement C-6).
- Existing `on_error: skip|retry|fail|fallback` semantics for map and
  non-map nodes must remain expressible and pass their current
  witnesses; FR-069 timeout classification (`TIMEOUT_ERROR` before
  `Exception`) must remain intact.
- Witnesses must cover retryable-then-success with attempt count,
  exhausted retries, non-retryable immediate failure, and the single
  final `on_error` disposition — deterministic mocks, no network.
- Per-branch results must keep `_map_index` attribution and
  `sorted_add` ordering after retries.
- `is_this_a_graph`: must be answered — the research must state whether
  a graph-shaped retry (a loop edge with `loop_limits` around the map,
  or a second map over failed items) is the right primitive, or whether
  branch-level retry is necessarily a node-registration contract.

## Witnessed incidents

- 2026-08-31 FR-936 audit item 4: "No `RetryPolicy` surfaced" confirmed;
  judgement R-6 found the parent's `retry=` spelling wrong (actual
  keyword `retry_policy=`) and the wrapper's exception swallowing
  fatal to the proposal as written (`yamlgraph/compile/map_compiler.py:139-173`).
- 2026-09-02 FR-936 rejudgement R-5 / AC-07 / AC-10 / C-5 / C-6: the
  fence above.
- Installed LangGraph 1.2.11 `StateGraph.add_node` signature verified
  2026-09-02: `retry_policy: RetryPolicy | Sequence[RetryPolicy] | None`;
  `RetryPolicy` is a `NamedTuple` with `retry_on` defaulting to
  `default_retry_on`, which treats `ValueError`, `TypeError`,
  `LookupError`, `RuntimeError`, `OSError` and friends as non-retryable
  and everything else as retryable — a default whose failure modes
  differ from `executor_base.is_retryable`'s name-matching.
- FR-030 closure note (2026-02-14): "concurrency control belongs in LLM
  provider (RetryPolicy), not orchestration" — the repo already pointed
  at RetryPolicy as the right layer for burst handling and never wired
  it.
- FR-933 (Implemented 2026-08-31): node-level retry now carries
  validation feedback; `handle_retry` is fixed-count with no backoff
  (`yamlgraph/error_handlers.py:125-132`), so a rate-limit burst retried
  at this layer re-fires immediately.
- `docs/plan-web-toolkit.md` "Existing map node audit" item 4 and the
  LangGraph-native coverage table: transient LLM failures inside a
  fan-out named as "exactly RetryPolicy's case"; the fi-catalog pilot
  (component D) is the first consumer whose fan-out size makes 429/5xx
  bursts routine rather than exceptional.
