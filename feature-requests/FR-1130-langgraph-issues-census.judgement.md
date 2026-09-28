# Judgement: FR-1130 LangGraph upstream issues census — solves / inherits / leaves untouched

**Verdict:** APPROVED WITH REVISIONS — the full-corpus contrib/example is affordable and fits the established census pattern, but authority activates only after the FR freezes category semantics, replaces incremental discovery with a complete replayable snapshot, closes unresolved-row and citation contradictions, and makes roadmap dispositions explicitly advisory.

**Prior art:** dispositioned in the parent FR header ([FR-1130](FR-1130-langgraph-issues-census.md) — §5 table plus FR-802, FR-893, FR-896 gate hits); FR-940's first judgement was REJECTED and its rev-2 enforcement is the relied-on contract. (Line added by the enforcer at promotion for the FR-738 gate; verdict text unchanged.)

**Reviewed against:** `feature-requests/FR-1130-langgraph-issues-census.md`; `feature-requests/FR-1130.research.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `reference/patterns/corpus-map-reduce.md`; `examples/demos/corpus_census/graph.yaml`; `examples/demos/corpus_census/adapters/corpus_adapters.py`; `examples/demos/corpus_census/tools.py`; `feature-requests/FR-899-org-repo-census-azure.judgement.md`; `feature-requests/FR-1032-census-adapter-owned-extract-cache.judgement.md`; `feature-requests/FR-1116-map-memo-file-corpus.md`; `feature-requests/FR-1116-map-memo-file-corpus.judgement.md`; `feature-requests/FR-1120-census-map-memo.md`; `feature-requests/FR-1120-census-map-memo.judgement.md`; `feature-requests/FR-943-census-row-failure-containment.md`; `feature-requests/FR-943-census-row-failure-containment.judgement.md`; `feature-requests/FR-940-census-judgement-normalization.md`; `feature-requests/FR-940-census-judgement-normalization.judgement.md`; the status/verdict headers of `feature-requests/FR-936-map-node-hardening.md`, `feature-requests/FR-936-map-node-hardening.judgement.md`, `feature-requests/FR-957-map-branch-native-retry-policy.md`, `feature-requests/FR-957-map-branch-native-retry-policy.judgement.md`, `feature-requests/FR-983-map-concurrency-and-census-coverage-gate.md`, `feature-requests/FR-983-map-concurrency-and-census-coverage-gate.judgement.md`, `feature-requests/FR-1086-lint-compile-check.md`, and `feature-requests/FR-1086-lint-compile-check.judgement.md`.

## What is sound

The problem and first consumer are concrete. The operator needs counted upstream evidence when choosing framework work, and the FR identifies the first event as reading the three disposition lists rather than merely archiving a report (`feature-requests/FR-1130-langgraph-issues-census.md:6-9,25-28`). The measured population, search cap, list-endpoint probe, missing adapter, map ceiling, and module-size observation establish a real boundary problem rather than an anecdotal wish (`feature-requests/FR-1130-langgraph-issues-census.md:37-49`).

The measurement gate is substantively satisfied. Twelve raw records are described with details that shaped the plan: an issue/fix-PR pair, a Redis test-fixture defect, a typing request, provider/prebuilt-agent interaction, CLI work, documentation-only PRs, and non-pain submissions (`feature-requests/FR-1130-langgraph-issues-census.md:51-74`). This meets the local requirement to read raw model inputs before authorizing a measurement pipeline (`.github/skills/judge-fr/doctrine.md:112-117`; `.github/copilot-instructions.md:109-110,210`).

The chosen topology is correct. This is a finite enumerable corpus, each item needs one narrow semantic judgement, completeness matters, and counts can be reconciled in code—the exact use conditions for corpus map-reduce (`reference/patterns/corpus-map-reduce.md:26-40`). Reusing invocation-bound discovery/extraction, the existing closed-vocabulary reducer, row-failure representation, and the shared memo is preferable to adding a framework primitive (`feature-requests/FR-1130-langgraph-issues-census.md:129-188`). The current base graph confirms the relevant slots and deterministic reducer exist, while its two maps are capped at 200 and therefore cannot host the measured full run unchanged (`examples/demos/corpus_census/graph.yaml:16,45-61,75-114`).

The proposed implementation is bounded. A separate adapter module avoids extending the already large `corpus_adapters.py`; a sibling graph isolates the higher item ceiling and memo wiring; and the full-census estimate of roughly $5-$21 is materially cheaper than substituting an uncertifiable sample (`feature-requests/FR-1130-langgraph-issues-census.md:129-160,181-212,236-246`). The research record preserves the subtractionist objection and answers `is_this_a_graph` with the existing `corpus-census` shape (`feature-requests/FR-1130.research.md:16-22`).

| Criterion | Finding |
|---|---|
| Scope | One upstream corpus, one adapter family, one sibling graph, and one report form a cohesive contrib/example. The cache, memo, and reducer are supporting boundaries, not independent products (`FR-1130:16-23,127-198`). |
| Consistency | The direction is coherent, but “every item” conflicts with accepted abstained/row-failed rows; “three to five” citations conflicts with “up to 5”; and per-item counts are described as pains despite acknowledged issue/PR pairs (`FR-1130:19-23,55-58,76-85,156-160,225-232`). Fold R-1 and R-3. |
| Measurability | Population equality, crosstab sums, reference resolution, and label verification are measurable. Category correctness, complete snapshot identity, canary success, citation cardinality, and disposition substance are not yet frozen (`FR-1130:214-233`; `corpus-map-reduce.md:168-179`). Fold R-1 through R-5. |
| Feasibility | The list endpoint, local extraction cache, existing reducer, and implemented memo seam make the design workable. Incremental `since=max(updated_at)` merging does not by itself prove a current complete snapshot or removal detection (`FR-1130:138-159`; `corpus-map-reduce.md:50-71`). Fold R-2. |
| Architecture alignment | Deterministic GitHub ingestion and arithmetic remain Python tools, semantic classification remains YAML/prompt orchestration, and graph creation is routed through `scripts/author.sh` (`FR-1130:129-188`; `.github/copilot-instructions.md:13`). |
| Single responsibility | Discovery, classification, reconciliation, and rendering are stages of one census lifecycle. No split is required. |
| Strategic classification | **Contrib/example**: one named upstream corpus and one named operator event reuse existing census, normalization, failure-containment, and memo abstractions; no new framework primitive is justified (`FR-1130:6-9,181-198`; `judge-fr/doctrine.md:51-57`). |
| Testability | Direct tests can cover parsing, snapshot construction, sampling, version maps, extraction, crosstabs, memo invalidation, and artifact checks. The taxonomy, unresolved-row policy, pair language, and disposition schema must first be made exact (`FR-1130:214-233`). |

## Required revisions

### R-1: Freeze the classification contract and make final completeness truthful

Replace “for every pain category upstream” with the claim this run can prove: every frozen upstream item is assigned to exactly one category in the frozen FR-1130 taxonomy. Add exact inclusion terms, exclusion terms, and precedence for every category, including overlaps such as provider × prebuilt agent, checkpoint × test infrastructure, and docs × feature surface. Commit the 12 raw-read records as a sanitized fixture with one expected category and rationale per record; use ten named rows for the smoke and reserve at least one different named row as the withheld known-truth canary required by the corpus pattern (`reference/patterns/corpus-map-reduce.md:168-179`).

Resolve the contradiction between the summary's “classify each into one closed pain category” and acceptance of `abstain`/`row_failed` as final categories (`FR-1130:19-23,159-166,225-228`). Provisional runs may preserve those rows, but the final accepted census must contain zero abstained and zero row-failed rows. Any such row invalidates final crosstab and disposition emission until the row is resolved and re-run through the memo. Category changes after the smoke require updating the FR's frozen taxonomy and expected fixture before the paid full run; the smoke may not silently redefine scope.

### R-2: Freeze one complete, typed, replayable GitHub snapshot

Replace incremental discovery by `since=max(updated_at)` as the completeness boundary (`FR-1130:101-102,138-147`). Each accepted run must fully enumerate `repos/<owner>/<repo>/issues?state=all&per_page=100`, validate every projected record through a Pydantic model, deduplicate by exact positive issue number, and atomically replace—not merge into—the repository snapshot only after all pages validate. The snapshot must record repository, query, retrieval timestamp, ordered refs, item count, content hash, and the exact projected schema. A failed refresh leaves the previous snapshot untouched and aborts before model spend. The memo may still use each record's validated non-empty `updated_at` so unchanged items incur no new LLM call.

Define every projected field and bound exactly. In particular, state whether `comments` is a count or comment text, define the reactions shape, body-character limit, label limit, timestamp format, PR detection/merged semantics, timeout, subprocess argument vector, duplicate behavior, and malformed/null-field behavior. Freeze deterministic `:<n>` sampling with an explicit index formula, including `n=1`, `n=population`, and `n>population`. Add a typed manifest artifact to the committed results so corpus identity, provider/model, run identity, prompt/signature hashes, counts, and cost/call totals satisfy the pattern's freeze and render contracts (`reference/patterns/corpus-map-reduce.md:50-71,145-166`).

### R-3: Separate item arithmetic from pain claims and freeze citations

The crosstab counts issues and PRs as items, while the raw read says an issue and its fix PR must not become two pains in the narrative (`FR-1130:55-58,76-85,156-160`). Rename every computed total as an **item count** and forbid inferred unique-pain totals. If a narrative associates an issue with a fixing PR, require both refs plus a quoted/linkable relationship witness from the frozen records; that annotation does not alter item arithmetic. Do not add heuristic pair de-duplication under this FR.

Reconcile “three to five cited items per category” with “up to 5” (`FR-1130:78-80,156-157`). Require each non-empty category to cite between `min(3, category_item_count)` and `min(5, category_item_count)` distinct refs selected by one frozen deterministic rule. Validate that every citation belongs to that category and snapshot, resolves through the scripted GitHub check, and that every reported upstream label is present on its cited item.

### R-4: Freeze memo invalidation, ceilings, and the end-to-end graph witness

Name the sibling graph's complete state/tool contract, including `source`, `labels`, `rubric`, provider/model, output paths, memo store, versions, maximum items, concurrency, and every map-memo signature input. Set a concrete ceiling above the measured population; discovery must reject before model calls if the snapshot exceeds it. Changing the taxonomy/rubric, labels, model/provider, classification prompt, extraction schema/version, or relevant census code must invalidate every affected memo entry. A stable snapshot with stable signatures must make zero extraction/classification calls and reproduce byte-identical ledger/crosstab output.

Add a provider-free end-to-end witness over the frozen fixture that exercises discovery, sampling, extraction, memo split/merge, one contained judge failure, recovery of only that item, reducer normalization, canary validation, crosstab rendering, and disposition-input generation. Keep the full live run as the production witness. The 3× cost stop remains a human gate: record the measured smoke estimate and obtain operator approval before the full run if it exceeds the first estimate by that threshold (`FR-1130:96-106,199-212`).

### R-5: Make dispositions a typed advisory report, not an implicit product decision

Define `dispositions.md` as one row per frozen category, not one row per upstream item. Each row must contain category, item counts by kind/state, required citations, YAMLGraph surface/mechanism evidence, one of `solves | inherits | untouched`, and exactly one recommendation: candidate-FR title plus one-sentence objective, `accept`, `out of scope`, or `already covered by FR-XXX`. A `solves` row requires a cited repository mechanism; an `already covered` row requires an existing FR reference; an `inherits` row requires either a candidate-FR recommendation or `accept`; an `untouched` row requires `out of scope`.

State that these are recommendations for the named operator, not authorized roadmap decisions. Filing candidate FRs, changing existing FR priorities/statuses, or implementing any discovered fix is outside FR-1130. If the operator's product decision is required for publication, record that decision explicitly rather than letting the enforcer silently choose it (`.github/skills/judge-fr/doctrine.md:99-102`).

### R-6: Disposition all cited prior art and dependency authority

Add one prior-art table covering every FR named by the research record, Planned Operations, Alternatives, and Related sections. For each, record status, exact reused contract, distinction, and whether FR-1130 changes it. This must include the SPLIT/REJECTED records surfaced by the research (`FR-936`, `FR-983`, and FR-940's rejected first judgement), their relevant successor/enforced state where applicable, plus FR-899, FR-943, FR-957, FR-962, FR-1032, FR-1058, FR-1086, FR-1116, and FR-1120 (`feature-requests/FR-1130.research.md:9-22`; `feature-requests/FR-1130-langgraph-issues-census.md:92,177,236-250`). The current Related list is not a disposition.

Make implemented FR-940 normalization, FR-943 row containment, and FR-1120 caller-version memo explicit prerequisites. If enforcement discovers that their shipped contracts cannot support the frozen graph without modifying those shared surfaces, stop and return to planning; do not absorb a shared abstraction change into this census.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revisions R-1 through R-6 folded into `feature-requests/FR-1130-langgraph-issues-census.md`, including the frozen taxonomy, prior-art table, snapshot contract, and advisory disposition schema |
| D-2 | `examples/demos/corpus_census/adapters/gh_issues_adapters.py` with typed snapshot/discovery, versions, extraction, and crosstab functions |
| D-3 | `examples/demos/corpus_census/adapters/gh-issues-discover.tool.yaml`, `gh-issues-versions.tool.yaml`, `gh-issues-extract.tool.yaml`, and `gh-issues-crosstab.tool.yaml` |
| D-4 | `examples/demos/langgraph_issues_census/graph.yaml` and only the prompt files required for its frozen classification contract, authored through `scripts/author.sh` |
| D-5 | `tests/unit/test_fr1130_gh_issues_adapters.py` plus focused provider-free graph tests and the committed sanitized raw-read/canary fixture |
| D-6 | `examples/demos/langgraph_issues_census/results/manifest.json`, complete ledger JSONL, crosstab markdown, `dispositions.md`, and the scripted citation-validation witness |
| D-7 | CAP-294 / REQ-YG-717 registry wiring, regenerated architecture traceability, changelog fragment, FR implementation/operation record, authoring report, and diary entry with `Seed:` |

Not authorized: changes under `yamlgraph/`; changes to the existing `corpus_census` graph, reducer semantics, row-failure taxonomy, closed-vocabulary normalization, shared map-memo implementation/schema, or existing GitHub adapters; generic GitHub Issues framework APIs; heuristic issue/PR de-duplication; comment-body fetching through per-item API calls; a generic cache service; changes to hooks, CI, judge/review doctrine, or enforcement infrastructure; filing candidate FRs, changing roadmap priorities, or implementing any issue discovered by the census.

## Revised acceptance criteria

- [ ] AC-01: The FR contains the complete category rubric with inclusion, exclusion, and precedence rules; the committed 12-row fixture has exact expected categories/rationales, ten named smoke rows, and at least one different withheld canary.
- [ ] AC-02: RED then GREEN commits prove strict source parsing and deterministic sample indices for `n=1`, an interior `n`, `n=population`, and rejection of zero, malformed, or over-population limits.
- [ ] AC-03: Discovery executes one fixed full-pagination argument vector, validates every line as the frozen Pydantic record model, rejects command failure, timeout, malformed JSON, invalid/missing fields, duplicate numbers, empty population, and over-ceiling population, and performs no model call on failure.
- [ ] AC-04: A successful discovery atomically replaces a typed manifest/snapshot containing repository/query identity, retrieval time, ordered refs, count, schema version, and hash. A failed discovery leaves the prior snapshot byte-identical. Removal from the next full listing removes the item from the next snapshot.
- [ ] AC-05: Versions returns exactly `{ref: updated_at}` for the selected snapshot population and rejects missing, extra, empty, or invalid versions; extraction returns the frozen bounded bundle and rejects an absent ref or invalid required field without a per-item API call.
- [ ] AC-06: The sibling graph has a concrete item ceiling and bounded concurrency, carries every frozen memo-signature input, and is authored through `scripts/author.sh`; the substantive `tmp/draft-authoring-report.md` records lint and deterministic smoke evidence.
- [ ] AC-07: The provider-free end-to-end fixture run produces one ledger row per frozen ref, surfaces the withheld canary, contains a simulated judge failure, then re-runs only that failed item and reaches zero final abstained and zero final row-failed rows.
- [ ] AC-08: An unchanged second run makes zero extraction/classification calls and emits byte-identical semantic artifacts. Independently changing taxonomy/rubric, labels, model/provider, prompt, extraction schema/version, or a frozen signature file invalidates the applicable memo entries.
- [ ] AC-09: Final ledger row count equals snapshot ref count; every ref appears exactly once; every row has exactly one frozen category; category item counts sum to the snapshot count; no final `abstain` or `row_failed` row exists.
- [ ] AC-10: Every non-empty category has between `min(3, N)` and `min(5, N)` distinct, deterministically selected citations. Each citation belongs to the category and snapshot; scripted checks prove every ref resolves and every displayed upstream label belongs to that item.
- [ ] AC-11: All computed totals are labeled item counts. Any issue/fix-PR relationship stated in prose cites both refs and a relationship witness and does not alter arithmetic; no unique-pain total is emitted.
- [ ] AC-12: `dispositions.md` has exactly one typed row per frozen category and exactly three sections (`solves`, `inherits`, `untouched`); every row satisfies R-5's mechanism, evidence, and recommendation rules.
- [ ] AC-13: The manifest records provider/model, run identity, corpus and artifact hashes, actual item/model-call counts, token usage, and measured cost. If the smoke estimate exceeds the first estimate by more than 3×, the full run has a recorded operator approval.
- [ ] AC-14: The prior-art table satisfies R-6 and implementation changes none of the excluded shared/core surfaces. Existing directly relevant FR-940, FR-943, FR-1116, and FR-1120 tests remain green.
- [ ] AC-15: CAP-294 / REQ-YG-717 owns the exact graph, adapter, result-contract, and test surfaces; every new test carries `@pytest.mark.req("REQ-YG-717")`; strict requirement coverage passes.
- [ ] AC-16: Changelog fragment, FR implementation status/decisions/deviations, completed operation table with unplanned operations, authoring record, committed result artifacts, and diary reflection with `Seed:` are present.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority is inactive until R-1 through R-6 and AC-01 through AC-16 are folded into FR-1130. | GATE |
| C-2 | Every accepted full run starts from a complete validated snapshot and passes the withheld canary before final artifacts are emitted; incremental `since=` merging alone may not claim corpus completeness. | GATE |
| C-3 | Final artifacts may contain no unresolved abstained or row-failed rows, fabricated refs/labels, dangling citations, or arithmetic described as unique pains. | GATE |
| C-4 | All graph/prompt creation or material modification goes through `scripts/author.sh`; the authoring report, lint, and smoke substance must be inspected. | GATE |
| C-5 | The smoke is read before the paid run. A greater-than-3× estimate requires recorded operator approval; no model fallback or silent provider change is permitted. | GATE |
| C-6 | Dispositions are advisory outputs only. Filing or implementing candidate FRs and changing roadmap status or priority require separate human action and independently judged FRs. | GATE |
| C-7 | If implementation requires changes to YAMLGraph core, existing census reducer/normalization/failure behavior, shared memo behavior/schema, existing adapters, hooks, CI, or doctrine, enforcement stops and the concern returns to planning. | GATE |

Authority granted: after the six revisions are folded and the gates above are accepted, implement only the typed LangGraph GitHub-issues snapshot adapters, authored sibling census graph, deterministic witnesses, and advisory census artifacts within D-1 through D-7.
