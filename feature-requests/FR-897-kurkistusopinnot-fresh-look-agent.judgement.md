# Judgement: FR-897 Kurkistusopinnot Fresh-Look Agent

**Verdict:** APPROVED WITH REVISIONS — the domain instrument is sound and testable, but authority activates only after the FR folds in the FR-892 reuse boundary, the official institution-population authority, and source-layer labelling rules below.

**Reviewed against:** `feature-requests/FR-897-kurkistusopinnot-fresh-look-agent.md`; `feature-requests/FR-897.research.md`; `feature-requests/research-briefs/fr-897-kurkistusopinnot-fresh-look.md`; `feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md`; `feature-requests/FR-894-corpus-map-reduce-github-scope-reconciliation-reference.md`; `reference/patterns/corpus-map-reduce.md`; `examples/surplus/diary-discourse-analysis/`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`.

**Prior art:** The governing FR and FR-897 research record are current inputs,
not competing proposals. FR-892, FR-894, corpus-census, and diary-discourse
precedents are dispositioned under What is sound, R-1, and Scope is frozen.

## What is sound

The problem is real and bounded. The FR names a first consumer and first event (`feature-requests/FR-897-kurkistusopinnot-fresh-look-agent.md:8-12`), states that the output is neither ranking nor causal effect evaluation (`feature-requests/FR-897-kurkistusopinnot-fresh-look-agent.md:31-35`), and grounds the need in a closed brief that says no dated, source-reconciled dossier exists in this repository (`feature-requests/research-briefs/fr-897-kurkistusopinnot-fresh-look.md:18-26`).

The raw-read gate is substantively satisfied. The FR records seven concrete source observations, including Metropolia category mixing, Vaasa identity/MFA access friction, Tavastia offer-family contamination, Lukiolaisbarometri as learner context rather than effect evidence, and QAA as a reconciliation precedent (`feature-requests/FR-897-kurkistusopinnot-fresh-look-agent.md:89-130`). This meets the local judge rule that substance matters, not just the presence of a research artifact (`.github/skills/judge-fr/doctrine.md:118-130`; `.github/copilot-instructions.md:231-233`).

The architecture direction fits the corpus map-reduce doctrine: finite corpus, independent semantic judgement, completeness/coverage accounting, cheap structured primary map, and deterministic counts (`reference/patterns/corpus-map-reduce.md:24-33`). The FR preserves the core trust boundary: model output is a claim, while Python owns source identity, evidence-span reconciliation, coverage, and arithmetic (`feature-requests/FR-897-kurkistusopinnot-fresh-look-agent.md:196-206`; `reference/patterns/corpus-map-reduce.md:141-168`).

The strategic classification is **Contrib/example**, not framework primitive. The use case is one retained domain research instrument with one named downstream consumer; existing corpus topology is reused, while domain-specific extraction, source-layer reconciliation, six lenses, positive controls, and Finnish report rendering justify an example-level artifact if the FR-892 boundary is tightened. The FR already excludes YAMLGraph runtime changes, generic schema overrides, dashboards, rankings, private data, and writes to the nested consumer repository (`feature-requests/FR-897-kurkistusopinnot-fresh-look-agent.md:357-366`).

The test surface is mostly derivable. The FR demands RED-first deterministic tests for deduplication, query/fetch state distinctions, ceiling refusal, map-index reconciliation, evidence-span validation, map-error rejection, citation reconciliation, and positive controls (`feature-requests/FR-897-kurkistusopinnot-fresh-look-agent.md:293-296`), and it carries repo traceability/changelog/diary obligations (`feature-requests/FR-897-kurkistusopinnot-fresh-look-agent.md:327-330`; `.github/copilot-instructions.md:174-177`).

## Required revisions

### R-1: Freeze the FR-892 reuse boundary

Amend the Proposed Solution and Alternatives so the enforcer can tell exactly why this work authors a retained surplus instrument instead of binding adapters to the shipped `corpus_census` graph. The corpus pattern says FR-892 tool slots are the executable precedent and that "a new corpus supplies adapters, not a new graph" (`reference/patterns/corpus-map-reduce.md:54-61`), while this FR currently authorizes one new graph (`feature-requests/FR-897-kurkistusopinnot-fresh-look-agent.md:134-139`). Fold in a mechanical boundary:

- state which FR-892 invariants/components are reused unchanged: freeze, collector-owned IDs, fail-closed reconciliation, no-drop ledger, provider/model/run provenance;
- state which requirements exceed unchanged `corpus_census`: the four-field source-reading schema, four evidence layers, six fixed lens prompts, positive controls, and Finnish report renderer;
- add a stop condition: if implementation requires changing `examples/demos/corpus_census/`, YAMLGraph runtime, tool-slot semantics, generic schema override, or provider support, stop and file a separate FR.

### R-2: Name the official institution population authority

Amend the collector contract to name the committed source of truth for Finnish universities and universities of applied sciences: the authority, retrieval date, exact frozen file path, stable institution ID fields, approved-domain fields, expected count or count-derivation rule, and checksum. The current FR requires an "official list" and approved domains (`feature-requests/FR-897-kurkistusopinnot-fresh-look-agent.md:150-157`) but does not say what makes the list official or how an enforcer proves the population is complete. The revised AC must require a test that fails if an institution row lacks type, ID, approved domain, or retrieval metadata.

### R-3: Resolve source-layer coverage and label semantics

Amend AC-04 and AC-10 so they no longer pull in opposite directions. AC-04 currently says the collector "covers both institution types and all four source layers" (`feature-requests/FR-897-kurkistusopinnot-fresh-look-agent.md:300-303`), while AC-10 allows honest incomplete/sample labels for uncovered layers (`feature-requests/FR-897-kurkistusopinnot-fresh-look-agent.md:320-322`) and the Ideal Result says missing source layers must make the run visibly incomplete (`feature-requests/FR-897-kurkistusopinnot-fresh-look-agent.md:84-87`). Replace this with explicit label rules:

- `national bounded scan` requires every frozen institution to have a discovery record;
- `four-layer pilot` requires at least one curated or discovered source in each of provider, learner, participation/progression, and evaluation layers;
- any missing layer or unqueried institution forces `sample` or `incomplete`, never `census`;
- `census` is prohibited unless the stronger FR-894 invariants are proved for a defined offer population, as the FR already states (`feature-requests/FR-897-kurkistusopinnot-fresh-look-agent.md:163-167`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/authoring-briefs/fr-897-kurkistusopinnot-fresh-look.md` |
| D-2 | `examples/surplus/kurkistusopinnot-fresh-look/graph.yaml` and YAML prompts, authored only through `scripts/author.sh` |
| D-3 | Collector, reconciliation, batching, positive-control, and writer tools under `examples/surplus/kurkistusopinnot-fresh-look/nodes/` |
| D-4 | Bounded local fixture plus deterministic unit tests |
| D-5 | Run-dated public-safe proof folder containing `source-ledger.jsonl`, `dossier.json`, `fresh-look.md`, and `run-evidence.txt` |
| D-6 | Instrument README plus `examples/surplus/README.md` index entry |
| D-7 | Changelog fragment, requirement traceability, FR implementation record, and diary reflection |

