# Judgement: FR-962 Person-Profile Census (authored PRs across owner, pinned Azure)

**Verdict:** APPROVED WITH REVISIONS — the person-profile census is a coherent contrib/example on the existing census architecture, but authority activates only after the FR makes corpus completeness, typed reconciliation, URL provenance, the hidden canary, and public visibility mechanically valid.

**Prior art:** [FR-962-person-profile-census-authored-prs.md](FR-962-person-profile-census-authored-prs.md) — the sibling FR this judgement governs (paired artifact, not overlap). The FR itself carries the dispositioned prior-art block covering FR-892, FR-895, FR-899, FR-940, FR-943, FR-893, FR-874.

**Reviewed against:** `feature-requests/FR-962-person-profile-census-authored-prs.md`; `feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md`; `feature-requests/FR-895-census-synthesize-tail.md`; `feature-requests/FR-899-org-repo-census-azure.md`; `feature-requests/FR-899-org-repo-census-azure.judgement.md`; `feature-requests/FR-940-census-judgement-normalization.md`; `feature-requests/FR-943-census-row-failure-containment.md`; `feature-requests/FR-893-diary-trap-census.md`; `feature-requests/FR-890-research-sole-route-closed-input-alternatives.md`; `feature-requests/FR-874-cross-device-agent-memory-sync.md`; `reference/patterns/corpus-map-reduce.md`; `examples/demos/corpus_census/graph.yaml`; `examples/demos/corpus_census/adapters/corpus_adapters.py`; `examples/demos/repo_census/graph.yaml`; `examples/demos/repo_census/tools.py`; `examples/demos/repo_census/prompts/judge_repo_purpose.yaml`; `examples/demos/git-report/graph.yaml`; `yamlgraph/compile/map_compiler.py`; `yamlgraph/node_factory/llm_nodes.py`; `yamlgraph/utils/llm_providers.py`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`. The FR's cited path `feature-requests/FR-874-public-repo-data-locality.md` is not a tracked artifact; the actual FR-874 precedent reviewed is `feature-requests/FR-874-cross-device-agent-memory-sync.md`.

## What is sound

The first consumer and first event are concrete: one operator runs a self-audit of authored PRs in a named customer owner and the public precedent runs against `sheikkinen@sheikkinen` (`feature-requests/FR-962-person-profile-census-authored-prs.md:8-12`). The underlying problem is real: manual review of a large PR population is biased and unrepeatable, while customer PR content must remain on the approved Azure provider (`feature-requests/FR-962-person-profile-census-authored-prs.md:43-49`).

The graph shape is correct. The proposal freezes a finite PR corpus, maps one narrow semantic classification per PR, computes arithmetic in code, and renders one cited synthesis (`feature-requests/FR-962-person-profile-census-authored-prs.md:23-32,108-127`). That matches the canonical pattern's discover/extract slot reuse, deterministic reconciliation, and code-owned counts (`reference/patterns/corpus-map-reduce.md:54-61,141-182`). A deterministic-only inventory would not supply the requested `problem_class`, `surfaces`, `intent`, or narrative brief; the research record preserves that dissent instead of dismissing it (`feature-requests/FR-962-person-profile-census-authored-prs.md:278-284`).

The proposal conforms before extending. FR-892 owns the generic slot pipeline; FR-899 supplies the directly analogous Azure-pinned sibling graph, first-node preflight, repo-specific reducer, and one synthesis tail. The shipped sibling demonstrates explicit Azure map and synthesis nodes after preflight (`examples/demos/repo_census/graph.yaml:80-133`). FR-962 also freezes graph-authoring scope and forbids a generic provider override, graph inheritance, and changes to existing census defaults (`feature-requests/FR-962-person-profile-census-authored-prs.md:167-193`).

The in-body research record satisfies the prospective research gate in substance: it names five genuine classes, gives precedent, preserves disagreement over both provider override and an LLM-free alternative, and answers `is_this_a_graph` (`feature-requests/FR-962-person-profile-census-authored-prs.md:264-284`; `.github/skills/judge-fr/doctrine.md:118-130`).

Strategic classification: **Contrib/example**. Existing abstractions already supply tool slots, map orchestration, Azure sibling precedent, and the citation tail; this FR adds one concrete PR-census vertical for one named consumer. It is not a framework primitive, and its adapters, reducer, graph, prompts, and tests form one cohesive vertical rather than orthogonal work requiring a split.

## Required revisions

### R-1: Make discovery exhaustive within one declared hard ceiling

Replace the ambiguous `--limit <n>` / `MAX_PRS = 500` contract with an overflow-detecting collector contract (`feature-requests/FR-962-person-profile-census-authored-prs.md:80-88`). Validate `since` as an ISO `YYYY-MM-DD` date; query at most `MAX_PRS + 1`; reject before extraction or any LLM call when the result has 501 items; reject duplicate `<repo_nwo>#<number>` identities; otherwise emit exactly the complete, sorted set. Do not slice 501 results to 500.

