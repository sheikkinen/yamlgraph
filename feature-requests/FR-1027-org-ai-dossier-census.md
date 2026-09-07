# Feature Request: Org AI Dossier — GitHub + Jira Census with One-Page Overview

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 3 days
**Requested:** 2026-09-07
**First consumer / first event:** the operator, asked by management "which of
our projects are active, which use AI, with what tools, and who carries them"
— answered by one command whose output lands in gitignored `research/`, and
re-answered next quarter by re-running it
**Research:** brief committed at
[research-briefs/org-ai-dossier.md](research-briefs/org-ai-dossier.md);
`scripts/research.sh` run 2026-09-07 failed before any persona call — the
Anthropic key in `.env` returns 401 on `/v1/models` (operator-side; key
rotation needed). `FR-1027.research.md` is promoted once the route runs;
until then this FR carries no authority (FR-890). Sizing probes and the
Copilot-API / code-search alternative probes are recorded in gitignored
`research/org-ai-dossier/sizing.md`.
**Prior art:** FR-892 (corpus_census: injected discover/extract slots, LLM-free
reduce, one synthesis tail) — FOUNDATION, reused unchanged. FR-899
(repo_census: org repos → purpose/persons/activity on pinned Azure, customer
org as runtime var) — DISTINCT: no AI-usage signal, no Jira source, no
cross-org person rank, no dossier/onepager shape; its evidence bundle is
frozen by judgement, so this FR is a SIBLING (FR-962 pattern), not an
extension. FR-962 (person_profile_census: one person's authored PRs, consent
warning R-1..R-5) — OVERLAPPING TERRITORY on persons; dispositioned in
§ Persons: this FR ranks by mechanical footprint and bounds the LLM to a
professional-contribution summary over work-system facts, inheriting the
FR-962 warning verbatim. FR-896 (own-footprint pattern/model census) —
distinct subject (author's repos, public artifact). FR-874 (REJECTED memory
transport into this public repo) — the reason every output is gitignored.

## Summary

One graph, `examples/demos/org_ai_dossier/`, composes the corpus_census
pipeline three times — GitHub active repositories, Jira active projects, and
the persons derived from both — with LLM-free reducers for activity,
ranking, AI-tool inventory, and coverage denominators, then spends two Azure
synthesis calls on a full dossier and a one-page overview. Every LLM node
pins `provider: azure`. Org name, Jira site, activity window, and output
directory are runtime inputs; nothing org-specific is committed.

## Value Statement

The operator answers a recurring management question with a cited,
repeatable, corp-endpoint-only dossier instead of a session of `gh`/JQL
spelunking whose result dies with the transcript.

## Problem

See the brief. In short: the org has hundreds of repositories (majority
private) and dozens of Jira projects; no artifact says which are alive, which
use AI in the product or in the dev tooling, which AI tools/providers appear,
or who carries the work. `repo_census` (FR-899) lacks the AI signal and Jira;
`person_profile_census` (FR-962) profiles one person, not an org; nothing
reads Jira — the only Jira access on the machine is the editor's MCP server,
which a graph cannot call. Hand-written dossiers
(`research/shared-ai-capabilities/findings.md`) cover one repo per session.

## Ideal Result

```bash
yamlgraph graph run examples/demos/org_ai_dossier/graph.yaml \
  --var org="<org>" --var window_days=90 --var top_persons=30 \
  --var out_dir=research/org-ai-dossier/2026-09-07 --full
```

produces, under gitignored `out_dir`:

