# Judgement: FR-899 Org Repository Census with Pinned-Azure Delegation

**Prior art:** FR-896 (cross-repo pattern/model census) — DISTINCT scope: own-footprint pattern incidence vs customer-org inventory under azure compliance pinning; both reuse the FR-892 corpus_census base by design. FR-893.research.md / FR-895.research.md — foundation research for the base pipeline and synthesize tail; no conflict.

**Verdict:** APPROVED WITH REVISIONS — the repo-census shape is a coherent contrib/example built on FR-892 and FR-895, but authority activates only after the FR repairs its research record, freezes the repo-specific reducer/ledger contract, and makes Azure fail-fast happen before any `gh` discovery.

**Reviewed against:** feature-requests/FR-899-org-repo-census-azure.md; feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md; feature-requests/FR-892-corpus-census-pipeline-injected-adapters.judgement.md; feature-requests/FR-895-census-synthesize-tail.md; feature-requests/FR-895-census-synthesize-tail.judgement.md; feature-requests/FR-874-cross-device-agent-memory-sync.md; feature-requests/FR-890-research-sole-route-closed-input-alternatives.md; examples/demos/corpus_census/graph.yaml; examples/demos/corpus_census/README.md; examples/demos/corpus_census/adapters/corpus_adapters.py; examples/demos/corpus_census/tools.py; examples/demos/corpus_census/adapters/census_brief.py; examples/demos/corpus_census/prompts/judge_item.yaml; examples/demos/corpus_census/prompts/synthesize_brief.yaml; reference/patterns/corpus-map-reduce.md; yamlgraph/node_factory/llm_nodes.py; yamlgraph/utils/llm_providers.py; .github/skills/judge-fr/doctrine.md; .github/skills/judge-fr/judgement.template.md; .github/copilot-instructions.md.

## What is sound

The first consumer is concrete: an operator needs an organization repository inventory at a corp platform-audit moment, with purpose, persons, activity, and one corp-level brief on the approved Azure endpoint (feature-requests/FR-899-org-repo-census-azure.md:8, 21-25). The data-governance problem is real and not merely preference: the FR states repo contents and contributor identities are corp data that must not transit the default provider (feature-requests/FR-899-org-repo-census-azure.md:29-34).

The graph shape is correct. FR-899 maps a finite enumerable corpus, asks one semantic judgement per repo, keeps persons/activity in deterministic code, and renders a cited brief (feature-requests/FR-899-org-repo-census-azure.md:13-19, 67-78). That matches the corpus-map-reduce doctrine: use the pattern for finite corpora with independent semantic judgements where counts, identities, and coverage can be checked deterministically (reference/patterns/corpus-map-reduce.md:24-33), and keep model-authored meaning separate from code-owned identity, coverage, and arithmetic (reference/patterns/corpus-map-reduce.md:141-168, 181-182).

The proposal conforms to existing architecture before extending it. FR-892 shipped invocation-time `discover` and `extract` tool slots and explicitly says a new corpus supplies adapters rather than a new graph (feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md:64-85; reference/patterns/corpus-map-reduce.md:54-61). The current `corpus_census` graph already has those slots plus a map LLM node, deterministic reducer, synthesis input preparation, one synthesis LLM node, and a citation-checked render step (examples/demos/corpus_census/graph.yaml:38-61, 63-145). FR-895 already established the cited brief tail and its LLM-free validation boundary (feature-requests/FR-895-census-synthesize-tail.md:32-43, 151-169; examples/demos/corpus_census/adapters/census_brief.py:74-94, 108-142).

The Azure boundary is correctly elevated to a compliance constraint. The existing graph defaults to Anthropic and both LLM nodes pin Anthropic today (examples/demos/corpus_census/graph.yaml:10-13, 84-100, 113-123), while FR-899 requires every LLM node in the repo-census invocation to pin `provider: azure` (feature-requests/FR-899-org-repo-census-azure.md:80-90). A sibling graph variant is narrower than a framework-wide provider override, matching the FR's rejected alternative at feature-requests/FR-899-org-repo-census-azure.md:134.

Strategic classification: **Contrib/example**. This is not a new framework primitive because FR-892 and FR-895 already provide the core abstraction; it is a new concrete census vertical with one named consumer and generic `gh` adapters. It is not merely documentation because the existing abstraction lacks GitHub-org discovery/extraction, repo-specific ledger fields, and Azure-pinned demo wiring.

## Required revisions

### R-1: Replace the self-conditional research field with a committed or substantively equivalent research record

Revise the `**Research:**` field so it no longer says "run `scripts/research.sh` sole route before Judgement if the Judge requires the promoted artifact" (feature-requests/FR-899-org-repo-census-azure.md:9). The local judge doctrine is not optional: newly created FRs need a committed research record or equivalent committed dispositioned alternatives table, and the Judge checks for 4-6 genuine solution classes, precedent lines, preserved disagreement, and the `is_this_a_graph` answer (.github/skills/judge-fr/doctrine.md:118-130). Fold a research record into the FR by either promoting `feature-requests/FR-899.research.md` or expanding the in-body Alternatives table to meet that substance bar. The revised record must include precedent/evidence lines for each class, preserve any dissent rather than only listing rejected options, and state the `is_this_a_graph` answer for the chosen path.

