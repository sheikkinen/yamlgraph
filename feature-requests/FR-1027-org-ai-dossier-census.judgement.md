# Judgement: FR-1027 Org AI Dossier — GitHub + Jira Census with One-Page Overview

**Verdict:** APPROVED WITH REVISIONS — the dossier is a coherent contrib/example on the existing census architecture, but authority activates only after the FR freezes an executable multi-corpus topology, closes completeness and privacy boundaries, and replaces ambiguous identity, provenance, and output claims with typed mechanical contracts.

**Reviewed against:** `feature-requests/FR-1027-org-ai-dossier-census.md`; `feature-requests/FR-1027.research.md`; `feature-requests/research-briefs/org-ai-dossier.md`; `feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md`; `feature-requests/FR-892-corpus-census-pipeline-injected-adapters.judgement.md`; `feature-requests/FR-899-org-repo-census-azure.md`; `feature-requests/FR-899-org-repo-census-azure.judgement.md`; `feature-requests/FR-962-person-profile-census-authored-prs.md`; `feature-requests/FR-962-person-profile-census-authored-prs.judgement.md`; `feature-requests/FR-1028-graph-run-provider-model-override.md` lines 120-150; `reference/patterns/corpus-map-reduce.md`; `examples/demos/corpus_census/graph.yaml`; `examples/demos/repo_census/graph.yaml`; `examples/demos/repo_census/tools.py`; `examples/demos/person_profile_census/graph.yaml`; `yamlgraph/utils/token_tracker.py`; `yamlgraph/cli/graph_run_helpers.py` lines 140-270; `.gitignore`; `ARCHITECTURE.md`; `capabilities/`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`. The gitignored `research/org-ai-dossier/sizing.md` was not consumed because it is outside the committed input closure.

## What is sound

The first consumer and recurring event are concrete: an operator must answer a management question about active projects, AI use, tools, and contributors now and on later reruns (`feature-requests/FR-1027-org-ai-dossier-census.md:8-11`). The problem is real and differentiated from the existing repo and single-person censuses (`feature-requests/FR-1027-org-ai-dossier-census.md:48-57`).

The selected architecture is directionally correct. GitHub repositories and Jira projects are finite corpora with independent semantic classifications, while activity, counts, identities, coverage, and tool aggregation remain code-owned (`feature-requests/FR-1027-org-ai-dossier-census.md:82-95,163-200`). That matches the corpus pattern's separation between model-authored meaning and deterministic identity, coverage, and arithmetic (`reference/patterns/corpus-map-reduce.md:141-182,196-208`). The proposed fixed-argv GitHub calls, fixed Jira REST requests, bounded evidence bundles, Azure pinning, and preflight-first ordering preserve established FR-899 boundaries (`feature-requests/FR-1027-org-ai-dossier-census.md:98-160,218-235`; `examples/demos/repo_census/graph.yaml:11-16,80-142`).

The research gate is satisfied in substance. The promoted record contains five genuine solution classes, precedent, an explicit graph/no-graph position, and preserved subtractionist dissent; the FR dispositions each row and separately probes narrower alternatives (`feature-requests/FR-1027.research.md:1-23`; `feature-requests/FR-1027-org-ai-dossier-census.md:267-288`). The proposal also explicitly re-enters FR-962's person-analysis territory instead of pretending it is novel (`feature-requests/FR-1027-org-ai-dossier-census.md:202-214`).

Strategic classification: **Contrib/example**. FR-892 already supplies the reusable census primitive, and FR-899/FR-962 supply Azure-pinned sibling examples, preflight, specialized reducers, and cited synthesis. FR-1027 adds one named organizational dossier consumer and concrete GitHub/Jira adapters; it does not justify a new framework primitive. GitHub collection, Jira collection, deterministic joining, and dossier rendering serve one end-to-end management answer, so the work has one responsibility and does not require a split.

## Required revisions

### R-1: Freeze one executable graph topology and its live/smoke bindings

Replace the claim that one graph "composes the corpus_census pipeline three times" with the exact sibling-graph contract. The shipped `corpus_census` graph has one discover slot, one extract slot, one map judgement, one reducer, and one synthesis tail (`examples/demos/corpus_census/graph.yaml:42-48,76-123,132-145`); FR-1027 instead diagrams two source branches plus a derived-person map and two synthesis nodes (`feature-requests/FR-1027-org-ai-dossier-census.md:34-38,82-95`). State explicitly that `org_ai_dossier/graph.yaml` reuses the **pattern**, not the unchanged graph, and freeze its tool declarations, state keys, branch/join edges, reducer order, and output-writing order.

Declare preflight, GitHub discovery/extraction, Jira discovery/extraction, and fixture substitutes as invocation-bound Python tool slots, or name another already-existing binding mechanism. The live command must bind live tools; the smoke command must bind a smoke preflight and Jira fixture. Resolve the current contradiction between mandatory Jira credentials before every fetch and a fixture smoke "without credentials" (`feature-requests/FR-1027-org-ai-dossier-census.md:158-161,220-223`): define the smoke as credential-free for Jira only, while still requiring Azure and public GitHub authentication, or make every external source fixture-backed. No test may bypass the same first-node preflight edge used by its mode.

Correct "one-judgement-tail" to two bounded synthesis judgements. Every LLM node, including person summaries and both renderers, must explicitly pin `provider: azure`, resolve the approved deployment, set temperature zero, and have no fallback provider.

### R-2: Freeze typed source, ledger, and failure contracts

Add exact Pydantic models for the GitHub evidence bundle, Jira evidence bundle, `RepoAIRow`, `JiraAIRow`, source-namespaced `PersonRow`, `AIToolRow`, coverage record, and `RunRecord`. For every field, state its type, provenance owner (collector, reducer, or model), bound, and nullability. Freeze the JSONL/CSV serialization columns rather than describing only document content (`feature-requests/FR-1027-org-ai-dossier-census.md:69-75,163-183`).

Define reducer failure semantics. Unknown, missing, duplicate, or out-of-range source identities; malformed mechanical bundles; invalid model schemas; and fabricated evidence references must either fail the run or become an explicitly typed failed row where the row can be attributed without weakening corpus completeness. Nothing may be silently dropped. If `on_error: skip` is used, deterministic reconciliation must reject missing/map-error rows before accepted artifacts exist, as required by the corpus pattern (`reference/patterns/corpus-map-reduce.md:136-138,198-208`).

For GitHub, reconcile each code-search result against the frozen active-repository identities; unknown, inactive, archived, truncated-tree, and search-cap results must be represented as typed coverage/caveat data rather than merged implicitly. For Jira, freeze request and response parsing, URL/JQL encoding, pagination continuation, non-2xx behavior, bounded Atlassian Document Format extraction, and AI-keyword query semantics. Construct the AI search as validated terms/clauses rather than the ambiguous quoted `text ~ "AI OR LLM ..."` string (`feature-requests/FR-1027-org-ai-dossier-census.md:139-156`).

### R-3: Make corpus completeness, cost, and semantic validity fail closed

Replace symbolic or absent limits with numeric ceilings for visible repositories, Jira projects/pages, issues, manifests, workflows, code-search terms/results, evidence characters, map items, total LLM calls, total API calls, concurrency, and wall-clock duration. Discovery must fetch one beyond each corpus ceiling or use an equally deterministic overflow witness and reject before LLM spend; `gh repo list --limit 1000`, `MAX_PAGES`, and per-keyword `--limit 100` must not silently turn an exhaustive dossier into a sample (`feature-requests/FR-1027-org-ai-dossier-census.md:104-137,145-156`). Both extraction maps and all LLM maps must carry matching `max_items` values, with boundary fixtures proving N succeeds and N+1 emits no accepted artifact.

Add independently declared hidden canaries for both semantic source classifiers: a frozen repo/evidence family and Jira issue/evidence family, withheld from the prompts and checked before any ledger or narrative is accepted. The canonical pattern requires this semantic witness in addition to coverage arithmetic (`reference/patterns/corpus-map-reduce.md:196-217`). Record corpus identities/hashes, artifact hashes, estimated and actual API/LLM call counts, provider/model, prompt versions, run ID, timestamps, and every truncation/partial-coverage flag in `run.json`.

Remove `token totals` from the required `run.json` contract unless the FR names and tests an existing mechanism that injects `TokenUsageCallbackHandler.summary()` into graph state. Today token tracking is optional CLI configuration and is printed after invocation rather than exposed to graph render tools (`yamlgraph/cli/graph_run_helpers.py:161-165,246-258`; `yamlgraph/utils/token_tracker.py:36-90`). Do not widen this contrib/example into a framework token-accounting change.

### R-4: Define honest coverage and output measurements

Freeze every denominator and status. GitHub coverage must distinguish API-reported total, token-visible listed repositories, active repositories, successfully extracted repositories, classified repositories, unclear classifications, truncated trees, and capped code-search signals. If `total_private_repos` is unavailable or not comparable to the token-visible listing, record it as unknown and do not present a completeness percentage. Jira coverage must distinguish visible, active, extracted, classified, unclear, and page-cap overflow. Define each AI-use percentage over a named frozen denominator and include `unclear` in the displayed accounting (`feature-requests/FR-1027-org-ai-dossier-census.md:71-75,198-200,241-243`; `feature-requests/research-briefs/org-ai-dossier.md:71-75,123-126`).

Replace the non-mechanical "`≤1 page`" promise with a fixed `onepager.md` bound of at most 800 words, while retaining exactly three findings and the required coverage/method/caveat fields (`feature-requests/FR-1027-org-ai-dossier-census.md:71`). Define `git SHA of the graph` as repository `HEAD` plus a SHA-256 of `graph.yaml`; a commit SHA alone does not identify an uncommitted graph file.

### R-5: Remove the unsafe cross-system identity and ranking ambiguity

Delete `same_person` and all email/display-name equality joining. The proposed bundles collect GitHub logins and Jira display names, not a shared verified identity, and the FR already concedes that login and display name are not mechanically joinable (`feature-requests/FR-1027-org-ai-dossier-census.md:189-197,244-245`). Store source-qualified identities instead: `github:<login>` and `jira:<accountId>`, with display names as labels only. Render two independently ranked lists using frozen source-local formulas; do not form a union rank across incomparable GitHub PR/contributor counts and Jira assignee/reporter frequencies.

A person summary may consume exactly one source-qualified footprint and may not assert cross-system identity. Tests must reject invented repositories/projects, identity changes, unsupported comparative claims, and prohibited seniority, performance, workload, sentiment, or intent claims.

### R-6: Make colleague summarization an explicit no-default policy decision

Replace `persons_llm=true` as the default with a required, no-default boolean runtime input. `false` must be the public smoke setting and must bypass the person-summary LLM node completely. `true` must require an explicit operator authorization acknowledgement accepted by preflight and recorded in `run.json`; the README must reproduce the FR-962 warning and identify the accountable controller (`feature-requests/FR-1027-org-ai-dossier-census.md:202-214,246-255,290-293`). This preserves the human decision rather than having the Judge silently make it.

The human reviewer must answer before promotion: **Does the employer's applicable policy authorize org-scale LLM summaries of colleagues from GitHub/Jira work-system facts for this management use?** A "no" keeps the mechanical source-separated rankings and removes the `summarize_person` node from authorized live use; a "yes" permits only the bounded, source-separated summary contract above.

### R-7: Enforce visibility and output locality at preflight

Add a required, no-default GitHub visibility policy input. Discovery must request/collect repository visibility and reject any item outside the approved set before extraction. The committed public smoke must allow only `public`, the `sheikkinen` owner, fixture Jira data, and exact demo output paths. A mechanical locality audit must scan graph defaults, README commands, fixtures, `demo-output.log`, proofs, and run metadata for disallowed organizations, Jira sites, issue text, people, and output roots, following the FR-962 visibility precedent (`feature-requests/FR-962-person-profile-census-authored-prs.judgement.md:71-79,95-99`).

Live preflight must resolve `out_dir` under the gitignored `research/org-ai-dossier/` root and reject tracked paths, traversal, symlink escape, and any other destination before GitHub/Jira fetches. Accepted dossier artifacts must be written only after reconciliation and canary gates succeed; failure must not leave success-shaped ledgers or narratives. The existing `.gitignore` entry for `research/` is necessary but not sufficient to enforce the runtime path claim (`feature-requests/FR-1027-org-ai-dossier-census.md:251-253`).

### R-8: Replace the acceptance list with direct witnesses and freeze allocation

Fold the revised criteria below into the FR. Add fixtures for empty corpora, overflow, duplicate identities, malformed timestamps, non-2xx GitHub/Jira responses, page continuation, unavailable coverage totals, truncated trees, capped searches, invalid evidence, model/map failure, both person modes, canary misses, and artifact non-emission. Retain the raw-output read, but require the cited 10 repo and 5 Jira samples before aggregate acceptance and record provider/model plus one non-template surprising detail per sample (`feature-requests/FR-1027-org-ai-dossier-census.md:256-259`).

Immediately before allocation, mechanically confirm `REQ-YG-670` and `CAP-266` remain free; then allocate them atomically. FR-1028 currently records those IDs as held for FR-1027 (`feature-requests/FR-1028-graph-run-provider-model-override.md:132-136`), but prose reservation is not registry enforcement.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `examples/demos/org_ai_dossier/graph.yaml` and `examples/demos/org_ai_dossier/prompts/*.yaml`, authored only through `scripts/author.sh` |
| D-2 | `examples/demos/corpus_census/adapters/gh_ai_adapters.py` plus exact GitHub live/fixture tool manifests |
| D-3 | `examples/demos/corpus_census/adapters/jira_adapters.py` plus exact Jira live/fixture tool manifests |
| D-4 | `examples/demos/org_ai_dossier/tools.py` and, only if required by the module-size limit, org-dossier-local typed reducer/render helpers |
| D-5 | Typed repository, Jira, person, AI-tool, coverage, and run-record models with deterministic reconciliation |
| D-6 | Gitignored live artifacts: `dossier.md`, `onepager.md`, `repos.md`, `jira.md`, three JSONL ledgers, AI-tools CSV, and `run.json` |
| D-7 | Public-safe README, fixture-backed Jira smoke, `demo-output.log`, and mechanical locality audit |
| D-8 | Unit/integration tests for topology, adapters, bounds, failure semantics, coverage, canaries, person policy, rendering, and artifact locality |
| D-9 | `CAP-266` / `REQ-YG-670` wiring if still free, `ARCHITECTURE.md`, changelog fragment, FR implementation record, authoring report, and diary reflection |

Not authorized: changes to the generic `corpus_census`, `repo_census`, or `person_profile_census` graph/prompt contracts; a new graph-composition, provider/model override, token-accounting, identity-resolution, or generic failure-containment framework primitive; Jira development-panel joins; GitHub Copilot seat/billing collection; cross-system person identity joins or combined person ranking; behavioural, performance, seniority, workload, sentiment, or intent inference; committing private organization names, Jira sites, issue text, person data, live ledgers, dossiers, or run metadata; hooks, CI, judge/review doctrine, or other enforcement-infrastructure changes. Adjacent needs require separate FRs.

## Revised acceptance criteria

- [ ] AC-01: The FR retains the committed five-class research record, preserved dissent, prior-art dispositions, and explicit `is_this_a_graph` answer.
- [ ] AC-02: The FR and graph freeze the exact two-source/derived-person topology, state keys, slot bindings, joins, reducer sequence, synthesis sequence, and artifact-write boundary; no claim remains that the unchanged one-corpus graph is composed three times.
- [ ] AC-03: Live and smoke invocations bind explicit preflight/discovery/extraction tools. Live preflight validates Azure, GitHub auth/visibility, Jira credentials, person-policy inputs, and output root before any fetch; smoke preflight permits fixture Jira without Jira credentials while retaining Azure and public-GitHub checks.
- [ ] AC-04: Every LLM node explicitly uses `provider: azure`, the approved Azure deployment, temperature zero, and no fallback; every extraction/classification map has a numeric `max_items`.
- [ ] AC-05: GitHub discovery validates inputs, freezes stable unique identities, filters the activity window, rejects overflow, and records archived/inactive/visibility counts without silent truncation.
- [ ] AC-06: GitHub extraction uses fixed no-shell argv and emits the exact typed bounded bundle; tests cover missing auth, command failure, malformed data, manifest/workflow/content caps, tree truncation, bot flags, and final bundle size.
- [ ] AC-07: Org code search enforces the frozen keyword/call/time/result ceilings, reconciles hits only to frozen repo identities, and records capped, unknown, inactive, and archived hits as coverage/caveat data.
- [ ] AC-08: Jira discovery uses fixed authenticated REST requests, deterministic pagination and JQL encoding, stable unique project identities, numeric page/project ceilings, active/dormant accounting, and overflow failure before LLM spend.
- [ ] AC-09: Jira extraction emits the exact typed bounded bundle and tests project metadata, approximate counts, at most 30 issues, account-ID-backed person facts, ADF description normalization, top-ten frequencies, AI-term clauses, non-2xx failures, timeouts, and final bundle size.
- [ ] AC-10: Typed reducers reconcile every discovered identity exactly once; structural failures and fabricated evidence abort before accepted artifacts, and any contained model failure remains an explicit typed row included in coverage.
- [ ] AC-11: Repo/Jira AI claims survive only with bundle-present paths/issue keys; otherwise tools are removed and usage becomes `unclear`. Fixtures prove accepted and rejected evidence and both semantic canaries.
- [ ] AC-12: Numeric corpus, byte, API-call, LLM-call, concurrency, and wall-clock ceilings are enforced; N succeeds, N+1 emits no accepted artifact; `run.json` records estimated/actual calls, hashes, provider/model, prompt versions, run identity, timestamps, and partial-coverage flags.
- [ ] AC-13: Coverage renderers use the frozen denominator definitions, show unknown/unavailable totals honestly, account for `unclear`, and append `of <denominator>` to every percentage in `run.json`, `onepager.md`, `dossier.md`, `repos.md`, and `jira.md`.
- [ ] AC-14: `onepager.md` is at most 800 words and contains coverage, GitHub/Jira active counts, denominator-qualified AI shares, top tools, source-separated top persons, exactly three cited findings, method/date, and caveats.
- [ ] AC-15: Persons remain source-qualified (`github:<login>`, `jira:<accountId>`), produce two source-local rankings with frozen formulas, never populate `same_person`, and never create a combined cross-system rank.
- [ ] AC-16: `persons_llm` is required with no default; `false` bypasses the summary node and renders mechanical tables, while `true` requires and records explicit operator authorization and enforces the bounded source-separated summary contract.
- [ ] AC-17: Public smoke uses only `sheikkinen`, GitHub visibility `public`, fixture Jira data, `persons_llm=false`, and exact demo paths; the locality audit rejects any private identifier, content, person data, visibility, source, or output-root deviation.
- [ ] AC-18: Live output is restricted to a resolved non-escaping path beneath gitignored `research/org-ai-dossier/`; preflight/reconciliation/canary failure leaves no success-shaped dossier, ledger, or run record.
- [ ] AC-19: Ten raw repo classifications and five raw Jira classifications are read before aggregate acceptance and cited in the FR implementation record with provider/model and one concrete surprising detail each.
- [ ] AC-20: Graph/prompt artifacts have a substantive authoring report with lint and smoke evidence; all new tests carry `@pytest.mark.req("REQ-YG-670")`; `CAP-266`/`REQ-YG-670` are confirmed free immediately before atomic allocation; requirement coverage, changelog, FR status/decisions/deviations, and diary reflection are complete.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority is inactive until R-1 through R-8 and AC-01 through AC-20 are folded into FR-1027. | GATE |
| C-2 | The implementation is one contrib/example; no framework primitive or modification to existing census contracts is authorized. | GATE |
| C-3 | Preflight must complete before any GitHub/Jira fetch or LLM execution, and no accepted artifact may be written before reconciliation and both semantic canaries pass. | GATE |
| C-4 | Azure is the sole LLM provider for live and smoke execution; no fallback or inherited non-Azure provider is permitted. | GATE |
| C-5 | Corpus completeness, identity, arithmetic, rankings, coverage, evidence reconciliation, policy inputs, and artifact locality are code-owned; the LLM owns only bounded semantic classifications, optional authorized person prose, and cited findings/onepager prose. | GATE |
| C-6 | The human reviewer must answer the employer-policy question in R-6 before enabling `persons_llm=true`; absent an affirmative recorded answer, only `persons_llm=false` is authorized. | GATE |
| C-7 | No cross-system person join or combined person rank is permitted under this FR. | GATE |
| C-8 | Live corp artifacts and identifiers must remain under the enforced gitignored output root and must never be committed to this public repository. | GATE |
| C-9 | Every new or materially modified graph/prompt artifact must be produced through `scripts/author.sh` and evidenced by the substantive authoring report, not exit status alone. | GATE |
| C-10 | If implementation requires changes to generic graph composition, provider override, token tracking/export, map semantics, shared reducers, hooks, CI, or judge/review doctrine, enforcement stops and a separate FR enters the pipeline with required human review. | GATE |

Authority granted: after the required revisions are folded into FR-1027 and the R-6 human policy decision is recorded, the enforcer may build the bounded Azure-pinned org AI dossier contrib/example, its GitHub/Jira adapters, typed local reducers, public-safe smoke, and gitignored live artifacts only within D-1 through D-9 and C-1 through C-10.

---
**Prior art:** inherits the FR-1027 prior-art disposition (FR-892 foundation, FR-899/FR-962 siblings, FR-874 rejected, FR-1028 unblock).
**Folded:** 2026-09-07 by the operator session from `tmp/draft-judgement-copilot-FR-1027-*.md` (backend copilot, gpt-5.6-sol); R-1..R-8 folded into the FR the same day; R-6 human answer: "Yes — authorized" (FR § Decisions 5). Advisory until human-reviewed.