| Artifact | Producer | Content |
| --- | --- | --- |
| `onepager.md` | 1 Azure synthesis call over code-reduced tables | ≤1 page: coverage denominators, active-project counts (GitHub / Jira), AI-using share WITH denominator, top AI tools, top persons, three findings, method + date + caveats |
| `dossier.md` | code-rendered tables + 1 Azure synthesis call for the findings section | coverage, findings, AI-tool inventory (tool → kind → repos/projects → evidence), per-person section (footprint + 2–3 sentence contribution summary) |
| `repos.md`, `jira.md` | code-rendered from ledgers | per-repo section (purpose, activity, AI usage, tools, evidence paths, top contributors); per-Jira-project section (purpose, activity counts, AI usage, tools, evidence issue keys, top assignees) |
| `ledgers/repos.jsonl`, `ledgers/jira.jsonl`, `ledgers/persons.jsonl`, `ledgers/ai_tools.csv` | LLM-free reducers | deterministic, one row per unit, every LLM claim carries its evidence citation |
| `run.json` | code | org, window, timestamps, git SHA of the graph, coverage: visible-repo count vs org-API count, archived, active; Jira visible vs active; Azure deployment name; token totals |

Zero LLM calls leave the pinned Azure deployment; zero org identifiers enter
this repo.

## Proposed Solution

### Pipeline (cheap-map / code-reduce / one-judgement-tail)

```text
preflight ─► coverage ─► gh_discover ──► map gh_extract ──► map classify_repo ─┐
                    └──► jira_discover ► map jira_extract ► map classify_jira ─┤
                                                                               ▼
                                                  reduce (code): activity, AI-tool
                                                  inventory, claim reconciliation,
                                                  person footprint + top-N rank
                                                                               │
                                          map summarize_person (top-N, Azure) ◄┘
                                                                               │
                        render_dossier (code tables + 1 Azure findings call) ◄─┘
                        render_onepager (1 Azure call)  ─► out_dir
```

Authored via `scripts/author.sh` (FR-767 sole route). The graph is a sibling
of `repo_census/graph.yaml`: same preflight-first shape, `provider: azure`
on every `type: llm` node, `max_items` caps on every map.

### Adapters (FR-892 slot contract: state-dict in, `list[str]`/`str` out)

New module `examples/demos/corpus_census/adapters/gh_ai_adapters.py`
(`corpus_adapters.py` is at 364 lines — the 400-line rule forbids growing it):

- **`gh_org_active_discover(state)`** — `source` = `<org>:<window_days>`;
  fixed argv `gh repo list <org> --limit 1000 --json
  name,pushedAt,isArchived`; returns non-archived repos with `pushedAt`
  inside the window. Malformed source → `ValueError`.