### R-2: Freeze the repo-specific reducer and ledger surface

The FR says only to add `gh` adapters next to existing corpus adapters (feature-requests/FR-899-org-repo-census-azure.md:48-64), but its target ledger requires `name`, `purpose`, `persons`, `activity`, and evidence citations (feature-requests/FR-899-org-repo-census-azure.md:38-42, 118-122). The existing reducer writes `item_ref`, `judgement`, `confidence`, `evidence_span`, `model`, `prompt_version`, `abstained`, `abstain_reason`, and `disagreement` (examples/demos/corpus_census/tools.py:23-35, 117-149). Revise the FR to name the exact repo-census code surface that transforms map findings plus extracted GitHub metadata into the repo ledger. It must specify the Pydantic row model, required columns, rejection rules, and artifact paths for both `.md` and `.jsonl`. Do not leave this as "adapters only"; activity/persons computation is a reducer responsibility.

### R-3: Add an Azure preflight before discovery and extraction

The current execution order is `discover -> extract_items -> judge_items -> reduce_ledger -> prepare_brief_input -> synthesize -> render_brief` (examples/demos/corpus_census/graph.yaml:129-145). LLM provider creation happens inside LLM node execution, after node variables resolve (yamlgraph/node_factory/llm_nodes.py:331-351), and Azure env validation happens in `_create_azure_llm` only when the Azure LLM is constructed (yamlgraph/utils/llm_providers.py:143-184). Therefore the FR's claim that existing `llm_factory` behavior makes missing `AZURE_AI_ENDPOINT` abort before any discover call is false (feature-requests/FR-899-org-repo-census-azure.md:91-92). Add an explicit first node or wrapper preflight that checks `AZURE_AI_ENDPOINT`, `AZURE_AI_API_KEY`, and `AZURE_MODEL` before `gh_org_discover` can run; tests must assert neither discovery, extraction, nor LLM execution is invoked when that preflight fails.

### R-4: Define the `gh` adapter contract and bounds mechanically

Replace the adapter pseudocode with a mechanically testable contract. The existing adapters use fixed subprocess argument lists, bounds, and loud empty-result errors (examples/demos/corpus_census/adapters/corpus_adapters.py:15-24, 30-38, 58-78). The repo-census adapters must likewise freeze: `source` grammar (`<org>` and optional positive integer limit), maximum repositories, maximum README bytes/chars, contributor count, timeout behavior, `gh auth`/permission failure behavior, empty org behavior, fork/archive inclusion or exclusion, item identity format, and exact extraction bundle schema. The test surface must include malformed `source`, empty result, missing `gh` auth or failing `gh` command, and bounds enforcement.

### R-5: Make public-repo data locality checkable

The public-repo boundary is essential and well named: FR-899 requires zero customer identifiers committed here (feature-requests/FR-899-org-repo-census-azure.md:94-100, 123), and FR-874's rejection records the cost of failing to verify public visibility before committing customer-sensitive material (feature-requests/FR-874-cross-device-agent-memory-sync.md:9-16, 24-30). Revise the acceptance criteria so the committed demo uses a named public-safe fixture or public org, and so the committed artifacts are mechanically audited for the demo source string and output paths. Human PR review may remain a condition for customer-identifier absence, but it cannot be the only witness for the committed demo contract.

### R-6: Freeze graph-authoring and non-authorized framework scope

The FR correctly chooses a sibling `examples/demos/repo_census/graph.yaml` because the current graph pins Anthropic at defaults and node level (feature-requests/FR-899-org-repo-census-azure.md:85-90; examples/demos/corpus_census/graph.yaml:10-13, 90-93, 113-117). Revise the scope to state the exact graph and prompt artifacts that may be created through `scripts/author.sh`, and state that a generic provider override mechanism, graph inheritance/template system, or changes to `corpus_census` provider defaults are not authorized. Repo doctrine requires every `graph.yaml` or `prompts/*.yaml` creation/material modification to go through `scripts/author.sh` and be verified by `tmp/draft-authoring-report.md`, not by exit code alone (.github/copilot-instructions.md:15).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `examples/demos/corpus_census/adapters/corpus_adapters.py` or a named adjacent module containing `gh_org_discover`, `gh_repo_extract`, and any repo-census reducer/preflight helpers required by R-2/R-3 |
| D-2 | `examples/demos/corpus_census/adapters/gh-org-discover.tool.yaml` and `examples/demos/corpus_census/adapters/gh-repo-extract.tool.yaml` or equivalent exact tool-manifest paths named in the revised FR |
| D-3 | `examples/demos/repo_census/graph.yaml` and its prompt files, authored through `scripts/author.sh`, with all LLM nodes explicitly pinned to `provider: azure` and no non-Azure fallback |
| D-4 | Repo-census ledger artifacts: markdown and JSONL with frozen repo row schema, deterministic activity/persons fields, and citation-compatible purpose/evidence fields |
| D-5 | Repo-census brief using the existing FR-895 citation boundary over the repo ledger |
| D-6 | Tests for adapter bounds/failures, reducer schema/rejection, Azure preflight-before-discovery, provider pinning, no LLM-owned activity/persons, and public-safe committed demo artifacts |
| D-7 | Public-org demo output log and docs/README invocation updates for repo census |
| D-8 | Changelog fragment, valid REQ/CAP wiring as needed, FR implementation-status update, and diary reflection |

