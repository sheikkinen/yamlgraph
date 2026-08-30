# Judgement: FR-905 Validate ranked stories at the rank->format boundary

**Verdict:** APPROVED WITH REVISIONS - the boundary fix is real, scoped, and aligned with repo doctrine, but authority activates only after the target repository/surface, invalid-status failure semantics, and optional URL-reconciliation ambiguity are made mechanically enforceable.

**Reviewed against:** `feature-requests/FR-905-ranked-story-boundary-validation.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/TEMPLATE.md`; `feature-requests/FR-908-daily-digest-slot-bound-refactor.md`; `feature-requests/FR-908-daily-digest-slot-bound-refactor.judgement.md`; `feature-requests/FR-894-corpus-map-reduce-github-scope-reconciliation-reference.md`; `feature-requests/FR-894-corpus-map-reduce-github-scope-reconciliation-reference.judgement.md`; `feature-requests/FR-903-digest-archive-then-email-ordering.md`; `feature-requests/FR-903-digest-archive-then-email-ordering.judgement.md`; `feature-requests/FR-904-slot-bound-digest-collection.md`; `examples/daily_digest/prompts/rank_stories.yaml`; `examples/daily_digest/nodes/formatting.py`; `yamlgraph/schema_loader.py`.

## What is sound

The problem is real and correctly located at a model-output boundary. FR-905 names the first consumer and event: the next `yamlgraph-daily-digest` scheduled run that rejects malformed ranked output loudly instead of crashing a renderer or producing a green no-op (`feature-requests/FR-905-ranked-story-boundary-validation.md:8-11`). The prompt asks for structured story objects while declaring only `stories: list[Any]` (`examples/daily_digest/prompts/rank_stories.yaml:18-30`), and the schema loader maps `Any` directly and resolves `list[T]` generically (`yamlgraph/schema_loader.py:29-37`, `yamlgraph/schema_loader.py:83-87`). That leaves item shape unenforced before deterministic formatting.

The solution follows repo doctrine rather than expanding the framework. The FR proposes Pydantic validation of each ranked item with required `title` and `url`, optional/defaulted display fields, individual drops for bad items, and a fail-closed raise when no valid survivor remains (`feature-requests/FR-905-ranked-story-boundary-validation.md:86-100`). That matches the repo law to normalize external data at the boundary (`.github/copilot-instructions.md:50-56`), sanctify outputs with Pydantic (`.github/copilot-instructions.md:217`), and raise rather than emit success-shaped fallbacks (`.github/copilot-instructions.md:219`).

The FR is a faithful child of the FR-908 split. FR-908's judgement required a separate rank-format child for typed validation, dropping individual non-conforming ranked items, raising when a non-empty ranked response has no conforming survivor, and preserving the no-op/malformed distinction (`feature-requests/FR-908-daily-digest-slot-bound-refactor.judgement.md:35-45`, `feature-requests/FR-908-daily-digest-slot-bound-refactor.judgement.md:77-79`, `feature-requests/FR-908-daily-digest-slot-bound-refactor.judgement.md:90`). FR-905 takes only that slice and explicitly excludes delivery ordering, slot-bound collection, framework nested-schema work, and ledger changes (`feature-requests/FR-905-ranked-story-boundary-validation.md:163-168`).

The research and alternatives record is sufficient for this small bug FR. The header points to an in-body alternatives table (`feature-requests/FR-905-ranked-story-boundary-validation.md:12-13`), which the local gate permits when it is an equivalent committed dispositioned record (`.github/skills/judge-fr/doctrine.md:118-128`; `feature-requests/TEMPLATE.md:11-20`). The table dispositions six real alternatives, including framework nested-model support, `list[dict]`, string coercion, downstream renderer guards, empty-bulletin laundering, and doing nothing (`feature-requests/FR-905-ranked-story-boundary-validation.md:147-156`). It also answers `is_this_a_graph` as no because this is deterministic validation inside an existing Python node and deliberately avoids prompt/graph authoring (`feature-requests/FR-905-ranked-story-boundary-validation.md:158-161`).

Strategic classification: **contrib/example bug fix**. This is not a framework primitive because the FR deliberately leaves `yamlgraph/schema_loader.py` unchanged (`feature-requests/FR-905-ranked-story-boundary-validation.md:123-128`, `feature-requests/FR-905-ranked-story-boundary-validation.md:144-145`). It is not merely documentation because the scheduled digest has a live failure mode and needs deterministic validation before rendering (`feature-requests/FR-905-ranked-story-boundary-validation.md:52-71`).

## Required revisions

### R-1: State the target repository and implementation surfaces explicitly