Not authorized: changes to YAMLGraph runtime, map semantics, provider support, generic prompt/schema overrides, tool-slot semantics, `examples/demos/corpus_census/`, CI/hooks/judge/review doctrine, public service/dashboard/RAG/UI surfaces, surveys/interviews/private learner data, institution rankings, admissions advice, causal effectiveness claims, committed full-page fetched text, or any write inside `projects/opinto_ohjaus/.git`.

## Revised acceptance criteria

- [ ] AC-01: `feature-requests/FR-897.research.md` passes `scripts/research_preflight.py --verify-artifact`; the FR dispositions all five solution classes and preserves the `is_this_a_graph` answer.
- [ ] AC-02: R-1 through R-3 are folded into the FR before enforcement authority activates.
- [ ] AC-03: RED first — deterministic failing tests cover URL/source deduplication, query/fetch state distinctions, ceiling refusal, missing/duplicate/unknown map indexes, invalid evidence spans, map-error rejection, citation reconciliation, source-layer labelling, official institution-list validation, and all three positive controls.
- [ ] AC-04: The graph and prompts are authored only through `scripts/author.sh`; the accepted `tmp/draft-authoring-report.md` records graph lint, prompt lint where applicable, and a live Mercury smoke over a bounded public-safe fixture.
- [ ] AC-05: The collector loads a run-versioned config with Finnish, Swedish, and English discovery terms; freezes the named official institution population from R-2; records every fixed query/result pair including zero-result and error records; and rejects inference above the frozen source, byte, query, wall-clock, or 115-call ceilings.
- [ ] AC-06: Every institution receives a discovery record with one of the explicit states `candidate_found`, `no_candidate_found`, `fetch_failed`, or `not_queried`; `not_queried` blocks `national bounded scan`, and any uncovered source layer applies the R-3 incomplete/sample label.
- [ ] AC-07: All source-reading, batch-memo, and lens-memo nodes pin `provider: inception`, `model: mercury-2`, and low temperature; the only other LLM call is one pinned Sonnet synthesis after deterministic reconciliation passes.
- [ ] AC-08: Source readings use the typed four-field contract in the FR, support abstention, carry exact short spans, and tests prove every span is present in normalized fetched source text.
- [ ] AC-09: The LLM-free reducer proves one result per fetched source, retains all primary rows, computes institution/type/language/offer-family/source-layer/query/fetch/abstention/call coverage from the frozen manifest, and fails the run on any skipped/error/missing result.
- [ ] AC-10: Exactly six lens memos are present; each cites only valid source IDs from at least two source layers or explicitly abstains, preserves at least one contradiction where evidence exists, and attaches a falsifier to every hypothesis.
- [ ] AC-11: The final report contains the frozen sections, uses no unknown source IDs or model-authored totals, distinguishes observation/inference/hypothesis, and contains no institution ranking, admissions decision, or unsupported causal claim.
- [ ] AC-12: Fixture smoke proves count-in equals count-out and artifact creation. A bounded live Finnish pilot passes the Vaasa, Tavastia, and Lukiolaisbarometri positive controls and records honest incomplete/sample labels according to R-3.
- [ ] AC-13: No fetched full-page text, personal data, credentials, private learner data, or regulated records are committed; committed spans are short, source-linked, and public-safe.
- [ ] AC-14: No file inside `projects/opinto_ohjaus/.git` changes; the README names that repository only as the downstream consumer.
- [ ] AC-15: Tests carry valid `@pytest.mark.req(...)` markers; `python scripts/req_coverage.py` passes; a changelog fragment, FR implementation record, `examples/surplus/README.md` link, and diary reflection with Seed are added.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not start implementation until R-1 through R-3 are folded into `feature-requests/FR-897-kurkistusopinnot-fresh-look-agent.md`. | GATE |
| C-2 | Governed graph and prompt writes must occur through `scripts/author.sh`; if the route fails, fix the route or stop, never author manually (`.github/copilot-instructions.md:15`). | GATE |
| C-3 | No YAMLGraph runtime, generic corpus-census, CI, hook, judge, review, provider, or tool-slot semantics may change under this FR. | GATE |
| C-4 | No file may be written, staged, or committed inside `projects/opinto_ohjaus/.git`. | GATE |
| C-5 | The collector must refuse inference before the first paid call if source, byte, query, wall-clock, or call ceilings would be exceeded. | GATE |
| C-6 | Model outputs are claims only; source identity, evidence spans, counts, coverage, and call totals must be reconciled in code. | GATE |
| C-7 | A missing source layer, failed fetch, failed positive control, unsupported effect claim, or unqueried institution must be visible in the run evidence and must prevent `census` labelling. | GATE |
| C-8 | Public-safe artifact boundaries are mandatory: full fetched page text remains under `tmp/`, and committed artifacts contain only metadata, hashes, and short evidence spans. | GATE |
| C-9 | RED/GREEN traceability, requirement coverage, changelog, FR update, and diary reflection are enforcement obligations, not cleanup. | GATE |

Authority granted: after R-1 through R-3 are folded into the FR, the enforcer may build the retained `examples/surplus/kurkistusopinnot-fresh-look/` research instrument and its local nodes, fixtures, tests, docs, public-safe proof artifacts, and traceability updates within the frozen scope above.