Freeze `max_items: 500` on both the extraction and classification map nodes and test it. This is required because the framework silently truncates a list above a map's configured ceiling (`yamlgraph/compile/map_compiler.py:350-361`), while the existing sibling precedent caps both maps at 200 (`examples/demos/repo_census/graph.yaml:85-101`). A discovery cap of 500 with a smaller or unspecified map cap would produce a plausible but incomplete census.

Add deterministic run metadata to the machine-readable artifact: normalized source query, collection timestamp (the effective upper boundary of the since-only window), discovered count, classified count, row-failed count, actual map/synthesis call counts, Azure provider/model, prompt versions, run ID, and artifact hash. The canonical pattern requires code-computed coverage/call totals and recorded provider, model, corpus, and run identity (`reference/patterns/corpus-map-reduce.md:156-164,196-208`).

### R-2: Repair the evidence bundle, ledger schema, and mechanical field semantics

Add mechanical `url`, `base_sha`, and `head_sha` fields to `PRLedgerRow` and to the exact extraction bundle. The FR promises brief citations by PR URL (`feature-requests/FR-962-person-profile-census-authored-prs.md:60-61,125-127`) but the frozen bundle and row schema contain no URL (`feature-requests/FR-962-person-profile-census-authored-prs.md:98-100,134-155`). The brief-input adapter must use the validated `url` as the FR-895 citation identity so a fabricated URL is rejected.

Define `state` mechanically as `merged` when `merged_at` is non-null, otherwise the validated lowercase API `state` (`open` or `closed`). Amend AC-09 accordingly: `state` is derived, not copied verbatim. Define `labels` as the first `MAX_LABELS` API labels with values and order preserved, not as the entire API list, because the proposal also caps labels at ten (`feature-requests/FR-962-person-profile-census-authored-prs.md:96-100,146-151,249`).

Remove `linked issues` from the summary because neither the endpoint contract nor the exact bundle retrieves them (`feature-requests/FR-962-person-profile-census-authored-prs.md:25-26,90-101`). Permit `evidence_span` to be an exact non-empty span from either `title` or `body_head`, so a valid PR with an empty body remains classifiable; require the reducer to verify substring membership mechanically. Freeze validation for positive PR number, non-negative additions/deletions/changed-files, parseable timestamps, base/head SHA shape, final blob length, and the rule that fixed fields exceeding `MAX_CHARS` fail rather than being silently malformed.

### R-3: Fold FR-940 and FR-943 into the specialized reducer instead of claiming automatic inheritance

Delete the claim that FR-940 and FR-943 are inherited from the generic reducer without an override (`feature-requests/FR-962-person-profile-census-authored-prs.md:18`). FR-962 introduces a different `reduce_pr_ledger`, row model, and semantic fields, and then declares every violation batch-fatal (`feature-requests/FR-962-person-profile-census-authored-prs.md:129-161`); those properties do not automatically execute the generic reducer's normalization or containment behavior. FR-943 explicitly distinguishes attributable model failures, which become visible failed rows, from structural impossibilities, which remain batch-fatal (`feature-requests/FR-943-census-row-failure-containment.md:50-67,118-132`).

