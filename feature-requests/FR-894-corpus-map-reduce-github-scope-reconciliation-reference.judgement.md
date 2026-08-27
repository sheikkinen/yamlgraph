# Judgement: FR-894 Corpus Map-Reduce and GitHub Scope-Reconciliation Reference

**Verdict:** APPROVED WITH REVISIONS — the documentation-only pattern is strategically sound and properly bounded, but implementation authority activates only after the missing research-gate evidence and unresolved generated triage are folded into the FR.

**Prior art:** inherited from and dispositioned by the parent FR-894; this
judgement independently checked FR-892, FR-857, FR-855, and the specialized
corpus graph precedents.

**Reviewed against:** feature-requests/FR-894-corpus-map-reduce-github-scope-reconciliation-reference.md; .github/skills/judge-fr/doctrine.md; .github/skills/judge-fr/judgement.template.md; reference/patterns.md; reference/map-nodes.md; reference/patterns/coded-classification.md; reference/README.md; reference/patterns/batch-runner.md; examples/demos/prompt_theme_analyzer/graph.yaml; examples/demos/fr-atlas/graph.yaml; examples/demos/req_witness_audit/graph.yaml; examples/demos/session-shapes/graph.yaml; examples/demos/corpus_census/graph.yaml; examples/demos/recap/graph.yaml; docs/the-questioner-and-the-trace.md; .github/skills/review-pr/doctrine.md; scripts/review.sh; feature-requests/FR-402-prompt-theme-analyzer-demo-implementation.md; feature-requests/FR-748-fr-atlas-onboarding-summary.md; feature-requests/FR-851-requirement-witness-audit.md; feature-requests/FR-884-session-task-shape-mining-for-sole-route-extraction.md; feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md; feature-requests/FR-892-corpus-census-pipeline-injected-adapters.judgement.md; feature-requests/FR-857-corpus-analysis-fanout-graph.md; feature-requests/FR-855-generated-pattern-index.md; repo doctrine in project instructions.

## What is sound

The proposal is correctly classified as **Pattern documentation**, not a framework primitive. The FR explicitly limits itself to a reference document and links, and excludes any new graph, GitHub integration, scorer, merge gate, or runtime feature (feature-requests/FR-894-corpus-map-reduce-github-scope-reconciliation-reference.md:15-29, 96-104, 247-248). That keeps scope minimal: the executable skeleton already exists in FR-892, whose implementation record says `examples/demos/corpus_census/` is a shared discover-extract-map-reduce pipeline with invocation-time tool slots, fail-closed reducer tests, PDF and git-timeline proofs, and reference documentation (feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md:140-178).

The evidence base supports the need for a higher-level corpus pattern. Existing references document map mechanics and batching mechanics, but not the corpus authority/provenance contract: Pattern 8 describes parallel fan-out and collection only (reference/patterns.md:532-652), Pattern 10 describes pre-chunking for rate and memory control (reference/patterns.md:802-933), and the map-node reference documents fan-out/fan-in behavior, reducers, and map syntax (reference/map-nodes.md:7-20, 122-136). The proposed new document therefore fills an architectural-reference gap rather than duplicating syntax.

The cited precedents substantiate the topology. FR-402 and its graph show list -> map -> deterministic aggregate -> grouped report with an explicit `inception/mercury-2` pin (feature-requests/FR-402-prompt-theme-analyzer-demo-implementation.md:9-15, 84-90; examples/demos/prompt_theme_analyzer/graph.yaml:11-15, 52-82). FR-748 documents corpus collection, chunked map judgement, code-side coverage reconciliation, bounded synthesis, and render (feature-requests/FR-748-fr-atlas-onboarding-summary.md:52-80), with its graph mirroring collect -> map -> assemble -> merge -> finalize -> story -> render (examples/demos/fr-atlas/graph.yaml:27-50, 59-104). FR-851 documents deterministic construction plus batched LLM audit and reconciliation that rejects hallucinated IDs and prevents silent disappearance (feature-requests/FR-851-requirement-witness-audit.md:20-31, 132-139), and its graph maps batch files then persists raw results (examples/demos/req_witness_audit/graph.yaml:45-65). FR-884 uses a cheap pinned classifier graph with deterministic aggregation (feature-requests/FR-884-session-task-shape-mining-for-sole-route-extraction.md:137-147; examples/demos/session-shapes/graph.yaml:10-13, 43-64). The Questioner essay records the full-corpus run that the FR cites: 1,278 files, 83 chunks/map memoranda, 11 reductions, deterministic byte coverage, and zero skipped map errors (docs/the-questioner-and-the-trace.md:675-682).

