# Judgement: FR-1079 Retry ownership — one retry layer per failure class for every LLM call

**Prior art:** `FR-1079-retry-ownership.md` is the FR this judgement governs. FR-1064 (split parent), FR-1073, FR-957, 031, FR-708, FR-710 and FR-408 (Rejected) are dispositioned in the FR and below.

**Verdict:** APPROVED WITH REVISIONS — one explicit owner per LLM failure class is the right framework correction, but implementation authority activates only after R-1 through R-6, the complete provider/call-path witness, and the human decision below are folded into the FR and human-reviewed.

**Reviewed against:** `feature-requests/FR-1079-retry-ownership.md`; `docs/issues-2026-09-24.md`; `feature-requests/FR-1064-map-branch-contract.judgement.md`; `feature-requests/FR-1073-map-result-contract.md`; `feature-requests/FR-1073-map-result-contract.judgement.md`; `feature-requests/FR-1076-shared-map-reuse-helpers.judgement.md`; `feature-requests/FR-957-map-branch-native-retry-policy.md`; `feature-requests/FR-957-map-branch-native-retry-policy.judgement.md`; `feature-requests/031-native-retry-policy.md`; `feature-requests/FR-708-llm-client-request-timeout.md`; `feature-requests/FR-710-provider-deadline-floors.md`; `feature-requests/FR-408-runtime-repair-metadata.md`; `yamlgraph/config.py`; `yamlgraph/executor.py`; `yamlgraph/executor_async.py`; `yamlgraph/executor_base.py`; `yamlgraph/error_handlers.py`; `yamlgraph/utils/llm_bounds.py`; `yamlgraph/utils/llm_factory.py`; `yamlgraph/utils/llm_factory_async.py`; `yamlgraph/utils/llm_providers.py`; `yamlgraph/utils/structured_output.py`; `yamlgraph/utils/guard_runtime.py`; `yamlgraph/node_factory/llm_nodes.py`; `yamlgraph/node_factory/llm_execution.py`; `yamlgraph/node_factory/validation_feedback.py`; `yamlgraph/node_factory/race_node.py`; `yamlgraph/tools/agent.py`; `tests/unit/test_executor_retry.py`; `tests/unit/test_llm_factory_async.py`; `capabilities/CAP-03-node-execution.yaml`; `reference/graph-yaml.md`; `reference/development-operations.md`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The defect is real and located at a framework boundary. Every provider constructor receives SDK retries from `_bounded()`, while the sync and async prompt paths add their own loops and the node handler can re-enter those loops again (`yamlgraph/utils/llm_bounds.py:56-74`; `yamlgraph/executor.py:143-179`; `yamlgraph/utils/llm_factory_async.py:74-120`; `yamlgraph/error_handlers.py:108-135`). The incident record independently observed approximately three 30-second requests for one failed branch and explicitly withheld the inferred larger multiplication pending a real witness (`docs/issues-2026-09-24.md:75-107,642-671`). Measuring actual provider exception shapes before freezing a mapping is therefore necessary, not ceremony.

The proposed ownership boundary is also directionally correct. Transport faults belong in one shared invocation policy; Pydantic output rejection is the one class for which the node can add sanitized feedback (`yamlgraph/node_factory/validation_feedback.py:1-68`; `yamlgraph/node_factory/llm_execution.py:103-160`). Disabling fuzzy `"rate"` substring matching removes the demonstrated `GenerateError` false positive (`yamlgraph/executor_base.py:63-87`; `feature-requests/FR-1079-retry-ownership.md:65-77,142-143`). Keeping map-result records, streaming redesign, per-node transport policy, and repair metadata out preserves the split ordered by FR-1064 and distinguishes rejected FR-408 territory (`FR-1064-map-branch-contract.judgement.md:15-29`; `feature-requests/FR-1079-retry-ownership.md:185-190`).