Add a `### Files` or `### Surface` section stating that the implementation paths are in the external `yamlgraph-daily-digest` repository unless the FR is deliberately authorizing a separate change to this repository's `examples/daily_digest`. FR-905 currently names the first consumer as `yamlgraph-daily-digest` (`feature-requests/FR-905-ranked-story-boundary-validation.md:8-11`) but cites `examples/daily_digest/nodes/formatting.py` as a sibling renderer and crash site (`feature-requests/FR-905-ranked-story-boundary-validation.md:56-60`, `feature-requests/FR-905-ranked-story-boundary-validation.md:175-176`). That leaves the enforcer unable to tell whether `examples/daily_digest` is evidence only or an implementation target. Fold the rule as: `examples/daily_digest/*` is cited evidence only; implementation is limited to `yamlgraph-daily-digest/nodes/formatting.py`, its tests, and `run_digest.py` only if needed to surface the invalid failure in run output. If the intent is to fix both repositories, split the sibling example fix into its own judged FR.

### R-2: Make `invalid` a failure contract, not an ambiguous successful state

Rewrite the status section so the state/output behavior is exact. FR-905 says `format_markdown` emits `digest_status` alongside `digest_markdown` and adds `invalid`, but the `invalid` row also says "raise" (`feature-requests/FR-905-ranked-story-boundary-validation.md:102-114`). In LangGraph-style node execution, a raised exception does not also return a normal state update, so the current text leaves two incompatible interpretations: returned `digest_status == invalid` or raised failure classified as invalid.

Fold this contract: `format_markdown` returns `digest_status == no_articles` only when collection/ranking was not invoked because there were no input articles; returns `digest_status == ready` only when at least one ranked story validates and rendered markdown is non-empty; and raises a named failure, for example `InvalidRankedStoriesError`, when the ranker was invoked but the ranked payload is empty, all items are invalid, or no valid survivor remains. The exception/run output must include `digest_status=invalid`, the ranked item count, and the observed element types. `digest_status == invalid` may appear only as a failure classification, never as a successful graph result.

### R-3: Remove optional URL reconciliation from the acceptance gate or make it mandatory in a separate FR

Delete the optional reconciliation acceptance criterion from this FR's required scope and park it as a follow-up, unless the FR is revised to make reconciliation mandatory with exact input shapes and tests. The current proposal says URL reconciliation "may" be performed and is "scoped as optional," while also listing it under Acceptance Criteria (`feature-requests/FR-905-ranked-story-boundary-validation.md:116-121`, `feature-requests/FR-905-ranked-story-boundary-validation.md:142-143`). Acceptance criteria must be mechanically checkable commands, files, or assertions (`.github/skills/judge-fr/doctrine.md:43-44`); optional gates are not gates. The required fix is the drop/raise boundary. FR-894 remains a precedent for a later mandatory reconciliation FR, not optional enforcement scope here.

### R-4: Add an observable drop requirement for mixed malformed responses

Promote the "dropped with a logged reason" prose into an acceptance criterion. FR-905 correctly requires individual non-conforming items to be dropped and mixed responses to render the conforming subset (`feature-requests/FR-905-ranked-story-boundary-validation.md:97-100`, `feature-requests/FR-905-ranked-story-boundary-validation.md:134-135`), but without a log/assertion requirement the implementation can silently discard model output. Repo doctrine forbids silent success-shaped failure (`.github/copilot-instructions.md:219`). Add a test using the project's logging test pattern, e.g. `caplog`, proving each dropped item records at least its index, observed type, and validation reason without dumping unnecessary full payload content.

### R-5: Define the empty ranked-response case

Add the missing case where the ranker was invoked and returns an empty `stories` list. FR-905 currently raises only when a **non-empty** ranked response yields no conforming item (`feature-requests/FR-905-ranked-story-boundary-validation.md:23-25`, `feature-requests/FR-905-ranked-story-boundary-validation.md:136-137`), while also defining `no_articles` as "the ranker was never invoked" (`feature-requests/FR-905-ranked-story-boundary-validation.md:107-111`). An invoked ranker returning zero stories is neither a no-articles day nor a partially bad response; if left unspecified it can become the same empty-bulletin laundering the FR is meant to kill. Fold it into the `invalid` failure path and test it separately from all-strings and mixed-valid cases.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | FR-905 update folding R-1 through R-5 before enforcement starts |
| D-2 | External `yamlgraph-daily-digest/nodes/formatting.py`: ranked-story validation in `format_markdown`, including `ready`, `no_articles`, and invalid-failure classification |
| D-3 | External `yamlgraph-daily-digest/tests/`: focused boundary tests for all-strings RED/GREEN, mixed valid/invalid, empty ranked payload after ranker invocation, no-articles, non-empty markdown for ready, and invalid run-output classification |
| D-4 | External `yamlgraph-daily-digest/run_digest.py`: only the minimal change needed, if any, to surface invalid ranked output as a non-zero run with a clear message |
| D-5 | FR-905 implementation notes: RED/GREEN commit references, validation commands/results, and any implementation deviations |

