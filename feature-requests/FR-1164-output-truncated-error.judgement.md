# Judgement: FR-1164 Report replies cut off by the output-token limit, with the thinking share

**Route:** scripts/judge.sh (copilot gpt-6.1-sol), draft folded verbatim. Disposition: REJECTED; FR returned to plan, revisions R-1..R-5 folded, re-judge required.
**Prior art:** dispositioned in the FR's Prior art line and judged in the rubric below.


**Verdict:** REJECTED — return to plan: the cited research record fails the mandatory substance gate, and the raw-response binding and coverage contract require correction; no implementation authority is granted.

**Reviewed against:** `feature-requests/FR-1164-output-truncated-error.md`; `feature-requests/FR-1164.research.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `CLAUDE.md` (supplied repository doctrine); `feature-requests/FR-998-anthropic-constrained-structured-output.judgement.md:1-140`; `feature-requests/FR-464-deepseek-structured-output-fallback.md:1-95`; `feature-requests/FR-679-consolidate-retry-fallback-post-676.md:1-90`; `feature-requests/FR-1148-anthropic-thinking-off.md:1-130`; `feature-requests/FR-1152-thinking-tokens-in-token-usage.md:1-100`; `feature-requests/FR-071-thinking-budget-graph-level.md:1-65`; `feature-requests/FR-230-google-vertex-thinking-budget.md:1-65`; `feature-requests/FR-465-llm-safety-settings.md:1-90`; `yamlgraph/executor_base.py`; `yamlgraph/utils/structured_output.py`; `yamlgraph/node_factory/race_node.py`; `yamlgraph/utils/json_extract.py:1-130`; `examples/dungeon_master/chapter_close.yaml:1-100`; `reference/graph-yaml.md` (matched `max_tokens` and `thinking_budget` sections).

The FR and research record are tracked at reviewed HEAD `1cbf646d`; the working tree was clean. The cited `research-briefs/fr1164-truncated-reply-reported-empty-brief.md` does not exist in this tree and is not tracked; no brief content was consumed. No author conversation, uncommitted notes, provider-package inspection, live call, or additional judge execution was consumed or performed.

## What is sound

The strongest case against the proposal is that retaining raw structured responses changes a central policy used by several recovery paths, while a stop-reason check cannot guarantee completeness for every execution surface. That argues for a bounded contract and composition witnesses, not for continuing to accept known truncated answers.

The problem is real. FR-1148 records two thinking-only `max_tokens` responses with 1500 output tokens and zero text characters (`feature-requests/FR-1148-anthropic-thinking-off.md:81-95`). The dungeon-master comment records the analogous Gemini incident (`examples/dungeon_master/chapter_close.yaml:27-31`). The executor normalizes content immediately after plain invocations, losing the opportunity to inspect stop metadata (`yamlgraph/executor_base.py:436-447`). Checking before that normalization is the appropriate boundary.

The eight rubric findings are:

| Criterion | Finding and evidence |
|---|---|
| Scope | A shared classifier plus existing executor/race wiring is minimal for the named defect. The universal guarantee is not minimal or supported by the enumerated surfaces (`FR-1164:29-35,72-74,119-128`). Bound it rather than adding adjacent execution modes. |
| Consistency | The FR requires `include_raw=True` while declaring the only binder unchanged (`FR-1164:123-127`); that binder currently accepts only `method` and returns the library binding (`structured_output.py:45-63`). R-3 resolves this contradiction. |
| Measurability | AC-01/02/04/07 provide useful concrete assertions. Missing-usage behavior, fallback attempts, and the live probe's executable/artifact contract remain unspecified (`FR-1164:104-117,140-164`). |
| Feasibility | The cited code exposes the required raw-message seams, and FR-1152 identifies the normalized reasoning field (`FR-1152:27-32`). Actual provider raw-envelope contracts are still planned probes, not committed results (`FR-1164:79-85`). Authority must not assume those results. |
| Architecture alignment | Reusing the FR-998 policy and FR-679 shared attempt avoids a second provider policy (`FR-1164:15-22`; `FR-679:49-68`). Preserve the sole library binder and existing invocation configuration. |
| Single responsibility | Detecting token-limit termination and explaining its thinking share are one error-reporting concern, not a bundle. Safety-blocked replies and thinking configuration are correctly separate (`FR-1164:23-24,179-184`). No split is required. |
| Strategic classification | **Framework primitive**, extending existing execution policy: ordinary text, JSON-extraction, structured-schema, and race consumers need the same missing check (`FR-1164:45-57`). Existing abstractions supply placement but do not classify truncation. No new graph is justified. |
| Testability | Most direct fakes are derivable, but tests must model the actual raw envelope and exercise the second-attempt/fallback composition rather than fail on an incorrectly mocked return shape (`FR-1164:82-84,149-154`; `structured_output.py:100-147`). |

The prior-art dispositions for FR-464, FR-679, FR-1148 and FR-1152 are substantively appropriate. FR-465 is safety configuration, not token-limit termination (`FR-465-llm-safety-settings.md:48-51`). FR-679 explicitly distinguishes the rejected FR-672 from its later evidence of duplication (`FR-679:24-36`); this proposal must preserve that distinction and must not resurrect an unnecessary retry-loop refactor.

## Required revisions

### R-1: Replace persona convergence with dispositioned research evidence

The prospective research gate demands genuine solution classes, precedent lines, preserved disagreement, and an explicit graph-fit answer (`.github/skills/judge-fr/doctrine.md:118-130`). The cited record instead contains four predominantly repeated boundary-check proposals, all marked `pursue`, including a claimed existing provider-factory response wrapper (`FR-1164.research.md:21-26`). The FR itself disputes that location (`FR-1164:170-174`). Four personas are not four alternatives.

Replace or supplement the committed record with a dispositioned table covering the genuine alternatives already identified in the FR: invocation-boundary rejection; a newly introduced provider-client response wrapper; carrying diagnostic fields downstream; warning without rejection; and constructor budget validation. For each, record the concrete code/precedent lines, cost or limitation, and chosen/rejected disposition. Correct the factory-wrapper claim instead of retaining it as established evidence; preserve the data-process validation failure as a failed finding, not a successful persona. State explicitly that this is deterministic boundary validation, not an LLM graph.

Remove the missing brief reference from both artifacts or commit the actual brief. Include an explicit rejected-precedent disposition, including FR-672's context as recorded by FR-679. Do not manufacture another research run or imply that the existing run tested provider behavior.

### R-2: Bound the completeness guarantee to the enumerated invocation surfaces

Replace "every LLM node call," "No LLM reply ... ever," and "all of them" (`FR-1164:29,72-74,119`) with this contract: recognized output-limit stop reasons are rejected in `attempt_structured_invoke`, `invoke_structured`/`ainvoke_structured`, and `_invoke_candidate_async`, including their existing re-invocations.

Explicitly exclude direct binder consumers such as agent finalization, streaming/token-delivery paths, and arbitrary direct provider calls. The FR already leaves agent binding untouched, while FR-998 treats agent finalization as a distinct surface (`FR-1164:127`; `FR-998` judgement: shared-policy scope). Do not add agent or streaming implementation to repair the wording. State that absent or unrecognized stop metadata does not prove a response complete; it merely produces no new rejection.

### R-3: Freeze a workable raw-binding API and preserve both policy attempts

Replace "bind_structured_output ... is unchanged" with: add a keyword-only `include_raw: bool = False` to the existing binder; ordinary direct binder calls retain their parsed-only result shape, while the sync/native-async invocation helpers request raw output on both primary and earned `function_calling` second attempts. Continue to use the sole production `.with_structured_output(...)` expression. Do not create a second binder or accept both envelope and model shapes in production.

For each attempt, inspect the raw message before examining `parsing_error` or returning `parsed`. Preserve exception identity for a non-truncated parsing failure. Preserve the FR-998 second-attempt mark, exactly-one unsupported-capability retry, caller config, and native-async `second_attempt_config` behavior (`structured_output.py:100-147`). A truncation error must not earn that retry or the caller's FR-464 JSON fallback.

Commit the planned provider-contract probe results before freezing the provider table: exact package/version and metadata key/value evidence, and the actual `include_raw` envelope or invocation exception for the supported structured path. If the provider raises before returning raw data, record and bound that limitation; do not promise an unavailable raw message. A divergent contract returns to plan rather than authorizing a silent shim or an expanded catch.

### R-4: Define unavailable usage and safe diagnostic behavior

Specify that recognized truncation raises even when `usage_metadata`, `output_tokens`, or the reasoning detail is absent or `None`. Keep unavailable counts as `None` and render them as `unknown`; never claim missing reasoning usage is zero. Report each available count independently. Define the metadata precedence as the first nonempty `stop_reason`, otherwise `finish_reason`, and freeze the three recognized values pending R-3 evidence (`FR-1164:102-115`).

Type the helper's message parameter with the repository's LangChain message type. Derive `visible_chars` and the at-most-200-character preview only from `normalize_content(message.content)`. Do not include a raw message, thinking block, or provider payload in the diagnostic. Assert the sentinel is absent from both the exception string and preview. The advice to lower thinking must remain qualified by model support (`FR-1164:106,117,157-158`).

### R-5: Add composition witnesses, traceability, and a reproducible live gate

Extend AC-04/05 beyond the primary attempt: test truncation during the FR-998 earned second attempt and the FR-464 plain fallback, in sync and native async. Assert invocation counts, second-attempt marking, distinct async retry run IDs, and that a truncated candidate cannot win a race with a complete candidate. Retain non-truncated parsing-error identity and successful parsed-model returns. Verify `is_retryable(OutputTruncatedError(...))` is false; do not change existing node error-policy semantics.

Assign the tests a concrete registered requirement, extending the appropriate existing capability rather than duplicating the FR-998 policy registry. Record the capability/requirement and architecture update in the FR; every new test needs its requirement marker (`.github/copilot-instructions.md:170-171`).

Name a committed executable probe, exact Haiku model ID, command, credential prerequisite, bounded request count/spend, and committed result path containing package versions, git SHA, sanitized metadata and resulting error. Resolve the current discrepancy between planned plain-plus-structured probes and plain-only AC-08 (`FR-1164:80,159-160`). The judge grants no new spend approval: explicitly identify the operator's authorization before any paid call; lacking credentials or approval leaves the live gate unmet.

Record the targeted regression command, full required unit-suite command, `python scripts/req_coverage.py --strict`, `lint-imports`, and repository lint/format checks. Include the fix changelog fragment, implementation record and diary entry with `**Seed:**` as scoped support artifacts.

## Scope is frozen

These are the boundaries for a corrected proposal, not current permission to implement.

| Deliverable | Surface |
|---|---|
| D-1 | Revised `feature-requests/FR-1164-output-truncated-error.md` and substantive `feature-requests/FR-1164.research.md`; repaired or removed brief citation |
| D-2 | `yamlgraph/utils/stop_reason.py`: typed truncation error and one metadata classifier |
| D-3 | `yamlgraph/utils/structured_output.py`: explicit raw binding for invocation helpers, preserving direct binder defaults and FR-998 policy |
| D-4 | `yamlgraph/executor_base.py` and `yamlgraph/node_factory/race_node.py`: checks before normalization on existing plain/fallback paths |
| D-5 | Focused classifier, executor, structured-policy and race tests; mock-envelope updates only where raw-enabled calls require them |
| D-6 | `reference/graph-yaml.md`: shared output/thinking budget and explicitly bounded rejection behavior |
| D-7 | Concrete requirement/capability registration, architecture traceability, bounded committed probe/result, changelog fragment, FR implementation record and diary reflection |

Not authorized: agent-finalization or tool-loop changes; streaming changes; new provider wrappers; graph/prompt authoring; automatic token-budget increases; thinking-setting changes; safety-block classification; new retry policy; reordered fallback tiers; weakening tests; production acceptance of both raw and parsed-only return shapes; enforcement-infrastructure changes; unrelated refactoring or dependency changes. Any demonstrated dependency-floor gap requires a revised proposal, not an implicit scope extension.

## Revised acceptance criteria

The following are requirements for a corrected proposal and its eventual enforcement; they do not override the rejection.

- [ ] AC-01: The committed FR/research artifacts fold R-1 through R-5, contain dispositioned genuine alternatives and rejected-precedent treatment, and have no dangling brief citation.
- [ ] AC-02: Provider evidence names package versions and exact stop metadata/envelope shapes; the FR states a bounded invocation-surface guarantee and excludes unchanged direct binder/streaming consumers.
- [ ] AC-03: Thinking-only, mixed thinking/text and partial text messages with each recognized stop value raise `OutputTruncatedError` before normalization or JSON extraction; available 2000/1921 counts are reported.
- [ ] AC-04: Missing/`None` usage and reasoning details still raise on truncation, preserve unavailable fields as `None`, and print `unknown` rather than a guessed zero; stop-key precedence is tested.
- [ ] AC-05: Missing, unrecognized and ordinary `end_turn`/`stop` metadata produce no truncation error and retain existing successful results.
- [ ] AC-06: Raw-enabled sync/native-async structured primary and earned second attempts check truncation before parsing; complete successful calls return the parsed model, and complete parsing failures re-raise the identical exception object.
- [ ] AC-07: Direct binder consumers remain parsed-only by default; the sole production library-binding call is retained; config forwarding, exactly-one FR-998 fallback and second-attempt marking remain intact.
- [ ] AC-08: Executor and native-async race FR-464 plain re-invocations reject truncation without another fallback; call counts and distinct async run IDs are asserted.
- [ ] AC-09: A truncated race candidate fails and cannot win against a complete candidate; existing race cancellation and node error-policy regressions remain green; truncation is not retryable.
- [ ] AC-10: Exception fields preserve stop reason, available usage, normalized visible-character count and a preview of at most 200 visible characters; a thinking sentinel is absent from both string and preview.
- [ ] AC-11: The authorized, credentialed live probe is reproducible from its committed command and records exact model, budget, package versions, producing SHA, sanitized raw stop metadata and the truncation error; structured behavior is evidenced or its limitation is explicitly frozen.
- [ ] AC-12: The reference states the provider-supported shared thinking/output budget, qualified remediation advice, and the bounded `OutputTruncatedError` behavior without a universal completeness claim.
- [ ] AC-13: RED precedes GREEN; focused and required unit tests, strict requirement coverage, import boundaries and existing lint/format checks pass; new tests carry registered requirement markers.
- [ ] AC-14: The fix fragment, implementation decisions/deviations and diary entry with `**Seed:**` are committed within the authorized support scope.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | This draft is REJECTED and grants no code-edit authority. Return to plan; a corrected committed FR and substantive evidence require a subsequent independent approving judgement before enforcement. | GATE |
| C-2 | Do not treat folding these revisions alone as approval; the mandatory research-substance gate must be judged again. | GATE |
| C-3 | Preserve the FR-998 single binder, second-attempt policy, error identity/marking and invocation config, and FR-464/679 caller responsibilities. | GATE |
| C-4 | No missing metadata or usage value may be presented as proof of completeness or a fabricated thinking count. | GATE |
| C-5 | Paid probes require explicit operator spend authorization and credentials; absence is a blocked live criterion, not an offline success substitute. | GATE |
| C-6 | No agent, streaming, safety, graph/prompt, enforcement-infrastructure or unrelated provider/dependency expansion is covered by this proposal. | GATE |

Authority granted: none. The truncation-reporting direction is sound, but the current proposal returns to plan under the mandatory research gate.