Not authorized: a generic provider override CLI flag; graph template inheritance or code generation; changes to `corpus_census` Anthropic defaults for existing demos; asking the LLM to compute activity, persons, counts, percentages, repository inclusion, or data-safety decisions; committing customer org names, customer contributor identities, customer ledgers, or customer briefs; changes to hooks, CI, judge/review doctrine, or Chaplain runtime behavior; migration of unrelated census demos.

## Revised acceptance criteria

- [ ] AC-01: The FR has a committed or in-body research record satisfying the FR-890 judge gate: 4-6 genuine solution classes, precedent/evidence line per class, preserved disagreement, and an explicit `is_this_a_graph` answer for the chosen path.
- [ ] AC-02: `gh_org_discover` and `gh_repo_extract` are implemented behind `.tool.yaml` manifests using fixed `gh` argument vectors; tests cover source parsing, max-repo bound, README/content bound, contributor bound, missing auth or failing `gh`, empty org, and malformed item refs.
- [ ] AC-03: A repo-census preflight runs before discovery and fails loudly when `AZURE_AI_ENDPOINT`, `AZURE_AI_API_KEY`, or `AZURE_MODEL` is missing; tests assert discovery, extraction, and LLM execution are not called on preflight failure.
- [ ] AC-04: `examples/demos/repo_census/graph.yaml` and prompts are authored via `scripts/author.sh`; `tmp/draft-authoring-report.md` records graph lint and smoke evidence for the repo-census graph.
- [ ] AC-05: Every repo-census LLM node explicitly carries `provider: azure`, an Azure model/deployment from `AZURE_MODEL`, and no `fallback_provider`; a configuration test fails if any LLM node resolves to a non-Azure provider.
- [ ] AC-06: The map prompt asks only for one-sentence repository purpose from the evidence bundle; a prompt/input test proves the LLM is not instructed to compute activity, persons, counts, percentages, or ownership.
- [ ] AC-07: The repo-census reducer is LLM-free and validates a Pydantic row schema with at least `name`, `purpose`, `persons`, `activity`, `evidence_citation`, `model`, `prompt_version`, and source identity/provenance; tests reject missing findings, duplicate findings, malformed activity, missing persons, empty purpose, and dangling citations.
- [ ] AC-08: `activity` is computed deterministically as `archived` when the API marks the repo archived, `active` when `pushed_at` is within the configured day threshold, and `dormant` otherwise; boundary-date tests cover all three outcomes.
- [ ] AC-09: `persons` is copied verbatim from the top contributor API data, bounded to the configured limit; tests prove no LLM output can add, remove, or reorder persons.
- [ ] AC-10: The corp brief is rendered through the existing FR-895 citation boundary over the repo ledger; tests cover accepted citations and rejected fabricated repo citations.
- [ ] AC-11: The committed demo run uses only a named public-safe org or fixture; `demo-output.log`, committed fixtures, graph vars in docs, ledger proofs, and brief proofs contain no customer org string or customer output paths. Human PR review of customer-identifier absence is recorded in addition to the mechanical fixture/source check.
- [ ] AC-12: Changelog fragment, valid REQ/CAP wiring as needed, `@pytest.mark.req(...)` on new tests, FR status/update notes, and diary reflection are included.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority is inactive until R-1 through R-6 are folded into FR-899. | GATE |
| C-2 | Azure configuration preflight must run before any `gh` discovery/extraction or LLM execution; relying on LLM factory construction after discovery is forbidden. | GATE |
| C-3 | All graph and prompt artifacts created or materially modified for repo census must go through `scripts/author.sh`; `tmp/draft-authoring-report.md` is the evidence artifact. | GATE |
| C-4 | The only authorized LLM role is purpose judgement and final cited synthesis; activity, persons, counts, thresholds, citations, schema validation, and public-safety checks are code-owned. | GATE |
| C-5 | No customer identifiers, customer contributor identities, customer ledgers, or customer briefs may be committed to this public repository. | GATE |
| C-6 | If implementation requires a generic provider override, graph inheritance/template mechanism, or changes to existing `corpus_census` provider defaults, enforcement must stop and a separate FR must enter the pipeline. | GATE |
| C-7 | Any changes to hooks, CI, judge/review doctrine, or other enforcement infrastructure require explicit human review before merge. | GATE |

Authority granted: after the required revisions are folded into FR-899, the enforcer may implement the Azure-pinned repo-census contrib/example, its `gh` adapters, repo-specific deterministic reducer/preflight, public-safe demo, and citation-checked brief within the frozen scope above.