Freeze this specialized boundary as follows:

1. Parse `problem_labels` and `surface_labels` as non-empty JSON arrays of non-empty strings unique under casefold. A judged row must use the caller's exact canonical `problem_class`; `surfaces` must contain one to five distinct canonical members; `change_kind` must match its literal enum; `intent` must be one non-empty line of at most 280 characters; and `evidence_span` must pass the title/body substring check. This closes the current omission where only `surfaces`, not `problem_class`, is rejected outside its vocabulary (`feature-requests/FR-962-person-profile-census-authored-prs.md:110-116,158-161`).
2. Extend `PRLedgerRow` with a typed `classification_status: Literal["judged", "row_failed"]`, `failure_reason`, and `raw_finding`. For a row-owned map `_error` or model-field validation failure with a valid source index, emit one `row_failed` row retaining all mechanical PR fields; semantic fields are nullable/empty only under that status, and the raw finding is preserved deterministically. Mechanical rollups include every PR; semantic histograms exclude failed classifications and report classification coverage.
3. Keep non-dict findings, invalid/missing/duplicate/out-of-range source indexes, duplicate findings, missing findings, invalid mechanical bundles, and failed replacement-row validation batch-fatal. Reuse the focused FR-943 helper where its closed error-location and reason-format contracts fit; do not add a framework API.

Tests must distinguish every contained model-owned class from every fatal structural class. This preserves one row per discovered PR without reviving the O(batch) rerun failure that FR-943 removed (`feature-requests/FR-943-census-row-failure-containment.md:63-73`).

### R-4: Replace the circular canary with an independently declared semantic known truth

Replace AC-10's `--var canary=<repo>#<number>` condition (`feature-requests/FR-962-person-profile-census-authored-prs.md:250`). Presence of a PR proves coverage, not semantic judgement, and an extracted PR has no independently declared `surfaces`; therefore the current `AND` condition cannot implement invariant 8.

Freeze `canary` as a typed object containing `item_ref` and a non-empty `surface_family`, for example `{"item_ref":"owner/repo#123","surface_family":["ci","infra"]}`. The expected family is supplied to deterministic reconciliation but withheld from the map prompt. Before any ledger or brief artifact is emitted, fail when the item is absent **or** none of the judged surfaces family-matches an expected member under the FR-893 casefolded substring-family rule. The public demo must name a real public PR and an independently verified family in a committed fixture; tests must cover missing item, exact match, drifted-family match, and semantic miss. This is the required distinction between coverage invariants 1-7 and semantic invariant 8 (`reference/patterns/corpus-map-reduce.md:196-217`).

### R-5: Enforce repository visibility before the public demo crosses the collection boundary

Correct the dangling prior-art link at FR lines 19 and 275-289 to `FR-874-cross-device-agent-memory-sync.md` and identify it as a rejected precedent. Its surviving rule requires visibility verification as a written precondition before material is committed (`feature-requests/FR-874-cross-device-agent-memory-sync.md:9-16,24-29`).

Add a required, no-default `visibility` input validated as a non-empty list drawn from `public`, `private`, and `internal`; pass it to discovery as fixed repeated visibility arguments. The committed public invocation must pass exactly `["public"]`, and its tests must prove that constraint reaches the `gh search prs` argv before any PR extraction. Corp runs must pass an explicit approved visibility set; omission or an unknown value fails preflight.