- **`gh_repo_ai_extract(state)`** — FR-899 bundle (metadata, README head,
  contributors) PLUS deterministic AI-signal probes, each a fixed `gh api`
  call, bundle capped at `MAX_CHARS`:
  - one `git/trees/HEAD?recursive=1` call (truncated flag honoured) →
    presence of agent-instruction paths (`.github/copilot-instructions.md`,
    `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `.cursor/`, `.claude/`,
    `.github/skills/`, `.github/agents/`) and the list of dependency
    manifests (`package.json`, `requirements*.txt`, `pyproject.toml`,
    `*.csproj`, `Directory.Packages.props`, `go.mod`, `composer.json`);
  - ≤6 manifest fetches, each grepped in code against a fixed AI-package
    vocabulary (`openai`, `@azure/openai`, `Azure.AI.*`, `anthropic`,
    `langchain*`, `langgraph`, `llama-index`, `semantic-kernel`,
    `Microsoft.SemanticKernel`, `ai` (Vercel), `transformers`, `ollama`,
    `mistralai`, `google-generativeai`, `cohere`, `@anthropic-ai/*`) —
    matched lines recorded with path;
  - ≤5 workflow files grepped for AI actions (`copilot`, `openai`,
    `claude`, `ai-inference`);
  - `pulls?state=all&per_page=30` → author logins with bot flags
    (`copilot-swe-agent[bot]`, `Copilot`, `dependabot[bot]`, `renovate`).
- **`gh_org_code_search(state)`** — org-wide `gh search code --owner <org>
  <keyword>` for a fixed keyword list (English package/agent terms plus
  Finnish `tekoäly`, `kielimalli`, `tekoälyavustaja`); ONE call per keyword (code-search
  limit is 10/min, so the node sleeps to budget); returns `repo → keywords
  hit`. Probe 2026-09-07 confirmed this works on the private org and
  surfaces repos the per-repo manifest grep can miss (AI usage in source,
  not in a manifest). Result is a discover-side signal merged into the repo
  ledger by code; `--limit 100` cap per keyword is recorded in `run.json`.

New module `examples/demos/corpus_census/adapters/jira_adapters.py`, REST v3
with basic auth from `JIRA_URL` / `JIRA_USERNAME` / `JIRA_API_TOKEN` (the
same names the editor's `mcp-atlassian` server already uses; the operator
exports them). `urllib.request`, fixed URLs, no shell, `timeout` on every
call:

- **`jira_active_discover(state)`** — `GET /rest/api/3/project/search`
  paginated (≤ `MAX_PAGES`); per project one
  `POST /rest/api/3/search/approximate-count` with `project = <KEY> AND
  updated >= -<window>d`; returns keys with count > 0. Dormant keys are
  written to the coverage record, not silently dropped.
- **`jira_project_extract(state)`** — project meta (name, type, lead
  displayName), approximate counts (updated-in-window, created-in-window),
  ≤30 most recently updated issues (`key`, `summary`, `issuetype`,
  `status`, `assignee.displayName`, `reporter.displayName`, first 300 chars
  of description), assignee/reporter frequency top-10, and an AI-keyword
  count via `text ~ "AI OR LLM OR GPT OR Copilot OR tekoäly OR kielimalli"`
  (Finnish terms included — the org's issues are bilingual). Bundle capped.

Smoke route: a committed `jira_fixture` adapter returns a public-safe fixture
bundle so `demo-output.log` can be produced without credentials (FR-962
`smoke_preflight.tool.yaml` pattern). The committed `graph.yaml` binds the
live adapters; the fixture is bound only by the README smoke command.

### LLM nodes (Azure, temperature 0, schema-validated, one judgement each)

- `classify_repo_ai.yaml` — input: the extract bundle. Output schema:
  `purpose` (one sentence), `ai_usage ∈ {none, product, dev_tooling, both,
  unclear}`, `ai_tools: [{name, kind ∈ {provider, framework, coding_agent,
  model}, evidence_path}]`, `rationale`. **Boundary:** code drops any
  `ai_tools` entry whose `evidence_path` is not a path/line present in the
  bundle, and demotes `ai_usage` to `unclear` when no entry survives
  (`two_strike_split`: the model's output is a claim reconciled against the
  source).
- `classify_jira_ai.yaml` — same shape; `evidence` is an issue key that must
  appear in the bundle.
- `summarize_person.yaml` — input: the person's footprint row ONLY (repos +
  their purpose sentences, PR count in window, Jira projects + counts).
  Output: `summary` (2–3 sentences, professional contribution). Bounded:
  "Do NOT infer seniority, performance, workload, sentiment, or intent; do
  NOT mention anything not in the footprint." Code rejects summaries that
  name a repo or project absent from the footprint.
- `render_findings.yaml` (dossier findings section) and `render_onepager.yaml`
  — the two synthesis calls, over code-reduced tables with citations
  (FR-895 citation boundary: every cited row must exist in a ledger).

### Reducers (code, LLM-free, deterministic)

- Activity: `active` if `pushed_at`/`updated` within window (the discover
  already filtered; the reducer records the timestamp used).
- AI-tool inventory: aggregate surviving `ai_tools` across both ledgers →
  `ai_tools.csv` (tool, kind, n_repos, n_jira_projects, evidence list).
- Persons: GitHub side — PR authors (bots excluded) and contributors across
  active repos, weighted by in-window PR count; Jira side — assignee +
  reporter frequency across active projects. **No cross-system identity
  join** (login ≠ displayName is not mechanically decidable); the persons
  ledger holds two ranked lists and a `same_person` column that is filled
  only on exact e-mail/displayName equality when GitHub exposes it, else
  `unknown`. Top-N (`top_persons`, default 30) from the union by rank.
- Coverage: `gh api /orgs/<org>` (`public_repos + total_private_repos`) vs
  listed count; archived; active; Jira visible vs active. Written to
  `run.json` and printed at the top of both rendered documents.

### Persons — disposition against FR-962

FR-962 admitted person profiling only under an explicit consent warning, a
visibility preflight, and outputs never committed. This FR re-enters that
territory at org scale, so it inherits all three and narrows further: the
LLM sees only work-system facts already aggregated by code; the output
class is a contribution summary, not a behavioural profile; the FR-962
warning block is copied verbatim into the demo README; the operator is the
accountable controller. Whether org-scale summaries of colleagues are
admissible under the employer's policy is an **operator/legal decision
recorded in `run.json` (`persons_llm: true|false`)** — with `false` the
person stage is mechanical only (ranked table, no prose). Default is `true`
per the operator's 2026-09-07 decision; the judge may overrule.

## Acceptance Criteria

- [ ] `examples/demos/org_ai_dossier/graph.yaml` lints; every `type: llm`
      node has `provider: azure`; every map has `max_items`.
- [ ] Preflight fails (before any GitHub/Jira fetch) when any of
      `AZURE_AI_ENDPOINT`, `AZURE_AI_API_KEY`, `AZURE_MODEL`, `gh auth
      status`, `JIRA_URL`, `JIRA_USERNAME`, `JIRA_API_TOKEN` is missing —
      unit test per variable.
- [ ] `gh_org_active_discover` filters archived and out-of-window repos;
      malformed source raises (unit, mocked `gh`).
- [ ] `gh_repo_ai_extract` bundle contains instruction-file presence,
      manifest AI hits with path, workflow AI hits, PR author bot flags;
      bundle ≤ `MAX_CHARS` (unit, mocked `gh`, fixture repo).
- [ ] `gh_org_code_search` budgets ≤10 calls/min and records the per-keyword
      cap (unit, mocked `gh` + clock).
- [ ] `jira_active_discover` paginates, counts via approximate-count, and
      returns only active keys; dormant keys reach the coverage record
      (unit, mocked HTTP).
- [ ] `jira_project_extract` bundle has meta, counts, ≤30 issues, top-10
      assignee/reporter, AI-keyword count; ≤ `MAX_CHARS` (unit, mocked HTTP).
- [ ] Claim reconciliation: an `ai_tools` entry with an `evidence_path` not
      in the bundle is dropped and `ai_usage` demotes to `unclear` when none
      survive (unit — RED first).
- [ ] Person summary boundary: a summary naming a repo/project outside the
      footprint is rejected (unit — RED first).
- [ ] Coverage denominators appear in `run.json`, `onepager.md` line 1–5,
      and the `dossier.md` / `repos.md` / `jira.md` headers; every percentage in the rendered documents is
      followed by `of <denominator>` (renderer unit test).
- [ ] Persons ledger has no cross-system join unless exact e-mail/displayName
      equality; `same_person` otherwise `unknown` (unit).
- [ ] `persons_llm=false` skips `summarize_person` and renders the mechanical
      table (unit on graph routing).
- [ ] Smoke against the public demo org (`sheikkinen`) with the
      `jira_fixture` adapter produces `demo-output.log`; committed output
      contains no private org identifier (grep gate in the demo test).
- [ ] Live run against the operator's org writes to `research/org-ai-dossier/
      <date>/`; `git status` shows nothing under `research/` (gitignore
      test).
- [ ] README carries the FR-962 warning block verbatim plus the
      `persons_llm` switch.
- [ ] `read_raw_output_first`: before any aggregate is trusted, 10 raw
      `classify_repo_ai` outputs and 5 `classify_jira_ai` outputs are read
      end-to-end and cited in this FR's implementation notes with one
      surprising detail each.
- [ ] Tests tagged `@pytest.mark.req("REQ-YG-670")`; `capabilities/CAP-266-
      org-ai-dossier.yaml`; `ARCHITECTURE.md` row; changelog fragment;
      `python scripts/req_coverage.py --strict` green. (IDs allocated at
      enforce; verify no race per repo memory.)
- [ ] `FR-1027.research.md` promoted from `scripts/research.sh` output and
      dispositioned here before Judge.

## Alternatives Considered (probed 2026-09-07 unless marked)

| Alternative | Probe / evidence | Verdict |
| --- | --- | --- |
| Hand-written dossier per repo (`research/shared-ai-capabilities/findings.md` precedent) | one repo took one session; active corpus is O(200) repos | Rejected — `impossibly_large_sequential_task`; the census is the affordable form |
| GitHub Copilot org metrics / seat API as the "who uses AI" answer | `gh api /orgs/<org>/copilot/billing` → 404, requires `admin:org` scope the operator lacks; would answer Copilot seats only, not product AI nor Jira | Rejected for now — recorded as an operator escalation (ask an org admin for a one-time export); complementary, not a substitute |
| Org-wide code search as the ONLY AI-signal discover (no per-repo extract) | `gh search code --owner <org> <kw>` works on the private org; five keywords returned 3–17 repos each; code-search limit 10/min; results capped at 100/keyword and indexed on default branch only | Partially adopted — it is one discover-side signal merged by code; alone it cannot say *purpose*, *activity*, *who*, or distinguish product vs dev-tooling use |
| Jira dev-panel API to join issues ↔ PRs ↔ repos mechanically | `jira_get_issues_development_info` exists but is per-issue; thousands of in-window issues → not within one run's budget | Deferred — correspondence is asserted only with both ledger rows cited, or marked operator input |
| Use the editor's Atlassian MCP server directly in a chat session | it is how the sizing probes were done; not callable from a graph; not repeatable; no ledger | Rejected as the route; its env var names are reused for the REST adapter |
| Extend `repo_census` (FR-899) in place with AI fields and a Jira slot | FR-899 evidence bundle and outputs are frozen by judgement and its PR is pending | Rejected — sibling graph (FR-962 precedent) keeps FR-899's contract intact |
| Provider: default/Copilot instead of pinned Azure | operator decision 2026-09-07: Azure | Rejected — corp data governance (FR-899) |
| Jira scope: all visible projects | operator decision 2026-09-07: active only | Rejected — dormant projects listed by key in coverage |

## Decisions (operator, 2026-09-07)

1. `persons_llm` default **`true`** — LLM contribution summaries on; FR-962
   warning block in README; operator is the accountable controller.
2. `gh_org_code_search` keyword list **includes Finnish terms** (`tekoäly`,
   `kielimalli`, `tekoälyavustaja`), mirroring the Jira JQL.
3. Rendered output is **split**: `dossier.md` (coverage, findings, AI-tool
   inventory, persons) + `repos.md` (per-repo sections) + `jira.md`
   (per-Jira-project sections). The Ideal Result table and AC below are
   read with this split.
4. Research route unblock: **run `scripts/research.sh` on another provider**
   (Azure/OpenAI) rather than wait for Anthropic key rotation — requires a
   provider override in the research route, tracked as a separate change.

## Related

- [FR-892](FR-892-corpus-census-pipeline-injected-adapters.md),
  [FR-899](FR-899-org-repo-census-azure.md),
  [FR-962](FR-962-person-profile-census-authored-prs.md), FR-874 (rejected)
- [examples/demos/repo_census/](../examples/demos/repo_census/),
  [examples/demos/person_profile_census/](../examples/demos/person_profile_census/),
  [examples/demos/corpus_census/adapters/](../examples/demos/corpus_census/adapters/)
- [reference/patterns/corpus-map-reduce.md](../reference/patterns/corpus-map-reduce.md)
- Gitignored: `research/org-ai-dossier/sizing.md` (probes, counts, cost order)