Not authorized: edits to `yamlgraph/schema_loader.py` or any YAMLGraph framework schema behavior; edits to `prompts/rank_stories.yaml` or graph/prompt artifacts; delivery ordering, SMTP/email, archive/write ordering, workflow-shape changes, or other FR-903 scope; slot-bound collection or FR-904 scope; committed-SQLite or JSONL ledger work; optional URL reconciliation against `analyzed` unless re-entered as mandatory judged scope; fixing `examples/daily_digest` in this repository unless R-1 is changed and judged to include that second implementation surface; any CI, hook, judge/review doctrine, or other enforcement-infrastructure change.

## Revised acceptance criteria

- [ ] AC-01: FR-905 is revised to fold R-1 through R-5 before enforcement starts.
- [ ] AC-02: The FR states that all implementation paths are in the external `yamlgraph-daily-digest` repository; `examples/daily_digest/*` is evidence only and is not modified under this FR.
- [ ] AC-03: A RED commit, separate from the fix commit, adds a failing test proving `format_markdown` fed `["a string", "another"]` is not accepted as a successful bulletin.
- [ ] AC-04: `format_markdown` validates each ranked item with a typed model requiring `title: str` and `url: str`, with `summary` and `reason` defaulting to empty strings and `relevance` accepted as `float | None`.
- [ ] AC-05: A mixed ranked response drops only invalid items, renders the conforming subset, returns `digest_status == ready`, and produces non-empty `digest_markdown`.
- [ ] AC-06: Each dropped invalid item is logged or otherwise recorded with its index, observed type, and validation reason; the mixed-response test asserts this record.
- [ ] AC-07: A non-empty ranked response with zero conforming items raises the invalid-ranked-stories failure; the message includes `digest_status=invalid`, the ranked item count, and observed element types.
- [ ] AC-08: A ranker-invoked response with an empty `stories` list raises the same invalid-ranked-stories failure and is not treated as `no_articles`.
- [ ] AC-09: `digest_status == no_articles` is returned only for the legitimate no-input path where collection/filtering produced no articles and the ranker was not invoked.
- [ ] AC-10: `no_articles` and invalid ranked output are distinguishable by an assertion on returned state versus raised error/run output, not by reading logs manually.
- [ ] AC-11: No path reports an empty bulletin as success: `digest_status == ready` requires non-empty rendered markdown, and invalid ranked output exits non-zero or raises.
- [ ] AC-12: `digest_status == invalid` is never committed, archived, emailed, or reported as a successful graph result; it appears only as a failure classification.
- [ ] AC-13: No URL reconciliation against `analyzed` is implemented under this FR; if wanted, it re-enters as a mandatory, separately judged reconciliation FR with exact source identity tests.
- [ ] AC-14: No change is made to `yamlgraph/schema_loader.py`, framework schema behavior, `prompts/rank_stories.yaml`, graph artifacts, delivery ordering, SMTP/email, slot-bound collection, CI, hooks, or judge/review doctrine.
- [ ] AC-15: FR-905 records implementation status, RED/GREEN commit references, validation commands and results, and any deviations from this judgement.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority is inactive until R-1 through R-5 are folded into `feature-requests/FR-905-ranked-story-boundary-validation.md`. | GATE |
| C-2 | Enforcement may touch only the external `yamlgraph-daily-digest` formatter/tests and, if required, the runner error-surfacing path named in D-4; do not commit that external repository or generated digest artifacts into this YAMLGraph repository. | GATE |
| C-3 | If the ranker was invoked, an empty or all-invalid ranked payload must fail closed as invalid; it must not become `no_articles`, an empty markdown success, an archive, or an email. | GATE |
| C-4 | Individual invalid ranked items in a mixed response may be dropped only with an asserted diagnostic record; silent drop-and-success is forbidden. | GATE |
| C-5 | Do not modify `yamlgraph/schema_loader.py`, prompt YAML, graph YAML, YAMLGraph core schema behavior, FR-903 delivery surfaces, or FR-904 slot surfaces under this FR. | GATE |
| C-6 | Optional URL reconciliation is not enforcement scope; implementing it requires a mandatory scoped FR or a revised judgement that specifies exact source identity and failure tests. | GATE |
| C-7 | Any change to CI, hooks, judge/review doctrine, or other enforcement infrastructure requires explicit human review before merge. | GATE |

Authority granted: after the required revisions are folded into FR-905, the enforcer may implement only the external digest rank-format boundary validation, invalid failure classification, diagnostic logging, and focused tests within the frozen scope above.
