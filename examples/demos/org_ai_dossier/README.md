# Org AI dossier

FR-1029 provides an organisation AI-use dossier graph that mirrors the FR-892
corpus census slot pipeline, the FR-899 Azure-pinned repository census, and the
FR-962 consent warning discipline. It inventories active GitHub repositories
and active Jira projects, classifies one unit per LLM call, reduces the ledgers
in Python, and writes bounded dossier artifacts atomically.

> **Use only on your own footprint or with the subject's explicit written
> permission.** Profiling another person's authored PRs — even from public
> repositories — may implicate labour law, data-protection law (GDPR
> Art. 4, 6, 22 in the EU), platform terms of service, and employer
> policies. Public availability of the source PR does not by itself
> license aggregated behavioural analysis of the author. The corp-run
> path additionally requires that the subject's employer has authorised
> the LLM analysis under the applicable data-processing agreement. This
> tool ships no consent mechanism; the operator is the accountable
> controller.

The operator running this graph is the accountable controller; `persons_llm` is
required with no default and `true` requires `persons_llm_ack`.

## Structure

| Path | Purpose |
| --- | --- |
| `graph.yaml` | Two-source GitHub/Jira census topology with Azure-pinned LLM nodes and slot-bound collectors. |
| `prompts/classify_repo_ai.yaml` | One-repository AI-use classifier. |
| `prompts/classify_jira_ai.yaml` | One-Jira-project AI-use classifier. |
| `prompts/summarize_person.yaml` | Optional source-local person footprint summarizer. |
| `prompts/synthesize_findings.yaml` | Bounded dossier findings synthesis. |
| `prompts/synthesize_onepager.yaml` | Exactly three manager-facing onepager claims. |
| `tools.py` | Graph-facing coverage, canary, reduce, prepare, and render functions (module-loaded). |
| `preflight.py` | Self-contained live/smoke preflight (path-loaded by the `preflight` slot manifests; ceilings mirrored from `models.py` and asserted equal by tests). |
| `models.py`, `reduce.py`, `aggregates.py`, `render.py`, `docs.py`, `canaries.py` | Typed contracts, LLM-free reduction, artifact rendering, markdown/ledger helpers, and hidden semantic canary bundles. |
| `preflight.tool.yaml`, `smoke_preflight.tool.yaml` | Live and smoke preflight manifests for the `preflight` slot. |
| `../corpus_census/adapters/*.tool.yaml` | Runtime manifests for GitHub and Jira discovery, extraction, search, coverage, and fixtures. |
| `../corpus_census/adapters/fixtures/jira/` | Committed Jira smoke fixture corpus. |

## Smoke

```bash
yamlgraph graph run examples/demos/org_ai_dossier/graph.yaml --tool preflight=examples/demos/org_ai_dossier/smoke_preflight.tool.yaml --tool gh_discover=examples/demos/corpus_census/adapters/gh-org-active-discover.tool.yaml --tool gh_extract=examples/demos/corpus_census/adapters/gh-repo-ai-extract.tool.yaml --tool gh_search=examples/demos/corpus_census/adapters/gh-org-code-search.tool.yaml --tool jira_coverage=examples/demos/corpus_census/adapters/jira-fixture-coverage.tool.yaml --tool jira_discover=examples/demos/corpus_census/adapters/jira-fixture-discover.tool.yaml --tool jira_extract=examples/demos/corpus_census/adapters/jira-fixture-extract.tool.yaml --var org=sheikkinen --var visibility=public --var window_days=90 --var top_persons=5 --var persons_llm=false --var persons_llm_ack= --var out_dir=tmp/org-ai-dossier-smoke/authoring --full
```

## Live command shape

```bash
yamlgraph graph run examples/demos/org_ai_dossier/graph.yaml --tool preflight=examples/demos/org_ai_dossier/preflight.tool.yaml --tool gh_discover=examples/demos/corpus_census/adapters/gh-org-active-discover.tool.yaml --tool gh_extract=examples/demos/corpus_census/adapters/gh-repo-ai-extract.tool.yaml --tool gh_search=examples/demos/corpus_census/adapters/gh-org-code-search.tool.yaml --tool jira_coverage=examples/demos/corpus_census/adapters/jira-coverage.tool.yaml --tool jira_discover=examples/demos/corpus_census/adapters/jira-active-discover.tool.yaml --tool jira_extract=examples/demos/corpus_census/adapters/jira-project-extract.tool.yaml --var org=<org> --var visibility=public,private,internal --var window_days=90 --var top_persons=20 --var persons_llm=false --var persons_llm_ack= --var out_dir=research/org-ai-dossier/<org>-90d --full
```

## Outputs

The live output root is gitignored `research/org-ai-dossier/`, and preflight
rejects anything else. The renderer writes `onepager.md` (800 words or less),
`dossier.md`, `repos.md`, `jira.md`, `ledgers/*.jsonl`, `ledgers/*.csv`, and
`run.json`. Every share prints `n of <denominator>=<value>`.

## Persons

Person rows are two source-local rankings only: `github:<login>` and
`jira:<accountId>`. They are never joined across systems.
