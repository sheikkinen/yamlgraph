# Judgement: FR-1164 Report replies cut off by the output-token limit, with the thinking share

**Route:** scripts/judge.sh (copilot gpt-6.1-sol, session ea6177d4), re-judge of revised HEAD `c594f34c`, draft folded verbatim below. Disposition: APPROVED WITH REVISIONS; R-1 folded into the FR at fold time (AC-11, AC-13, Planned Operations).
**Prior art:** FR-464, FR-672 (REJECTED, dispositioned via FR-679), FR-679, FR-998, FR-1148, FR-1152, FR-071/FR-230, FR-465 — dispositioned in the FR's Prior art line and judged in the rubric below.

**Verdict:** APPROVED WITH REVISIONS - the revised research and bounded raw-response design support implementation; authority activates only after R-1 corrects the optional probe's impossible expectation and command gate.

**Reviewed against:** committed HEAD `c594f34ca515437cd83ad430254ac1b45b2c31b7`, with a clean working tree at review:

- `feature-requests/FR-1164-output-truncated-error.md`
- `feature-requests/FR-1164.research.md`
- `feature-requests/FR-1164-output-truncated-error.judgement.md`
- `feature-requests/research-briefs/fr1164-truncated-reply-reported-empty-brief.md`
- `feature-requests/evidence/FR-1164-truncation-probe.json`
- `scripts/probe_fr1164_truncation.py`
- `yamlgraph/utils/structured_output.py`
- `yamlgraph/executor_base.py:45-115,360-447`
- `yamlgraph/node_factory/race_node.py:90-220`
- `yamlgraph/utils/content.py`
- `yamlgraph/utils/json_extract.py`
- `capabilities/CAP-164-structured-output-fallback.yaml`; capability registry searched only for the proposed `REQ-YG-729` allocation
- `feature-requests/FR-672-extract-shared-retry-policy.md`
- `feature-requests/FR-679-consolidate-retry-fallback-post-676.md:1-90`
- `feature-requests/FR-998-anthropic-constrained-structured-output.judgement.md:1-145`
- `feature-requests/FR-464-deepseek-structured-output-fallback.md:1-95`
- `feature-requests/FR-1148-anthropic-thinking-off.md:65-110`
- `feature-requests/FR-1152-thinking-tokens-in-token-usage.md:1-110`
- `reference/graph-yaml.md` matched `max_tokens` and `thinking_budget` sections
- `.github/skills/judge-fr/doctrine.md`
- `.github/skills/judge-fr/judgement.template.md`
- `.github/copilot-instructions.md` and `CLAUDE.md` as supplied repository doctrine

No author conversation or uncommitted notes were consumed. The research brief was treated as historical problem input, not as implementation authority: its factory-only constraint is explicitly superseded by the corrected research and bounded FR. No provider request, installed-package inspection, or further judge execution was performed. Provider-package observations are assessed as claims in the committed research record, not independently reproduced observations.

## What is sound

The strongest case against approval is that changing structured helpers from parsed-only results to raw envelopes affects a central recovery policy, while detecting a few stop values cannot prove general completeness. The revision now answers that objection with an explicit invocation-surface boundary, an envelope-only contract for raw-enabled helpers, unchanged direct binder defaults, and composition witnesses for both existing recovery tiers (`FR-1164:90-97,164-190,229-247`). A new provider wrapper or a universal completeness claim would be unjustified; neither is needed for the witnessed defect.

The raw evidence establishes a subtler failure than an empty parse result. The structured response ends inside a quoted array element, yet `parsing_error` is null and the returned model contains a fabricated empty trailing country (`feature-requests/evidence/FR-1164-truncation-probe.json:115-121`). That is substantive evidence for checking raw stop metadata before accepting even a valid parsed model. The absence of reasoning details in the same response also supports reporting unknown rather than inventing zero (`evidence:101-111`; `FR-1164.research.md:77-95`).

