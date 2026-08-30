# Judgement: FR-933 Retry Cannot Recover a Deterministic Schema Rejection

**Prior art:** the FR-738 gate's sole hit on this file is
`FR-933-retry-cannot-recover-deterministic-rejection.md` — this judgement's
own subject, not precedent. Judgements are siblings of the FR they judge;
`build_prior_art` excludes the exact query path but not the sibling, so
every judgement retrieves its own FR. Recorded under FR-932's extraction
findings, not fixed here. The precedent this judgement actually consumed is
enumerated in **Reviewed against** below, and its dispositive finding is
`feature-requests/FR-408-runtime-repair-metadata.md`.

**Verdict:** REJECTED - the defect is real, but this post-FR-890 FR lacks the mandatory committed `**Research:**` evidence and cites a dangling FR-926 prior-art path, so it grants no implementation authority.

**Reviewed against:** `feature-requests/FR-933-retry-cannot-recover-deterministic-rejection.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/TEMPLATE.md`; `feature-requests/FR-890-research-sole-route-closed-input-alternatives.md`; `feature-requests/FR-896-research-route-precedent-traceability.md`; `feature-requests/FR-408-runtime-repair-metadata.md`; `capabilities/CAP-248-research-sole-route.yaml`; `examples/demos/research-route/graph.yaml`; `examples/demos/research-route/prompts/os_infra_primitivist.yaml`; `examples/demos/research-route/prompts/data_process_planner.yaml`; `examples/demos/research-route/prompts/yamlgraph_native_planner.yaml`; `examples/demos/research-route/prompts/subtractionist.yaml`; `examples/demos/research-route/prompts/librarian.yaml`; `examples/demos/research-route/prompts/librarian_structure.yaml`; `yamlgraph/node_factory/llm_execution.py`; `yamlgraph/node_factory/llm_nodes.py`; `yamlgraph/error_handlers.py`; `yamlgraph/executor.py`; `yamlgraph/executor_base.py`; `tests/unit/test_reliability.py`; `tests/unit/test_executor_retry.py`; `tests/unit/test_fr926_recorded_cause_witness.py`. Cited but unavailable and therefore not consumed: `feature-requests/FR-926-research-route-error-surfacing.md` (the repository contains `feature-requests/FR-926-research-failure-cites-recorded-cause.md` instead).

## What is sound

The problem is concrete and bounded. FR-933 names `scripts/research.sh` as the first consumer and says that route is failing every run (`feature-requests/FR-933-retry-cannot-recover-deterministic-rejection.md:8-9`), records five over-length schema failures across two briefs and several persona/field combinations (`feature-requests/FR-933-retry-cannot-recover-deterministic-rejection.md:25-40`), and ties the failure to an active capability claim (`capabilities/CAP-248-research-sole-route.yaml:2-4`, `capabilities/CAP-248-research-sole-route.yaml:20-26`). This satisfies the "problem is real" part of Scope and Strategic classification.

The code evidence supports the root cause. The research graph runs at `temperature: 0.0` (`examples/demos/research-route/graph.yaml:14`) and all five structured persona nodes use `on_error: retry` with `max_retries: 2` (`examples/demos/research-route/graph.yaml:88-92`, `examples/demos/research-route/graph.yaml:101-105`, `examples/demos/research-route/graph.yaml:114-118`, `examples/demos/research-route/graph.yaml:128-132`, `examples/demos/research-route/graph.yaml:171-175`). The node-level retry handler invokes `lambda: attempt_execute(cfg.provider)` without passing attempt state or revised variables (`yamlgraph/node_factory/llm_execution.py:125-128`), while the LLM node resolves variables once before defining the closure (`yamlgraph/node_factory/llm_nodes.py:323-335`). That makes the claimed identical retry plausible and mechanically testable.

The architectural instinct is mostly right. FR-896 intentionally froze "rejected, not truncated" cell ceilings (`feature-requests/FR-896-research-route-precedent-traceability.md:166`, `feature-requests/FR-896-research-route-precedent-traceability.md:221`) and records that a second live overflow was mechanized with node-level retry instead of more prompt wording (`feature-requests/FR-896-research-route-precedent-traceability.md:315-321`). The current prompt schemas already repeat `max_length=400` and "over-length output is rejected, never truncated" across the structured fields (`examples/demos/research-route/prompts/os_infra_primitivist.yaml:6-35`, `examples/demos/research-route/prompts/data_process_planner.yaml:6-35`, `examples/demos/research-route/prompts/yamlgraph_native_planner.yaml:6-35`, `examples/demos/research-route/prompts/subtractionist.yaml:6-35`, `examples/demos/research-route/prompts/librarian_structure.yaml:6-35`). The repo doctrine's `two_strike_split` cure says repeated guard failures belong in code, not more prompt text (`.github/copilot-instructions.md:117`).