The GitHub scope-reconciliation distinction is architecturally aligned. The FR separates the authority plane from the reality plane and refuses to label changes `unauthorized` without an independent frozen authority source (feature-requests/FR-894-corpus-map-reduce-github-scope-reconciliation-reference.md:68-76, 160-197). That matches the review doctrine, which treats the actual GitHub PR head and merge diff as reality and compares them against the governing FR and judgement as authority (.github/skills/review-pr/doctrine.md:19-38). The FR also preserves the live-review boundary: cheap corpus findings are claims, while live PR merge review remains the `scripts/review.sh` route and human decision (feature-requests/FR-894-corpus-map-reduce-github-scope-reconciliation-reference.md:198-203; scripts/review.sh:56-64; .github/skills/review-pr/doctrine.md:47-69).

Single responsibility is acceptable. The recap and authority-aware reconciliation examples are two applications of the same frozen-corpus topology, and the FR explicitly keeps them as worked documentation rather than separate executable surfaces (feature-requests/FR-894-corpus-map-reduce-github-scope-reconciliation-reference.md:20-29, 143-203). The nearby alternatives are dispositioned: extending only `map-nodes.md`, reviving FR-857, overloading `recap`, running the full reviewer over history, and building a GitHub collector are all rejected with concrete reasons (feature-requests/FR-894-corpus-map-reduce-github-scope-reconciliation-reference.md:255-287).

## Required revisions

### R-1: Add the mandatory research evidence pointer

Add a `**Research:**` field near the FR header that points to a committed research record for FR-894, normally `feature-requests/FR-894.research.md`, or to an explicitly equivalent committed dispositioned alternatives table. The record must satisfy the local judge gate: 4-6 genuine solution classes, precedent lines, preserved disagreement, and an `is_this_a_graph` answer. The current header has Priority, Type, Status, Effort, Requested, and First consumer, but no `**Research:**` field (feature-requests/FR-894-corpus-map-reduce-github-scope-reconciliation-reference.md:1-12), while the judge doctrine says a newly created FR with an absent or dangling `**Research:**` field receives no authority (.github/skills/judge-fr/doctrine.md:118-130).

### R-2: Resolve the generated triage block

Convert every `[pending]` generated triage claim into a dispositioned FR claim, acceptance criterion, pre-mortem note, or remove it. The FR currently ends with nine pending generated claims requiring disposition (feature-requests/FR-894-corpus-map-reduce-github-scope-reconciliation-reference.md:319-329). Authority cannot activate while the FR itself marks unresolved claims as pending; the enforcer should receive frozen scope, not a residue queue.

### R-3: Freeze the Markdown link-validation command

Replace "a script that resolves every workspace-relative Markdown link" with an exact validation command, either a committed script path or the complete inline one-off command to run. The doctrine requires mechanical acceptance criteria expressed as a command, file, or assertion (.github/skills/judge-fr/doctrine.md:43-44), and the current AC only names an unspecified script while calling the validation list "Exact" (feature-requests/FR-894-corpus-map-reduce-github-scope-reconciliation-reference.md:249-253). The command must be scoped to the three touched reference files and must fail nonzero on any missing workspace-relative Markdown target.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `reference/patterns/corpus-map-reduce.md` |
| D-2 | One link from `reference/README.md` under Examples & Guides |
| D-3 | Short cross-links from Pattern 8 and Pattern 10 in `reference/patterns.md` |
| D-4 | FR-894 update recording the research pointer, resolved triage, implementation status, and validation record |