| Rubric criterion | Finding |
|---|---|
| Scope | Retry ownership is properly separated from FR-1073's map-result contract and is one causal concern (`feature-requests/FR-1079-retry-ownership.md:19-39,185-190`). The claimed “every LLM call” surface is incomplete because `race_node` and `agent` invoke factory clients without either executor loop (`yamlgraph/node_factory/race_node.py:150-180,203-208`; `yamlgraph/tools/agent.py:100-134,311-328`); R-1 closes the required surface rather than adding an adjacent feature. |
| Consistency | The value statement promises a predictable request budget for every call, but SDK-off plus executor ownership leaves direct callers with no transport owner, while “streaming requests” is excluded even though changing the cached client changes its stream-start behavior too (`feature-requests/FR-1079-retry-ownership.md:1,47-51,101-102,127-129,185-188`). R-1 narrows “streaming” to token/chunk semantics and makes all affected factory call paths explicit. |
| Measurability | Status, attempt count, elapsed/scheduled delay, and request-count formulas are mechanical. AC-08 is expressly non-gating and spend-dependent, so it is not an acceptance criterion; AC-07 also compares a formula to single-failure rows that cannot witness mixed failure classes (`feature-requests/FR-1079-retry-ownership.md:132-153`). R-5 and R-6 replace both with deterministic gates. |
| Feasibility | The constructors, sync loop, async loop, and validation-feedback seam exist. The proposed single local endpoint is not feasible through the stated public API: `create_llm()` accepts no `base_url` or transport override, supports twelve providers, and only LM Studio/RunPod expose environment-selected endpoints (`yamlgraph/utils/llm_factory.py:22-35,88-105`; `yamlgraph/utils/llm_providers.py:148-176,185-255,287-324`). R-2 requires wrapper-appropriate transport interception without adding a production endpoint knob. |
| Architecture alignment | Classification at the provider/invocation boundary follows the repository's normalization law, and CAP-03 already owns sync/async factory and bounded-provider work (`capabilities/CAP-03-node-execution.yaml:21-25,47-60`). One shared transport policy must replace, not duplicate, the two current loops and must be used by direct callers; R-1 and R-5 freeze that shape. |
| Single responsibility | Provider classification, backoff, SDK disabling, node validation re-ask, and request-budget documentation are inseparable parts of assigning exactly one owner per failure class. Map result semantics, LangGraph branch retry, timeout-thread lifecycle, and streaming transport redesign remain separate. No further split is warranted. |
| Strategic classification | **Framework primitive.** The affected use cases include synchronous prompts, asynchronous prompts, race candidates, agent/tool loops, structured-output protocol fallback, and LLM nodes across twelve provider constructors (`yamlgraph/utils/llm_factory.py:22-35`; `yamlgraph/executor_base.py:412-445`; `yamlgraph/node_factory/race_node.py:150-180`; `yamlgraph/tools/agent.py:100-134,311-328`). No existing abstraction owns transport retry across those paths. |
| Testability | Failing tests can assert exact transport sends, exception classification, scheduled sleeps, node re-asks, and mixed-path budgets. The current “witness (RED)” conflates a passing characterization table with a failing desired-behavior test (`feature-requests/FR-1079-retry-ownership.md:91-100,132-136`); R-2 separates them so RED fails on missing behavior rather than missing fixtures. |

The research gate is substantive. The FR contains five genuine solution classes, preserves the SDK-owned dissent, dispositions FR-957 and rejected FR-408, and answers `is_this_a_graph` (`feature-requests/FR-1079-retry-ownership.md:13-39,159-182`). That is the equivalent committed alternatives form permitted by the local judge doctrine, not a dangling “research skipped” field (`.github/skills/judge-fr/doctrine.md:118-129`). The direction is therefore revisable rather than rejectable.

## Required revisions

### R-1: Freeze the complete call-path ownership matrix

Replace the three-layer inventory with a table covering every factory-backed request path before setting SDK retries to zero:

1. sync `PromptExecutor._invoke_with_retry`;
2. async `invoke_async`;
3. race candidate `ainvoke_structured` / `llm.ainvoke`;
4. agent tool-loop and agent finalization invocations;
5. structured-output protocol negotiation/fallback;
6. node validation re-ask, verification retry, post-guard retry, and fallback-provider invocation; and
7. `invoke`, `ainvoke`, `stream`, and `astream` startup behavior exposed by factory clients.