The likely strategic classification is a narrow Framework primitive: the surface is core LLM-node retry semantics, not a research-route-only workaround. Existing executor retry already distinguishes retryable provider failures from non-retryable errors (`yamlgraph/executor_base.py:60-77`, `yamlgraph/executor.py:140-164`), while node-level `on_error: retry` currently retries any caught exception. Existing tests cover both node-level retry count behavior and executor non-retry behavior (`tests/unit/test_reliability.py:159-207`, `tests/unit/test_executor_retry.py:185-219`), so the proposed fix is feasible to witness without inventing a new runner.

## Required revisions

### R-1: Add mandatory research evidence before resubmission

Add a `**Research:**` field to FR-933 that points to a committed, non-dangling research record or equivalent committed alternatives table. The current FR header jumps from first consumer/prior art into summary and has no `**Research:**` field (`feature-requests/FR-933-retry-cannot-recover-deterministic-rejection.md:3-17`), but the active template requires it (`feature-requests/TEMPLATE.md:11-20`) and judge doctrine gives no authority to newly created FRs whose research field is absent, dangling, or strawman (`.github/skills/judge-fr/doctrine.md:118-128`). If `scripts/research.sh` cannot produce the record because this defect blocks it, the equivalent committed record must say that explicitly and still include dispositioned alternatives, precedent lines, and the `is_this_a_graph` answer; the exception itself is a human/product process decision, not something the Judge may silently absorb.

### R-2: Correct and complete prior-art disposition

Replace the dangling cited path `feature-requests/FR-926-research-route-error-surfacing.md` with the actual committed FR-926 artifact or remove the claim. Also disposition `feature-requests/FR-408-runtime-repair-metadata.md`, which is directly adjacent prior art: it describes blind `on_error: retry` on validation errors (`feature-requests/FR-408-runtime-repair-metadata.md:16-31`) and a rejected `retry-with-schema`/`auto_repair` design (`feature-requests/FR-408-runtime-repair-metadata.md:56-111`, `feature-requests/FR-408-runtime-repair-metadata.md:144-146`). The revised FR must distinguish itself by explicitly forbidding FR-408's rejected bulk mechanisms: no new `on_error: auto_repair`, no broad `PipelineError` repair registry, no `inject-default`, no threshold relaxation, and no silent coercion/truncation.

### R-3: Choose one retry policy and freeze it

Fold the two candidate mechanisms into one authorized behavior: for a Pydantic `ValidationError` raised while parsing structured LLM output, the next node-level retry must receive bounded validation feedback derived from the failed schema parse; non-validation exceptions keep existing retry/fallback behavior. The feedback must include the field path and validation message, plus limit/actual length when available, but must not paste the full over-length value back into the prompt. This preserves FR-896's rejection-never-truncation contract (`feature-requests/FR-896-research-route-precedent-traceability.md:166`, `feature-requests/FR-896-research-route-precedent-traceability.md:221`) while making retry meaningfully different from the first attempt. "Classify `ValidationError` as non-retryable" may remain an alternative in the research record, but it is not the implementation path for this FR because it cannot satisfy the stated first consumer need to make the research route complete (`feature-requests/FR-933-retry-cannot-recover-deterministic-rejection.md:8-9`, `feature-requests/FR-933-retry-cannot-recover-deterministic-rejection.md:86-91`).

### R-4: Make the acceptance criteria fully mechanical

Rewrite the acceptance criteria as final, checkable obligations rather than "draft, for the Judge to sharpen" (`feature-requests/FR-933-retry-cannot-recover-deterministic-rejection.md:94`). The unit tests must verify the actual retry-call inputs, not merely call counts; the unchanged-transient behavior must name the existing test surfaces or add a targeted witness; and the live `scripts/research.sh` criterion must name the brief path, expected artifact, provenance line, and verification command. The current AC-04 says the live run completes and appends provenance (`feature-requests/FR-933-retry-cannot-recover-deterministic-rejection.md:102-103`) but does not define what artifact is accepted or how the append is checked.

### R-5: Preserve the graph-authoring boundary and excluded surfaces