The previous rejection's research gate is now satisfied. The committed record distinguishes five genuine alternatives, corrects the nonexistent factory-wrapper premise, preserves the failed persona as a failure, and explicitly answers the graph-fit question (`FR-1164.research.md:15-57`). Its OpenAI/Google rows are honestly offline-only, not represented as live probes (`research:63-71`). The rejected FR-672 is dispositioned against the later evidence in FR-679 rather than silently resurrected (`research:51-57`; `FR-679:26-36`). The repaired brief and evidence links resolve relative to the FR's directory and are tracked.

| Criterion | Finding and evidence |
|---|---|
| Scope | Minimal for the named defect: one classifier and wiring at the existing executor, structured-policy and race seams. Agent/tool loops, streaming and arbitrary provider calls are explicitly excluded (`FR-1164:90-97,162-190`). |
| Consistency | The earlier binder contradiction is resolved by keyword-only `include_raw=False` and raw-enabled invocation helpers (`FR-1164:164-178`). One contradiction remains: AC-11 requires a direct provider call to raise the new framework error despite excluding that surface; R-1 corrects it (`FR-1164:95,252-262`; `probe_fr1164_truncation.py:92-95`). |
| Measurability | AC-03 through AC-10 specify observable stop values, counts, exception identity, call counts, run IDs and race outcomes (`FR-1164:219-251`). AC-11 and AC-13 need the conditional command gate made explicit under R-1 (`FR-1164:252-267`). |
| Feasibility | The recorded live envelope supplies `raw`, `parsed` and `parsing_error`; existing helpers expose both primary and earned second attempts (`evidence:57-63,115-121`; `structured_output.py:100-147`). Stop vocabularies and package versions are recorded, with unsupported envelope shapes returning to plan rather than triggering a shim (`research:63-71`; `FR-1164:108`). |
| Architecture alignment | The classifier belongs before normalization/parsing, while FR-998 remains the sole production library binder and FR-679 retains shared sync/threaded attempt ownership (`executor_base.py:404-447`; `race_node.py:150-182`; `structured_output.py:45-63,100-147`). Extending CAP-164 avoids a parallel policy registry (`FR-1164:192-197`; `CAP-164` requirements). |
| Single responsibility | Detecting output-limit termination and explaining its available thinking share are one error-reporting concern. Safety blocks, thinking configuration and new retry policy remain separate (`FR-1164:24-32,188-206`). No split is needed. |
| Strategic classification | **Framework primitive**, extending existing invocation policy rather than adding an orchestration abstraction. Plain text, JSON extraction, schema parsing and race candidates all need the same missing check; current abstractions place calls but do not reject this stop condition (`FR-1164:45-71,179-186`). This is deterministic validation, not an LLM graph (`research:37-39`). |
| Testability | Real `AIMessage` fixtures and the recorded envelope can condemn the defect without network access. The criteria require valid parsed models alongside truncated raw replies, complete parsing-error identity, second-attempt marking, fallback call counts and a complete race winner (`FR-1164:219-251`). Keep those assertions when converting mocks; an envelope-shape/import failure alone is not the RED witness. |

FR-464's JSON-extraction fallback remains a caller responsibility, and FR-998's typed unsupported-capability retry remains exactly one attempt. FR-1148's thinking switch and FR-1152's aggregate usage reporting do not replace per-response rejection. These precedents support the proposed placement without authorizing changes to those policies.

## Required revisions

### R-1: Align the optional post-GREEN probe and command gate with the bounded guarantee

Replace AC-11's requirement that both `plain` and `structured_today` show `OutputTruncatedError` (`FR-1164:258-262`) with this executable contract:

1. The committed pre-fix artifact remains evidence of the provider contract and defect, not evidence that the fix already works. Without fresh operator approval, perform no post-GREEN paid call; record that no such rerun occurred and use the offline acceptance witnesses.
2. If a post-GREEN rerun receives fresh approval, keep the current probe's three logical calls. `plain` remains a direct `llm.invoke` metadata observation (`scripts/probe_fr1164_truncation.py:92-95`), and `structured_include_raw` remains a direct provider envelope observation (`probe:97-110`). Neither is required to raise the framework error. For a response reporting recognized truncation, `structured_today`, which invokes YAMLGraph's policy (`probe:112-116`), must record `OutputTruncatedError` instead of a parsed success. Validate the JSON entries, not the probe's exit code: `main` returns zero even when it records errors (`probe:118-120`).
3. Keep the existing request/spend bound and record producing SHA, model, package versions and sanitized metadata for any authorized rerun. Do not modify the provider client or add a new executor probe just to satisfy the incorrect expectation. The plain executor path is covered by AC-03.
4. Amend Planned Operations and AC-13 to distinguish completed research/judgement steps, mandatory offline enforcement checks, and the optional paid probe. Require the targeted pytest command, required unit suite, strict requirement coverage, import check, Ruff check and Ruff format check to pass. Do not require rerunning the judge during enforcement or running the optional paid command to satisfy "the commands ... pass" (`FR-1164:114-121,266-267`).