Extract one shared sync/async **transport** retry policy and route sync executor, async executor, race, and agent transport calls through it before `_DEFAULT_MAX_RETRIES` becomes zero. The policy must accept the provider identity and an invocation callable, share one classifier and delay calculator, and preserve native async sleep/cancellation. Structured-output protocol negotiation, Pydantic correction, verification, guards, fallback-provider selection, and agent iterations remain distinct semantic owners; do not misclassify them as transport retries or delete them (`yamlgraph/executor_base.py:412-445`; `yamlgraph/utils/structured_output.py:84-130`; `yamlgraph/node_factory/llm_execution.py:38-68,103-160`; `yamlgraph/node_factory/llm_nodes.py:222-260`; `yamlgraph/utils/guard_runtime.py:185-218`; `yamlgraph/tools/agent.py:100-134`).

Revise the streaming exclusion to “token-streaming/chunk-gap redesign is out of scope.” Because SDK configuration is client-wide, stream/astream startup request counts are in scope and require regression witnesses; no token-streaming feature or graph change is authorized.

### R-2: Commit a feasible provider-complete baseline before freezing the mapping

Replace the single generic local endpoint with a committed provider matrix for all twelve `_PROVIDER_FACTORIES` entries. For each wrapper family, intercept the real SDK transport at a wrapper-supported test seam and produce the actual exception module, type, HTTP status, and response headers that reach the shared policy. Do not add a public `base_url`, credential, or production test hook solely to make the fixture work. The matrix must cover 500, 429 without `Retry-After`, 429 with both supported header forms, 400, 401, request timeout, connection drop, and schema-invalid output on sync and async paths. If any supported constructor cannot be exercised without credentials or production API traffic, enforcement remains blocked until a deterministic seam is identified; do not silently infer it from another provider.

Commit the characterization as `feature-requests/FR-1079.retry-witness.md` with columns for provider, wrapper family, call path, injected failure, exception module/type, status/header shape, SDK sends, framework sends, and elapsed/scheduled delay. This baseline may pass on current code; it is not RED. Add separate desired-state tests that fail on current behavior because SDK retries remain enabled, direct callers lack the shared owner, fuzzy classification remains, or node retry repeats transport errors. Preserve RED and GREEN as separate commits as required by repository doctrine (`.github/copilot-instructions.md:198`; `FR-1064-map-branch-contract.judgement.md:27-29`).

Fold the witnessed provider-qualified mapping into the FR before production implementation. If the witness changes the solution class, ownership boundary, or permanent/transient classification, return the revised plan to judgement rather than choosing during GREEN (`feature-requests/FR-1079-retry-ownership.md:91-100`).

### R-3: Define one closed classifier and exact `Retry-After` semantics

Add a typed classifier result shared by every transport caller. Freeze the predicates from the R-2 witness for connection failures, 429, 500-599, other 4xx, authentication, non-streaming request timeouts, and unmapped exceptions. The result must carry provider, qualified exception type, optional status, failure class, attempt number, and parsed retry delay; do not return an untyped dict. An unmapped exception is attempted once and logged with provider plus qualified type. A class merely containing `"rate"` is never sufficient (`feature-requests/FR-1079-retry-ownership.md:103-110,142-143`).

Define `LLM_MAX_RETRIES` as **total transport attempts**, validate it as an integer at least one, and validate non-negative backoff values with `LLM_RETRY_MAX_DELAY >= LLM_RETRY_DELAY`. Sync and async use the same delay calculator; tests inject wall clock, monotonic clock, sleeper, and jitter source if jitter is retained.

For 429, support standard delay-seconds and HTTP-date `Retry-After` values against the injected wall clock. No header uses ordinary capped exponential backoff. A valid delay at or below `RETRY_MAX_DELAY` waits `max(backoff, retry_after)`; a negative, malformed, or over-cap value makes no retry and raises/logs an error naming the raw value and configured cap. Do not call that rate limit “permanent”: it remains a transient provider response that exceeded or violated the local retry budget. This removes the current contradiction between “capped at” and “above the cap fails as permanent” (`feature-requests/FR-1079-retry-ownership.md:112-114,139-141`).