Keep the fix in the Python retry boundary unless the revised FR explicitly authorizes governed graph/prompt edits. FR-933 itself excludes changing persona prompts, `max_length=400`, rejection-never-truncation, and FR-932 scope (`feature-requests/FR-933-retry-cannot-recover-deterministic-rejection.md:105-108`); repo doctrine requires material graph or prompt changes to go through `scripts/author.sh` and be evidenced by `tmp/draft-authoring-report.md` (`.github/copilot-instructions.md:13-15`). If enforcement discovers graph or prompt edits are required, stop and amend/rejudge rather than slipping them into this FR.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised `feature-requests/FR-933-retry-cannot-recover-deterministic-rejection.md` with `**Research:**`, corrected prior-art links, final ACs, and implementation-status section |
| D-2 | Committed research/equivalent alternatives record referenced by D-1 |
| D-3 | Targeted RED/GREEN tests for node-level structured-output validation retry, most likely under `tests/unit/test_reliability.py` or a focused new unit test |
| D-4 | Surgical retry implementation at the LLM-node execution boundary, limited to `yamlgraph/node_factory/llm_nodes.py`, `yamlgraph/node_factory/llm_execution.py`, `yamlgraph/error_handlers.py`, and `yamlgraph/executor.py` only if the existing call signature must carry feedback |
| D-5 | Regression coverage proving executor/provider transient retry behavior remains unchanged |
| D-6 | Live research-route witness artifact and provenance line proving the original first consumer completes |
| D-7 | Changelog fragment, requirement-tagged tests where applicable, FR implementation record, and diary reflection |

Not authorized: changing `max_length=400`; truncating invalid model output; weakening Pydantic schemas; changing research-route persona prompts or `examples/demos/research-route/graph.yaml` without the authoring route; changing FR-932 scope; adding a new `on_error` mode; reviving FR-408's `auto_repair`, diagnostic-code registry, `inject-default`, or threshold relaxation; changing judge/research/author invocation routes; treating missing research evidence as waived without explicit human review.

## Revised acceptance criteria

- [ ] AC-01: FR-933 contains a non-dangling `**Research:**` link to a committed research record or equivalent alternatives table; that record dispositions FR-408, FR-890, FR-896, FR-926, "feedback retry", and "validation is non-retryable", and includes an `is_this_a_graph` answer.
- [ ] AC-02: All prior-art paths in FR-933 resolve to committed artifacts; the FR either cites the actual FR-926 path or removes the bad path.
- [ ] AC-03: A RED unit test for an LLM node with structured output, `on_error: retry`, `max_retries: 2`, and a Pydantic `ValidationError` records the initial `execute_prompt` variables and the retry variables, proving the retry attempt receives validation feedback instead of a byte-identical request.
- [ ] AC-04: After the fix, the same test proves the retry feedback includes the failing field path and validation message, includes limit/actual-length metadata when available, and does not include the full rejected over-length field value.
- [ ] AC-05: A success-path unit test proves a second structured-output attempt can pass after receiving validation feedback and stores the parsed output under the node `state_key`.
- [ ] AC-06: An exhausted validation-feedback retry returns a `PipelineError` preserving the node name, exception type, and validation message; it does not truncate, coerce, or return success-shaped fallback state.
- [ ] AC-07: Existing transient/provider retry behavior remains unchanged: retryable provider exceptions still retry according to the existing executor policy, and node-level non-validation retry tests still satisfy their current call-count and error-surfacing contracts.
- [ ] AC-08: No persona prompt, research graph, `max_length=400`, or rejection-never-truncation contract is changed. If a governed graph or prompt artifact changes, `scripts/author.sh` produces it and `tmp/draft-authoring-report.md` records lint, smoke, and any limitation.
- [ ] AC-09: A live `scripts/research.sh <brief>` run for the failing research-route class completes, writes the expected alternatives artifact, passes the artifact verifier, and appends a matching provenance line to `feature-requests/research-runs.jsonl`.
- [ ] AC-10: The implementation updates FR-933's implementation record, adds an appropriate changelog fragment, tags new tests with relevant `REQ-YG-XXX` markers where applicable, and adds the required diary reflection.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | No implementation authority exists until R-1 and R-2 are folded into the FR and the revised FR is judged again. | GATE |
| C-2 | Enforcement must start with failing tests that prove identical validation retries and the desired feedback-bearing retry. | GATE |
| C-3 | The implementation must remain a narrow LLM structured-output retry repair and must not reintroduce FR-408's rejected `auto_repair` framework. | GATE |
| C-4 | The fix must preserve rejection-never-truncation and must not weaken or remove the 400-character schema constraints. | GATE |
| C-5 | Material graph or prompt artifact changes require the graph-authoring route evidence before they are accepted. | GATE |
| C-6 | If a human wants to waive the research-evidence gate because the research route is the broken component, that waiver must be explicitly recorded before rejudgement; this draft judgement does not grant it. | GATE |

Authority granted: none; FR-933 must return to planning with the required research evidence and corrected prior-art disposition before any code may be built under it.
