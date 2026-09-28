# Judgement: FR-1140 Reconcile a bare list answer with a single-list-field output model

**Verdict:** APPROVED WITH REVISIONS — the narrow boundary reconciliation is justified and implementable, but authority activates only after the FR supplies substantive alternatives research, freezes the observed exception contract, and covers every existing structured-output validation surface without reopening FR-998's second-attempt policy.

**Reviewed against:** `feature-requests/FR-1140-bare-list-structured-output.md`; `feature-requests/FR-1140.research.md`; `feature-requests/research-briefs/fr1140-bare-list-structured-output-brief.md`; `feature-requests/FR-998-anthropic-constrained-structured-output.md`; `feature-requests/FR-998-anthropic-constrained-structured-output.judgement.md`; `feature-requests/FR-464-deepseek-structured-output-fallback.md`; `feature-requests/FR-933-retry-cannot-recover-deterministic-rejection.md`; `feature-requests/FR-933-retry-cannot-recover-deterministic-rejection.judgement.md`; `feature-requests/FR-678-narrow-agent-structured-output-catch.md`; `feature-requests/FR-449-agent-structured-output-anthropic-bugfix.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `CLAUDE.md`; `yamlgraph/utils/structured_output.py`; `yamlgraph/executor_base.py`; `yamlgraph/node_factory/race_node.py`; `yamlgraph/tools/agent.py`; `capabilities/CAP-164-structured-output-fallback.yaml`; `ARCHITECTURE.md`; `reference/prompt-yaml.md`. No author chat transcript or uncommitted working notes were consumed.

## What is sound

**Scope and single responsibility:** the FR names a real, bounded shape defect: 3 of 545 calls returned a root list where the declared model required one object field, and Pydantic reported `model_type` with `input_type=list` (`feature-requests/FR-1140-bare-list-structured-output.md:7-9`, `51-58`). The proposed repair is uniquely determined only when there is exactly one model field, that field is list-typed, and the rejected root input is a list; the FR explicitly refuses ambiguous multi-field, non-list-field, and non-list-input cases (`feature-requests/FR-1140-bare-list-structured-output.md:60-63`, `104-109`). That is one concern, not a bundle, and no smaller consumer-local change would protect all structured-output callers.

**Architecture alignment and feasibility:** the selected boundary already exists. `invoke_structured` and `ainvoke_structured` centralize primary structured invocation (`yamlgraph/utils/structured_output.py:100-113`, `119-145`), while CAP-164 already owns JSON extraction plus Pydantic validation across executor and race paths (`ARCHITECTURE.md:2191-2202`). A shared, typed helper in that module follows the repository's boundary-normalization rule rather than adding per-graph repair. Pydantic exposes the model fields and structured validation errors needed by the proposed predicate, and the final `model_validate({field: input})` keeps item validation authoritative. The WARNING requirement also makes a successful repair observable instead of silent (`feature-requests/FR-1140-bare-list-structured-output.md:104-110`).

**Measurability and testability:** AC-1 through AC-6 identify observable return values, invocation counts, error identity, negative shapes, post-wrap item validation, and log count (`feature-requests/FR-1140-bare-list-structured-output.md:124-135`). These can be expressed as network-free unit tests. The first consumer and exact failing schema are also recorded, including provider/model/version and the required `records` array field (`feature-requests/research-briefs/fr1140-bare-list-structured-output-brief.md:56-69`).

**Consistency:** the summary, value statement, and core predicate agree on a deterministic repair and preserve ordinary validation failure (`feature-requests/FR-1140-bare-list-structured-output.md:32-43`, `104-120`). The remaining inconsistencies are finite and mechanically repairable: the planned probe has not yet resolved direct versus wrapped exceptions, and the call-site list does not cover the race and agent JSON-validation paths required by the ideal result.

**Strategic classification: Framework primitive extension.** Ordinary LLM execution, native-async race execution, and agent finalization already share the structured-output policy (`yamlgraph/utils/structured_output.py:3-7`), so the behavior belongs in the existing framework boundary rather than a contrib example or pattern-only document. The existing abstraction fits and must be extended; no second abstraction is authorized.

## Required revisions

### R-1: Replace convergent persona repetition with substantive alternatives evidence

Amend the promoted research record so it contains four to six genuine solution classes, each with a disposition, precedent, effort/risk, and `is_this_a_graph` answer. The current five rows reduce to boundary wrapping repeated by four personas plus prompt guidance/retry (`feature-requests/FR-1140.research.md:15-21`); changing labels such as `schema-data` does not make the same wrapping operation a distinct alternative. At minimum, disposition these distinct classes already named by the FR: narrow boundary reconciliation, prompt guidance plus retry, raw-response reparse via `include_raw`, and provider constrained decoding (`feature-requests/FR-1140-bare-list-structured-output.md:139-149`). Preserve the subtractionist disagreement. This revision is required by the research-substance gate, which demands four to six genuine solution classes rather than a table that only shape-checks (`.github/skills/judge-fr/doctrine.md:118-128`).

### R-2: Resolve and freeze the exception-delivery contract before enforcement

Execute the planned network-free LangChain/Pydantic probe and commit or fold its exact result into the FR: whether the runnable raises `pydantic.ValidationError` directly or a specific wrapper, the exact documented `__cause__`/`__context__` chain if wrapped, and the observed `errors()` entry containing `type == "model_type"`, `loc == ()`, and the root list in `input`. The FR currently leaves this decision to enforcement while its proposed signature and AC-1 assume a direct `ValidationError` (`feature-requests/FR-1140-bare-list-structured-output.md:76-80`, `100-106`, `124-126`).

Freeze the catch to the observed type. If wrapped, name the exact wrapper and traverse only the observed documented cause link; do not walk arbitrary exception chains. If the root list is not recoverable from structured error data, this judgement grants no implementation authority: return the FR to planning rather than reparsing raw provider text or broadening the catch.

### R-3: Enumerate every authorized validation surface and preserve prior fallback policy

Replace the incomplete call-site section with an explicit matrix covering:

1. the primary sync and native-async calls in `invoke_structured` and `ainvoke_structured`;
2. executor/threaded-async FR-464 extraction in `attempt_structured_invoke`, which already admits `dict | list` before `model_validate` (`yamlgraph/executor_base.py:402-438`);
3. native-async race FR-464 extraction, which currently admits only `dict` (`yamlgraph/node_factory/race_node.py:158-177`);
4. agent cheap extraction and the later plain-reinvoke validation path, which currently admit only `dict` (`yamlgraph/tools/agent.py:62-100`, `121-140`).

All four surfaces must use the same reconciliation helper; no duplicate field/error-shape logic may be added to callers. Existing dict behavior and fallback ordering remain unchanged. A bare list that validates after wrapping must return without an additional model invocation.

Narrow the ideal-result wording from "every structured-call path" to the enumerated primary and JSON-extraction paths. FR-998's forced-tool-call second-attempt errors must continue to propagate unchanged: FR-998 explicitly froze that behavior (`yamlgraph/utils/structured_output.py:17-20`; `feature-requests/FR-998-anthropic-constrained-structured-output.judgement.md:123-130`). FR-1140 does not authorize reconciliation of an error raised by that second attempt.

### R-4: Make success, failure identity, observability, and traceability exact

Replace the current acceptance criteria with the revised criteria below. Define a "reconciliation" as a successful wrapped `model_validate` result: emit exactly one WARNING only after that validation succeeds. An item-validation failure must raise the new validation error and must not log a successful reconciliation. For every non-qualifying error, assert object identity (`raised.value is original_error`), not only type or message.

Extend the existing `capabilities/CAP-164-structured-output-fallback.yaml` with a new FR-1140 requirement and regenerate/update its `ARCHITECTURE.md` entry; do not create a duplicate capability. CAP-164 already owns executor, race, shared policy, and agent structured-output behavior (`capabilities/CAP-164-structured-output-fallback.yaml:1-43`; `ARCHITECTURE.md:2191-2202`). Keep the requested `reference/prompt-yaml.md` documentation update limited to the exact deterministic rule and its WARNING.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised `feature-requests/FR-1140-bare-list-structured-output.md` and substantive `feature-requests/FR-1140.research.md` folding R-1 through R-4 |
| D-2 | One typed reconciliation helper and primary sync/native-async wiring in `yamlgraph/utils/structured_output.py` |
| D-3 | Shared-helper wiring for extracted JSON in `yamlgraph/executor_base.py`, `yamlgraph/node_factory/race_node.py`, and `yamlgraph/tools/agent.py`, preserving existing fallback order |
| D-4 | Focused RED/GREEN tests in `tests/unit/`, including the observed LangChain exception seam and executor, race, and agent path coverage |
| D-5 | One new FR-1140 requirement in `capabilities/CAP-164-structured-output-fallback.yaml` and the corresponding `ARCHITECTURE.md` update |
| D-6 | The exact rule in `reference/prompt-yaml.md`; fix changelog fragment; FR implementation record; diary entry |

Not authorized: raw provider-text reparsing; `include_raw=True`; arbitrary exception-chain walking; broad `except Exception` recovery; reconciliation for multi-field models, non-list fields, non-list root inputs, multi-error failures, or non-root locations; schema weakening; `model_construct` as the new repair; prompt or graph changes; a configuration flag; provider-specific imports or model allowlists; changes to retry counts, retryability, backoff, run-ID, cancellation, or race-winner behavior; changes to Anthropic method selection; reconciliation of FR-998's forced-tool-call second-attempt errors; reordering or removal of FR-456/464/678/809/933/998 fallback behavior; a new capability file.

## Revised acceptance criteria

- [ ] AC-01: `feature-requests/FR-1140.research.md` contains four to six genuinely distinct, dispositioned solution classes, preserves the subtractionist disagreement, cites precedent for each class, and answers `is_this_a_graph`.
- [ ] AC-02: Committed network-free evidence records the exact exception delivered by the representative `with_structured_output(...).invoke` and `.ainvoke` seams and proves that the bare list is recoverable from the direct error or one named documented cause link.
- [ ] AC-03: RED tests prove the shared helper accepts only a one-field model whose field annotation has list origin plus exactly one root `model_type` error whose input is a list; two-field, scalar-field, non-list-input, multi-error, non-root, and unrelated validation failures return no repair.
- [ ] AC-04: Sync `invoke_structured` returns the validated model for the witnessed bare-list failure, makes no additional invocation, and preserves the original exception object for every non-qualifying failure.
- [ ] AC-05: Native `ainvoke_structured` satisfies AC-04 using `ainvoke`, with no thread substitution and no change to invocation config.
- [ ] AC-06: Executor/threaded-async FR-464 extraction reconciles a bare list through the shared helper; existing dict extraction behavior is unchanged.
- [ ] AC-07: Native-async race FR-464 extraction reconciles a bare list through the shared helper while preserving run-ID and cancellation behavior; existing dict extraction behavior is unchanged.
- [ ] AC-08: Agent cheap extraction and plain-reinvoke extraction reconcile a valid bare list without an extra model call at that tier; existing dict validation, lenient-construction, `function_calling`, and plain-reinvoke ordering remain unchanged.
- [ ] AC-09: A wrapped list whose items violate the declared item model raises the post-wrap `ValidationError`; it does not return a model, call the provider again, or emit the successful-reconciliation WARNING.
- [ ] AC-10: Every successful reconciliation emits exactly one WARNING containing the output-model name, field name, and item count; no rejected or non-qualifying attempt emits that WARNING.
- [ ] AC-11: An error from FR-998's forced-tool-call second attempt remains the same exception object and is never reconciled; the one-second-attempt limit remains intact.
- [ ] AC-12: Existing structured-output regression suites, including `tests/unit/test_fr998_structured_output.py`, `tests/unit/test_race_node.py`, `tests/unit/test_fr448_agent_structured_output.py`, and `tests/unit/test_fr678_narrow_structured_catch.py`, pass without weakened assertions.
- [ ] AC-13: CAP-164 gains one new FR-1140 requirement covering the exact predicate and all authorized surfaces; every new test carries its requirement marker; `python scripts/req_coverage.py --strict` passes.
- [ ] AC-14: `reference/prompt-yaml.md` documents that YAMLGraph may reconcile only a bare list into an exactly one-list-field model and emits a WARNING; it does not promise repair for any other validation failure.
- [ ] AC-15: The RED commit precedes the GREEN commit; a `type: fix` changelog fragment, FR implementation-status record, and diary entry with a **Seed:** are present.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-4 are folded into the committed FR and research record. | GATE |
| C-2 | If the exact bare-list input cannot be recovered from the observed typed error contract, stop and return to planning; do not inspect raw provider text or widen exception handling. | GATE |
| C-3 | Reconciliation requires all predicate parts: exactly one model field, list-origin annotation, exactly one `model_type` error, root location, and list input. | GATE |
| C-4 | Every authorized surface uses one helper; caller-local copies of field inspection or error-shape matching are forbidden. | GATE |
| C-5 | FR-998's forced-tool-call second-attempt errors remain untouched, and every existing fallback tier retains its order and invocation limit. | GATE |
| C-6 | Log exactly one WARNING only after successful reconciliation; failed post-wrap validation remains an explicit error, not a success-shaped or success-logged result. | GATE |
| C-7 | No graph or prompt artifact may be changed under this FR; the only documentation surface authorized is `reference/prompt-yaml.md`. | GATE |
| C-8 | Enforcement follows RED-GREEN: commit the condemning exception-seam and path tests before production changes. | GATE |

Authority granted: after the required revisions are folded, enforcement may add the single deterministic bare-list reconciliation primitive, wire it into the frozen primary and extracted-JSON validation surfaces, and update CAP-164 documentation and witnesses within the scope above.

**Prior art:** `FR-1140-bare-list-structured-output.md` — the FR this judgement judges (self-match on nouns); FR-998 (both files) is the structured-output policy this FR extends, dispositioned in the FR header and cited throughout the judgement; `FR-1123.research.md` — untyped-subschema refusal under constrained decoding, dispositioned as A6 precedent (schemas refused, not weakened). *(Addendum at promotion, not judge output.)*