### R-4: Freeze node-level semantic retry and final error behavior

Define `on_error: retry` for LLM nodes as a Pydantic schema-correction owner only: it may re-ask only when `build_validation_feedback(error)` returns non-empty sanitized feedback. `max_retries` remains the number of **additional semantic re-asks after the initial logical invocation**. A transport-permanent, transport-timeout, unmapped, or transport-transient-exhausted error makes no node-level request; it produces exactly one existing `PipelineError` state update with no output. Keep `skip`, `fail`, and fallback-provider disposition unchanged apart from each provider invocation using the shared transport owner (`yamlgraph/node_factory/validation_feedback.py:45-68`; `yamlgraph/node_factory/llm_execution.py:103-160`).

State explicitly whether malformed/unextractable JSON that is not a Pydantic `ValidationError` is eligible. The minimal authorized contract is **no**: it fails once unless an existing structured-output protocol fallback handles it. Expanding semantic feedback beyond the existing Pydantic boundary requires separate evidence and revision; do not revive FR-408 repair/coercion behavior.

Add deterministic mixed-sequence tests: transient/transient/success; permanent once; timeout once; validation rejection followed by corrected output; validation rejection whose re-ask encounters transient faults; exhausted transient under `on_error: retry`; and fallback-provider invocation after a primary permanent error. Every case must assert transport sends, semantic invocations, scheduled delays, emitted error count, and feedback presence/absence.

### R-5: Specify request-budget formulas, delivery surfaces, and documentation

Replace “the documented worst-case equals the witnessed maximum” with formulas derived from the frozen execution order. Define separate variables for transport attempts, protocol-negotiation requests, validation re-asks, verification re-executions, post-guard re-executions, fallback-provider calls, agent iterations, and race candidates. Document ordinary, structured-output, validation, verification/guard, fallback, race, and agent budgets separately, then add at least one deterministic mixed-path fixture for each formula. A row containing only a 500 or only invalid output cannot prove the product of sequential failure classes (`feature-requests/FR-1079-retry-ownership.md:47-51,87-89,147-149`).

Freeze these delivery surfaces:

| Deliverable | Surface |
|---|---|
| D-1 — baseline evidence | `feature-requests/FR-1079.retry-witness.md`; deterministic provider transport fixtures |
| D-2 — shared transport owner | `yamlgraph/utils/llm_bounds.py`; one focused typed retry-policy module under `yamlgraph/utils/`; `yamlgraph/executor.py`; `yamlgraph/utils/llm_factory_async.py`; only directly required classifier/config helpers |
| D-3 — complete caller routing | `yamlgraph/node_factory/race_node.py`; `yamlgraph/tools/agent.py`; `yamlgraph/node_factory/llm_execution.py`; directly required structured-output call wrapping without changing protocol-fallback policy |
| D-4 — witnesses | one focused `tests/unit/test_fr1079_retry_ownership.py`; directly affected executor, async-factory, provider-bound, race, agent, validation-feedback, verification, and guard regression suites |
| D-5 — contract and traceability | `reference/graph-yaml.md`; `reference/development-operations.md`; one new requirement under `capabilities/CAP-03-node-execution.yaml`; regenerated `ARCHITECTURE.md` traceability |
| D-6 — repository record | FR-1079 revision/implementation record; one fix changelog fragment; one diary distillation with `Seed:` |
| D-7 — planning/optional observation | FR-957 supersession note after authority activates; optional human-approved `innovation_matrix` run record |

Documentation must distinguish SDK retry count from framework total attempts, list failure-class owners, show formulas with the default values, describe malformed/over-cap `Retry-After`, and state that `LLM_REQUEST_TIMEOUT` is one non-streaming request bound rather than a node wall-clock bound. Correct the stale RunPod guidance that currently recommends stacking per-node `on_error: retry` for cold starts (`reference/development-operations.md:119`).

### R-6: Remove optional spend from acceptance and sequence supersession