This is a contract correction, not a request for additional spend or a wider implementation surface.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-1164-output-truncated-error.md`: fold R-1; record implementation status, decisions and deviations |
| D-2 | `yamlgraph/utils/stop_reason.py`: typed `OutputTruncatedError` and one shared raw-message classifier |
| D-3 | `yamlgraph/utils/structured_output.py`: keyword-only raw-binding option and one envelope unwrap path used by both attempts of both invocation helpers |
| D-4 | `yamlgraph/executor_base.py` and `yamlgraph/node_factory/race_node.py`: checks on existing plain and FR-464 fallback replies before normalization |
| D-5 | `tests/unit/test_fr1164_output_truncated.py` and directly affected structured-output/race tests: focused behavior witnesses and necessary raw-envelope mock conversions |
| D-6 | `capabilities/CAP-164-structured-output-fallback.yaml` and generated `ARCHITECTURE.md`: FR-1164 / REQ-YG-729 traceability |
| D-7 | `reference/graph-yaml.md`: shared output/thinking budget and bounded rejection behavior |
| D-8 | Fix fragment in `changelog/unreleased/`, implementation record and `docs/diary/` reflection with `**Seed:**` |
| D-9 | Existing `scripts/probe_fr1164_truncation.py` and `feature-requests/evidence/FR-1164-truncation-probe.json`: retain the committed reproduction; an explicitly reauthorized rerun may refresh evidence under R-1 |

Not authorized: agent-finalization or tool-loop changes; streaming changes; provider-client wrappers; direct-provider rejection; automatic budget increases; thinking configuration changes; safety-block handling; new retries or reordered fallbacks; dependency changes; production acceptance of both parsed-only and envelope return shapes; graph/prompt authoring; enforcement-infrastructure changes; unrelated refactoring. Test helper extraction is permitted only for the directly affected mocks under the FR's stated threshold, not as a new production abstraction.

## Revised acceptance criteria

- [ ] AC-01: The committed FR retains the substantive A1-A5 research dispositions, corrected factory-wrapper claim, failed-persona disclosure, graph-fit answer, rejected FR-672 disposition and resolving brief/evidence links.
- [ ] AC-02: Provider evidence retains exact versions, stop keys/values and the live raw envelope; the guarantee remains limited to the executor attempt, invocation helpers and race candidate, including their existing re-invocations.
- [ ] AC-03: Thinking-only, mixed thinking/text and partial-text replies for each of `max_tokens`, `length` and `MAX_TOKENS` raise `OutputTruncatedError` before normalization or JSON extraction on the executor path; output 2000 / reasoning 1921 appear in the diagnostic.
- [ ] AC-04: Missing metadata usage, missing individual counts and `None` values do not prevent truncation rejection; unavailable counts remain `None` and print `unknown`, independently of available counts. Nonempty `stop_reason` takes precedence; empty `stop_reason` falls through to `finish_reason`.
- [ ] AC-05: Missing/unrecognized stop values and ordinary `end_turn`/`stop` responses retain existing results without a new rejection.
- [ ] AC-06: Both sync/native-async structured helpers inspect raw truncation before accepting `parsed` or raising `parsing_error`, on primary and earned second attempts. A complete success returns the parsed model; a complete parsing failure re-raises the identical exception object.
- [ ] AC-07: Default direct binder calls omit the `include_raw` keyword and retain parsed-only results; one production `.with_structured_output(` expression remains. Config forwarding, exactly-one typed second attempt, error marking and distinct async second-attempt run IDs are preserved. Primary truncation performs one invocation, not a second attempt.
- [ ] AC-08: Executor and native-async race FR-464 plain fallback invocations reject truncated replies without another call; structured truncation earns no FR-464 fallback. Tests assert call counts and distinct race fallback run IDs.
- [ ] AC-09: A truncated race candidate fails and cannot defeat a complete candidate; existing race/cancellation behavior stays intact. `is_retryable(OutputTruncatedError(...))` is false and node error-policy semantics are unchanged.
- [ ] AC-10: Error fields expose only stop reason, available usage counts, normalized visible-character count and at most 200 normalized visible preview characters. A thinking-block sentinel is absent from both exception string and preview; the exception string cannot trigger the `response_format` fallback.
- [ ] AC-11: The committed pre-fix probe remains reproducible and is labeled as baseline evidence. No new paid run is mandatory or authorized by this judgement. If separately approved, a post-GREEN rerun obeys R-1: direct calls remain observations, and recognized truncation through `structured_today` records `OutputTruncatedError`; inspect the artifact rather than exit status. Otherwise record that unit witnesses used the committed envelope and no paid rerun occurred.
- [ ] AC-12: The reference documents shared thinking/output budgets only for applicable providers, qualifies thinking-budget advice by model support, and makes no universal completeness claim.
- [ ] AC-13: A behavioral RED commit precedes GREEN; the mandatory offline targeted tests, required unit suite, strict requirement coverage, import check and Ruff check/format commands pass. New tests carry individual `@pytest.mark.req("REQ-YG-729")` decorators; CAP-164 and generated architecture register that requirement.
- [ ] AC-14: The fix changelog fragment, implementation status with decisions/deviations and diary reflection with `**Seed:**` are committed within the frozen scope.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 into the FR before implementation authority activates; this requested draft is not itself a promoted judgement artifact. | GATE |
| C-2 | Preserve the sole production binder, explicit direct-binder defaults, typed FR-998 exactly-one second attempt, exception identity/marking, invocation configuration and FR-464/679 responsibilities. | GATE |
| C-3 | Check recognized truncation before accepting parsed output, including valid-looking partial-JSON repairs; do not broaden metadata absence into a completeness claim. | GATE |
| C-4 | Keep unknown counts unknown and hidden reasoning out of diagnostics. Preserve existing node error policies; add no automatic truncation retry. | GATE |
| C-5 | Any raw-enabled response lacking the contracted raw message returns to plan; do not add a silent fallback, dual return shape or dependency/provider expansion. | GATE |
| C-6 | A fresh paid rerun requires a fresh operator spend decision and credentials. This judgement answers no spend question on the operator's behalf; without approval, use the explicit offline branch. | GATE |
| C-7 | Do not re-enter the judge during enforcement or change enforcement infrastructure under this FR. | GATE |

Authority granted: conditional approval for the frozen truncation classifier, existing-call-site wiring and support artifacts only, after R-1 is folded into the FR and this draft is promoted through the existing route.

---

# Prior judgement (2026-11-14, first submission at `1cbf646d`): REJECTED

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