Not authorized: any new or modified `graph.yaml`; any prompt YAML; any Python tool, runtime, CLI, hook, CI workflow, capability, requirement, GitHub API integration, scorer, merge gate, or executable collector; any change to judge/review/author doctrine; any attempt to run cheap corpus triage as a live PR merge verdict; any modification of `scripts/review.sh` or `.github/skills/review-pr/doctrine.md`.

## Revised acceptance criteria

- [ ] AC-01: FR-894 contains a `**Research:**` field pointing to a committed FR-894 research record or equivalent committed dispositioned alternatives table that satisfies the local judge gate: 4-6 solution classes, precedent lines, preserved disagreement, and an `is_this_a_graph` answer.
- [ ] AC-02: The generated triage block is fully dispositioned or removed; no `[pending]` generated claim remains in FR-894.
- [ ] AC-03: `reference/patterns/corpus-map-reduce.md` exists.
- [ ] AC-04: `reference/README.md` links to `reference/patterns/corpus-map-reduce.md` under Examples & Guides.
- [ ] AC-05: Pattern 8 and Pattern 10 in `reference/patterns.md` link to the new reference without duplicating its content.
- [ ] AC-06: The new reference documents the six-stage topology: freeze, partition, typed map, deterministic reconciliation, optional hierarchical reduce, and render.
- [ ] AC-07: The seven coverage/provenance invariants from the FR are stated as requirements, not optional advice.
- [ ] AC-08: The GitHub recap worked application names immutable commit/PR identities and preserves one primary result per semantic unit, with PRs preferred when they exist and commits treated as fallback or transport units.
- [ ] AC-09: The scope-reconciliation worked application separates authority from reality, defines the authority hierarchy, and covers path drift, semantic drift, omission, and metadata drift.
- [ ] AC-10: The wording rule is explicit: absent independent authority, findings are `surprising` or `unexplained`, never `unauthorized`.
- [ ] AC-11: The reference states that cheap-model corpus triage cannot issue a merge verdict and that flagged live PRs must enter `scripts/review.sh`.
- [ ] AC-12: Cost ceilings, call-count arithmetic, provider pinning, privacy, secret, and binary-patch boundaries are documented.
- [ ] AC-13: The pattern cites at least the FR-402 prompt-theme analyzer, FR-748 atlas, FR-851 requirement-witness audit, FR-884 session-shapes classifier, FR-892 corpus census, `recap`, and review-pr precedents.
- [ ] AC-14: No `graph.yaml`, prompt, Python tool, runtime, CLI, hook, CI, capability, requirement, GitHub API integration, scorer, merge gate, or executable collector is added or changed under this FR.
- [ ] AC-15: The validation record in FR-894 includes exact commands and results for: `rg -n '[[:blank:]]+$' reference/patterns/corpus-map-reduce.md reference/README.md reference/patterns.md` with no matches; the frozen Markdown-link validation command from R-3 with success; and `git diff --check -- reference/patterns/corpus-map-reduce.md reference/README.md reference/patterns.md` with success.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority is inactive until R-1 through R-3 are folded into FR-894. | GATE |
| C-2 | Enforcement is documentation-only and may touch only D-1 through D-4. | GATE |
| C-3 | If implementation requires a graph, prompt, Python tool, runtime, CLI, hook, CI, capability, requirement, GitHub API integration, scorer, merge gate, or executable collector, stop and file a separate FR. | GATE |
| C-4 | The new reference may describe `examples/demos/corpus_census/` and `scripts/review.sh`, but must not modify or substitute either route. | GATE |
| C-5 | Any live PR flagged by the documented corpus pattern remains a claim requiring the independent review route and human merge decision. | GATE |

Authority granted: after the required revisions are folded into FR-894, the enforcer may add the corpus map-reduce reference document and the two documentation links within the frozen doc-only scope above.
