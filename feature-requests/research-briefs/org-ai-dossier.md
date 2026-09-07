# Problem brief: no repeatable answer to "which of our org's projects are active, which use AI, with what tools, and who carries them"

**Prior art:** FR-892 (corpus_census pipeline, injected discover/extract
adapters, LLM-free reduce, one synthesis tail); FR-899 (org repository census
on the pinned Azure endpoint — purpose / persons / activity per repo, customer
org as runtime `--var`, outputs never committed); FR-962 (person-profile
census of authored PRs; consent/GDPR warning as the governing constraint);
FR-896 (cross-repo pattern/model census of the author's own footprint);
FR-890 (research sole route). `research/shared-ai-capabilities/findings.md`
and `research/mercury-census/findings.md` are gitignored research dossiers of
the shape this brief needs — both were hand-written, neither is repeatable.

## Problem statement

The operator is asked, recurrently, for an organisation-level picture that
no artifact currently provides: across the employer's GitHub organisation
(hundreds of repositories, majority private) and its Jira site (dozens of
projects), which projects are alive right now, which of them use AI — in
the product or in the development tooling — which AI tools and providers
appear, and which people carry the work. Today each of these questions is
answered by ad-hoc `gh` and JQL spelunking in a chat session, the result
lives in the session transcript, and the next request starts from zero.

Three sources hold the evidence and none of them is joined:

- GitHub: repository metadata, README, dependency manifests, agent
  instruction files (`copilot-instructions.md`, `CLAUDE.md`, `AGENTS.md`),
  workflow files, PR authorship (including bot authors such as Copilot
  coding agent and Dependabot), contributor lists.
- Jira: project list, per-project issue activity, assignee/reporter
  frequency, issue summaries mentioning AI work.
- The operator's head: which repo belongs to which Jira project, who the
  "key persons" are — tribal knowledge that leaves with the operator.

The existing `repo_census` (FR-899) answers *purpose / persons / activity*
per repository but has no AI-usage signal, no Jira source, no person-level
reduce, and no dossier-plus-onepager output shape. `person_profile_census`
(FR-962) profiles ONE person's authored PRs; it does not rank persons
across an org. Nothing reads Jira at all — no adapter exists, and the only
Jira access on the machine is an editor-embedded MCP server that a graph
cannot call.

The deliverable is a research dossier, not a product feature: a full
per-project / per-person / per-tool record with citations, plus a one-page
overview, written into the gitignored `research/` folder and refreshed by
re-running one command.

## Classification

judgement/analysis/generation

## Constraints

- **Data governance.** Repository contents, issue text, and person
  identities are corp data. Every LLM call must go to the corp-approved
  pinned Azure deployment (FR-899 precedent: `provider: azure` on every
  LLM node, preflight blocks unconfigured runs before any fetch). No call
  may reach the default provider.
- **Public repo, private facts.** This repository is public. The graph,
  adapters, prompts, and FR are committed and must be generic (org and
  Jira site are runtime `--var`/env input); every output, ledger, log, and
  sizing number lands in gitignored `research/` and is never committed
  (FR-874 rollback is precedent for what happens otherwise).
- **Person profiling is legally weighted.** FR-962's warning applies:
  aggregated behavioural analysis of colleagues implicates GDPR Art. 4/6/22,
  employer policy, and platform ToS. Person output is bounded to
  work-system facts (which repos, how many PRs, which Jira projects) plus a
  short professional-contribution summary derived ONLY from that evidence;
  no performance, sentiment, or behavioural inference. The operator is the
  accountable controller; the artifact stays local.
- **Coverage must be stated, not implied.** The token sees a subset of the
  org's private repos (probe: org API count exceeds listable count by
  roughly a quarter). Any percentage in the dossier must name its
  denominator. A dossier that says "N% of projects use AI" over a silent
  subset is a plausible wrong answer.
- **AI-usage is a claim reconciled against evidence.** The classification
  "uses AI" must cite the evidence path (manifest line, instruction file,
  workflow, bot author, Jira issue key); an LLM judgement with no citation
  is discarded at the boundary, not trusted (`two_strike_split`,
  `read_raw_output_first`).
- **Cheap-map / code-reduce / one-judgement-tail** (FR-892, mercury
  census): per-item LLM calls hold one judgement on the cheapest adequate
  Azure deployment; ranking, counting, joining, and activity classification
  are code; at most two synthesis calls (dossier, onepager).
- **Bounded fan-out.** Per-item evidence bundles are size-capped; API call
  budget per run must fit one hour of the `gh` core rate limit (5k) and
  Jira Cloud's enhanced-search pagination (no `total` field — count via
  the approximate-count endpoint or by exhausting pages with a cap).
- **Activity window is an input**, default 3 months (operator decision
  2026-09-07), applied identically to GitHub `pushed_at` and Jira `updated`.
- **Jira scope is active projects only** (operator decision 2026-09-07):
  projects with no issue updated inside the window are listed by key and
  excluded from the LLM stage.
- **Repo ↔ Jira correspondence is not knowable mechanically** without the
  dev-panel API per issue (too expensive) — any correspondence asserted in
  the dossier must cite both ledger rows or be marked as operator input.
- **Graph authoring sole route** (FR-767): any new `graph.yaml`/prompts go
  through `scripts/author.sh`; Jira adapters follow the FR-892 slot
  contract (state-dict in, `list[str]`/`str` out, fixed argv/URL, no shell).
- **Repeatability.** The same command on the same day must produce the
  same ledgers (LLM-free stages deterministic; LLM stages temperature 0,
  outputs schema-validated).

## Witnessed incidents

- 2026-09-04, `research/shared-ai-capabilities/findings.md`: a single-repo
  dossier hand-written from `gh repo clone --depth 200` + reading; took a
  session, covers one of the org's repositories, not repeatable, and its
  header had to carry an explicit "do not promote into tracked docs"
  warning because the FR-874 leak happened two weeks earlier.
- 2026-08-24, FR-874 rollback: memory notes containing customer hostnames
  and pilot findings were transported into this public repo and reverted
  the same day; nobody in author/judge/enforcer verified visibility. The
  brief's public/private boundary constraint exists because of this.
- 2026-08-28, FR-899: `repo_census` was built for a customer-org run on
  Azure and shipped with a customer-org-as-runtime-var boundary; its
  evidence bundle (metadata, README head, top-5 contributor logins) has no
  AI signal — the question "which repos use AI" cannot be asked of it.
- 2026-09-02, FR-962 judgement (R-1..R-5): person-profile census admitted
  only under an explicit consent warning and a visibility preflight; a
  cross-org "key persons" ranking re-enters that territory and must be
  dispositioned against it.
- 2026-09-07 (this session): sizing probes — `gh api /orgs/<org>` vs `gh
  repo list` disagree on repo count (token visibility subset); Jira Cloud
  JQL returns `total: -1`; the only Jira credential on the machine is the
  editor MCP server's env (`JIRA_URL`/`JIRA_USERNAME`/`JIRA_API_TOKEN`),
  no CLI installed. Numbers recorded in gitignored
  `research/org-ai-dossier/sizing.md`.