Move the live haiku run out of acceptance into D-7 as optional operational evidence. **Human decision required:** after deterministic acceptance is green, does the operator authorize provider spend for one `innovation_matrix` haiku run with the explicit timeout? Until an affirmative decision is recorded, do not run it and make no live-provider claim. If approved, record provider/model, exact command, timeout, per-branch request count, elapsed time, final map verdict, and raw log location; the result cannot override deterministic acceptance (`feature-requests/FR-1079-retry-ownership.md:150-152`).

Replace “on judgement, FR-957 is superseded” with: after R-1 through R-6 are folded, the complete baseline is committed, this advisory judgement is human-reviewed, and FR-1079 authority activates, update FR-957 to `Superseded by FR-1079` with a note that its concurrent `error_handler` design was disproved. Preserve FR-031's non-LLM graph-wide proposal; FR-1079 does not authorize LangGraph `RetryPolicy` or generic tool-node retry (`FR-1064-map-branch-contract.judgement.md:15-17,44-46`; `feature-requests/FR-957-map-branch-native-retry-policy.md:15-25,281-290`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Provider-complete committed baseline and deterministic transport fixtures |
| D-2 | One typed shared sync/async transport retry owner; SDK retries disabled only after full caller coverage |
| D-3 | Sync prompt, async prompt, race, agent, and LLM-node routing through the shared transport owner |
| D-4 | Pydantic-validation-only node re-ask and exact final error disposition |
| D-5 | Focused RED/GREEN suites for classification, delays, request counts, formulas, and stream-start regression |
| D-6 | CAP-03/ARCHITECTURE traceability, retry/request documentation, changelog, FR record, and diary distillation |
| D-7 | FR-957 supersession note after authority activation; optional spend-approved live observation |

Not authorized: map result/failure-channel changes; LangGraph `RetryPolicy`; generic Python/tool-node retry; FR-1073 record or schema changes; an `error_class` field on `MapFailure`; per-node transport configuration; new retry env knobs; a public provider endpoint/base-URL test hook; repair/coercion registries; token-streaming or chunk-gap redesign; graph or prompt edits; map timeout-thread lifecycle; cross-run memory; provider credentials in tests; CI/hook/judge/review changes; or implementation of the remaining FR-031 proposal.

## Revised acceptance criteria

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

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-6 into FR-1079, commit the complete provider/call-path baseline and exact mapping, and obtain human review of this advisory judgement before production implementation authority activates. | GATE |
| C-2 | If the baseline changes the chosen owner, solution class, or permanent/transient mapping, revise the FR and return it to judgement before GREEN. | GATE |
| C-3 | Do not set SDK retries to zero until sync, async, race, agent, invoke/ainvoke, and stream/astream startup paths have a witnessed single transport owner. | GATE |
| C-4 | Do not add a public base-URL/transport test hook, use live credentials, or infer one provider's exception contract for an unwitnessed provider. | GATE |
| C-5 | Do not retry non-streaming timeouts, other 4xx, authentication failures, malformed/over-cap `Retry-After`, or unmapped exceptions; all must fail loudly with typed/logged attribution. | GATE |
| C-6 | Restrict node semantic re-ask to existing sanitized Pydantic validation feedback; no coercion, repair registry, generic malformed-JSON retry, or transport retry at the node layer. | GATE |
| C-7 | Preserve structured-output, fallback, verification, guard, race, and agent semantics while counting every transport send they can produce; do not hide them from the documented budget. | GATE |
| C-8 | Do not run the paid haiku observation without explicit human spend approval; absence of approval or credentials cannot fail acceptance. | GATE |
| C-9 | Preserve RED then GREEN commits, focused deterministic tests, CAP-03 traceability, exact docs, changelog, FR implementation record, and diary distillation. | GATE |
| C-10 | Keep map-result, LangGraph retry, token-streaming redesign, per-node transport policy, graph/prompt, and enforcement-infrastructure surfaces outside this FR. | GATE |

Authority granted: after C-1 through C-10 are satisfied, implement the provider-complete shared transport retry owner, Pydantic-validation-only node re-ask, deterministic witnesses, and documentation exactly within D-1 through D-6; D-7's live observation additionally requires recorded human spend approval.