Strengthen the mechanical locality audit to allow only the exact public demo source, public visibility, approved output roots, and rows whose repository owner is `sheikkinen`; scan graph defaults, README commands, demo output, ledger/brief proofs, fixtures, and run metadata. Owner equality alone is not proof of public visibility, so AC-11 as written is insufficient (`feature-requests/FR-962-person-profile-census-authored-prs.md:195-206,251`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `examples/demos/corpus_census/adapters/corpus_adapters.py`: bounded `gh_authored_prs_discover` and `gh_pr_extract`, plus only focused private helpers needed for parsing, fixed `gh` argv, visibility, and bundle bounds |
| D-2 | `examples/demos/corpus_census/adapters/gh-authored-prs-discover.tool.yaml` and `examples/demos/corpus_census/adapters/gh-pr-extract.tool.yaml` |
| D-3 | `examples/demos/person_profile_census/tools.py` and, only if needed to keep module limits, one person-profile-local reducer helper; Azure preflight, typed PR reconciliation, rollups, provenance, canary gate, and FR-895 brief adapters live here |
| D-4 | `examples/demos/person_profile_census/graph.yaml` and `examples/demos/person_profile_census/prompts/*.yaml`, authored only through `scripts/author.sh`, with both map and synthesis LLM nodes pinned to Azure and both map stages capped at 500 |
| D-5 | Person-profile markdown ledger, JSONL rows, machine-readable run metadata, and citation-checked brief under `tmp/` for corp runs and named public-safe demo/proof paths for committed evidence |
| D-6 | Person-profile README/demo invocation and public proof artifacts using only `sheikkinen@sheikkinen`, `visibility=["public"]`, and the committed public hidden-canary fixture |
| D-7 | Tests for adapter parsing/failures/overflow, no map truncation, Azure preflight order, provider pinning, typed reconciliation and containment, mechanical fields/rollups, URL citation boundary, hidden canary, and public-locality audit |
| D-8 | Changelog fragment, valid CAP/REQ wiring, requirement markers, FR implementation/status record, authoring report, and diary reflection |

Not authorized: a generic provider/model override CLI mechanism; graph inheritance, graph templates, or graph code generation; changes to `corpus_census` or `repo_census` graphs, prompts, defaults, demos, or public contracts; framework map truncation changes; generic failure-containment or classification APIs; linked-issue, review-comment, or diff-content collection; asking an LLM to compute identities, state, timestamps, counts, cadence, histograms, rankings, coverage, citations, visibility, canary validity, or data-safety decisions; committing customer owners, customer PR content, customer ledgers, customer briefs, or customer run metadata; hooks, CI, judge/review doctrine, or Chaplain runtime changes.

## Revised acceptance criteria

- [ ] AC-01: The FR retains its substantive in-body research record with five solution classes, precedent/evidence per class, preserved disagreement, and an explicit `is_this_a_graph` answer; the FR-874 citation resolves to `FR-874-cross-device-agent-memory-sync.md` and records its rejected-precedent status.
- [ ] AC-02: Discovery validates `<author>@<owner>:<since>` with an ISO `YYYY-MM-DD` date, fixed no-shell `gh` argv, required visibility enum list, timeout/check semantics, loud empty result, stable sorted identities, and duplicate rejection.
- [ ] AC-03: Discovery reads at most 501 results and rejects 501 before extraction or LLM execution; extraction and judgement maps both declare `max_items: 500`; a 500-item fixture maps all 500 and a 501-item fixture emits no output artifact.
- [ ] AC-04: `gh_pr_extract` validates `<repo_nwo>#<positive-number>`, fails loudly on missing/failing `gh` and 404, and emits exactly the revised bounded bundle including `url`, `base_sha`, and `head_sha`; tests cover body, label, and final-blob bounds, including an empty-body PR.
- [ ] AC-05: The graph's first node is Azure preflight; missing `AZURE_AI_ENDPOINT`, `AZURE_AI_API_KEY`, `AZURE_MODEL`, or required visibility prevents discovery, extraction, and every LLM call.
- [ ] AC-06: Graph and prompt artifacts are authored through `scripts/author.sh`; `tmp/draft-authoring-report.md` records lint plus a smoke that verifies artifact content, not exit code.
- [ ] AC-07: Every LLM node explicitly resolves to `provider: azure` and `AZURE_MODEL`, has no non-Azure fallback, and a configuration test fails on any other resolution.
- [ ] AC-08: The map prompt asks only for `problem_class`, `change_kind`, `surfaces`, `intent`, and an evidence span from title/body; it receives neither rollup instructions nor the hidden canary's expected family.
- [ ] AC-09: Reducer entry validates both vocabularies; judged rows enforce canonical `problem_class`, one-to-five canonical distinct surfaces, the frozen `change_kind` enum, bounded single-line intent, and mechanically verified evidence substring.
- [ ] AC-10: `PRLedgerRow` validates URL, base/head SHAs, timestamps, non-negative size fields, derived state, capped verbatim-order labels, provenance, and the judged/row-failed discriminator; tests prove no LLM output can add, remove, or alter mechanical fields.
- [ ] AC-11: Attributable model/map failures produce typed row-failed rows with mechanical fields and raw evidence; structural index/completeness/bundle failures abort the batch. Tests cover every class named in R-3.
- [ ] AC-12: Code computes total PRs, repo counts, timespan, merge rate, monthly cadence, label/change-kind/surfaces/problem-class histograms, top-N by additions plus deletions, and classification coverage from frozen fixtures; semantic histograms exclude row-failed classifications.
- [ ] AC-13: Machine-readable run metadata records normalized query, collection timestamp, counts, actual call totals, Azure provider/model, prompt versions, run ID, and artifact hash; fixture tests assert exact values.
- [ ] AC-14: FR-895 synthesis consumes validated URL-bearing ledger rows; accepted real URLs render and fabricated PR URLs reject before an accepted brief exists.
- [ ] AC-15: The hidden-canary gate consumes a typed item/family object withheld from the map prompt and emits no ledger or brief when the item is absent or the semantic family misses; exact and drifted-family matches pass.
- [ ] AC-16: Public demo discovery passes exactly `visibility=["public"]`; the locality audit scans all named committed person-profile surfaces and rejects any other visibility, source, repository owner, or output root. Corp artifacts and identifiers remain uncommitted.
- [ ] AC-17: Changelog fragment, CAP/REQ wiring, `@pytest.mark.req(...)` on every new test, FR status/decision/deviation record, authoring report, and diary reflection are included.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority is inactive until R-1 through R-5 are folded into FR-962 and the revised acceptance criteria replace the current set. | GATE |
| C-2 | No collector or map stage may silently truncate the frozen PR population; overflow must fail before extraction or LLM spend. | GATE |
| C-3 | Azure and visibility preflight must complete before any `gh` discovery/extraction or LLM execution. | GATE |
| C-4 | Model-owned failures may be contained only when attributable to a valid source index; structural identity, completeness, and mechanical-bundle failures remain batch-fatal. | GATE |
| C-5 | The only LLM-owned values are PR semantic classification and final cited narrative; identity, URL, state, timestamps, SHAs, labels, sizes, arithmetic, coverage, citations, visibility, and canary validation are code-owned. | GATE |
| C-6 | The public demo may collect only public PRs under the exact allowlisted public source and may not commit any customer identifier, content, ledger, brief, or run metadata. | GATE |
| C-7 | Every new or materially modified graph/prompt artifact must be produced through `scripts/author.sh` and witnessed by a substantive `tmp/draft-authoring-report.md`. | GATE |
| C-8 | If implementation requires a generic provider override, graph inheritance/template mechanism, map-framework change, existing census-default change, or shared containment API, enforcement stops and a separate FR re-enters the pipeline. | GATE |
| C-9 | Any change to hooks, CI, judge/review doctrine, or other enforcement infrastructure requires explicit human review before merge. | GATE |

Authority granted: after R-1 through R-5 are folded into FR-962, the enforcer may build the bounded Azure-pinned person-profile census contrib/example, PR adapters, specialized typed reducer, public-safe demo, and citation-checked brief only within D-1 through D-8 and conditions C-1 through C-9.
