# Feature Request: Org AI Dossier — GitHub + Jira Census with One-Page Overview

**Priority:** MEDIUM
**Type:** Feature
**Status:** Judged — APPROVED WITH REVISIONS 2026-09-07; R-1..R-8 folded
2026-09-07; R-6 human policy answer recorded (§ Decisions 5); see
[FR-1027-org-ai-dossier-census.judgement.md](FR-1027-org-ai-dossier-census.judgement.md)
**Effort:** 5 days (was 3; judgement R-2/R-3/R-7 added typed contracts,
ceilings, canaries, locality audit)
**Requested:** 2026-09-07
**First consumer / first event:** the operator, asked by management "which of
our projects are active, which use AI, with what tools, and who carries them"
— answered by one command whose output lands in gitignored `research/`, and
re-answered next quarter by re-running it
**Research:** [FR-1027.research.md](FR-1027.research.md) — brief
[research-briefs/org-ai-dossier.md](research-briefs/org-ai-dossier.md), run
2026-09-07T10:14Z on `azure/aaa-gpt-5.4-mini` via FR-1028 (`RESEARCH_PROVIDER`
/`RESEARCH_MODEL`), all five personas executed. Dispositioned in § Research
Disposition. Sizing probes and the Copilot-API / code-search alternative probes
are recorded in gitignored `research/org-ai-dossier/sizing.md` (outside the
judge's input closure by design).
**Prior art:** FR-892 (corpus_census: injected discover/extract slots, LLM-free
reduce, one synthesis tail) — FOUNDATION: this FR reuses the **pattern** and
the adapter slot contract, NOT the one-corpus `corpus_census/graph.yaml`
unchanged (judgement R-1). FR-899 (repo_census: org repos →
purpose/persons/activity on pinned Azure, customer org as runtime var) —
DISTINCT: no AI-usage signal, no Jira source, no dossier/onepager shape; its
evidence bundle is frozen by judgement, so this FR is a SIBLING (FR-962
pattern), not an extension. FR-962 (person_profile_census: one person's
authored PRs, consent warning R-1..R-5) — OVERLAPPING TERRITORY on persons;
dispositioned in § Persons: source-qualified identities only, two source-local
rankings, no cross-system join, LLM summary gated by a no-default policy
input, FR-962 warning verbatim in the README. FR-896 (own-footprint
pattern/model census) — distinct subject. FR-874 (REJECTED memory transport
into this public repo) — the reason every output is gitignored and
preflight-enforced (R-7). FR-1028 — the provider override that unblocked this
FR's research run; NOT used by this graph (every LLM node pins Azure).

## Summary

One new contrib/example graph, `examples/demos/org_ai_dossier/graph.yaml`,
built on the corpus-census PATTERN with its own frozen two-source topology:
GitHub active repositories and Jira active projects are discovered,
extracted, and classified (one Azure judgement per unit); typed LLM-free
reducers own activity, identities, coverage denominators, AI-tool inventory,
evidence reconciliation, and two source-local person rankings; an optional,
explicitly authorized Azure map writes per-person contribution summaries; two
bounded Azure synthesis judgements write the dossier findings and the
onepager. Every artifact lands under an enforced gitignored output root.
Nothing org-specific is committed.

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
  --tool preflight=examples/demos/org_ai_dossier/preflight.tool.yaml \
  --tool gh_discover=examples/demos/corpus_census/adapters/gh-org-active-discover.tool.yaml \
  --tool gh_extract=examples/demos/corpus_census/adapters/gh-repo-ai-extract.tool.yaml \
  --tool gh_search=examples/demos/corpus_census/adapters/gh-org-code-search.tool.yaml \
  --tool jira_discover=examples/demos/corpus_census/adapters/jira-active-discover.tool.yaml \
  --tool jira_extract=examples/demos/corpus_census/adapters/jira-project-extract.tool.yaml \
  --var org="<org>" --var visibility="private,internal,public" \
  --var window_days=90 --var top_persons=30 \
  --var persons_llm=true --var persons_llm_ack="I am the accountable controller; employer policy authorizes work-system-fact summaries" \
  --var out_dir=research/org-ai-dossier/2026-09-07 --full
```

produces, under `out_dir` (resolved beneath gitignored `research/org-ai-dossier/`):

| Artifact | Owner | Content |
| --- | --- | --- |
| `onepager.md` | 1 Azure synthesis judgement over code-reduced tables, code-verified | ≤ **800 words**: coverage block, GitHub/Jira active counts, AI-use shares each as `n of <denominator>` incl. `unclear`, top AI tools, two source-separated top-person lists, exactly three cited findings, method + date, caveats |
| `dossier.md` | code-rendered tables + 1 Azure synthesis judgement for the findings section | coverage block, findings, AI-tool inventory (tool → kind → repos/projects → evidence), person section (two rankings; summaries only when authorized) |
| `repos.md`, `jira.md` | code | per-unit sections from the ledgers |
| `ledgers/repos.jsonl`, `ledgers/jira.jsonl`, `ledgers/persons.jsonl`, `ledgers/ai_tools.csv` | typed reducers | one row per unit, frozen columns (§ Typed contracts), every model claim carries bundle-present evidence |
| `run.json` | code | `RunRecord` (§ Typed contracts): identities/hashes, estimated vs actual API and LLM call counts, provider/deployment, prompt versions, run id, timestamps, every truncation/partial-coverage flag. **No token totals** (R-3: no in-graph mechanism exists; not widened here) |

Zero LLM calls leave the pinned Azure deployment; zero org identifiers enter
this repo; no success-shaped artifact exists unless reconciliation and both
semantic canaries passed.

## Proposed Solution

### Frozen topology (R-1)

Sequential two-source pipeline, one graph, sibling of `repo_census`
(preflight-first, slots bound at invocation, `provider: azure` and
`temperature: 0` on every `type: llm` node, `on_error: fail` on every
mechanical node, `max_items` on every map).

```text
preflight ─► coverage_gh ─► gh_discover ─► map gh_extract ─► gh_search ─► map classify_repo
  ─► coverage_jira ─► jira_discover ─► map jira_extract ─► map classify_jira
  ─► reduce (typed; reconciliation + canaries; aborts before any artifact)
  ─► prepare_person_input ─┬─[persons_llm_active == true]─► map summarize_person ─┐
                           └─[persons_llm_active != true]──────────────────────────┤
  ─► prepare_findings_input ─► synthesize_findings ─► synthesize_onepager ─► render_artifacts ─► END
```

Frozen declarations:

- **Slots** (`slot: true`, FR-892): `preflight`, `gh_discover`, `gh_extract`,
  `gh_search`, `jira_discover`, `jira_extract`. Local python tools (module
  `examples.demos.org_ai_dossier.tools`): `coverage_gh`, `coverage_jira`,
  `reduce`, `prepare_person_input`, `prepare_findings_input`,
  `render_artifacts`.
- **State keys:** `org`, `visibility`, `window_days`, `top_persons`,
  `persons_llm`, `persons_llm_ack`, `out_dir`, `preflight_ok`,
  `coverage_gh` (dict), `repo_items` (list), `repo_bundles` (list,
  `sorted_add`), `search_hits` (dict), `repo_findings` (list, `sorted_add`),
  `coverage_jira` (dict), `jira_items` (list), `jira_bundles` (list,
  `sorted_add`), `jira_findings` (list, `sorted_add`), `reduced` (dict),
  `person_input` (list), `persons_llm_active` (bool), `person_summaries`
  (list, `sorted_add`), `findings_input` (dict), `findings_claims` (dict),
  `onepager_claims` (dict), `artifacts` (dict).
- **Edges:** linear as drawn; the single branch is two conditional edges out
  of `prepare_person_input` on `persons_llm_active` (FR-467 fixed the
  conditional→map fold); both paths join at `prepare_findings_input`.
- **Reducer order inside `reduce`:** (1) reconcile repo identities
  (discovered set == extracted set == classified set, each exactly once);
  (2) reconcile Jira identities likewise; (3) evidence reconciliation of
  every model claim (drop unsupported tools, demote `ai_usage` to
  `unclear`); (4) merge `search_hits` only onto frozen active-repo ids,
  everything else → caveats; (5) build source-qualified person footprints
  and the two rankings; (6) AI-tool inventory; (7) coverage record; (8)
  **canary check** (two families, § Canaries); (9) return `reduced`. Any
  failure in 1–8 raises → `on_error: fail` → no artifact.
- **Artifact-write boundary:** ONLY `render_artifacts` writes files, and only
  after `reduced` exists and both synthesis claims passed citation
  validation. It writes ledgers, `repos.md`, `jira.md`, `dossier.md`,
  `onepager.md`, `run.json` into a temp dir and renames it to `out_dir`
  atomically.
- **Live vs smoke bindings:** live binds `preflight.tool.yaml` (Azure +
  `gh auth status` + visibility policy + Jira env + `persons_llm` /
  `persons_llm_ack` + `out_dir` root) and the live gh/jira adapters. Smoke
  binds `smoke_preflight.tool.yaml` (Azure + `gh auth status` + visibility
  == `public` + `out_dir` root; **no Jira env check**) and
  `jira-fixture-discover.tool.yaml` / `jira-fixture-extract.tool.yaml`
  (committed public-safe fixture bundles); GitHub stays live against
  `sheikkinen` public repos. The committed `graph.yaml` binds nothing — the
  README carries both commands. Every mode enters through the same first
  node `preflight`.
- Authored via `scripts/author.sh` (FR-767 sole route); the authoring
  report is D-9 evidence.

### Adapters (FR-892 slot contract: state-dict in, `list[str]`/`str` out)

New module `examples/demos/corpus_census/adapters/gh_ai_adapters.py`
(`corpus_adapters.py` is at 364 lines). Fixed argv `gh` via `subprocess.run`
(no shell), `GH_TIMEOUT` per call.

- **`gh_org_active_discover(state)`** — `source` = `<org>:<window_days>`;
  `gh repo list <org> --limit <MAX_REPOS+1> --json
  name,pushedAt,isArchived,visibility`. If the listing returns
  `MAX_REPOS+1` rows → `OverflowError` (corpus exceeds ceiling; no LLM
  spend). Filters: `visibility ∈ state.visibility` (else `ValueError`
  naming the offending repo — visibility policy is enforced HERE, before
  extraction), `isArchived == false`, `pushedAt` within window (ISO parse;
  malformed → `ValueError`). Returns sorted unique `<org>/<name>`.
  Duplicates → `ValueError`.
- **`gh_repo_ai_extract(state)`** — `item` = `<org>/<name>`; emits
  `GitHubBundle` JSON (§ Typed contracts), capped `MAX_BUNDLE_CHARS`:
  `repos/{item}`, `readme` (head `MAX_README_CHARS`),
  `contributors?per_page=MAX_CONTRIBUTORS`, `git/trees/HEAD?recursive=1`
  (`truncated` flag copied into the bundle), ≤ `MAX_MANIFESTS` manifest
  fetches from the fixed path list (`package.json`, `requirements*.txt`,
  `pyproject.toml`, `*.csproj`, `Directory.Packages.props`, `go.mod`,
  `composer.json`) grepped in code against the fixed AI-package vocabulary
  (`openai`, `@azure/openai`, `Azure.AI.`, `anthropic`, `@anthropic-ai/`,
  `langchain`, `langgraph`, `llama-index`, `llama_index`, `semantic-kernel`,
  `Microsoft.SemanticKernel`, `"ai"` (Vercel), `transformers`, `ollama`,
  `mistralai`, `google-generativeai`, `cohere`) — hits recorded as
  `{path, line}`; ≤ `MAX_WORKFLOWS` workflow files grepped for `copilot`,
  `openai`, `claude`, `ai-inference`; instruction-file presence from the
  tree (`.github/copilot-instructions.md`, `CLAUDE.md`, `AGENTS.md`,
  `.cursorrules`, `.cursor/`, `.claude/`, `.github/skills/`,
  `.github/agents/`); `pulls?state=all&per_page=MAX_PRS&sort=updated` →
  in-window PR authors with bot flag (`[bot]` suffix, `Copilot`,
  `copilot-swe-agent`, `dependabot`, `renovate`). Non-zero `gh` exit on the
  metadata call → raise; on optional calls (readme, manifest) → typed
  `absent` marker, never a silent skip.
- **`gh_org_code_search(state)`** — one `gh search code --owner <org>
  <keyword> --limit MAX_SEARCH_RESULTS --json repository` per keyword in the
  frozen list (`openai`, `anthropic`, `langchain`, `Azure.AI`,
  `semantic-kernel`, `copilot-instructions`, `CLAUDE.md`, `AGENTS.md`,
  `tekoäly`, `kielimalli`, `tekoälyavustaja`; `MAX_SEARCH_TERMS` = 12);
  sleeps to stay ≤ 10 calls/min; returns
  `{keyword: {repos: [...], capped: bool}}` where `capped` is true when the
  result count equals `MAX_SEARCH_RESULTS`. The reducer maps hits onto
  frozen active-repo ids; unknown / inactive / archived / non-listed repos
  and every `capped` keyword become `CoverageRecord.search_caveats`, never
  silent merges.

New module `examples/demos/corpus_census/adapters/jira_adapters.py` — REST v3
via `urllib.request`, basic auth from `JIRA_URL` / `JIRA_USERNAME` /
`JIRA_API_TOKEN`, fixed URL templates, `urllib.parse.quote` on every path
segment and JQL, `timeout=JIRA_TIMEOUT`, non-2xx → `RuntimeError(status,
url)`; 429 → one retry after `Retry-After`, then raise.

- **`jira_active_discover(state)`** — `source` = `<window_days>`;
  `GET /rest/api/3/project/search?startAt=…&maxResults=50` until `isLast`
  or `MAX_PROJECT_PAGES` (+1 page → `OverflowError`); per project one
  `POST /rest/api/3/search/approximate-count` with JQL built from validated
  parts: `project = "<KEY>" AND updated >= -<N>d` (`KEY` must match
  `^[A-Z][A-Z0-9_]+$`, `N` int). Returns sorted unique active keys; dormant
  keys are returned through the coverage tool (`coverage_jira` calls the
  same listing and records `visible`, `active`, `dormant`).
- **`jira_project_extract(state)`** — `item` = `<KEY>`; emits `JiraBundle`
  JSON capped `MAX_BUNDLE_CHARS`: `GET /rest/api/3/project/<KEY>` (name,
  projectTypeKey, lead.accountId, lead.displayName), approximate counts
  (updated-in-window, created-in-window), `POST /rest/api/3/search/jql`
  with `fields=summary,issuetype,status,assignee,reporter,description,updated`,
  `maxResults=MAX_ISSUES` (30), ordered by `updated DESC`; description is
  Atlassian Document Format → flattened text via a bounded walker (concat
  `text` nodes, `MAX_DESC_CHARS` = 300); assignee/reporter frequencies keyed
  by `accountId` with `displayName` label, top `MAX_PERSONS_PER_PROJECT`
  (10); AI-term count via approximate-count with JQL built from the frozen
  term list as `text ~ "<term>"` clauses joined by `OR` (terms: `AI`,
  `LLM`, `GPT`, `Copilot`, `tekoäly`, `kielimalli`).
- **`jira_fixture_discover` / `jira_fixture_extract`** — read committed
  `examples/demos/org_ai_dossier/fixtures/jira/*.json` (public-safe,
  synthetic). Smoke only.

Manifests (`*.tool.yaml`) per adapter as in FR-899/FR-962.

### Typed contracts (R-2) — Pydantic v2, `extra="forbid"`

| Model | Fields (type · owner · bound/nullability) |
| --- | --- |
| `GitHubBundle` | `id: str` (collector, `<org>/<name>`), `description: str\|None`, `pushed_at: datetime`, `archived: bool`, `visibility: Literal[public,private,internal]`, `language: str\|None`, `readme_head: str` (≤3000), `contributors: list[str]` (≤10 logins), `tree_truncated: bool`, `instruction_files: list[str]` (subset of frozen list), `manifest_hits: list[{path: str, line: str}]` (≤60), `workflow_hits: list[{path, line}]` (≤30), `pr_authors: list[{login: str, bot: bool, n: int}]` (≤30), `absent: list[str]` (optional calls that returned 404) |
| `JiraBundle` | `key: str` (regex), `name: str`, `project_type: str`, `lead: {account_id: str, display_name: str}\|None`, `updated_in_window: int`, `created_in_window: int`, `ai_term_count: int`, `issues: list[{key, summary, issuetype, status, assignee_id\|None, reporter_id\|None, description_head: str ≤300}]` (≤30), `assignees: list[{account_id, display_name, n}]` (≤10), `reporters: list[...]` (≤10) |
| `RepoAIRow` | `id` (collector), `activity: Literal[active]` (reducer — discover already filtered; timestamp kept as `pushed_at`), `purpose: str` (model), `ai_usage: Literal[none,product,dev_tooling,both,unclear]` (model → reducer may demote), `ai_tools: list[{name, kind: Literal[provider,framework,coding_agent,model], evidence_path: str}]` (model, each `evidence_path` ∈ bundle paths — reducer-verified), `search_keywords: list[str]` (reducer), `contributors: list[str]` (collector), `status: Literal[classified, map_failed]` (reducer; `map_failed` rows carry `purpose=""`, `ai_usage=unclear`, `ai_tools=[]`) |
| `JiraAIRow` | `key`, `activity: active`, `purpose`, `ai_usage`, `ai_tools: list[{name, kind, evidence_issue: str ∈ bundle issue keys}]`, `updated_in_window`, `ai_term_count`, `status` — same failure semantics |
| `PersonRow` | `id: str` (`github:<login>` \| `jira:<accountId>`; never both), `label: str` (login or display name), `source: Literal[github, jira]`, `repos: list[str]` (github only), `projects: list[str]` (jira only), `score: int` (github: Σ in-window PRs authored across active repos + 1 per active repo where contributor; jira: Σ assignee n + Σ reporter n across active projects), `rank: int` (within source), `summary: str\|None` (model; only when authorized) |
| `AIToolRow` | `name`, `kind`, `n_repos: int`, `n_projects: int`, `evidence: list[str]` (`<repo>:<path>` or `<KEY>:<issue>`) |
| `CoverageRecord` | GitHub: `api_total: int\|None` (`public_repos + total_private_repos`; `None` when unavailable — then no completeness percentage is rendered), `listed: int`, `archived: int`, `out_of_window: int`, `visibility_rejected: int`, `active: int`, `extracted: int`, `classified: int`, `unclear: int`, `map_failed: int`, `tree_truncated: int`, `search_caveats: list[str]`; Jira: `visible: int`, `active: int`, `dormant: int`, `extracted`, `classified`, `unclear`, `map_failed`, `page_cap_hit: bool` |
| `RunRecord` | `run_id: str` (uuid4), `started/finished: datetime`, `org`, `window_days`, `visibility`, `persons_llm: bool`, `persons_llm_ack: str\|None`, `head_sha: str`, `graph_sha256: str` (of `graph.yaml`), `provider: azure`, `deployment: str`, `prompt_versions: dict[str,str]`, `api_calls_estimated: int`, `api_calls_actual: int`, `llm_calls_estimated: int`, `llm_calls_actual: int`, `coverage: CoverageRecord`, `artifact_sha256: dict[str,str]`, `canaries: {repo: pass, jira: pass}` |

JSONL columns = the model fields in declaration order; `ai_tools.csv` columns
= `AIToolRow` fields with `evidence` `;`-joined.

Failure semantics: structural failures (identity mismatch, duplicate,
malformed bundle, invalid model schema, overflow, canary miss) → raise → no
artifact. A contained model failure (`on_error: skip` on the classify maps)
becomes a typed `status=map_failed` row that the reconciliation step counts
and that coverage reports; the run continues only if
`map_failed ≤ MAX_MAP_FAILED` (5), else raise.

### Ceilings (R-3) — numeric, frozen, N succeeds / N+1 aborts before LLM spend

| Ceiling | Value |
| --- | --- |
| `MAX_REPOS` (active, after filter) | 400 (discover requests +1, overflow → abort) |
| `MAX_PROJECTS` (Jira visible) | 150; `MAX_PROJECT_PAGES` 4 (×50) |
| `MAX_ISSUES` per project | 30 |
| `MAX_MANIFESTS` / `MAX_WORKFLOWS` per repo | 6 / 5 |
| `MAX_SEARCH_TERMS` / `MAX_SEARCH_RESULTS` | 12 / 100 |
| `MAX_BUNDLE_CHARS` | 6000 |
| map `max_items` (all six maps) | 400 (gh), 150 (jira), `top_persons` ≤ 60 |
| `MAX_LLM_CALLS` | 400 + 150 + 60 + 2 = 612 (estimated in preflight from ceilings; actual recorded) |
| `MAX_API_CALLS` | 4 000 (GitHub, one hour of core budget minus headroom) + 400 (Jira) |
| `config.max_concurrency` | 4 |
| `config.timeout` | 5400 s |

### Canaries (R-3)

Two committed fixture families in `examples/demos/org_ai_dossier/canaries/`,
withheld from prompts, injected by the reducer BEFORE ledger acceptance:

- **repo family:** three synthetic `GitHubBundle`s with known answers — (a)
  `package.json` line `"openai": "^4"` + `.github/copilot-instructions.md`
  → `both`, tools ⊇ {openai/provider, copilot/coding_agent}; (b) README
  mentions "AI-powered" but no manifest/instruction/workflow evidence →
  `unclear` (the reducer must demote any claim); (c) plain library → `none`.
- **jira family:** two synthetic `JiraBundle`s — (a) issues with "Copilot
  rollout" + `ai_term_count > 0` → `dev_tooling` with evidence issue keys;
  (b) no AI terms → `none`.

The classify prompts are run on the canaries as extra map items (marked by a
reserved id prefix `__canary__/`) and stripped before ledgers; a miss on
ANY canary → raise → no artifact.

### LLM nodes (Azure, temperature 0, schema-validated, one judgement each)

- `classify_repo_ai.yaml` (`PROMPT_VERSION classify_repo_ai.v1`) — input:
  `GitHubBundle` JSON. Output schema: `purpose`, `ai_usage`, `ai_tools[]`,
  `rationale`. Reducer drops any tool whose `evidence_path` ∉ bundle paths
  and demotes `ai_usage` to `unclear` when none survive.
- `classify_jira_ai.yaml` (`v1`) — same shape; evidence = issue key ∈ bundle.
- `summarize_person.yaml` (`v1`) — input: ONE source-qualified `PersonRow`
  footprint (repos + their purpose sentences OR projects + their purpose
  sentences; never both sources). Output: `summary` (2–3 sentences).
  Bounded: no seniority, performance, workload, sentiment, intent, no
  cross-system identity claim, no comparison to other persons, nothing
  outside the footprint. Reducer rejects summaries that name a repo/project
  outside the footprint, mention another person id/label, or contain any of
  the banned-claim markers (frozen regex list in `tools.py`).
- `synthesize_findings.yaml` (`v1`) and `synthesize_onepager.yaml` (`v1`) —
  over code-reduced tables with row ids; every cited id must exist in a
  ledger (FR-895 citation boundary); onepager must contain exactly three
  findings and ≤ 800 words (code-counted) or the run fails.

### Coverage and output measurements (R-4)

Denominators are frozen names from `CoverageRecord`. Rendered percentages
are ALWAYS `n of <denominator-name>=<value>` and the `unclear` and
`map_failed` counts are shown beside every AI-use share. When
`api_total is None`, the coverage block prints `org API total: unavailable`
and no completeness ratio. `run.json.head_sha` + `graph_sha256` identify
the graph (a commit SHA alone would not identify an uncommitted file).

### Persons (R-5, R-6) — disposition against FR-962

- Identities are source-qualified (`github:<login>`, `jira:<accountId>`);
  display names are labels. **No `same_person`, no e-mail/display-name
  equality, no union rank.** Two rankings with the frozen score formulas
  above, each cut at `top_persons`.
- `persons_llm` is a **required, no-default** runtime input. `false` →
  `prepare_person_input` sets `persons_llm_active=false`, the summary map
  is bypassed, the person section is mechanical. `true` → preflight
  requires a non-empty `persons_llm_ack` string (recorded verbatim in
  `run.json`), else fails before any fetch. Smoke always runs `false`.
- README reproduces the FR-962 warning block verbatim and names the
  operator as accountable controller.
- The human policy answer (judgement R-6 / C-6) is recorded in § Decisions 5.

### Locality (R-7)

- Discovery enforces the visibility policy (`visibility` var, no default)
  before extraction; smoke README command passes `public` and the demo test
  asserts the committed `demo-output.log` shows only `sheikkinen/` ids.
- Preflight resolves `out_dir` with `Path.resolve(strict=False)` and requires
  it to be strictly beneath `<repo>/research/org-ai-dossier/` (real path;
  symlink escapes and `..` rejected), and requires that
  `git check-ignore -q research/org-ai-dossier` succeeds — else fail before
  any fetch. Smoke `out_dir` is `tmp/org-ai-dossier-smoke/` (allowed as the
  second root, smoke preflight only).
- Mechanical locality audit `tests/unit/test_fr1027_locality_audit.py`
  scans `graph.yaml`, prompts, README, fixtures, canaries,
  `demo-output.log`, and tool manifests for: any GitHub owner other than
  `sheikkinen` in commands/fixtures, any `*.atlassian.net` host, any
  `[A-Z]{2,}-\d+` issue key outside the synthetic fixture namespace
  (`DEMO-`), any `@`-e-mail, any output root outside the two allowed roots.

## Acceptance Criteria (judgement AC-01..AC-20, frozen)

- [ ] AC-01: FR retains the five-class research record, preserved dissent,
      prior-art dispositions, `is_this_a_graph` answer.
- [ ] AC-02: graph.yaml matches § Frozen topology exactly (state keys, slots,
      edges, reducer order, write boundary); test asserts node/edge/slot
      sets and that no LLM node lacks `provider: azure` / `temperature: 0`.
- [ ] AC-03: live and smoke commands bind explicit preflight/discovery/
      extraction manifests; live preflight validates Azure, `gh auth`,
      visibility, Jira env, `persons_llm` (+ack), `out_dir` root before any
      fetch; smoke preflight skips only the Jira env check. Unit test per
      check, plus a marker-file test proving no adapter ran on failure.
- [ ] AC-04: every LLM node `provider: azure`, deployment from `AZURE_MODEL`,
      `temperature: 0`, no `fallback`; every map has numeric `max_items`.
- [ ] AC-05: `gh_org_active_discover` — visibility rejection, archived,
      out-of-window, malformed timestamp, duplicate id, sorted unique
      output, `MAX_REPOS+1` → `OverflowError` (mocked `gh`).
- [ ] AC-06: `gh_repo_ai_extract` — typed `GitHubBundle`; tests: missing
      auth, command failure, malformed JSON, manifest/workflow caps, tree
      truncation flag, bot flags, 404 → `absent`, final size ≤ cap.
- [ ] AC-07: `gh_org_code_search` — term/result/rate ceilings (mocked clock),
      `capped` flag, reducer maps hits only onto active ids, others →
      `search_caveats`.
- [ ] AC-08: `jira_active_discover` — pagination, `isLast`, page-cap
      overflow, JQL encoding, key regex, sorted unique, dormant accounting
      via `coverage_jira` (mocked HTTP).
- [ ] AC-09: `jira_project_extract` — typed `JiraBundle`; ≤30 issues,
      accountId-keyed persons, ADF flattening + 300-char cap, top-10, AI-term
      clauses, non-2xx raise, 429 single retry, timeout, size ≤ cap.
- [ ] AC-10: reducer reconciles every discovered id exactly once; fixtures
      for missing id, duplicate id, extra id, malformed bundle, invalid
      model schema → raise; `map_failed` rows typed and counted;
      `> MAX_MAP_FAILED` → raise.
- [ ] AC-11: evidence reconciliation drops unsupported tools / demotes to
      `unclear` (fixtures accepted + rejected); both canary families pass on
      correct answers and a planted miss aborts the run.
- [ ] AC-12: ceilings enforced: N succeeds, N+1 emits no artifact (repos,
      projects/pages, issues, manifests, workflows, search terms/results,
      bundle chars, LLM calls, API calls); `run.json` records estimated vs
      actual calls, hashes, provider/deployment, prompt versions, run id,
      timestamps, coverage flags.
- [ ] AC-13: renderers print `n of <denominator>=<value>` for every share,
      show `unclear`/`map_failed`, print `unavailable` when `api_total` is
      None — in `run.json`, `onepager.md`, `dossier.md`, `repos.md`,
      `jira.md`.
- [ ] AC-14: `onepager.md` ≤ 800 words (code-counted), exactly three cited
      findings, coverage block, active counts, AI shares, top tools, two
      person lists, method/date, caveats.
- [ ] AC-15: persons source-qualified; two rankings with frozen formulas;
      `same_person` does not exist in any model; no combined rank.
- [ ] AC-16: `persons_llm` required (missing → preflight fail); `false`
      bypasses the summary map (routing test) and renders mechanical
      tables; `true` requires `persons_llm_ack`, records it, and the summary
      boundary rejects out-of-footprint / other-person / banned-claim text.
- [ ] AC-17: smoke = `sheikkinen`, `visibility=public`, Jira fixtures,
      `persons_llm=false`, `out_dir=tmp/org-ai-dossier-smoke/`; locality
      audit passes on all committed artifacts.
- [ ] AC-18: live `out_dir` must resolve beneath gitignored
      `research/org-ai-dossier/` (tests: tracked path, `..`, symlink escape
      → preflight fail); any preflight/reconciliation/canary failure leaves
      no file under `out_dir` (temp-dir + atomic rename test).
- [ ] AC-19: 10 raw `classify_repo_ai` and 5 raw `classify_jira_ai` outputs
      read before aggregate acceptance; cited in § Implementation Record
      with provider/deployment and one concrete surprising detail each.
- [ ] AC-20: `tmp/draft-authoring-report.md` substantive (lint + smoke);
      tests `@pytest.mark.req("REQ-YG-670")`; `CAP-266` / `REQ-YG-670`
      confirmed free by grep over `capabilities/`, `ARCHITECTURE.md`, and all
      `origin/*` branches immediately before the allocating commit;
      `req_coverage.py --strict`, changelog fragment, FR record, diary.
- [x] `FR-1027.research.md` promoted and dispositioned (2026-09-07).

## Research Disposition (FR-1027.research.md, five rows)

| persona | finding | disposition |
| --- | --- | --- |
| os-infra-primitivist | one local command, gitignored outputs, Jira adapter on the MCP env names, Azure forced by preflight, fail closed before any fetch | **adopted** — preflight + enforced `out_dir` root + env contract |
| data-process-planner | change the output shape to ledgers + dossier + onepager with explicit coverage and citations | **adopted** — § Ideal Result; typed `CoverageRecord`; denominators are ACs |
| yamlgraph-native-planner | corpus-census discover/extract/map-reduce with invocation-time slots, code joins, one Azure tail | **adopted** — `is_this_a_graph` = yes (corpus-census family); two bounded tails, not one (R-1) |
| subtractionist | delete the cross-org person ranking; keep a bounded "key contributors" list per project | **partially adopted, dissent preserved** — the judge's R-5 sided with it on the JOIN (no cross-system identity, no union rank); the operator kept per-source rankings and authorized summaries (§ Decisions 5). `persons_llm=false` is exactly the subtractionist's shape. |
| librarian | external precedent: Jira MCP connector + development context (commits/PRs) | **acknowledged, not adopted as route** — MCP not callable from a graph; REST adapter reuses the MCP env names; dev-panel join deferred |

## Alternatives Considered (probed 2026-09-07 unless marked)

| Alternative | Probe / evidence | Verdict |
| --- | --- | --- |
| Hand-written dossier per repo (`research/shared-ai-capabilities/findings.md` precedent) | one repo took one session; active corpus is O(200) repos | Rejected — `impossibly_large_sequential_task` |
| GitHub Copilot org metrics / seat API | `gh api /orgs/<org>/copilot/billing` → 404, needs `admin:org`; answers Copilot seats only | Rejected — operator escalation to an org admin; complementary |
| Org-wide code search as the ONLY AI signal | works on the private org (five keywords, 3–17 repos each); 10/min; capped 100/keyword; default branch only | Partially adopted — one discover-side signal, reconciled by code |
| Jira dev-panel API join | per-issue; thousands of in-window issues | Deferred; judge: not authorized under this FR |
| Editor Atlassian MCP directly | not callable from a graph; not repeatable | Rejected as route; env names reused |
| Extend `repo_census` in place | FR-899 contract frozen | Rejected — sibling graph |
| Provider: default/Copilot | operator decision | Rejected — corp data governance |
| Jira scope: all visible projects | operator decision | Rejected — dormant listed in coverage |

## Decisions (operator, 2026-09-07)

1. ~~`persons_llm` default `true`~~ → superseded by judgement R-6: **no
   default**, required input; see 5.
2. `gh_org_code_search` keyword list **includes Finnish terms**.
3. Rendered output is **split**: `dossier.md` + `repos.md` + `jira.md`.
4. Research route unblock via **another provider** → FR-1028 (done).
5. **R-6 / C-6 human policy answer (2026-09-07, operator):** "Yes —
   authorized": the employer's applicable policy authorizes org-scale LLM
   summaries of colleagues from GitHub/Jira work-system facts for this
   management use, under the bounded source-separated summary contract; the
   operator is the accountable controller and supplies `persons_llm_ack` at
   each live run. `persons_llm=true` is therefore authorized for live use;
   smoke stays `false`.
6. Proceed with the judge's frozen scope (D-1..D-9) in this arc.

## Implementation Record

**Commits (worktree `feat/fr1027-org-ai-dossier`):**

| Step | RED | GREEN | Scope |
| --- | --- | --- | --- |
| Adapters (D-2, D-3) | `cc3108a4` | `cfdb3b05` | `gh_ai_adapters.py`, `jira_adapters.py`, 9 manifests, Jira smoke fixtures (relocated to `corpus_census/adapters/fixtures/jira/` — the demo audit forbids any file under a demo dir before its README/graph exist) |
| Tools + graph (D-1, D-4, D-5, D-7, D-8) | `78127455` | `578ada5c` | `graph.yaml` + 5 prompts + README via `scripts/author.sh` (brief `authoring-briefs/fr-1027-org-ai-dossier-brief.md`, report verified by artifact); `preflight.py` (path-loaded, ceilings mirrored + asserted), `models.py`, `reduce.py`, `render.py`, `docs.py`, `canaries.py`; public smoke → `demo-output.log`; topology + locality audit |
| Live-run fixes | — | `2fafd2ea` | `MAX_LISTED=1000` (cheap listing) separated from `MAX_REPOS=400` (active/LLM spend); `on_error: skip` error findings contained as `map_failed` rows |

**Deviations from the frozen plan (all narrowing or mechanical):**

- Jira fixtures live under `examples/demos/corpus_census/adapters/fixtures/jira/`
  (not `org_ai_dossier/fixtures/`): the examples README audit scans the
  filesystem and rejects a demo dir without README + graph, so adapter fixtures
  had to ship with the adapters.
- `preflight` is its own module `preflight.py` (not `tools.py`): slot manifests
  are path-loaded without the repo root on `sys.path`, so the preflight module is
  stdlib-only with ceilings mirrored from `models.py` and a test asserting
  equality (`test_preflight_ceiling_mirrors_match_models`).
- `gh_org_active_discover` accepts `org` + `window_days` state keys as well as
  `source` — yamlgraph templates resolve one placeholder per string, so the
  brief's `"{state.org}:{state.window_days}"` resolves to `None`.
- Code-search hits are filtered by the visibility policy at the adapter (the
  first smoke put private repo names of the demo owner into a public-only log).
- Out-of-set search hits are COUNTED in caveats, never named (same reason).
- Demo proofs are stripped of provider-endpoint httpx lines (`*.cognitiveservices.azure.com`
  etc.) before commit — the Azure endpoint hostname is corp infrastructure in a
  public repo (operator instruction 2026-09-07); the locality audit now rejects
  any provider endpoint host in committed artifacts, including the
  `corpus_census` proof (38 such lines were in the first committed proof).
- Demo proof runs without `--full`: the gate's fatal-marker regex
  `Node .+ failed` is greedy across a dumped state line and matched README
  prose inside a bundle (`node … A failed send`). Not a defect in this FR;
  recorded for the gate's owner.
- Ceiling split: the org lists ~590 repos but only ~200 are active; the
  judge's "N+1 aborts before LLM spend" applies to the LLM-spend ceiling
  (active repos), while the single listing call has its own cheap ceiling.

**Raw-output read (AC-19) — public smoke, `azure/aaa-gpt-5.4-mini`, 2026-09-07:**

Ten `classify_repo_ai` and two `classify_jira_ai` raw findings read end-to-end
(`ledgers/raw_*.jsonl` are now written on every run for this purpose). What
the read changed in CODE before any aggregate was trusted:

1. Tool names drift: `Copilot`, `GitHub Copilot`, `GitHub Copilot CLI`,
   `copilot instructions` for one tool; `Anthropic Claude` as a provider →
   `canonical_tool_name` at the reducer boundary (`junk_drawer_cap`).
2. `evidence_path: "README excerpt"` / `"README.md"` for tools only mentioned
   in prose → correctly dropped by the evidence boundary; the row demotes to
   `unclear` (3 of 10 repos) — the canary family (b) exists for exactly this.
3. Instruction-file paths returned as tool NAMES (`.github/skills/`,
   `AGENTS.md`) → canonicalized to `agent-skills` / `agents-md`.
4. `actions-user` ranked #2 person with score 5 → added to bot markers.
5. Synthesis claims echoed `row:…` ids inside the prose → stripped by the
   renderer; citations stay in brackets.
6. The Jira canary (a) was classified `both` on the first pass (the reviewer
   considered "AI-assisted ticket summarization" product use) — the canary
   expects `dev_tooling`; the prompt was not changed, the fixture makes the
   evidence unambiguous, and the live run's canary check remains the witness.
7. Onepager landed at 468–556 words of the 800 budget with 3 findings.
8. Coverage on the public owner: `api_total: unavailable` (org endpoint 404
   for a user account) rendered exactly as R-4 requires.

Live-run raw read (10 repo + 5 Jira from `research/…/ledgers/raw_*.jsonl`):
_pending — run in progress; recorded on completion._

**Observed, not fixed (out of scope):**

- `tests/unit/test_ramp_installer.py::test_wrapper_delegates` depends on
  `.venv` being on `PATH` (bare `python3`).
- `.venv/bin/yamlgraph` is the main checkout's editable install; worktree
  runs need a `python -m yamlgraph.cli` shim (also hit by FR-1028 AC-10).
- Azure deployment rate limit: ~530 HTTP 429s vs 240 200s at
  `max_concurrency: 4`; the client's retry absorbed all but 2 of ~200
  classifications. Lowering concurrency is a graph edit (author.sh route),
  deferred.

## Related

- [FR-892](FR-892-corpus-census-pipeline-injected-adapters.md),
  [FR-899](FR-899-org-repo-census-azure.md),
  [FR-962](FR-962-person-profile-census-authored-prs.md),
  [FR-1028](FR-1028-graph-run-provider-model-override.md), FR-874 (rejected)
- [examples/demos/repo_census/](../examples/demos/repo_census/),
  [examples/demos/person_profile_census/](../examples/demos/person_profile_census/),
  [examples/demos/corpus_census/adapters/](../examples/demos/corpus_census/adapters/)
- [reference/patterns/corpus-map-reduce.md](../reference/patterns/corpus-map-reduce.md)
- Gitignored: `research/org-ai-dossier/sizing.md` (probes, counts, cost order)
